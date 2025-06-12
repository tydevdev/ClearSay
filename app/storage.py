import os
import json
from datetime import datetime
from typing import List, Dict, Optional

from utils.fileio import atomic_write
from constants import TRANSCRIPT_DIR, METADATA_DIR, TIMESTAMP_FORMAT


class TranscriptStorage:
    """Handle saving of transcription segments and full transcripts."""

    def __init__(self) -> None:
        self.base_timestamp: Optional[str] = None
        self.current_path: Optional[str] = None
        self.metadata_path: Optional[str] = None
        self.segments: List[Dict[str, str]] = []
        self.text_parts: List[str] = []

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _extract_timestamp(self, audio_path: str) -> str:
        name = os.path.splitext(os.path.basename(audio_path))[0]
        if name.startswith("RECORDING_"):
            return name[len("RECORDING_") :]
        return datetime.now().strftime(TIMESTAMP_FORMAT)

    def _save_metadata(self) -> None:
        if self.metadata_path is None:
            return
        os.makedirs(METADATA_DIR, exist_ok=True)
        try:
            atomic_write(
                self.metadata_path,
                json.dumps({"segments": self.segments}, indent=2),
            )
        except OSError:
            pass

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def new(self) -> None:
        """Reset internal state so a new transcript is created on save."""
        self.base_timestamp = None
        self.current_path = None
        self.metadata_path = None
        self.segments = []
        self.text_parts = []

    def load_latest(self) -> None:
        """Load the most recent transcript metadata and segments from disk."""
        files = [f for f in os.listdir(METADATA_DIR) if f.endswith(".json")]
        if not files:
            return
        files.sort()
        latest = files[-1]
        self.metadata_path = os.path.join(METADATA_DIR, latest)
        self.base_timestamp = os.path.splitext(latest)[0]
        self.current_path = os.path.join(TRANSCRIPT_DIR, f"{self.base_timestamp}.txt")
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except OSError:
            return
        self.segments = data.get("segments", [])
        self.text_parts = []
        for seg in self.segments:
            seg_file = os.path.join(TRANSCRIPT_DIR, seg.get("transcript", ""))
            try:
                with open(seg_file, "r", encoding="utf-8") as tf:
                    self.text_parts.append(tf.read().strip())
            except OSError:
                self.text_parts.append("")

    def append_segment(self, text: str, audio_path: str) -> bool:
        """Persist ``text`` for ``audio_path`` and update the combined transcript."""
        if not text:
            return True
        if self.base_timestamp is None:
            self.base_timestamp = self._extract_timestamp(audio_path)
            self.current_path = os.path.join(
                TRANSCRIPT_DIR, f"{self.base_timestamp}.txt"
            )
            self.metadata_path = os.path.join(
                METADATA_DIR, f"{self.base_timestamp}.json"
            )
        timestamp = self._extract_timestamp(audio_path)
        seg_name = f"TRANSCRIPT_{timestamp}.txt"
        seg_path = os.path.join(TRANSCRIPT_DIR, seg_name)
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        try:
            atomic_write(seg_path, text.strip() + "\n")
        except OSError:
            pass
        base_audio = os.path.basename(audio_path)
        try:
            idx = next(i for i, s in enumerate(self.segments) if s["audio"] == base_audio)
        except StopIteration:
            self.segments.append({"audio": base_audio, "transcript": seg_name})
            self.text_parts.append(text.strip())
        else:
            self.segments[idx] = {"audio": base_audio, "transcript": seg_name}
            self.text_parts[idx] = text.strip()
        if self.current_path:
            try:
                atomic_write(self.current_path, "\n\n".join(self.text_parts) + "\n")
            except OSError:
                return False
        self._save_metadata()
        return True

    # compatibility wrappers
    def append(self, text: str, audio_path: str) -> bool:
        return self.append_segment(text, audio_path)

    def add_segment(self, text: str, audio_path: str) -> bool:
        return self.append_segment(text, audio_path)

    def save_full(self, text: str, timestamp: Optional[str] = None) -> Optional[str]:
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
            atomic_write(self.current_path, text + "\n")
        except OSError:
            return None
        self.text_parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        self._save_metadata()
        return self.current_path

    def save(self, text: str, timestamp: Optional[str] = None) -> Optional[str]:
        return self.save_full(text, timestamp)

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


