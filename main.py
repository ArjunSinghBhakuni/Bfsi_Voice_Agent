# main.py — Render-ready version
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from twilio.twiml.voice_response import VoiceResponse, Gather
from datetime import datetime
from business_logic_bfsi import BFSIBusinessLogic
from pathlib import Path
import requests, os, logging

# === BASE PATH SETUP (ensures templates/static found on Render) ===
BASE_DIR = Path(__file__).resolve().parent

# --- Initialize FastAPI app ---
app = FastAPI(title="BFSI Voice Agent with Dashboard")

# --- Mount static and template directories ---
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# --- Core AI logic + memory ---
logic = BFSIBusinessLogic()
conversations = {}
chat_log = []
demo_data = {
    "name": "Aarav Sharma",
    "balance": 125430.00,
    "card_status": "Active",
    "emi_due": "Nov 5, 2025",
    "claim_status": "Under Review",
}

# ================================================================
# 🖥️ DASHBOARD ROUTES
# ================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard view — loads index.html"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "chat_log": chat_log, "demo_data": demo_data}
    )

@app.get("/conversation")
async def get_conversation():
    return JSONResponse({"chat": chat_log})

@app.post("/conversation")
async def add_conversation(request: Request):
    data = await request.json()
    chat_log.append(data)
    return JSONResponse({"ok": True})

@app.post("/demo-update")
async def demo_update(request: Request):
    """Simulate changes in BFSI data (for demo visuals)."""
    data = await request.json()
    intent = data.get("intent")

    if intent == "balance":
        demo_data["balance"] -= 500
    elif intent == "card_block":
        demo_data["card_status"] = "Blocked"
    elif intent == "emi_info":
        demo_data["emi_due"] = "Paid"
    elif intent == "claim_status":
        demo_data["claim_status"] = "Settled"

    return JSONResponse({"ok": True, "demo_data": demo_data})

@app.get("/demo-data")
async def get_demo_data():
    return JSONResponse(demo_data)

# ================================================================
# 📞 TWILIO VOICE ROUTES
# ================================================================

@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "SIM-" + datetime.now().isoformat())
    conversations[call_sid] = {"phone": None, "history": []}

    vr = VoiceResponse()
    vr.say("Welcome to your bank's AI voice assistant.", voice="Polly.Joanna", language="en-IN")
    g = Gather(input="speech", action="/get-phone", method="POST",
               timeout=6, speech_timeout="4", language="en-IN")
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
                   timeout=6, speech_timeout="4", language="en-IN")
        g.say("Sorry, I couldn't understand. Please say your mobile number clearly.")
        vr.append(g)
        return Response(str(vr), media_type="application/xml")

    conversations.setdefault(call_sid, {})["phone"] = phone
    vr.say(f"Thanks. I have your number as {phone}.", voice="Polly.Joanna", language="en-IN")
    g = Gather(input="speech", action="/process", method="POST",
               timeout=10, speech_timeout="5", language="en-IN")
    g.say("How can I help you today? Ask about balance, blocking a card, EMI, claim status, or contact update.")
    vr.append(g)
    vr.say("I didn't hear anything. Goodbye!")
    return Response(str(vr), media_type="application/xml")


@app.post("/process")
async def process(request: Request, SpeechResult: str = Form(None)):
    form = await request.form()
    call_sid = form.get("CallSid")
    user_text = SpeechResult or ""
    phone = conversations.get(call_sid, {}).get("phone")

    vr = VoiceResponse()
    if not phone:
        vr.say("I need your verified number first. Transferring you back.", voice="Polly.Joanna")
        g = Gather(input="speech", action="/get-phone", method="POST",
                   timeout=6, speech_timeout="4", language="en-IN")
        g.say("Please say your mobile number.")
        vr.append(g)
        return Response(str(vr), media_type="application/xml")

    conversations.setdefault(call_sid, {}).setdefault("history", []).append({"user": user_text})
    answer = logic.generate_response(phone, user_text)
    vr.say(answer, voice="Polly.Joanna", language="en-IN")
    g = Gather(input="speech", action="/process", method="POST",
               timeout=8, speech_timeout="4", language="en-IN")
    g.say("Anything else?")
    vr.append(g)
    vr.say("Thank you for calling. Goodbye!")
    return Response(str(vr), media_type="application/xml")


@app.post("/call-status")
async def call_status(request: Request):
    form = await request.form()
    call_status = form.get("CallStatus")
    chat_log.append({"role": "system", "text": f"📞 Call status: {call_status}"})
    return JSONResponse({"ok": True, "status": call_status})


# ================================================================
# 🧠 SYSTEM + DEBUG ROUTES
# ================================================================

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/debug")
async def debug():
    import os
    return {
        "cwd": os.getcwd(),
        "base_dir": str(BASE_DIR),
        "files": os.listdir(),
        "templates_dir_exists": os.path.isdir(BASE_DIR / "templates"),
        "static_dir_exists": os.path.isdir(BASE_DIR / "static"),
        "routes": [r.path for r in app.routes],
    }


# ================================================================
# 🔥 ENTRY POINT
# ================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
