# Transcript and Outcome Fixes

## Overview

The appointment bot makes calls to patients to confirm or reschedule appointments. After a call is completed, we need to access two key pieces of information:

1. **Call Transcript**: A record of the conversation between the AI assistant and the patient
2. **Call Outcome**: Whether the appointment was confirmed or rescheduled

Currently, there are issues with both of these features:

1. **Transcript Issue**: User responses are not being captured in the transcript
2. **Outcome Issue**: The outcome is not being correctly detected and stored

## Relevant Files

The following files are involved in the transcript and outcome functionality:

- **app.py**: Contains the FastAPI endpoints and WebSocket handler for processing calls
- **twilio_handler.py**: Handles Twilio API interactions and stores call data
- **openai_handler.py**: Processes OpenAI messages and captures transcripts/outcomes
- **test_transcript.py**: Test script for making a call and retrieving the transcript/outcome
- **check_call.py**: Utility script for checking the transcript/outcome of an existing call

## Current Implementation

### Transcript Capture

1. The system initializes a transcript with a system message in `openai_handler.py`
2. The AI's responses are captured in the transcript via the `process_openai_message` method
3. User responses should be captured from Twilio "mark" events with transcript data
4. The transcript is stored in the `TwilioHandler.calls` dictionary

### Outcome Detection

1. The system attempts to detect outcomes based on keywords in the AI's responses
2. Keywords like "confirm" and "reschedule" are used to determine the outcome
3. The outcome is stored in the `TwilioHandler.calls` dictionary

## Issues Identified

### Transcript Issue

- User responses are not appearing in the transcript
- Server logs show no "mark" events with transcript data from Twilio
- Only the AI's side of the conversation is being captured

### Outcome Issue

- The outcome detection is not working correctly
- Keywords may not be comprehensive enough
- The outcome is always `None` even when the appointment is confirmed or rescheduled

## Potential Solutions

### Transcript Issue

Two potential approaches:

1. **OpenAI-based Approach**:
   - Capture user speech transcripts from OpenAI events
   - Listen for `input_audio_buffer.transcription` events (*research OpenAI's real-time API first to see if this is a viable option before implementing*)
   - Add these transcripts to the conversation record

2. **Twilio-based Approach**:
   - Enable Twilio's speech recognition in the TwiML
   - Configure parameters for speech recognition
   - Process the resulting "mark" events with transcript data

### Outcome Issue

- Enhanced keyword detection in both AI responses and user responses
- More comprehensive list of confirmation and rescheduling phrases
- Improved logging to track where and when outcomes are being set

## Testing Methodology

1. Use `test_transcript.py` to make a test call and retrieve the transcript/outcome
2. Use `check_call.py` to check the transcript/outcome of an existing call
3. Analyze server logs for debugging information

## Current Status

- We've improved the outcome detection with more keywords
- We've added more detailed logging for debugging
- We've identified that Twilio is not sending transcript events
- We've identified two potential approaches to fix the transcript issue

## Next Steps

1. Implement one of the transcript capture approaches
2. Test the solution with real calls
3. Refine the outcome detection if needed
4. Consider implementing persistent storage for call data
