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
# Include microseconds to avoid filename collisions when recordings
# happen in quick succession.
TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"

# Directories for recorded audio and discussion data
RECORDING_DIR = os.path.join(DATA_DIR, "recorded_audio")
DISCUSSIONS_DIR = os.path.join(DATA_DIR, "discussions")

# Timestamp format for discussion folders (no microseconds)
DISCUSSION_ID_FORMAT = "%Y-%m-%d_%H-%M-%S"
os.makedirs(RECORDING_DIR, exist_ok=True)
os.makedirs(DISCUSSIONS_DIR, exist_ok=True)
