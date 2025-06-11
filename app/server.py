from __future__ import annotations

import os
import logging

try:
    import fastapi
    from fastapi import FastAPI, HTTPException, Request, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    print("fastapi", fastapi.__version__)
except Exception as exc:  # pragma: no cover - startup check
    raise SystemExit(f"Couldn't import fastapi: {exc}") from exc

try:
    from recorder import Recorder
except Exception as exc:  # pragma: no cover - optional dep
    Recorder = None  # type: ignore
    logging.error("Failed to import Recorder: %s", exc)

try:
    from model import run_model
except Exception as exc:  # pragma: no cover - optional dep
    run_model = None  # type: ignore
    logging.error("Failed to import run_model: %s", exc)

try:
    from constants import RECORDING_DIR, TRANSCRIPT_DIR
except Exception as exc:  # pragma: no cover - should always exist
    logging.error("Failed to import constants: %s", exc)
    RECORDING_DIR = "recorded_audio"  # type: ignore
    TRANSCRIPT_DIR = "transcripts"  # type: ignore

from datetime import datetime

try:
    from buffer_manager import TranscriptBuffer
except Exception as exc:  # pragma: no cover - optional
    TranscriptBuffer = None  # type: ignore
    logging.error("Failed to import TranscriptBuffer: %s", exc)

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

if Recorder is not None:
    try:
        recorder = Recorder()
    except Exception as exc:  # pragma: no cover - init failure
        logger.error("Failed to initialize Recorder: %s", exc)
        recorder = None
else:
    recorder = None

if TranscriptBuffer is not None:
    try:
        transcript_buffer = TranscriptBuffer()
    except Exception as exc:  # pragma: no cover - init failure
        logger.error("Failed to initialize TranscriptBuffer: %s", exc)
        transcript_buffer = None
else:
    transcript_buffer = None


@app.post("/record")
async def record(request: Request):
    """Start or stop recording based on the ``action`` field."""
    data = await request.json()
    action = data.get("action")
    if recorder is None:
        logger.error("Recorder not initialized")
        raise HTTPException(status_code=503, detail="Recording unavailable")
    if action == "start":
        logger.info("Starting recording")
        recorder.start()
        return {"status": "recording"}
    if action == "stop":
        try:
            path = recorder.stop()
        except Exception as exc:  # pragma: no cover - stop may fail
            logger.error("Failed to stop recording: %s", exc)
            raise HTTPException(status_code=500, detail="Stop recording failed")
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
    if run_model is None:
        logger.error("run_model not available")
        raise HTTPException(status_code=503, detail="Transcription unavailable")
    try:
        text = run_model(path)
    except Exception as exc:  # broad but ensures we never crash
        logger.exception("run_model failed for %s", path)
        raise HTTPException(status_code=500, detail="Transcription failed") from exc

    transcript_buffer.append(text, path)
    return {"transcript": text}


@app.post("/transcribe")
async def transcribe_upload(file: UploadFile = File(...)):
    """Accept an uploaded audio file and return its transcript."""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    ext = os.path.splitext(file.filename or "")[1] or ".webm"
    save_path = os.path.join(RECORDING_DIR, f"UPLOAD_{timestamp}{ext}")
    with open(save_path, "wb") as f:
        f.write(await file.read())
    logger.info("Transcribe uploaded file %s", save_path)
    if run_model is None:
        logger.error("run_model not available")
        raise HTTPException(status_code=503, detail="Transcription unavailable")
    try:
        text = run_model(save_path)
    except Exception as exc:  # broad but ensures we never crash
        logger.exception("run_model failed for %s", save_path)
        raise HTTPException(status_code=500, detail="Transcription failed") from exc

    transcript_buffer.append(text, save_path)
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
    """Save provided text to a ``.txt`` file in ``TRANSCRIPT_DIR``."""
    data = await request.json()
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    path = os.path.join(TRANSCRIPT_DIR, f"EXPORT_{timestamp}.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return {"path": path}


def main() -> None:
    try:
        import uvicorn
    except Exception as exc:  # pragma: no cover - startup check
        logger.error("Couldn't import uvicorn: %s", exc)
        print("Uvicorn is required to run the server.")
        return

    try:
        # Run the FastAPI ``app`` directly to avoid import path issues when
        # this module is executed with ``python -m app.server``.
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as exc:
        logger.exception("Failed to launch Uvicorn")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - catch all
        logger.exception("Server crashed during startup: %s", exc)
