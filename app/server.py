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
from constants import RECORDING_DIR, DISCUSSIONS_DIR
from storage import TranscriptStorage

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
transcript_buffer = TranscriptStorage()


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
    """Transcribe ``file`` from ``recorded_audio`` or ``discussions``."""
    path = os.path.abspath(os.path.join(RECORDING_DIR, file))
    recording_root = os.path.abspath(RECORDING_DIR)
    valid = path.startswith(recording_root + os.sep) and os.path.exists(path)
    if not valid:
        path = os.path.abspath(os.path.join(DISCUSSIONS_DIR, file))
        disc_root = os.path.abspath(DISCUSSIONS_DIR)
        valid = path.startswith(disc_root + os.sep) and os.path.exists(path)
    logger.info("Transcribe request for %s", path)
    if not valid:
        logger.warning("File not found or outside allowed dirs: %s", file)
        raise HTTPException(status_code=404, detail="File not found")
    try:
        text = run_model(path)
    except Exception as exc:  # broad but ensures we never crash
        logger.exception("run_model failed for %s", path)
        raise HTTPException(status_code=500, detail="Transcription failed") from exc

    transcript_buffer.append(text, path)
    return {"transcript": text}


@app.get("/current_discussion")
async def current_discussion() -> dict[str, str | None]:
    """Return the currently active discussion ID, if any."""
    return {"id": transcript_buffer.current_id}


def main() -> None:
    try:
        import uvicorn
    except Exception as exc:  # pragma: no cover - startup check
        logger.error("Couldn't import uvicorn: %s", exc)
        raise SystemExit(1) from exc

    try:
        uvicorn.run("server:app", host="127.0.0.1", port=8000)
    except Exception as exc:
        logger.error("Failed to launch Uvicorn: %s", exc)
        raise


if __name__ == "__main__":
    main()
