# ClearSay

ClearSay is a simple desktop application to help children like William practice speech. Click **Start Recording** and the app records from your microphone before transcribing it with a fine-tuned Whisper model.

Transcripts accumulate in a single buffer so you can pause and resume dictation. Data now lives under `saved_data/` with `recorded_audio/` for the audio files and `audio_transcripts/` for the text. Each recording is saved as `RECORDING_YYYY-MM-DD_HH-MM-SS-ffffff.wav` and has a matching transcript file `TRANSCRIPT_YYYY-MM-DD_HH-MM-SS-ffffff.txt`. A metadata file tracks the order of these segments when building the combined transcript. The microsecond component prevents collisions when recordings are created rapidly.

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
