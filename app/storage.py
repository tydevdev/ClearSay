import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Callable

from utils.fileio import atomic_write
from constants import (
    DISCUSSIONS_DIR,
    DISCUSSION_ID_FORMAT,
    TIMESTAMP_FORMAT,
)


class DiscussionStorage:
    """Manage recordings and transcripts grouped by discussion."""

    def __init__(self) -> None:
        self.current_id: Optional[str] = None
        self.discussion_path: Optional[str] = None
        self.audio_dir: Optional[str] = None
        self.transcripts_dir: Optional[str] = None
        self.segments_json: Optional[str] = None
        self.full_transcript: Optional[str] = None
        self.segments: List[Dict[str, str]] = []
        self.segment_count: int = 0
        self.name: Optional[str] = None

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _write_segments(self) -> None:
        if not self.segments_json:
            return
        data = {"created_at": self.current_id, "name": self.name, "segments": self.segments}
        atomic_write(self.segments_json, json.dumps(data, indent=2))

    def _start_new_discussion(self) -> None:
        timestamp = datetime.now().strftime(DISCUSSION_ID_FORMAT)
        self.current_id = timestamp
        self.discussion_path = os.path.join(DISCUSSIONS_DIR, timestamp)
        self.audio_dir = os.path.join(self.discussion_path, "audio")
        self.transcripts_dir = os.path.join(self.discussion_path, "transcripts")
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.transcripts_dir, exist_ok=True)
        self.segments_json = os.path.join(self.discussion_path, "segments.json")
        self.full_transcript = os.path.join(
            self.discussion_path, "transcript_full.txt"
        )
        self.segments = []
        self.segment_count = 0
        self.name = None
        atomic_write(
            self.segments_json,
            json.dumps({"created_at": timestamp, "name": None, "segments": []}, indent=2),
        )
        atomic_write(self.full_transcript, "")

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def new(self) -> None:
        """Reset the internal state."""
        self.current_id = None
        self.discussion_path = None
        self.audio_dir = None
        self.transcripts_dir = None
        self.segments_json = None
        self.full_transcript = None
        self.segments = []
        self.segment_count = 0
        self.name = None

    def add_segment(self, text: str, audio_path: str, duration: float = 0.0) -> bool:
        """Persist ``text`` and ``audio_path`` inside the current discussion."""
        if not text:
            return True
        if self.current_id is None:
            self._start_new_discussion()
        assert (
            self.discussion_path
            and self.audio_dir
            and self.transcripts_dir
            and self.full_transcript
        )
        self.segment_count += 1
        seg_id = f"seg{self.segment_count:03d}"
        wav_name = f"{seg_id}.wav"
        txt_name = f"{seg_id}.txt"
        wav_dest = os.path.join(self.audio_dir, wav_name)
        try:
            shutil.move(audio_path, wav_dest)
        except Exception:
            wav_dest = audio_path
        txt_dest = os.path.join(self.transcripts_dir, txt_name)
        atomic_write(txt_dest, text.strip() + "\n")
        entry = {
            "id": seg_id,
            "wav": os.path.relpath(wav_dest, self.discussion_path),
            "txt": os.path.relpath(txt_dest, self.discussion_path),
            "timestamp": datetime.now().strftime(TIMESTAMP_FORMAT),
            "duration": duration,
        }
        self.segments.append(entry)
        self._write_segments()
        # append to transcript
        existing = os.path.exists(self.full_transcript) and os.path.getsize(self.full_transcript) > 0
        with open(self.full_transcript, "a", encoding="utf-8") as f:
            if existing:
                f.write("\n\n")
            f.write(text.strip())
        return True

    # compatibility wrapper
    def append_segment(self, text: str, audio_path: str) -> bool:
        return self.add_segment(text, audio_path)

    def append(self, text: str, audio_path: str) -> bool:
        return self.add_segment(text, audio_path)

    def save_full(self, text: str, timestamp: Optional[str] = None) -> Optional[str]:
        if not self.full_transcript:
            if timestamp is None:
                return None
            self._start_new_discussion()
        assert self.full_transcript
        atomic_write(self.full_transcript, text.strip() + "\n")
        return self.full_transcript

    def save(self, text: str, timestamp: Optional[str] = None) -> Optional[str]:
        return self.save_full(text, timestamp)

    def list(self, filter_text: str = "") -> List[str]:
        """Return available discussion folders."""
        if not os.path.exists(DISCUSSIONS_DIR):
            return []
        dirs = [d for d in os.listdir(DISCUSSIONS_DIR) if os.path.isdir(os.path.join(DISCUSSIONS_DIR, d))]
        dirs.sort()
        if filter_text:
            dirs = [d for d in dirs if filter_text.lower() in d.lower()]
        return dirs

    def load(self, name: str) -> Optional[str]:
        path = os.path.join(DISCUSSIONS_DIR, name, "transcript_full.txt")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def set_name(self, name: Optional[str]) -> None:
        """Set a user-friendly name for the current discussion."""
        self.name = name.strip() if name else None
        self._write_segments()

    def retranscribe_last_segment(self, transcribe_func: Callable[[str], str]) -> Optional[str]:
        if not self.segments:
            return None
        last = self.segments[-1]
        wav = os.path.join(self.discussion_path, last["wav"])
        txt = os.path.join(self.discussion_path, last["txt"])
        try:
            new_text = transcribe_func(wav)
        except Exception:
            return None
        atomic_write(txt, new_text.strip() + "\n")
        # rebuild full transcript
        texts = []
        for seg in self.segments:
            p = os.path.join(self.discussion_path, seg["txt"])
            with open(p, "r", encoding="utf-8") as f:
                texts.append(f.read().strip())
        atomic_write(self.full_transcript, "\n\n".join(texts) + "\n")
        return new_text


# Backwards compatibility
TranscriptStorage = DiscussionStorage
