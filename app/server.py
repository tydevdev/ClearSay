from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from recorder import Recorder
from model import run_model
from constants import RECORDING_DIR

app = FastAPI()

# Allow the Electron UI to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

recorder = Recorder()


@app.post("/record")
async def record(request: Request):
    """Start or stop recording based on the ``action`` field."""
    data = await request.json()
    action = data.get("action")
    if action == "start":
        recorder.start()
        return {"status": "recording"}
    if action == "stop":
        path = recorder.stop()
        if path is None:
            raise HTTPException(status_code=400, detail="No audio recorded")
        return {"file": os.path.basename(path)}
    raise HTTPException(status_code=400, detail="Invalid action")


@app.get("/transcribe")
async def transcribe(file: str):
    """Transcribe ``file`` from :data:`RECORDING_DIR`."""
    path = os.path.join(RECORDING_DIR, file)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    text = run_model(path)
    return {"transcript": text}


def main() -> None:
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
