import os
import queue
import wave
from datetime import datetime
from typing import Optional

import numpy as np
try:
    import sounddevice as sd
except Exception as exc:  # pragma: no cover - optional dep
    sd = None  # type: ignore
    print(f"sounddevice not available: {exc}")

from constants import RECORDING_DIR, SAMPLE_RATE, TIMESTAMP_FORMAT


class Recorder:
    """Handle audio recording using sounddevice."""

    def __init__(self) -> None:
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self.stream: Optional[object] = None
        self.recording = False
        self.last_timestamp: Optional[str] = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def start(self) -> bool:
        """Begin recording from the microphone.

        Returns
        -------
        bool
            ``True`` if recording successfully started, else ``False``.
        """
        if sd is None:
            print("Recording unavailable: sounddevice not installed")
            return False
        if self.recording:
            return True
        # create a new queue to avoid thread-safety issues
        self.audio_queue = queue.Queue()
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                callback=self._callback,
            )
            self.stream.start()
        except Exception as exc:
            print(f"Failed to start recording: {exc}")
            self.stream = None
            return False
        self.recording = True
        return True

    def stop(self) -> Optional[str]:
        """Stop recording and save the audio to disk.

        Returns
        -------
        Optional[str]
            Path to the saved audio file or ``None`` if no audio was recorded.
        """
        if sd is None or not self.recording:
            print("Stop called but no recording in progress")
            return None
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as exc:
                print(f"Failed to stop recording: {exc}")
            finally:
                self.stream = None
        frames = []
        while not self.audio_queue.empty():
            frames.append(self.audio_queue.get())
        self.recording = False
        if not frames:
            return None
        audio = np.concatenate(frames, axis=0)
        audio = np.int16(audio * 32767)
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        self.last_timestamp = timestamp
        file_path = os.path.join(RECORDING_DIR, f"RECORDING_{timestamp}.wav")
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
        return file_path
