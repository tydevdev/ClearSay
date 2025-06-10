import os
from datetime import datetime
from typing import List, Optional

from constants import TRANSCRIPT_DIR


class TranscriptManager:
    """Manage saving and loading of transcript files."""

    def __init__(self) -> None:
        self.current_path: Optional[str] = None

    def save(self, text: str) -> Optional[str]:
        """Write ``text`` to the current transcript file."""
        if not text:
            return None
        if self.current_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_path = os.path.join(
                TRANSCRIPT_DIR, f"transcript_{timestamp}.txt"
            )
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        try:
            with open(self.current_path, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        except OSError:
            return None
        return self.current_path

    def new(self) -> None:
        """Reset the current transcript so a new file is created on save."""
        self.current_path = None

    def list(self, filter_text: str = "") -> List[str]:
        """Return available transcript file names."""
        files = sorted(
            f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt")
        )
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
