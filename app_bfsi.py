# Minimal FastAPI app to simulate a voice intent loop for BFSI (prototype).
# Adapts the TVS reference flow but keeps everything in-memory.

from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from datetime import datetime
from business_logic_bfsi import BFSIBusinessLogic
# ✅ Twilio Status Callback: add this endpoint
import requests

# app_bfsi.py
import requests, os
import logging  # 👈 added for simple server-side logs

app = FastAPI(title="BFSI Voice Agent (Prototype)")
logic = BFSIBusinessLogic()

# In-memory store (per-call)
conversations = {}

@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "SIM-" + datetime.now().isoformat())
    conversations[call_sid] = {"phone": None, "history": []}

    vr = VoiceResponse()
    vr.say("Welcome to your bank's AI voice assistant.", voice="Polly.Joanna", language="en-IN")
    g = Gather(input="speech", action="/get-phone", method="POST", timeout=6, speech_timeout="4", language="en-IN")
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
        g = Gather(input="speech", action="/get-phone", method="POST", timeout=6, speech_timeout="4", language="en-IN")
        g.say("Sorry, I couldn't understand. Please say your mobile number clearly.")
        vr.append(g)
        return Response(str(vr), media_type="application/xml")

    conversations.setdefault(call_sid, {})["phone"] = phone
    vr.say(f"Thanks. I have your number as {phone}.", voice="Polly.Joanna", language="en-IN")
    g = Gather(input="speech", action="/process", method="POST", timeout=10, speech_timeout="5", language="en-IN")
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
        g = Gather(input="speech", action="/get-phone", method="POST", timeout=6, speech_timeout="4", language="en-IN")
        g.say("Please say your mobile number.")
        vr.append(g)
        return Response(str(vr), media_type="application/xml")

    # (Optional) keep a tiny history if you want
    conversations.setdefault(call_sid, {}).setdefault("history", []).append({"user": user_text})

    answer = logic.generate_response(phone, user_text)

    vr.say(answer, voice="Polly.Joanna", language="en-IN")
    g = Gather(input="speech", action="/process", method="POST", timeout=8, speech_timeout="4", language="en-IN")
    g.say("Anything else?")
    vr.append(g)
    vr.say("Thank you for calling. Goodbye!")
    return Response(str(vr), media_type="application/xml")



DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8080")

@app.post("/call-status")
async def call_status(request: Request):
    form = await request.form()
    call_status = form.get("CallStatus")
    try:
        requests.post(f"{DASHBOARD_URL}/conversation", json={
            "role": "system",
            "text": f"📞 Call status: {call_status}"
        })
    except Exception as e:
        print(f"Dashboard update failed: {e}")
    return JSONResponse({"ok": True, "status": call_status})

@app.get("/health")
async def health():
    return {"status": "ok"}
