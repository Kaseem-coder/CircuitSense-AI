"""
Circuit-Sense AI — Main FastAPI Server
Autonomous Multimodal Agent for Hardware Debugging & Safety
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import base64
import threading
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from PIL import Image

from rag import RAGEngine
from vision import VisionEngine
from alert import AlertEngine
from heartbeat import HeartbeatMonitor

app = FastAPI(title="Circuit-Sense AI", version="1.0.0")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )

rag = RAGEngine()
vision = VisionEngine()
alert = AlertEngine(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
    chat_id=os.getenv("TELEGRAM_CHAT_ID")
)
heartbeat = HeartbeatMonitor(rag=rag, vision=vision, alert=alert)

class AnalyzeRequest(BaseModel):
    image_base64: str
    chip_context: str = ""

class AnalyzeResponse(BaseModel):
    agent_message: str
    violations: list[str]
    chip_detected: str
    safe: bool

class TextAnalyzeRequest(BaseModel):
    description: str

@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8") as f:
        return f.read()

@app.post("/upload-datasheet")
async def upload_datasheet(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF datasheets are supported.")
    contents = await file.read()
    os.makedirs("datasheets", exist_ok=True)
    path = f"datasheets/{file.filename}"
    with open(path, "wb") as f:
        f.write(contents)
    rag.ingest_pdf(path)
    return {"status": "ingested", "filename": file.filename}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    img_bytes = base64.b64decode(req.image_base64)
    image = Image.open(BytesIO(img_bytes))

    vision_result = vision.analyze(image)

    chip = vision_result.get("chip", req.chip_context or "Unknown")
    connections = vision_result.get("connections", [])
    warnings = vision_result.get("warnings", [])
    violations = []
    rag_notes = []

    for conn in connections:
        result = rag.query(f"{chip} {conn} voltage safety")
        if result:
            rag_notes.append(result)
            if any(w in result.lower() for w in [
                "danger", "exceeds", "violation", "not recommended", "maximum",
                "do not", "must not", "cannot", "3.3v", "3.3 v", "tolerant",
                "absolute maximum", "damage", "overvoltage", "caution", "warning"
            ]):
                violations.append(f"{conn}: {result[:120]}")

    for w in warnings:
        if w.lower() not in ["none", ""] and w not in violations:
            violations.append(f"Vision detected: {w}")

    if violations:
        msg = "STOP! Safety violation detected on " + chip + ":\n" + "\n".join(violations)
        alert.send(msg)
        safe = False
    else:
        msg = chip + " looks safe. " + ("; ".join(rag_notes[:2]) if rag_notes else "No violations found.")
        safe = True

    return AnalyzeResponse(agent_message=msg, violations=violations, chip_detected=chip, safe=safe)

@app.post("/analyze-text")
async def analyze_text(req: TextAnalyzeRequest):
    result = vision.analyze_text(req.description)
    chip = result.get("chip", "Unknown")
    connections = result.get("connections", [])
    warnings = result.get("warnings", [])
    violations = []

    for conn in connections:
        rag_result = rag.query(f"{chip} {conn} voltage safety")
        if rag_result and any(w in rag_result.lower() for w in [
            "danger", "exceeds", "violation", "damage", "maximum", "3.3v", "caution"
        ]):
            violations.append(f"{conn}: {rag_result[:120]}")

    for w in warnings:
        if w.lower() not in ["none", ""] and w not in violations:
            violations.append(f"Vision detected: {w}")

    if violations:
        msg = "STOP! Violation on " + chip + ":\n" + "\n".join(violations)
        alert.send(msg)
        safe = False
    else:
        msg = chip + " looks safe. No violations found."
        safe = True

    return {"agent_message": msg, "violations": violations, "chip_detected": chip, "safe": safe}

@app.post("/heartbeat/start")
async def start_heartbeat():
    thread = threading.Thread(target=heartbeat.run, daemon=True)
    thread.start()
    return {"status": "heartbeat started"}

@app.post("/heartbeat/stop")
async def stop_heartbeat():
    heartbeat.stop()
    return {"status": "heartbeat stopped"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)