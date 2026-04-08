# WhatsApp Bot Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your Twilio credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your Twilio credentials:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 3. Test Twilio Setup

```bash
python test_twilio_setup.py
```

This will verify your credentials and optionally send a test message.

### 4. Set Up ngrok (for local testing)

Install ngrok:
```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

Start ngrok in a separate terminal (port must match `PORT` in `.env`, default **8080**):
```bash
ngrok http 8080
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 5. Configure Twilio Webhook

1. Go to Twilio Console: https://console.twilio.com
2. Navigate to: Messaging → Settings → WhatsApp Sandbox Settings
3. In "When a message comes in", enter your ngrok URL:
   ```
   https://your-ngrok-url.ngrok.io/webhook
   ```
4. Set HTTP method to: **POST**
5. Click **Save**

For a **stable HTTPS URL** (no ngrok, works while your laptop is off), deploy to **Google Cloud Run**: see [docs/DEPLOY_GCP.md](docs/DEPLOY_GCP.md). Use the same `/webhook` path on your Cloud Run service URL in Twilio.

### 6. Start the Flask Server

```bash
python server.py
```

The server will start on `http://localhost:8080` (or whatever you set as `PORT` in `.env`).

### 7. Test the bot locally (no Twilio)

Run the full conversation flow in your terminal:

```bash
python test_chatbot_flow.py
```

This walks through scripted paths (Levi’s reference, no reference, invalid input recovery) and checks the session reaches `COMPLETE`.

To type each reply yourself:

```bash
python test_chatbot_flow.py -i
```

Start with `start`, then follow the prompts (e.g. `slim`, `3`, `1`, `32`, `similar`, …).

### 8. Test the Bot on WhatsApp

1. Make sure you've joined the WhatsApp Sandbox (send join code to Twilio's sandbox number)
2. Send a message to your Twilio WhatsApp number
3. The bot should respond!

## Manual Steps You Need to Complete

### ✅ Already Done (by code):
- Flask webhook server created
- Bot logic implemented
- State management set up
- Message formatting ready
- Test script created

### ⚠️ You Need to Do:

1. **Create `.env` file** with your Twilio credentials
   ```bash
   cp .env.example .env
   # Then edit .env with your credentials
   ```

2. **Join WhatsApp Sandbox**
   - Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message
   - Send the join code to the sandbox number shown
   - Wait for confirmation

3. **Set up ngrok** (for local testing)
   - Install ngrok
   - Run: `ngrok http 8080`
   - Copy the HTTPS URL

4. **Configure Webhook in Twilio**
   - Use your ngrok URL: `https://your-url.ngrok.io/webhook`
   - Set method to POST

5. **Test the bot**
   - Send a message to your Twilio WhatsApp number
   - Try commands: `start`, `help`, `reset`

## Conversation Flow

1. **Welcome** → User types `start`
2. **Fit preference** → relaxed, slim, tapered, straight, bootcut, skinny, or **skip**
3. **Reference brand** → N&F (1), Nudie (2), Levi's (3), or none (4)
4. **If 1–3:** pick model/fit → **size in that model** → rise / thigh / leg → **full recommendations** (top picks per brand).
   - If user **skipped** fit in step 2 but names a model (e.g. Super Guy), that model **infers** fit (e.g. skinny) and the normal flow continues.
5. **If 4 and user skipped fit:** bot explains we need fit or reference → **promotions?** yes/no.
   - **No** → thank you, session ends.
   - **Yes** → usual waist size + rise / thigh / leg → **up to 10 on-sale items** (N&F-heavy + Levi's; straight-fit benchmark for scoring). Nudie skipped if no sale data.
6. **If 4 but user already gave a fit in step 2:** general size → fine-tune → full recommendations as usual.

## Commands

- `start` - Begin new recommendation
- `help` - Show help message
- `reset` - Reset current session

## Troubleshooting

### Server not receiving messages
- Check ngrok is running
- Verify webhook URL in Twilio Console
- Check Flask server logs
- Ensure webhook URL uses HTTPS

### "Unable to create record" error
- Verify Account SID and Auth Token
- Check WhatsApp number format: `whatsapp:+1234567890`
- Ensure you have Twilio credits

### Bot not responding
- Check Flask server is running
- Verify webhook is configured correctly
- Check server logs for errors
- Ensure you joined WhatsApp Sandbox

### Invalid input errors
- Use exact keywords (case-insensitive)
- Check valid options in help message
- Type `help` to see all valid inputs

## Production Deployment

For production, consider:

1. **Deploy to a server** (Heroku, Railway, Render, etc.)
2. **Use Redis** for state management (instead of in-memory)
3. **Add authentication** to webhook endpoint
4. **Set up logging** and monitoring
5. **Use production WhatsApp** (not sandbox)

## Files Created

- `server.py` - Flask webhook server
- `src/whatsapp/bot.py` - Bot logic
- `src/whatsapp/state_manager.py` - Conversation state
- `src/whatsapp/formatter.py` - Message formatting
- `test_twilio_setup.py` - Setup verification
- `.env.example` - Environment template

## Next Steps

1. Complete the manual setup steps above
2. Test with `python test_twilio_setup.py`
3. Start server: `python server.py`
4. Test the full conversation flow
5. Deploy to production when ready!

