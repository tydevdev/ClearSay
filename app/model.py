"""Speech-to-text model integration using a fine-tuned Whisper model."""

from typing import Any
import os

from constants import ROOT_DIR

import torch
import whisper

_MODEL: Any | None = None


def _load_model() -> Any:
    """Load and cache the fine-tuned Whisper model."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    base_model: Any = whisper.load_model("small.en")
    weights_path = os.path.join(ROOT_DIR, "models", "fine_tuned_whisper_small_en_v4.pth")
    if not os.path.exists(weights_path):
        raise FileNotFoundError(weights_path)
    state_dict = torch.load(weights_path, map_location="cpu")
    base_model.load_state_dict(state_dict)
    _MODEL = base_model
    return _MODEL


def run_model(audio_path: str) -> str:
    """Transcribe ``audio_path`` using a fine-tuned Whisper model.

    Parameters
    ----------
    audio_path:
        Path to the audio file that should be transcribed.

    Returns
    -------
    str
        The transcribed text.
    """

    model: Any = _load_model()

    # Perform transcription on the given audio file
    result = model.transcribe(audio_path)

    # Return the text component of the result (empty string if missing)
    return result.get("text", "")
