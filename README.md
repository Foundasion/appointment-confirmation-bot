# Appointment Confirmation Bot

A Python-based system that makes outbound phone calls to patients to confirm or reschedule their appointments using Twilio Voice and OpenAI's Realtime API.

## Features

- **Outbound Calling**: Make automated calls to patients about upcoming appointments
- **Natural Language Conversations**: Use OpenAI's Realtime API for fluid, natural conversations
- **Appointment Confirmation**: Allow patients to confirm their appointments
- **Appointment Rescheduling**: Offer available time slots for rescheduling
- **Call Transcripts**: Record and store conversation transcripts
- **Call Outcomes**: Track the result of each call (confirmed, rescheduled, etc.)

## Prerequisites

- Python 3.9+
- A Twilio account with a phone number that has Voice capabilities
- An OpenAI account with access to the Realtime API
- ngrok or another tunneling solution for local development

## Installation

1. Clone this repository or copy the files to your local machine.

2. Create a virtual environment and activate it:
   ```bash
   cd appointment_bot
   python -m venv appointment_bot_env
   source appointment_bot_env/bin/activate  # On Windows: appointment_bot_env\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the provided `env.example`:
   ```bash
   cp env.example .env
   ```

5. Edit the `.env` file and add your API keys and configuration:
   ```
   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key_here

   # Twilio Configuration
   TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
   TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
   TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

   # Server Configuration
   PORT=5050
   DOMAIN=your_ngrok_domain_here

   # Application Settings
   VOICE=alloy
   ```

## Running the Application

1. Start ngrok to expose your local server:
   ```bash
   ngrok http 5050
   ```

2. Copy the ngrok URL (without the protocol) and update the `DOMAIN` variable in your `.env` file.

3. Start the application:
   ```bash
   python run.py
   ```

4. The server will start on port 5050 (or the port specified in your `.env` file).

## Making Test Calls

You can use the provided test script to make outbound calls:

```bash
# From the appointment_bot directory
python test_call.py --phone "+1234567890"

# Or from the parent directory
python -m appointment_bot.test_call --phone "+1234567890"
```

Replace `+1234567890` with a phone number that is either:
- A Twilio phone number you own
- A verified caller ID in your Twilio account

For testing purposes, you can add your own phone number as a verified caller ID in the Twilio console.

## API Endpoints

The application provides the following API endpoints:

- `GET /`: Check if the server is running
- `POST /make-call`: Make an outbound call to a patient
- `GET /call-status/{call_sid}`: Get the status of a call
- `GET /call-transcript/{call_sid}`: Get the transcript of a call
- `GET /call-outcome/{call_sid}`: Get the outcome of a call

## Project Structure

```
appointment_bot/
├── .env                  # Environment variables (create from env.example)
├── requirements.txt      # Python dependencies
├── app.py                # Main application
├── run.py                # Entry point script
├── test_call.py          # Script for making test calls
├── twilio_handler.py     # Twilio integration
├── openai_handler.py     # OpenAI Realtime API integration
├── conversation.py       # Conversation flow logic
├── database.py           # Mock database interface
└── models/               # Data models
    ├── patient.py        # Patient model
    └── appointment.py    # Appointment model
```

## Customization

You can customize the system by modifying the following:

- **System Message**: Edit the `APPOINTMENT_SYSTEM_MESSAGE` in `openai_handler.py` to change the AI's behavior
- **Voice**: Change the `VOICE` variable in your `.env` file to use a different voice (options: alloy, echo, shimmer)
- **Conversation Flow**: Modify the logic in `conversation.py` to change how the system handles appointment confirmations and rescheduling

## Production Considerations

For a production deployment, consider the following:

1. Replace the mock database with a real database system
2. Implement proper error handling and logging
3. Add authentication and security measures
4. Deploy to a cloud provider with proper scaling
5. Implement monitoring and alerting
6. Add compliance features for healthcare regulations (HIPAA, etc.)

## Troubleshooting

- **Call not connecting**: Make sure your ngrok URL is correct and the `DOMAIN` variable is set properly
- **OpenAI API errors**: Verify your API key and ensure you have access to the Realtime API
- **Twilio errors**: Check your Twilio credentials and ensure your phone number has Voice capabilities
- **Permission errors**: Ensure the phone number you're calling is either a Twilio number you own or a verified caller ID

## License

This project is licensed under the MIT License - see the LICENSE file for details.
