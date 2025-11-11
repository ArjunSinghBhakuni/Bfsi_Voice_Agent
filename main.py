# main.py — Unified BFSI Voice Agent with Twilio + OpenAI + Dashboard
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from datetime import datetime
from pathlib import Path
from business_logic_bfsi import BFSIBusinessLogic
import os, requests, logging

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="BFSI Voice Agent Unified")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

logic = BFSIBusinessLogic()

# --- In-memory store ---
chat_log = []
conversations = {}
demo_data = {
    "name": "Aarav Sharma",
    "phone": "+91XXXXXXXXXX",
    "balance": 125430.00,
    "card_status": "Active",
    "emi_due": "Nov 5, 2025",
    "claim_status": "Under Review",
}

# --- ENV VARS ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER")
BACKEND_URL = os.getenv("BACKEND_URL", os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000"))
DASHBOARD_URL = os.getenv("DASHBOARD_URL", BACKEND_URL)

# === Helper ===
def push_to_dashboard(role: str, text: str):
    chat_log.append({"role": role, "text": text})
    try:
        requests.post(f"{DASHBOARD_URL}/conversation", json={"role": role, "text": text}, timeout=2)
    except Exception:
        pass

# ===============================================================
# 🖥️ DASHBOARD ROUTES
# ===============================================================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "chat_log": chat_log, "demo_data": demo_data})

@app.get("/conversation")
async def get_conversation():
    return JSONResponse({"chat": chat_log})

@app.post("/conversation")
async def add_conversation(request: Request):
    payload = await request.json()
    chat_log.append(payload)
    return JSONResponse({"ok": True})

@app.get("/start-call")
async def start_call():
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, YOUR_PHONE_NUMBER]):
        return JSONResponse({"error": "Missing Twilio credentials"}, status_code=500)
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=YOUR_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{BACKEND_URL}/voice",
            status_callback=f"{BACKEND_URL}/call-status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            method="POST"
        )
        push_to_dashboard("system", f"📞 Outbound call initiated — SID: {call.sid}")
        return JSONResponse({"status": "success", "sid": call.sid})
    except Exception as e:
        logging.exception("start-call failed")
        return JSONResponse({"error": str(e)}, status_code=500)

# ===============================================================
# 📞 TWILIO VOICE ROUTES
# ===============================================================
@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "SIM-" + datetime.now().isoformat())
    conversations[call_sid] = {"phone": None, "history": []}

    vr = VoiceResponse()
    vr.say("Welcome to your bank's AI voice assistant.", voice="Polly.Joanna", language="en-IN")

    g = Gather(
        input="speech",
        action="/get-phone",
        method="POST",
        timeout=8,
        speech_timeout="auto",
        hints="zero one two three four five six seven eight nine",
        enhanced=True,
        language="en-IN"
    )
    g.say("Please say your 10 digit mobile number.", voice="Polly.Joanna")
    vr.append(g)
    vr.say("I didn't catch that. Please call again. Goodbye!")
    return Response(str(vr), media_type="application/xml")

@app.post("/get-phone")
async def get_phone(request: Request, SpeechResult: str = Form(None)):
    form = await request.form()
    call_sid = form.get("CallSid")
    said = (SpeechResult or "").lower().replace(" ", "")
    digits = "".join(ch for ch in said if ch.isdigit())
    phone = "+91" + digits[-10:] if len(digits) >= 10 else None

    vr = VoiceResponse()
    if not phone:
        g = Gather(input="speech", action="/get-phone", method="POST",
                   timeout=8, speech_timeout="auto", enhanced=True, language="en-IN")
        g.say("Sorry, I couldn't understand. Please say your mobile number clearly.")
        vr.append(g)
        return Response(str(vr), media_type="application/xml")

    conversations.setdefault(call_sid, {})["phone"] = phone
    demo_data["phone"] = phone  # ✅ update top panel
    push_to_dashboard("system", f"User identified: {phone}")

    vr.say(f"Thanks. I have your number as {phone}.", voice="Polly.Joanna", language="en-IN")
    g = Gather(input="speech", action="/process", method="POST",
               timeout=10, speech_timeout="auto", enhanced=True, language="en-IN")
    g.say("How can I help you today? Ask about balance, blocking a card, EMI, claim status, or contact update.")
    vr.append(g)
    vr.say("I didn't hear anything. Goodbye!")
    return Response(str(vr), media_type="application/xml")

@app.post("/process")
async def process(request: Request, SpeechResult: str = Form(None)):
    form = await request.form()
    call_sid = form.get("CallSid")
    user_text = (SpeechResult or "").strip()
    phone = conversations.get(call_sid, {}).get("phone")

    vr = VoiceResponse()
    if not phone:
        vr.say("I need your verified number first.", voice="Polly.Joanna")
        g = Gather(input="speech", action="/get-phone", method="POST",
                   timeout=8, speech_timeout="auto", enhanced=True, language="en-IN")
        g.say("Please say your mobile number.")
        vr.append(g)
        return Response(str(vr), media_type="application/xml")

    push_to_dashboard("user", user_text or "(no speech)")

    answer = logic.generate_response(phone, user_text)
    push_to_dashboard("agent", answer)

    # if user blocked a card, update UI
    if "block" in user_text.lower():
        demo_data["card_status"] = "Blocked"

    vr.say(answer, voice="Polly.Joanna", language="en-IN")
    g = Gather(input="speech", action="/process", method="POST",
               timeout=8, speech_timeout="auto", enhanced=True, language="en-IN")
    g.say("Anything else?")
    vr.append(g)
    vr.say("Thank you for calling. Goodbye!")
    return Response(str(vr), media_type="application/xml")

@app.post("/call-status")
async def call_status(request: Request):
    form = await request.form()
    call_status = form.get("CallStatus")
    push_to_dashboard("system", f"📞 Call status: {call_status}")
    return JSONResponse({"ok": True, "status": call_status})

# ===============================================================
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/debug")
async def debug():
    return {
        "TWILIO_SID": TWILIO_ACCOUNT_SID,
        "TWILIO_FROM": TWILIO_PHONE_NUMBER,
        "YOUR_PHONE": YOUR_PHONE_NUMBER,
        "BACKEND_URL": BACKEND_URL,
        "ROUTES": [r.path for r in app.routes],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
