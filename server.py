"""
Flask webhook server for Twilio WhatsApp integration
"""

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from src.whatsapp.bot import WhatsAppBot

# Load environment variables (.env locally; Cloud Run uses injected env)
load_dotenv()

app = Flask(__name__)

# Initialize bot
bot = WhatsAppBot()

# Twilio rejects outbound bodies over ~1600 chars (error 21617). Stay under with margin.
TWILIO_MAX_SEGMENT = 1500


def _twilio_message_segments(body: str, max_len: int = TWILIO_MAX_SEGMENT) -> list[str]:
    """Split reply into segments each <= max_len for Twilio Messaging / WhatsApp."""
    if len(body) <= max_len:
        return [body]
    parts: list[str] = []
    buf = ""
    for line in body.split("\n"):
        candidate = buf + ("\n" if buf else "") + line
        if len(candidate) <= max_len:
            buf = candidate
            continue
        if buf:
            parts.append(buf)
        if len(line) <= max_len:
            buf = line
        else:
            for i in range(0, len(line), max_len):
                parts.append(line[i : i + max_len])
            buf = ""
    if buf:
        parts.append(buf)
    return parts if parts else [body[:max_len]]


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint for receiving WhatsApp messages from Twilio
    """
    # Get incoming message
    incoming_message = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    
    print(f"Received message from {from_number}: {incoming_message}")
    
    # Process message through bot
    response_message = bot.process_message(from_number, incoming_message)
    
    print(f"Sending response: {response_message[:100]}...")
    print(f"Response length: {len(response_message)} characters")
    
    # Create TwiML response (each <Message> must be <= Twilio body limit)
    resp = MessagingResponse()
    segments = _twilio_message_segments(response_message)
    if len(segments) > 1:
        print(f"Splitting message into {len(segments)} Twilio segments (max {TWILIO_MAX_SEGMENT} chars each)")
    for seg in segments:
        resp.message(seg)
    
    return str(resp)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'naked-famous-recommender'}, 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    base = request.url_root.rstrip("/")
    return f"""
    <h1>Jeans fit recommender — WhatsApp webhook</h1>
    <p>Service is running. Point Twilio &quot;When a message comes in&quot; to:</p>
    <p><code>{base}/webhook</code> (POST)</p>
    <p>Health: <a href="{base}/health">/health</a></p>
    """


if __name__ == '__main__':
    # Run Flask server (local dev). Production: gunicorn (see Dockerfile).
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Flask server on port {port}")
    print(f"Webhook URL: http://localhost:{port}/webhook")
    print(f"Make sure to configure this URL in Twilio Console")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
