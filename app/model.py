"""Speech-to-text model integration using a fine-tuned Whisper model."""

from typing import Any
import os

from constants import ROOT_DIR

try:
    import torch
    import whisper
except Exception as exc:  # pragma: no cover - optional deps
    torch = None  # type: ignore
    whisper = None  # type: ignore
    print(f"Whisper dependencies not available: {exc}")

_MODEL: Any | None = None


def _load_model() -> Any | None:
    """Load and cache the fine-tuned Whisper model if available."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    if whisper is None:
        return None

    try:
        base_model: Any = whisper.load_model("small.en")
    except Exception as exc:
        print(f"Failed to load base model: {exc}")
        return None

    weights_path = os.path.join(ROOT_DIR, "models", "fine_tuned_whisper_small_en_v4.pth")
    if os.path.exists(weights_path) and torch is not None:
        try:
            state_dict = torch.load(weights_path, map_location="cpu")
            base_model.load_state_dict(state_dict)
        except Exception as exc:
            print(f"Failed to load fine-tuned weights: {exc}")

    _MODEL = base_model
    return _MODEL


def run_model(audio_path: str) -> str:
    """Transcribe ``audio_path`` if Whisper is available.

    Parameters
    ----------
    audio_path:
        Path to the audio file that should be transcribed.

    Returns
    -------
    str
        The transcribed text.
    """

    model: Any | None = _load_model()
    if model is None:
        return "[transcription unavailable]"

    try:
        result = model.transcribe(audio_path)
    except Exception as exc:
        print(f"Transcription failed: {exc}")
        return "[transcription error]"

    return result.get("text", "")
