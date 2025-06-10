# ClearSay

ClearSay is a simple desktop application to help children like William practice speech. When you click **Start Transcription**, a file dialog opens so you can choose a `.wav` recording, which is then transcribed using a fine-tuned Whisper model.

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
