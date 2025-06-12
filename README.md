# ClearSay

ClearSay is a simple desktop application to help children like William practice speech. Click **Start Recording** and the app records from your microphone before transcribing it with a fine-tuned Whisper model.

Transcripts accumulate within a *Discussion* folder so you can pause and resume dictation. When you start recording the app creates `saved_data/discussions/YYYY-MM-DD_HH-MM-SS/` with `audio/` and `transcripts/` subfolders plus `segments.json` and `transcript_full.txt`. Each subsequent recording becomes `audio/segNNN.wav` with a matching `transcripts/segNNN.txt`. The transcript snippets are appended to the full transcript file while `segments.json` tracks ordering and timestamps. An optional `name` field in `segments.json` stores a custom discussion title without renaming the folder. If you press **Re-Transcribe** with no active discussion, ClearSay automatically uses the most recent session so the previous name carries forward.

## Requirements

- Python 3.8+
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter)

Two ``requirements`` files split the dependencies:

* ``requirements-server.txt`` – packages needed to run the FastAPI server
* ``requirements-ui.txt`` – UI dependencies such as ``customtkinter``

Install server requirements (no UI packages) with:

```bash
pip install -r requirements-server.txt
```

The ``check-server.sh`` script creates a ``venv`` and installs only these
packages before running a quick health check. It requires no GUI libraries.

To install the UI dependencies later, place the wheel files in ``wheels/`` and
run ``./install-ui.sh`` or execute the command below:

```bash
pip install --no-index --find-links=./wheels -r requirements-ui.txt
```

## Running

Execute the application from the `app` folder:

```bash
python app.py
```

The app now uses a single light theme with soft blue accents for readability. A
**Re-Transcribe** button in both the Python and Electron interfaces lets you run
the model again on the most recent recording.

### API server

A lightweight FastAPI server provides recording and transcription endpoints for
the Electron UI. Install its dependencies and launch it with ``./check-server.sh``
or run it manually:

```bash
python -m app.server
```

The server binds only to `localhost` on port `8000`.

## Electron wrapper

A minimal Electron app lives in `electron/` to package ClearSay for the desktop. Install Node dependencies and launch it in development mode with:

```bash
cd electron
npm install
npm run start
```

`Option + Space` toggles focus of the window when running on macOS.
