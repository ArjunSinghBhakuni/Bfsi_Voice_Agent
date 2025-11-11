# web_ui.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess, threading, os

app = FastAPI(title="BFSI Voice Agent - Interactive Demo")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- In-memory demo customer data (same as sample_data.py) ---
demo_data = {
    "name": "Aarav Sharma",
    "balance": 125430.00,
    "card_status": "Active",
    "emi_due": "Nov 5, 2025",
    "claim_status": "Under Review",
}

# In-memory chat log
chat_log = []

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "chat_log": chat_log,
            "demo_data": demo_data
        }
    )

@app.get("/start-call")
async def start_call():
    """Triggers call_me.py asynchronously."""
    def run_call():
        subprocess.run(["python", "call_me.py"])
    threading.Thread(target=run_call).start()
    return JSONResponse({"status": "Call initiated"})

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
    """Simulate changes in BFSI data (for demo)."""
    data = await request.json()
    intent = data.get("intent")

    if intent == "balance":
        demo_data["balance"] -= 500  # simulate transaction
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

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
