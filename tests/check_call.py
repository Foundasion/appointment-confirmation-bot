#!/usr/bin/env python3
"""
Script to check the transcript and outcome for an existing call SID.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv('PORT', 5050))
SERVER_URL = f"http://localhost:{PORT}"


def check_call(call_sid: str, server_url: str = SERVER_URL):
    """Check the transcript and outcome for a call."""
    print(f"Checking call with SID: {call_sid}")
    
    # Get call status using the API endpoint
    try:
        status_response = requests.get(f"{server_url}/call-status/{call_sid}")
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
        transcript_response = requests.get(f"{server_url}/call-transcript/{call_sid}")
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
        outcome_response = requests.get(f"{server_url}/call-outcome/{call_sid}")
        if outcome_response.status_code == 200:
            outcome_data = outcome_response.json()
            outcome = outcome_data.get('outcome')
            print(f"\nOutcome: {outcome}")
        else:
            print(f"\nFailed to get outcome: {outcome_response.status_code}")
            print(outcome_response.text)
    except Exception as e:
        print(f"\nError getting outcome: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check call transcript and outcome.")
    parser.add_argument('--call-sid', required=True, help="The SID of the call to check")
    parser.add_argument('--server-url', help=f"URL of the server (default: {SERVER_URL})")
    args = parser.parse_args()
    
    server_url = args.server_url if args.server_url else SERVER_URL
    check_call(args.call_sid, server_url)
