import os
import json
from datetime import datetime
from typing import List, Optional, Dict

from constants import TRANSCRIPT_DIR, TIMESTAMP_FORMAT, METADATA_DIR


class TranscriptManager:
    """Manage saving and loading of transcript files."""

    def __init__(self) -> None:
        self.current_path: Optional[str] = None
        self.metadata_path: Optional[str] = None
        self.base_timestamp: Optional[str] = None
        self.segments: List[Dict[str, str]] = []

    def _extract_timestamp(self, audio_path: str) -> str:
        """Return timestamp portion from an audio filename."""
        name = os.path.splitext(os.path.basename(audio_path))[0]
        if name.startswith("RECORDING_"):
            return name[len("RECORDING_") :]
        return datetime.now().strftime(TIMESTAMP_FORMAT)

    def _save_metadata(self) -> None:
        if self.metadata_path is None:
            return
        os.makedirs(METADATA_DIR, exist_ok=True)
        try:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump({"segments": self.segments}, f, indent=2)
        except OSError:
            pass

    def add_segment(self, text: str, audio_path: str) -> None:
        """Persist ``text`` for ``audio_path`` and update metadata."""
        if not text:
            return
        timestamp = self._extract_timestamp(audio_path)
        if self.base_timestamp is None:
            self.base_timestamp = timestamp
            self.current_path = os.path.join(TRANSCRIPT_DIR, f"{self.base_timestamp}.txt")
            self.metadata_path = os.path.join(METADATA_DIR, f"{self.base_timestamp}.json")
        seg_name = f"TRANSCRIPT_{timestamp}.txt"
        seg_path = os.path.join(TRANSCRIPT_DIR, seg_name)
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        try:
            with open(seg_path, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        except OSError:
            pass
        self.segments.append({"audio": os.path.basename(audio_path), "transcript": seg_name})
        self._save_metadata()

    def save(self, text: str, timestamp: Optional[str] = None) -> Optional[str]:
        """Write ``text`` to the current transcript file."""
        if not text:
            return None
        if self.current_path is None:
            if timestamp is None:
                timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
            self.current_path = os.path.join(TRANSCRIPT_DIR, f"{timestamp}.txt")
            self.metadata_path = os.path.join(METADATA_DIR, f"{timestamp}.json")
            self.base_timestamp = timestamp
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        try:
            with open(self.current_path, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        except OSError:
            return None
        self._save_metadata()
        return self.current_path

    def new(self) -> None:
        """Reset the current transcript so a new file is created on save."""
        self.current_path = None
        self.metadata_path = None
        self.base_timestamp = None
        self.segments = []

    def list(self, filter_text: str = "") -> List[str]:
        """Return available transcript file names."""
        files = [
            f
            for f in os.listdir(TRANSCRIPT_DIR)
            if f.endswith(".txt") and not f.startswith("TRANSCRIPT_")
        ]
        files.sort()
        if filter_text:
            files = [f for f in files if filter_text.lower() in f.lower()]
        return files

    def load(self, name: str) -> Optional[str]:
        """Load the contents of ``name`` if it exists."""
        path = os.path.join(TRANSCRIPT_DIR, name)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
