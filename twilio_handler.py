import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from twilio.rest import Client
from dotenv import load_dotenv
import time
from pathlib import Path

# Load environment variables
load_dotenv()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
DOMAIN = os.getenv('DOMAIN')


class TwilioHandler:
    """Handler for Twilio API interactions."""
    
    def __init__(self):
        """Initialize the Twilio client."""
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            raise ValueError("Twilio credentials are not set. Please set them in the .env file.")
        
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.calls = {}  # Store active calls by SID
    
    async def check_number_allowed(self, to_number: str) -> bool:
        """Check if a number is allowed to be called."""
        try:
            # Check if it's a Twilio number we own
            incoming_numbers = self.client.incoming_phone_numbers.list(phone_number=to_number)
            if incoming_numbers:
                return True
            
            # Check if it's a verified caller ID
            outgoing_caller_ids = self.client.outgoing_caller_ids.list(phone_number=to_number)
            if outgoing_caller_ids:
                return True
            
            # In a production system, you would implement additional checks here
            # based on your compliance requirements and business rules
            
            # For testing purposes, you can enable this override to allow calls to specific test numbers
            # This is useful for testing with friends' numbers without verifying them in Twilio
            # NOTE: For Twilio trial accounts, you can only call verified numbers unless you upgrade
            TESTING_MODE = os.getenv('TWILIO_TESTING_MODE', 'false').lower() == 'true'
            if TESTING_MODE:
                OVERRIDE_NUMBERS = os.getenv('TWILIO_OVERRIDE_NUMBERS', '').split(',')
                if to_number in OVERRIDE_NUMBERS or OVERRIDE_NUMBERS == ['*']:
                    print(f"TESTING MODE: Allowing call to non-verified number {to_number}")
                    return True
            
            # If we get here, the number is not allowed
            print(f"Number {to_number} is not allowed for outbound calls.")
            print("To fix this, you can:")
            print("1. Verify this number as a caller ID in your Twilio account")
            print("   Visit: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
            print("2. Upgrade to a paid Twilio account to remove this restriction")
            print("3. Enable testing mode by setting TWILIO_TESTING_MODE=true in your .env file")
            print("   and add the number to TWILIO_OVERRIDE_NUMBERS (comma-separated list or '*' for all)")
            
            return False
        except Exception as e:
            print(f"Error checking phone number: {e}")
            return False
    
    async def make_call(self, to_number: str, appointment_data: Dict[str, Any] = None) -> Optional[str]:
        """Make an outbound call to a patient."""
        if not DOMAIN:
            raise ValueError("DOMAIN is not set. Please set it in the .env file.")
        
        # Check if the number is allowed to be called
        is_allowed = await self.check_number_allowed(to_number)
        if not is_allowed:
            print(f"The number {to_number} is not recognized as a valid outgoing number or caller ID.")
            return None
        
        # Create TwiML for the outbound call
        outbound_twiml = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect></Response>'
        )
        
        try:
            # Make the call
            call = self.client.calls.create(
                from_=TWILIO_PHONE_NUMBER,
                to=to_number,
                twiml=outbound_twiml
            )
            
            # Store call information
            self.calls[call.sid] = {
                'to': to_number,
                'status': call.status,
                'appointment_data': appointment_data,
                'transcript': [],
                'outcome': None
            }
            
            print(f"Call initiated with SID: {call.sid}")
            return call.sid
        except Exception as e:
            print(f"Error making call: {e}")
            return None
    
    def get_call_status(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get the status of a call."""
        if call_sid not in self.calls:
            try:
                # Try to fetch from Twilio API
                call = self.client.calls(call_sid).fetch()
                return {
                    'status': call.status,
                    'duration': call.duration,
                    'direction': call.direction,
                    'from': call.from_,
                    'to': call.to,
                    'start_time': call.start_time,
                    'end_time': call.end_time
                }
            except Exception as e:
                print(f"Error fetching call: {e}")
                return None
        
        return self.calls[call_sid]
    
    def update_call_transcript(self, call_sid: str, transcript: List[Dict[str, str]]) -> None:
        """Update the transcript for a call."""
        if call_sid in self.calls:
            self.calls[call_sid]['transcript'] = transcript
    
    def update_call_outcome(self, call_sid: str, outcome: str) -> None:
        """Update the outcome of a call."""
        if call_sid in self.calls:
            self.calls[call_sid]['outcome'] = outcome
            print(f"Call {call_sid} outcome updated to: {outcome}")
    
    def get_call_transcript(self, call_sid: str) -> List[Dict[str, str]]:
        """Get the transcript for a call."""
        if call_sid in self.calls:
            return self.calls[call_sid].get('transcript', [])
        return []
    
    def get_call_outcome(self, call_sid: str) -> Optional[str]:
        """Get the outcome of a call."""
        if call_sid in self.calls:
            return self.calls[call_sid].get('outcome')
        return None
