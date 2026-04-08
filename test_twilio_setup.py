#!/usr/bin/env python3
"""
Test script to verify Twilio setup
Sends a test message to verify credentials are working
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def test_twilio_setup():
    """Test Twilio credentials and send a test message"""
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    
    # Validate credentials
    if not account_sid:
        print("❌ Error: TWILIO_ACCOUNT_SID not found in .env file")
        return False
    
    if not auth_token:
        print("❌ Error: TWILIO_AUTH_TOKEN not found in .env file")
        return False
    
    if not whatsapp_number:
        print("❌ Error: TWILIO_WHATSAPP_NUMBER not found in .env file")
        return False
    
    print("✅ Credentials found in .env file")
    print(f"   Account SID: {account_sid[:10]}...")
    print(f"   WhatsApp Number: {whatsapp_number}")
    
    # Initialize Twilio client
    try:
        client = Client(account_sid, auth_token)
        print("✅ Twilio client initialized")
    except Exception as e:
        print(f"❌ Error initializing Twilio client: {e}")
        return False
    
    # Get your WhatsApp number for testing
    print("\n" + "=" * 60)
    print("To test sending a message, enter your WhatsApp number")
    print("Format: whatsapp:+1234567890 (include country code)")
    print("=" * 60)
    
    test_number = input("\nEnter your WhatsApp number (or press Enter to skip): ").strip()
    
    if not test_number:
        print("\n⏭️  Skipping message test")
        print("✅ Setup verification complete!")
        return True
    
    # Validate number format
    if not test_number.startswith('whatsapp:+'):
        if test_number.startswith('+'):
            test_number = 'whatsapp:' + test_number
        else:
            print("⚠️  Warning: Number should start with '+' or 'whatsapp:+'")
            print("   Adding 'whatsapp:+' prefix...")
            if not test_number.startswith('+'):
                test_number = '+' + test_number
            test_number = 'whatsapp:' + test_number
    
    # Send test message
    try:
        print(f"\n📤 Sending test message to {test_number}...")
        message = client.messages.create(
            body='Hello! This is a test message from your N&F Recommender bot. ✅',
            from_=whatsapp_number,
            to=test_number
        )
        
        print(f"✅ Message sent successfully!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        print("\n📱 Check your WhatsApp for the test message!")
        
        return True
    
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you've joined the WhatsApp Sandbox")
        print("2. Verify your number format: whatsapp:+1234567890")
        print("3. Check that your Twilio account has credits")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("  Twilio Setup Verification")
    print("=" * 60)
    print()
    
    success = test_twilio_setup()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Setup complete! You can now run the Flask server:")
        print("   python server.py")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Setup incomplete. Please check the errors above.")
        print("=" * 60)

