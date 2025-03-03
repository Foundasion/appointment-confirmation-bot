import os
import json
import base64
import asyncio
import argparse
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
import websockets
from dotenv import load_dotenv
import uvicorn

# Import our modules
from .database import Database
from .twilio_handler import TwilioHandler
from .openai_handler import OpenAIRealtimeHandler
from .conversation import ConversationManager

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv('PORT', 5050))
DOMAIN = os.getenv('DOMAIN', '')

# Initialize FastAPI app
app = FastAPI(title="Appointment Confirmation Bot")

# Initialize our components
db = Database()
twilio_handler = TwilioHandler()
conversation_manager = ConversationManager(db)

# Store active WebSocket connections
active_connections = {}
active_calls = {}


@app.get("/", response_class=JSONResponse)
async def index_page():
    """Root endpoint to check if the server is running."""
    return {"message": "Appointment Confirmation Bot is running!"}


@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
    
    # Get the caller's phone number
    form_data = await request.form()
    from_number = form_data.get('From', '')
    
    # Look up the caller in our database
    appointment_data = None
    if from_number:
        appointment_data = db.get_next_appointment_for_phone(from_number)
    
    # Create TwiML response
    response = VoiceResponse()
    
    if appointment_data:
        # Personalized greeting
        response.say(f"Hello {appointment_data.get('patient_name', '')}. This is an AI assistant calling from {appointment_data.get('doctor', 'your doctor')}'s office.")
        response.pause(length=1)
        response.say(f"I'm calling about your appointment on {appointment_data.get('date', '')} at {appointment_data.get('time', '')}. Would you like to confirm this appointment?")
    else:
        # Generic greeting
        response.say("Hello. This is an AI assistant calling from the doctor's office.")
        response.pause(length=1)
        response.say("I'm calling about your upcoming appointment. Would you like to confirm or reschedule?")
    
    # Connect to our WebSocket endpoint
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    await websocket.accept()
    print("WebSocket connection accepted")
    
    # Get call data from the start message
    call_sid = None
    appointment_data = None
    
    try:
        # Wait for the start message from Twilio
        message = await websocket.receive_text()
        data = json.loads(message)
        
        if data['event'] == 'start':
            call_sid = data['start']['callSid']
            print(f"Call SID: {call_sid}")
            
            # Store the WebSocket connection
            active_connections[call_sid] = websocket
            
            # Check if this is a call we initiated
            if call_sid in active_calls:
                appointment_data = active_calls[call_sid].get('appointment_data')
            else:
                # For incoming calls, try to get appointment data from the caller's phone number
                # This would be implemented in a real system
                pass
            
            # Initialize OpenAI handler with appointment data
            openai_handler = OpenAIRealtimeHandler(appointment_data)
            
            # Connect to OpenAI
            async with websockets.connect(
                'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
                extra_headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "OpenAI-Beta": "realtime=v1"
                }
            ) as openai_ws:
                # Initialize the OpenAI session
                await openai_handler.initialize_session(openai_ws)
                
                # Have the AI speak first with appointment context
                await openai_handler.send_initial_conversation_item(openai_ws)
                
                # Set up the conversation manager with appointment data
                if appointment_data:
                    conversation_manager.set_appointment(appointment_data)
                
                # Process audio between Twilio and OpenAI
                await process_audio_streams(websocket, openai_ws, openai_handler, call_sid)
                
                # Update call data with transcript and outcome
                if call_sid:
                    transcript = openai_handler.get_transcript()
                    outcome = openai_handler.get_call_outcome()
                    
                    if outcome:
                        twilio_handler.update_call_outcome(call_sid, outcome)
                    
                    if transcript:
                        twilio_handler.update_call_transcript(call_sid, transcript)
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for call {call_sid}")
    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
    finally:
        # Clean up
        if call_sid and call_sid in active_connections:
            del active_connections[call_sid]


async def process_audio_streams(websocket: WebSocket, openai_ws: websockets.WebSocketClientProtocol, 
                               openai_handler: OpenAIRealtimeHandler, call_sid: str):
    """Process audio streams between Twilio and OpenAI."""
    
    async def receive_from_twilio():
        """Receive audio data from Twilio and send it to OpenAI."""
        try:
            async for message in websocket.iter_text():
                data = json.loads(message)
                if data['event'] == 'media' and openai_ws.open:
                    audio_append = {
                        "type": "input_audio_buffer.append",
                        "audio": data['media']['payload']
                    }
                    await openai_ws.send(json.dumps(audio_append))
                elif data['event'] == 'stop':
                    print(f"Call {call_sid} has ended")
                    if openai_ws.open:
                        await openai_ws.close()
                    break
        except WebSocketDisconnect:
            print(f"Twilio WebSocket disconnected for call {call_sid}")
            if openai_ws.open:
                await openai_ws.close()
        except Exception as e:
            print(f"Error receiving from Twilio: {e}")
    
    async def send_to_twilio():
        """Receive events from OpenAI and send audio back to Twilio."""
        try:
            async for openai_message in openai_ws:
                response = await openai_handler.process_openai_message(openai_message)
                
                # Handle audio responses
                if response['type'] == 'response.audio.delta' and response.get('delta'):
                    try:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": call_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)
                    except Exception as e:
                        print(f"Error processing audio data: {e}")
        except Exception as e:
            print(f"Error sending to Twilio: {e}")
    
    # Run both coroutines concurrently
    await asyncio.gather(receive_from_twilio(), send_to_twilio())


@app.post("/make-call")
async def make_outbound_call(request: Request, background_tasks: BackgroundTasks):
    """Make an outbound call to a patient."""
    try:
        data = await request.json()
        to_number = data.get('to_number')
        appointment_id = data.get('appointment_id')
        
        if not to_number:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required parameter: to_number"}
            )
        
        # Get appointment data if an ID was provided
        appointment_data = None
        if appointment_id:
            appointment_data = db.get_appointment_details(appointment_id)
            if not appointment_data:
                return JSONResponse(
                    status_code=404,
                    content={"error": f"Appointment not found with ID: {appointment_id}"}
                )
        
        # Make the call
        call_sid = await twilio_handler.make_call(to_number, appointment_data)
        
        if not call_sid:
            return JSONResponse(
                status_code=400,
                content={"error": "Failed to make call. Check if the number is allowed."}
            )
        
        # Store call information
        active_calls[call_sid] = {
            'to': to_number,
            'appointment_data': appointment_data,
            'status': 'initiated'
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Call initiated successfully",
                "call_sid": call_sid
            }
        )
    
    except Exception as e:
        print(f"Error making call: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


@app.get("/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get the status of a call."""
    status = twilio_handler.get_call_status(call_sid)
    
    if not status:
        return JSONResponse(
            status_code=404,
            content={"error": f"Call not found with SID: {call_sid}"}
        )
    
    return JSONResponse(
        status_code=200,
        content=status
    )


@app.get("/call-transcript/{call_sid}")
async def get_call_transcript(call_sid: str):
    """Get the transcript of a call."""
    transcript = twilio_handler.get_call_transcript(call_sid)
    
    return JSONResponse(
        status_code=200,
        content={"transcript": transcript}
    )


@app.get("/call-outcome/{call_sid}")
async def get_call_outcome(call_sid: str):
    """Get the outcome of a call."""
    outcome = twilio_handler.get_call_outcome(call_sid)
    
    return JSONResponse(
        status_code=200,
        content={"outcome": outcome}
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Appointment Confirmation Bot server.")
    parser.add_argument('--port', type=int, default=PORT, help="Port to run the server on")
    args = parser.parse_args()
    
    print(f"Starting server on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
