"""
Circuit-Sense AI — Main FastAPI Server
Autonomous Multimodal Agent for Hardware Debugging & Safety
"""

import os
import base64
import threading
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from PIL import Image

from rag import RAGEngine
from vision import VisionEngine
from alert import AlertEngine
from heartbeat import HeartbeatMonitor

app = FastAPI(title="Circuit-Sense AI", version="1.0.0")

# --- Engine Initialization ---
rag = RAGEngine()
vision = VisionEngine()
alert = AlertEngine(bot_token=os.getenv("TELEGRAM_BOT_TOKEN"), chat_id=os.getenv("TELEGRAM_CHAT_ID"))
heartbeat = HeartbeatMonitor(rag=rag, vision=vision, alert=alert)

# --- API Models ---
class AnalyzeRequest(BaseModel):
    image_base64: str  # base64-encoded image from webcam
    chip_context: str = ""  # optional: already-known chip name

class AnalyzeResponse(BaseModel):
    agent_message: str
    violations: list[str]
    chip_detected: str
    safe: bool

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("src/index.html") as f:
        return f.read()

@app.post("/upload-datasheet")
async def upload_datasheet(file: UploadFile = File(...)):
    """Upload a PDF datasheet — ingests into ChromaDB vector store."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF datasheets are supported.")
    contents = await file.read()
    path = f"datasheets/{file.filename}"
    with open(path, "wb") as f:
        f.write(contents)
    rag.ingest_pdf(path)
    return {"status": "ingested", "filename": file.filename}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """Core endpoint: vision + RAG + safety check."""
    # Decode image
    img_bytes = base64.b64decode(req.image_base64)
    image = Image.open(BytesIO(img_bytes))

    # Step 1: Vision — identify components & wiring
    vision_result = vision.analyze(image)

    # Step 2: RAG — lookup datasheet constraints for detected chip
    chip = vision_result.get("chip", req.chip_context or "Unknown")
    connections = vision_result.get("connections", [])
    violations = []
    rag_notes = []

    for conn in connections:
        result = rag.query(f"{chip} {conn} voltage safety")
        if result:
            rag_notes.append(result)
            if "violation" in result.lower() or "exceeds" in result.lower() or "danger" in result.lower():
                violations.append(f"{conn}: {result}")

    # Step 3: Build agent message
    if violations:
        msg = f"⚠️ STOP! Safety violation detected on {chip}:\n" + "\n".join(violations)
        alert.send(msg)
        safe = False
    else:
        msg = f"✅ I see a {chip}. All connections look safe. {'; '.join(rag_notes[:2]) if rag_notes else 'No datasheet constraints violated.'}"
        safe = True

    return AnalyzeResponse(agent_message=msg, violations=violations, chip_detected=chip, safe=safe)

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
