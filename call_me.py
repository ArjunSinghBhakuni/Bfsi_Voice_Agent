"""
Trigger Twilio call to BFSI AI Voice Agent
"""

from twilio.rest import Client
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Your own number (who Twilio will call)
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER", "+919876543210")

# Your ngrok public URL (must point to your FastAPI server)
NGROK_URL = os.getenv("NGROK_URL", "https://your-ngrok-url.ngrok-free.app")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def call_me_bfsi():
    """Twilio calls YOU and connects to BFSI AI Agent"""
    print("=" * 60)
    print("📞 CALLING YOU WITH BFSI AI VOICE AGENT")
    print("=" * 60)
    print(f"📱 Your phone: {YOUR_PHONE_NUMBER}")
    print(f"📞 From Twilio: {TWILIO_PHONE_NUMBER}")
    print(f"🌐 AI Server: {NGROK_URL}")
    print("=" * 60)

    if "your-ngrok-url" in NGROK_URL:
        print("\n❌ ERROR: NGROK_URL not set!")
        print("\nTo fix:")
        print("1. Run: ngrok http 8000")
        print("2. Copy the https URL")
        print("3. Add this line to your .env file:")
        print("   NGROK_URL=<copied-url>")
        return None

    try:
        call = client.calls.create(
            to=YOUR_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{NGROK_URL}/voice",
            status_callback=f"{NGROK_URL}/call-status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            method="POST"
        )

        print("\n✅ Call initiated successfully!")
        print(f"📊 Call SID: {call.sid}")
        print(f"📍 Status: {call.status}")
        print("\n🔔 Your phone will ring in a few seconds...")
        print("🎙️ The AI agent will greet you and handle BFSI queries!")
        print("\n💡 Try saying:")
        print("   - 'What’s my account balance?'")
        print("   - 'I lost my credit card, please block it.'")
        print("   - 'When is my next EMI due?'")
        print("   - 'What’s the status of my insurance claim?'")
        print("   - 'Update my phone number to 9876512345.'")
        print("=" * 60)

        return call.sid

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Verify .env has correct Twilio credentials")
        print("2. Make sure ngrok is running (ngrok http 8000)")
        print("3. Update NGROK_URL in .env")
        print("4. Ensure FastAPI app (app_bfsi.py) is running")
        print("5. Check that YOUR_PHONE_NUMBER includes +91 prefix")
        return None


def get_call_status(call_sid: str):
    """Fetch call status"""
    try:
        call = client.calls(call_sid).fetch()
        print(f"📊 Status: {call.status}")
        print(f"⏱️ Duration: {call.duration}s")
        print(f"🆔 Call SID: {call.sid}")
        return call
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def list_recent_calls():
    """List last 5 calls from your Twilio account"""
    try:
        calls = client.calls.stream(limit=5)
        print("\n📞 Recent Calls:")
        print("-" * 60)
        for call in calls:
            print(f"{call.from_} → {call.to}")
            print(f"Status: {call.status} | Duration: {call.duration}s")
            print(f"SID: {call.sid}")
            print("-" * 60)
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "call":
            sid = call_me_bfsi()
            if sid:
                time.sleep(2)
                get_call_status(sid)
        elif cmd == "status" and len(sys.argv) > 2:
            get_call_status(sys.argv[2])
        elif cmd == "list":
            list_recent_calls()
        else:
            print("Usage:")
            print("  python call_me.py call          - Call you now")
            print("  python call_me.py status <SID>  - Check status")
            print("  python call_me.py list          - Show recent calls")
    else:
        call_me_bfsi()
