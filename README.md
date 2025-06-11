# ClearSay

ClearSay is a simple desktop application to help children like William practice speech. Click **Start Recording** and the app records from your microphone before transcribing it. If the optional Whisper dependencies are missing the server will simply return placeholder text.

Transcripts now accumulate in a single buffer so you can pause and resume dictation. Each recording is saved in `recorded_audio/` as `RECORDING_YYYY_MM_DD_HH_MM.wav`. The matching transcript is written to `transcripts/` with the identical timestamp, e.g. `TRANSCRIPT_YYYY_MM_DD_HH_MM.txt`.

## Requirements

- Python 3.8+
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter)

Two ``requirements`` files split the dependencies:

* ``requirements-server.txt`` – minimal packages for the FastAPI server
* ``requirements-ui.txt`` – UI dependencies such as ``customtkinter``

Install server requirements (no UI packages) with:

```bash
pip install -r requirements-server.txt
```

The ``check-server.sh`` script creates a ``venv`` and installs only these
packages before running a quick health check. Recording and transcription use
``sounddevice`` and ``whisper`` which are optional. When they are missing the
server simply returns placeholder transcripts.

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

The app now uses a single light theme with soft blue accents for readability.

### API server

A lightweight FastAPI server provides recording and transcription endpoints for
the Electron UI. Install its dependencies and launch it with ``./check-server.sh``
or run it manually:

```bash
python -m app.server
```

The server binds only to `localhost` on port `8000`.

If optional dependencies are missing or something fails during startup,
the server prints detailed error messages but continues running where
possible. Check the terminal output for diagnostics.

### Exporting transcripts

The optional DOCX export previously depended on `python-docx`. To simplify
setup, the `/export-docx` endpoint now saves plain text files instead. Any text
sent to this endpoint will be written to `transcripts/EXPORT_YYYY_MM_DD_HH_MM_SS.txt`.

## Electron wrapper

A minimal Electron app lives in `electron/` to package ClearSay for the desktop. Install Node dependencies and launch it in development mode with:

```bash
cd electron
npm install
npm run start
```

`Option + Space` toggles focus of the window when running on macOS.
