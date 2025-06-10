# ClearSay

ClearSay is a simple desktop application to help children like William practice speech. Click **Start Recording** and the app records from your microphone before transcribing it with a fine-tuned Whisper model. Each recording is saved in `recorded_audio/` and the matching transcript is written to `transcripts/`.

## Requirements

- Python 3.8+
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running

Execute the application from the `app` folder:

```bash
python app.py
```

A dark-themed window will appear with a button to trigger the dummy transcription model.
