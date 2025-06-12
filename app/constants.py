import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Location for persisted data
DATA_DIR = os.path.join(ROOT_DIR, "saved_data")

# Global UI colors
TEXT_COLOR = "#000000"
BUTTON_FG = "#d0e7ff"
BUTTON_HOVER = "#b0d4ff"

# Recording parameters
SAMPLE_RATE = 44100

# Shared timestamp format for recordings and transcripts
# Use seconds for easier pairing of audio and text
TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"

# Directories for recorded audio, transcripts and metadata
RECORDING_DIR = os.path.join(DATA_DIR, "recorded_audio")
TRANSCRIPT_DIR = os.path.join(DATA_DIR, "audio_transcripts")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")

os.makedirs(RECORDING_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)
