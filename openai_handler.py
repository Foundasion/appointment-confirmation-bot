import os
import json
import base64
import asyncio
import websockets
from typing import Dict, Any, Optional, Callable, Awaitable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VOICE = os.getenv('VOICE', 'alloy')

# Event types to log
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

# System message for appointment confirmation
APPOINTMENT_SYSTEM_MESSAGE = """
You are Samantha, a cheerful and friendly AI assistant for DentaVille Dental Clinic making calls to confirm patient appointments.

Your personality:
- Warm, upbeat, and personable - like talking to a friendly receptionist
- Conversational but professional
- Empathetic and understanding when patients need to reschedule
- Enthusiastic about helping patients

Your task is to:
1. Start by immediately identifying yourself: "Hi, this is Samantha, an automated assistant calling from DentaVille Dental Clinic"
2. Ask if it's a good time to talk about their upcoming appointment
3. Confirm their upcoming appointment (date, time, dentist)
4. If they confirm, express genuine appreciation and end the call warmly
5. If they need to reschedule, be understanding and help find a convenient alternative time
6. Do not discuss medical details or personal health information
7. End the call with a clear summary of the outcome (confirmed or rescheduled) and a friendly closing

Always disclose that you are an automated assistant calling on behalf of DentaVille Dental Clinic at the beginning of the call.
"""


class OpenAIRealtimeHandler:
    """Handler for OpenAI Realtime API interactions."""
    
    def __init__(self, appointment_data: Dict[str, Any] = None):
        """Initialize the handler with appointment data."""
        self.appointment_data = appointment_data or {}
        self.conversation_transcript = []
        self.call_outcome = None
    
    async def connect_to_openai(self) -> websockets.WebSocketClientProtocol:
        """Connect to the OpenAI Realtime API."""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not set. Please set it in the .env file.")
        
        return await websockets.connect(
            'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        )
    
    async def initialize_session(self, openai_ws: websockets.WebSocketClientProtocol) -> None:
        """Initialize the OpenAI session with appointment context."""
        # Create a custom system message with appointment details
        system_message = APPOINTMENT_SYSTEM_MESSAGE
        
        if self.appointment_data:
            # Add appointment-specific details to the system message
            system_message += f"\n\nAppointment Details:\n"
            system_message += f"Patient Name: {self.appointment_data.get('patient_name', 'the patient')}\n"
            system_message += f"Doctor: {self.appointment_data.get('doctor', 'the doctor')}\n"
            system_message += f"Date: {self.appointment_data.get('date', 'the scheduled date')}\n"
            system_message += f"Time: {self.appointment_data.get('time', 'the scheduled time')}\n"
            print(f"Added appointment details to system message: {self.appointment_data}")
        else:
            print("No appointment data available for system message")
        
        # Send session update to OpenAI
        session_update = {
            "type": "session.update",
            "session": {
                "turn_detection": {"type": "server_vad"},
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "voice": VOICE,
                "instructions": system_message,
                "modalities": ["text", "audio"],
                "temperature": 0.7,
            }
        }
        # Print a shorter version of the session update to reduce log noise
        print('Sending session update to OpenAI (instructions truncated for brevity)')
        try:
            await openai_ws.send(json.dumps(session_update))
            print("Session update sent successfully")
            
            # Wait for a response to confirm the session was created
            print("Waiting for session.created event...")
            for _ in range(5):  # Try up to 5 times with a timeout
                try:
                    response_raw = await asyncio.wait_for(openai_ws.recv(), timeout=2.0)
                    response = json.loads(response_raw)
                    print(f"Received response from OpenAI: {response}")
                    
                    if response.get('type') == 'session.created':
                        print("Session created successfully!")
                        return
                    elif response.get('type') == 'error':
                        print(f"Error from OpenAI: {response}")
                        raise Exception(f"OpenAI error: {response.get('error', {}).get('message', 'Unknown error')}")
                except asyncio.TimeoutError:
                    print("Timeout waiting for OpenAI response, retrying...")
            
            print("Failed to receive session.created event after multiple attempts")
        except Exception as e:
            print(f"Error sending session update to OpenAI: {e}")
            raise
    
    async def send_initial_conversation_item(self, openai_ws: websockets.WebSocketClientProtocol) -> None:
        """Send initial conversation item to start the call."""
        if self.appointment_data:
            dentist = self.appointment_data.get('doctor', 'your dentist')
            patient_name = self.appointment_data.get('patient_name', 'there')
            date = self.appointment_data.get('date', 'your upcoming appointment')
            time = self.appointment_data.get('time', '')
            
            greeting = (
                f"Hi there! This is Samantha, an automated assistant calling from DentaVille Dental Clinic. "
                f"Is this {patient_name}? I'm calling about your dental appointment with Dr. {dentist} "
                f"scheduled for {date} at {time}. Is now a good time to chat for a moment?"
            )
        else:
            greeting = (
                f"Hi there! This is Samantha, an automated assistant calling from DentaVille Dental Clinic. "
                f"I'm calling about your upcoming dental appointment. Is now a good time to chat for a moment?"
            )
        
        initial_conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": greeting
                    }
                ]
            }
        }
        await openai_ws.send(json.dumps(initial_conversation_item))
        await openai_ws.send(json.dumps({"type": "response.create"}))
        
        # Add to transcript
        self.conversation_transcript.append({"role": "assistant", "content": greeting})
    
    async def process_openai_message(self, message: str) -> Dict[str, Any]:
        """Process a message from OpenAI."""
        response = json.loads(message)
        
        # Handle text content for transcript
        if response['type'] == 'response.content.delta' and 'delta' in response:
            content = response['delta'].get('content', '')
            if content:
                self.conversation_transcript.append({"role": "assistant", "content": content})
                print(f"AI: \"{content}\"")
                
                # Check for appointment confirmation or rescheduling in the response
                lower_content = content.lower()
                if "confirm" in lower_content and "appointment" in lower_content:
                    self.call_outcome = "confirmed"
                elif "reschedule" in lower_content:
                    self.call_outcome = "rescheduled"
        # Log only error events
        elif response['type'] == 'error':
            print(f"Received error from OpenAI: {response}")
        
        return response
    
    def get_transcript(self) -> list:
        """Get the conversation transcript."""
        return self.conversation_transcript
    
    def get_call_outcome(self) -> Optional[str]:
        """Get the outcome of the call (confirmed, rescheduled, or None)."""
        return self.call_outcome
