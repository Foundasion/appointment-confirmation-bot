# OpenAI Realtime API Integration Not Working in Outbound Calls

## Problem Description
When making outbound calls with the appointment confirmation bot, the call connects successfully but the OpenAI voice assistant is not heard. WebSocket connections are established but immediately close without error messages.

## Steps to Reproduce
1. Configure `.env` file with valid Twilio and OpenAI credentials
2. Start ngrok: `ngrok http 5050`
3. Update the `DOMAIN` variable in `.env` with the ngrok URL (without https://)
4. Start the server: `python run.py`
5. In another terminal, make a test call: `python test_call.py --phone "+1XXXXXXXXXX"`
6. Answer the call when it comes in
7. Observe that the call connects but no AI voice is heard

## Current Behavior
- Call is initiated successfully and connects
- WebSocket connections are established but immediately close
- No error messages are displayed in the server logs
- No AI voice is heard on the call

## Expected Behavior
- Call connects and the AI assistant introduces itself
- The conversation proceeds as expected with the AI responding to voice input

## Server Logs
```
INFO:     Started server process [41114]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5050 (Press CTRL+C to quit)
INFO:     ('54.173.155.0', 0) - "WebSocket /media-stream" [accepted]
WebSocket connection accepted
INFO:     connection open
INFO:     connection closed
```

## ngrok Logs
```
HTTP Requests                                                                                            
-------------                                                                                            
                                                                                                         
02:04:35.231 EST GET /media-stream              101 Switching Protocols                                  
02:02:40.930 EST GET /media-stream              101 Switching Protocols 
```

## Potential Issues to Investigate
1. **OpenAI Realtime API Access**: Verify that the account has proper access to the Realtime API beta
2. **API Key Permissions**: Check if the API key has the necessary permissions for the Realtime API
3. **WebSocket Error Handling**: Improve error logging in the WebSocket connection code
4. **Audio Format Compatibility**: Verify that the audio format settings match what Twilio and OpenAI expect
5. **Model Availability**: Confirm that the specified model (`gpt-4o-realtime-preview-2024-10-01`) is available and accessible

## Next Steps for Debugging
1. Add more detailed logging to the `app.py` file, especially around the OpenAI WebSocket connection:
   ```python
   # Add this to the handle_media_stream function in app.py, right after the try block starts:
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
           print("Connecting to OpenAI Realtime API...")
           try:
               async with websockets.connect(
                   'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
                   extra_headers={
                       "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                       "OpenAI-Beta": "realtime=v1"
                   }
               ) as openai_ws:
                   print("Connected to OpenAI Realtime API successfully")
                   # Initialize the OpenAI session
                   try:
                       await openai_handler.initialize_session(openai_ws)
                       print("OpenAI session initialized successfully")
                       
                       # Have the AI speak first with appointment context
                       try:
                           await openai_handler.send_initial_conversation_item(openai_ws)
                           print("Initial conversation item sent successfully")
                           
                           # Rest of the code...
   ```

2. Add try/except blocks with explicit error logging in the WebSocket handling code
3. Check the OpenAI API status and ensure the Realtime API is operational
4. Test with different OpenAI voice options (alloy, echo, shimmer)
5. Verify the OpenAI API key works for other OpenAI API calls

## Environment Information
- Python version: 3.9+
- Twilio SDK version: 8.12.0
- OpenAI API version: Latest
- Operating System: macOS
