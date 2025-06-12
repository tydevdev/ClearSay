import os
import shutil
from datetime import datetime
from typing import List, Optional

from constants import TRANSCRIPT_DIR, TIMESTAMP_FORMAT


class TranscriptBuffer:
    """Accumulate transcription segments and persist to disk."""

    def __init__(self) -> None:
        self.base_timestamp: Optional[str] = None
        self.text_parts: List[str] = []
        self.counter = 1
        self.transcript_path: Optional[str] = None

    def _extract_timestamp(self, audio_path: str) -> str:
        """Return the timestamp portion from ``audio_path``."""
        name = os.path.splitext(os.path.basename(audio_path))[0]
        if name.startswith("RECORDING_"):
            return name[len("RECORDING_") :]
        return datetime.now().strftime(TIMESTAMP_FORMAT)

    def append(self, text: str, audio_path: str) -> bool:
        """Append a transcription and copy the audio file.

        Returns ``True`` if the transcript was written successfully."""
        if not text:
            return True
        if self.base_timestamp is None:
            self.base_timestamp = self._extract_timestamp(audio_path)
            self.transcript_path = os.path.join(
                TRANSCRIPT_DIR, f"{self.base_timestamp}.txt"
            )
        if os.path.exists(audio_path):
            dest = os.path.join(
                TRANSCRIPT_DIR,
                f"RECORDING_{self.base_timestamp}_{self.counter:03d}.wav",
            )
            try:
                shutil.copy2(audio_path, dest)
            except OSError:
                pass
        self.text_parts.append(text.strip())
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        try:
            with open(self.transcript_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(self.text_parts) + "\n")
        except OSError:
            return False
        finally:
            self.counter += 1
        return True
