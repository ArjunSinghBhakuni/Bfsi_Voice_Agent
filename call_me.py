from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER")
BACKEND_URL = os.getenv("BACKEND_URL")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def call_me_bfsi():
    print(f"📞 Calling {YOUR_PHONE_NUMBER} via Twilio...")
    try:
        call = client.calls.create(
            to=YOUR_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{BACKEND_URL}/voice",
            status_callback=f"{BACKEND_URL}/call-status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            method="POST"
        )
        print(f"✅ Call initiated: {call.sid}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    call_me_bfsi()
