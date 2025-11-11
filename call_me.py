# call_me.py
from twilio.rest import Client
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER", "+919876543210")

# Your public backend URL (deployed FastAPI)
BACKEND_URL = os.getenv("BACKEND_URL")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def call_me_bfsi():
    """Twilio calls YOU and connects to BFSI AI Voice Agent"""
    print("=" * 60)
    print("📞 CALLING YOU WITH BFSI AI VOICE AGENT")
    print("=" * 60)
    print(f"📱 Your phone: {YOUR_PHONE_NUMBER}")
    print(f"📞 From Twilio: {TWILIO_PHONE_NUMBER}")
    print(f"🌐 AI Server: {BACKEND_URL}")
    print("=" * 60)

    if not BACKEND_URL:
        print("❌ BACKEND_URL not set in .env")
        return None

    try:
        call = client.calls.create(
            to=YOUR_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{BACKEND_URL}/voice",
            status_callback=f"{BACKEND_URL}/call-status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            method="POST"
        )
        print("\n✅ Call initiated successfully!")
        print(f"📊 Call SID: {call.sid}")
        print(f"📍 Status: {call.status}")
        print("=" * 60)
        return call.sid

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

if __name__ == "__main__":
    call_me_bfsi()
