import os
import queue
import wave
from datetime import datetime
from typing import Optional

import numpy as np
import sounddevice as sd

from constants import RECORDING_DIR


class Recorder:
    """Handle audio recording using sounddevice."""

    def __init__(self) -> None:
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self.stream: Optional[sd.InputStream] = None
        self.recording = False

    def _callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def start(self) -> None:
        """Begin recording from the microphone."""
        if self.recording:
            return
        self.audio_queue.queue.clear()
        self.stream = sd.InputStream(samplerate=44100, channels=1, callback=self._callback)
        self.stream.start()
        self.recording = True

    def stop(self) -> Optional[str]:
        """Stop recording and save the audio to disk.

        Returns
        -------
        Optional[str]
            Path to the saved audio file or ``None`` if no audio was recorded.
        """
        if not self.recording:
            return None
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
        frames = []
        while not self.audio_queue.empty():
            frames.append(self.audio_queue.get())
        self.recording = False
        if not frames:
            return None
        audio = np.concatenate(frames, axis=0)
        audio = np.int16(audio * 32767)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(RECORDING_DIR, f"recording_{timestamp}.wav")
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(audio.tobytes())
        return file_path
