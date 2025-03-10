#!/usr/bin/env python3
"""
Test script for verifying call transcript and outcome functionality.
This script makes a test call and then retrieves the transcript and outcome.
"""

import os
import sys
import json
import asyncio
import argparse
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appointment_bot.database import Database
from appointment_bot.twilio_handler import TwilioHandler
from appointment_bot.test_call import make_test_call


async def test_transcript_and_outcome(phone_number: str, appointment_id: str = None, wait_time: int = 60):
    """Make a test call and then retrieve the transcript and outcome."""
    print(f"Making test call to {phone_number}...")
    
    # Make the call
    call_sid = await make_test_call(phone_number, appointment_id)
    
    if not call_sid:
        print("Failed to get call SID. Cannot proceed with transcript test.")
        return
    
    print(f"Call initiated with SID: {call_sid}")
    print(f"Waiting {wait_time} seconds for the call to complete...")
    
    # Wait for the call to complete
    for i in range(wait_time):
        # Print a progress indicator every 5 seconds
        if i % 5 == 0:
            print(f"Waited {i} seconds...")
        time.sleep(1)
    
    print("Wait time completed. Retrieving call data...")
    
    # Initialize the TwilioHandler
    twilio_handler = TwilioHandler()
    
    # Get call status
    status = twilio_handler.get_call_status(call_sid)
    print(f"\nCall Status:")
    print(json.dumps(status, indent=2))
    
    # Get transcript
    transcript = twilio_handler.get_call_transcript(call_sid)
    print(f"\nTranscript ({len(transcript)} items):")
    if transcript:
        for item in transcript:
            role = item.get('role', 'unknown')
            content = item.get('content', '')
            print(f"{role.capitalize()}: {content}")
    else:
        print("No transcript available.")
    
    # Get outcome
    outcome = twilio_handler.get_call_outcome(call_sid)
    print(f"\nOutcome: {outcome}")
    
    print("\nTest completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test call transcript and outcome functionality.")
    parser.add_argument('--phone', required=True, help="The phone number to call, e.g., '+1234567890'")
    parser.add_argument('--appointment', help="Optional appointment ID to use")
    parser.add_argument('--wait', type=int, default=60, help="Time to wait for call completion (seconds)")
    args = parser.parse_args()
    
    asyncio.run(test_transcript_and_outcome(args.phone, args.appointment, args.wait))
