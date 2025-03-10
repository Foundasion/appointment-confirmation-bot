#!/usr/bin/env python3
"""
Script to check the transcript and outcome for an existing call SID.
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appointment_bot.twilio_handler import TwilioHandler


def check_call(call_sid: str):
    """Check the transcript and outcome for a call."""
    print(f"Checking call with SID: {call_sid}")
    
    # Initialize the TwilioHandler
    twilio_handler = TwilioHandler()
    
    # Get call status
    status = twilio_handler.get_call_status(call_sid)
    print(f"\nCall Status:")
    print(json.dumps(status, indent=2) if status else "Call not found")
    
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check call transcript and outcome.")
    parser.add_argument('--call-sid', required=True, help="The SID of the call to check")
    args = parser.parse_args()
    
    check_call(args.call_sid)
