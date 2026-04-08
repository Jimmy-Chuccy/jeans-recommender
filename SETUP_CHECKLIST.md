# WhatsApp Bot Setup Checklist

## ✅ What I've Done (Automated)

- [x] Created Flask webhook server (`server.py`)
- [x] Implemented WhatsApp bot logic (`src/whatsapp/bot.py`)
- [x] Created state manager for conversations (`src/whatsapp/state_manager.py`)
- [x] Built message formatter (`src/whatsapp/formatter.py`)
- [x] Updated requirements.txt with Flask and Twilio
- [x] Created `.env.example` template
- [x] Created test script (`test_twilio_setup.py`)
- [x] Created setup documentation (`WHATSAPP_SETUP.md`)
- [x] Verified all imports work correctly

## ⚠️ What You Need to Do (Manual Steps)

### Step 1: Create `.env` File
```bash
cp .env.example .env
```
Then edit `.env` and add your Twilio credentials:
- `TWILIO_ACCOUNT_SID` - From Twilio Console
- `TWILIO_AUTH_TOKEN` - From Twilio Console  
- `TWILIO_WHATSAPP_NUMBER` - Your sandbox number (format: `whatsapp:+14155238886`)

### Step 2: Install Dependencies
```bash
pip install flask twilio
```
(Or install all: `pip install -r requirements.txt`)

### Step 3: Join WhatsApp Sandbox
1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Find the join code (e.g., "join example-code")
3. Send that code to the Twilio sandbox number shown
4. Wait for confirmation message

### Step 4: Install and Run ngrok
```bash
# Install ngrok
brew install ngrok  # macOS
# Or download from https://ngrok.com/download

# In a separate terminal, run:
ngrok http 8080
```
Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Step 5: Configure Webhook in Twilio
1. Go to: https://console.twilio.com/us1/develop/sms/sandbox/whatsapp-sandbox
2. Find "When a message comes in"
3. Enter: `https://your-ngrok-url.ngrok.io/webhook`
4. Set HTTP method: **POST**
5. Click **Save**

### Step 6: Test Setup
```bash
python test_twilio_setup.py
```

### Step 7: Start the Server
```bash
python server.py
```

### Step 8: Test the Bot
Send a WhatsApp message to your Twilio sandbox number with: `start`

## Quick Test Flow

1. Start server: `python server.py`
2. In WhatsApp, send: `start`
3. Follow the prompts:
   - `relaxed`
   - `501`
   - `30`
   - `higher`
   - `more`
   - `wider`
4. You should receive recommendations!

## Troubleshooting

If something doesn't work:
1. Check `.env` file has correct credentials
2. Verify ngrok is running and URL is correct
3. Check webhook URL in Twilio Console
4. Look at Flask server logs for errors
5. Ensure you joined WhatsApp Sandbox

## Files Reference

- `server.py` - Main Flask webhook server
- `src/whatsapp/bot.py` - Bot conversation logic
- `src/whatsapp/state_manager.py` - Tracks user state
- `src/whatsapp/formatter.py` - Formats messages
- `test_twilio_setup.py` - Test Twilio connection
- `.env` - Your credentials (create this!)
- `WHATSAPP_SETUP.md` - Detailed setup guide

## Ready to Go!

Once you complete the manual steps above, your WhatsApp bot will be fully functional! 🚀

