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
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appointment_bot.test_call import make_test_call

# Configuration
PORT = int(os.getenv('PORT', 5050))
SERVER_URL = f"http://localhost:{PORT}"


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
    
    # Get call status using the API endpoint
    try:
        status_response = requests.get(f"{SERVER_URL}/call-status/{call_sid}")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"\nCall Status:")
            print(json.dumps(status, indent=2))
        else:
            print(f"\nFailed to get call status: {status_response.status_code}")
            print(status_response.text)
    except Exception as e:
        print(f"\nError getting call status: {e}")
    
    # Get transcript using the API endpoint
    try:
        transcript_response = requests.get(f"{SERVER_URL}/call-transcript/{call_sid}")
        if transcript_response.status_code == 200:
            transcript_data = transcript_response.json()
            transcript = transcript_data.get('transcript', [])
            print(f"\nTranscript ({len(transcript)} items):")
            if transcript:
                for item in transcript:
                    role = item.get('role', 'unknown')
                    content = item.get('content', '')
                    print(f"{role.capitalize()}: {content}")
            else:
                print("No transcript available.")
        else:
            print(f"\nFailed to get transcript: {transcript_response.status_code}")
            print(transcript_response.text)
    except Exception as e:
        print(f"\nError getting transcript: {e}")
    
    # Get outcome using the API endpoint
    try:
        outcome_response = requests.get(f"{SERVER_URL}/call-outcome/{call_sid}")
        if outcome_response.status_code == 200:
            outcome_data = outcome_response.json()
            outcome = outcome_data.get('outcome')
            print(f"\nOutcome: {outcome}")
        else:
            print(f"\nFailed to get outcome: {outcome_response.status_code}")
            print(outcome_response.text)
    except Exception as e:
        print(f"\nError getting outcome: {e}")
    
    print("\nTest completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test call transcript and outcome functionality.")
    parser.add_argument('--phone', required=True, help="The phone number to call, e.g., '+1234567890'")
    parser.add_argument('--appointment', help="Optional appointment ID to use")
    parser.add_argument('--wait', type=int, default=60, help="Time to wait for call completion (seconds)")
    parser.add_argument('--server-url', help=f"URL of the server (default: {SERVER_URL})")
    args = parser.parse_args()
    
    if args.server_url:
        SERVER_URL = args.server_url
    
    asyncio.run(test_transcript_and_outcome(args.phone, args.appointment, args.wait))
