#!/usr/bin/env python3
"""
Entry point script for running the Appointment Confirmation Bot.
This script handles the proper Python module paths and starts the application.
"""

import os
import sys
import argparse
import uvicorn

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app
from appointment_bot.app import app, PORT

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Appointment Confirmation Bot server.")
    parser.add_argument('--port', type=int, default=PORT, help="Port to run the server on")
    args = parser.parse_args()
    
    print(f"Starting Appointment Confirmation Bot on port {args.port}...")
    print("Press Ctrl+C to stop the server.")
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)
