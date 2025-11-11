# BFSI AI Voice Agent — Prototype (No Database)

This prototype adapts your TVS voice-agent approach for BFSI. It keeps everything **in-memory** (no database) and focuses on a few **core functions** with **sample data**.

## What you get
- FastAPI app with Twilio-compatible endpoints (`/voice`, `/get-phone`, `/process`)
- In-memory sample data for **Banking** and **Insurance**
- Business logic functions:
  - `balance_inquiry` — savings balance + last transaction
  - `card_block` — immediate hotlisting of a card
  - `emi_info` — next EMI, outstanding principal, tenure left
  - `claim_status` — health insurance claim status & ETA
  - `update_contact` — email/phone update (mock)
- Simple intent classifier tailored for BFSI

## Install
```bash
# 1) Create & activate a virtual env
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt
```

## Run locally
```bash
uvicorn app_bfsi:app --reload --port 8000
```

Visit `http://localhost:8000/health` to check it is running.

## Optional: test with Twilio + ngrok
```bash
# In a new terminal
ngrok http 8000

# Copy the https URL and set it as your Twilio Voice webhook for:
#   <ngrok-url>/voice
# Outbound test calls (optional) will need .env with TWILIO creds.
```

## Reference you provided
- We mirrored the friendly Twilio + FastAPI flow from your TVS project and simplified it to in-memory logic so you can iterate fast.
- No database calls — all data lives in `sample_data.py`.

## Extend next
- Add OTP/biometric auth stubs
- Add Hindi/hinglish prompts (use `language="hi-IN"` in TwiML)
- Add outbound notifications (SMS/WhatsApp) after actions
- Swap in real connectors (CBS, LMS, Claims) when ready