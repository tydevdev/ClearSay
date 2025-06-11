import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Global UI colors
TEXT_COLOR = "#000000"
BUTTON_FG = "#d0e7ff"
BUTTON_HOVER = "#b0d4ff"

# Recording parameters
SAMPLE_RATE = 44100

# Directories for recorded audio and saved transcripts
RECORDING_DIR = os.path.join(ROOT_DIR, "recorded_audio")
TRANSCRIPT_DIR = os.path.join(ROOT_DIR, "transcripts")

os.makedirs(RECORDING_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
