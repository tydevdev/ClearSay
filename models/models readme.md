Please reference this document as it has important information for you to consider. 

# models/

This folder contains model files used by the application, but they are excluded from Git version control due to their size.

The following files should be assumed to exist here when writing code:

- `small.en.pt` — the original Whisper small.en model weights
- `small.en.pth` — an alternative copy of the same base model (may be used interchangeably)
- `fine_tuned_whisper_small_en_v4.pth` — fine-tuned weights trained on William's speech data

All model-loading code should reference these files from the `models/` directory using relative paths.

Do **not** generate or modify these files. Just write code that expects them to be present.