import os
import json
from datetime import datetime
from typing import List, Optional, Dict

from constants import TRANSCRIPT_DIR, TIMESTAMP_FORMAT, METADATA_DIR


class TranscriptBuffer:
    """Accumulate transcription segments and persist to disk."""

    def __init__(self) -> None:
        self.base_timestamp: Optional[str] = None
        self.text_parts: List[str] = []
        self.counter = 1
        self.transcript_path: Optional[str] = None
        self.metadata_path: Optional[str] = None
        self.segments: List[Dict[str, str]] = []

    def _extract_timestamp(self, audio_path: str) -> str:
        """Return the timestamp portion from ``audio_path``."""
        name = os.path.splitext(os.path.basename(audio_path))[0]
        if name.startswith("RECORDING_"):
            return name[len("RECORDING_") :]
        return datetime.now().strftime(TIMESTAMP_FORMAT)

    def append(self, text: str, audio_path: str) -> bool:
        """Append ``text`` for ``audio_path`` and update metadata.

        Returns ``True`` if the transcript was written successfully."""
        if not text:
            return True
        if self.base_timestamp is None:
            self.base_timestamp = self._extract_timestamp(audio_path)
            self.transcript_path = os.path.join(
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
            with open(seg_path, "w", encoding="utf-8") as f:
                f.write(text.strip() + "\n")
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
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        try:
            with open(self.transcript_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(self.text_parts) + "\n")
            if self.metadata_path:
                os.makedirs(METADATA_DIR, exist_ok=True)
                with open(self.metadata_path, "w", encoding="utf-8") as mf:
                    json.dump({"segments": self.segments}, mf, indent=2)
        except OSError:
            return False
        finally:
            self.counter += 1
        return True
