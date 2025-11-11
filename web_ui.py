from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess, threading

app = FastAPI(title="BFSI Voice Agent Dashboard")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

chat_log = []
demo_data = {"name": "Aarav Sharma", "balance": 125430.00, "card_status": "Active"}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "chat_log": chat_log, "demo_data": demo_data})

@app.get("/start-call")
async def start_call():
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
