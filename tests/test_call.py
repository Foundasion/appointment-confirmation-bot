import os
import sys
import json
import asyncio
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appointment_bot.database import Database
from appointment_bot.twilio_handler import TwilioHandler


async def make_test_call(phone_number: str, appointment_id: str = None):
    """Make a test call to the specified phone number."""
    print(f"Making test call to {phone_number}...")
    
    # Initialize components
    db = Database()
    twilio_handler = TwilioHandler()
    
    # Get appointment data if an ID was provided
    appointment_data = None
    if appointment_id:
        appointment_data = db.get_appointment_details(appointment_id)
        if not appointment_data:
            print(f"Appointment not found with ID: {appointment_id}")
            return None
        
        print(f"Using appointment data: {json.dumps(appointment_data, indent=2)}")
    else:
        # Use dummy appointment data
        appointment_data = {
            "appointment_id": "A001",
            "patient_name": "Michael Scott",
            "patient_phone": phone_number,
            "doctor": "Dr. Shah",
            "date": "Monday, March 20th",
            "time": "2:00 PM",
            "status": "scheduled",
            "duration": 30,
            "notes": "Test appointment"
        }
        print(f"Using dummy appointment data: {json.dumps(appointment_data, indent=2)}")
    
    # Make the call
    call_sid = await twilio_handler.make_call(phone_number, appointment_data)
    
    if call_sid:
        print(f"Call initiated successfully with SID: {call_sid}")
        print("The AI assistant will now call the specified number.")
        print("After the call completes, you can check the transcript and outcome.")
        return call_sid
    else:
        print("Failed to make call. Check if the number is allowed.")
        print("Make sure you've set up your Twilio credentials correctly in the .env file.")
        print("Also ensure the phone number is a verified caller ID or a Twilio number you own.")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make a test call with the Appointment Confirmation Bot.")
    parser.add_argument('--phone', required=True, help="The phone number to call, e.g., '+1234567890'")
    parser.add_argument('--appointment', help="Optional appointment ID to use")
    args = parser.parse_args()
    
    asyncio.run(make_test_call(args.phone, args.appointment))
