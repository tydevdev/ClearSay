from __future__ import annotations

import os
import logging

try:
    import fastapi
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    print("fastapi", fastapi.__version__)
except Exception as exc:  # pragma: no cover - startup check
    raise SystemExit(f"Couldn't import fastapi: {exc}") from exc

from recorder import Recorder
from model import run_model
from constants import RECORDING_DIR, TRANSCRIPT_DIR
from datetime import datetime
from docx import Document
from buffer_manager import TranscriptBuffer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow the Electron UI to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

recorder = Recorder()
transcript_buffer = TranscriptBuffer()


@app.post("/record")
async def record(request: Request):
    """Start or stop recording based on the ``action`` field."""
    data = await request.json()
    action = data.get("action")
    if action == "start":
        logger.info("Starting recording")
        recorder.start()
        return {"status": "recording"}
    if action == "stop":
        path = recorder.stop()
        logger.info("Stopped recording, saved to %s", path)
        if path is None:
            raise HTTPException(status_code=400, detail="No audio recorded")
        return {"file": os.path.basename(path)}
    raise HTTPException(status_code=400, detail="Invalid action")


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.get("/transcribe")
async def transcribe(file: str):
    """Transcribe ``file`` from :data:`RECORDING_DIR`."""
    path = os.path.abspath(os.path.join(RECORDING_DIR, file))
    logger.info("Transcribe request for %s", path)
    if not os.path.exists(path):
        logger.warning("File not found: %s", path)
        raise HTTPException(status_code=404, detail="File not found")
    try:
        text = run_model(path)
    except Exception as exc:  # broad but ensures we never crash
        logger.exception("run_model failed for %s", path)
        raise HTTPException(status_code=500, detail="Transcription failed") from exc

    transcript_buffer.append(text, path)
    return {"transcript": text}


@app.get("/list-transcripts")
async def list_transcripts():
    """Return transcript file names with modification times."""
    files = []
    if os.path.exists(TRANSCRIPT_DIR):
        for name in os.listdir(TRANSCRIPT_DIR):
            if name.endswith(".txt"):
                path = os.path.join(TRANSCRIPT_DIR, name)
                files.append({"name": name, "mtime": os.path.getmtime(path)})
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return {"files": files}


@app.get("/get-transcript")
async def get_transcript(name: str):
    """Return the contents of ``name`` from :data:`TRANSCRIPT_DIR`."""
    path = os.path.abspath(os.path.join(TRANSCRIPT_DIR, name))
    if not path.startswith(os.path.abspath(TRANSCRIPT_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}


@app.post("/export-docx")
async def export_docx(request: Request):
    """Export provided text to a DOCX file in ``TRANSCRIPT_DIR``."""
    data = await request.json()
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    path = os.path.join(TRANSCRIPT_DIR, f"EXPORT_{timestamp}.docx")

    doc = Document()
    for para in text.split("\n"):
        doc.add_paragraph(para)
    doc.save(path)

    return {"path": path}


def main() -> None:
    try:
        import uvicorn
    except Exception as exc:  # pragma: no cover - startup check
        logger.error("Couldn't import uvicorn: %s", exc)
        raise SystemExit(1) from exc

    try:
        # Run the FastAPI ``app`` directly to avoid import path issues when
        # this module is executed with ``python -m app.server``.
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as exc:
        logger.error("Failed to launch Uvicorn: %s", exc)
        raise


if __name__ == "__main__":
    main()
