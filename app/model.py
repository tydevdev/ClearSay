"""Speech-to-text model integration using a fine-tuned Whisper model."""

from typing import Any

import torch
import whisper


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

    # Load the base small.en Whisper model
    model: Any = whisper.load_model("small.en")

    # Load fine-tuned weights from the models directory
    state_dict = torch.load(
        "models/fine_tuned_whisper_small_en_v4.pth",
        map_location="cpu",
    )
    model.load_state_dict(state_dict)

    # Perform transcription on the given audio file
    result = model.transcribe(audio_path)

    # Return the text component of the result (empty string if missing)
    return result.get("text", "")
