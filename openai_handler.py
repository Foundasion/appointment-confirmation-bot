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
You are an AI assistant for a doctor's office making calls to confirm patient appointments.
Your task is to:
1. Greet the patient by name and identify yourself as calling from [Doctor's Office]
2. Confirm their upcoming appointment (date, time, doctor)
3. If they confirm, thank them and end the call
4. If they need to reschedule, collect their preferred date/time
5. Be professional, friendly, and concise
6. Do not discuss medical details or personal health information
7. End the call with a clear summary of the outcome (confirmed or rescheduled)

Always disclose that you are an AI assistant calling on behalf of the doctor's office.
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
        print('Sending session update:', json.dumps(session_update))
        await openai_ws.send(json.dumps(session_update))
    
    async def send_initial_conversation_item(self, openai_ws: websockets.WebSocketClientProtocol) -> None:
        """Send initial conversation item to start the call."""
        greeting = "Hello, I'm calling from "
        
        if self.appointment_data:
            doctor = self.appointment_data.get('doctor', 'the doctor')
            patient_name = self.appointment_data.get('patient_name', 'there')
            date = self.appointment_data.get('date', 'your upcoming appointment')
            time = self.appointment_data.get('time', '')
            
            greeting = (
                f"Hello, may I speak with {patient_name}? This is an AI assistant calling "
                f"on behalf of {doctor}'s office. I'm calling about your appointment "
                f"scheduled for {date} at {time}. I'd like to confirm if you're still "
                f"able to make this appointment or if you need to reschedule."
            )
        else:
            greeting += "the doctor's office. I'm an AI assistant calling to confirm your upcoming appointment."
        
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
        
        # Log specific event types
        if response['type'] in LOG_EVENT_TYPES:
            print(f"Received event: {response['type']}", response)
        
        # Handle text content for transcript
        if response['type'] == 'response.content.delta' and 'delta' in response:
            content = response['delta'].get('content', '')
            if content:
                self.conversation_transcript.append({"role": "assistant", "content": content})
                
                # Check for appointment confirmation or rescheduling in the response
                lower_content = content.lower()
                if "confirm" in lower_content and "appointment" in lower_content:
                    self.call_outcome = "confirmed"
                elif "reschedule" in lower_content:
                    self.call_outcome = "rescheduled"
        
        return response
    
    def get_transcript(self) -> list:
        """Get the conversation transcript."""
        return self.conversation_transcript
    
    def get_call_outcome(self) -> Optional[str]:
        """Get the outcome of the call (confirmed, rescheduled, or None)."""
        return self.call_outcome
