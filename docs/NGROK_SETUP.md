# Setting Up ngrok for Local Development

This guide will walk you through the process of installing and setting up ngrok, which is required for the Appointment Confirmation Bot to receive webhook callbacks from Twilio.

## What is ngrok?

ngrok is a tool that creates secure tunnels to expose your local development server to the internet. This is necessary for services like Twilio to send webhook requests to your local machine during development.

## Installation Instructions

### Option 1: Using Package Managers (Recommended)

#### macOS (using Homebrew)
```bash
brew install ngrok
```

#### Windows (using Chocolatey)
```bash
choco install ngrok
```

#### Linux (using Snap)
```bash
sudo snap install ngrok
```

### Option 2: Manual Installation

1. **Sign up for an ngrok account**
   - Go to [https://ngrok.com/signup](https://ngrok.com/signup) and create a free account

2. **Download ngrok**
   - Visit [https://ngrok.com/download](https://ngrok.com/download)
   - Download the appropriate version for your operating system

3. **Extract the downloaded file**
   - Unzip the downloaded file to a location of your choice
   - For convenience, you may want to add this location to your system's PATH

4. **Authenticate ngrok**
   - After signing up, you'll get an authtoken from the ngrok dashboard
   - Configure ngrok with your authtoken:
     ```bash
     ngrok config add-authtoken YOUR_AUTH_TOKEN
     ```

## Using ngrok with the Appointment Confirmation Bot

1. **Start your local server**
   - First, make sure your application is running on the specified port (default: 5050)
   - Run the application: `python run.py`

2. **Start ngrok**
   - Open a new terminal window and run:
     ```bash
     ngrok http 5050
     ```

3. **Update your .env file**
   - When ngrok starts, it will display a public URL (e.g., `https://a1b2c3d4.ngrok.io`)
   - Copy this URL (without the `https://` prefix) and update the `DOMAIN` variable in your `.env` file

   Example:
   ```
   DOMAIN=a1b2c3d4.ngrok.io
   ```

4. **Keep ngrok running**
   - Keep the ngrok terminal window open while you're testing your application
   - Each time you restart ngrok, you'll get a new URL and will need to update your `.env` file

## Troubleshooting

- **Connection refused**: Make sure your local server is running before starting ngrok
- **Timeout errors**: Free ngrok accounts have limitations on connection duration and bandwidth
- **Invalid host header**: Some frameworks require additional configuration to accept requests from ngrok

## Additional Resources

- [ngrok Documentation](https://ngrok.com/docs)
- [ngrok Dashboard](https://dashboard.ngrok.com/)
- [Twilio Webhook Guide](https://www.twilio.com/docs/usage/webhooks)
