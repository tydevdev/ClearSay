import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from storage import DiscussionStorage
from utils.fileio import atomic_write
import constants


class TestRetranscribeOverwrite(unittest.TestCase):
    def test_overwrite_existing_segment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = constants.DISCUSSIONS_DIR
            constants.DISCUSSIONS_DIR = os.path.join(tmpdir, "discussions")
            os.makedirs(constants.DISCUSSIONS_DIR, exist_ok=True)

            store = DiscussionStorage()

            audio = os.path.join(tmpdir, "a.wav")
            atomic_write(audio, b"data")
            store.add_segment("hello", audio)

            audio_existing = os.path.join(store.audio_dir, "seg001.wav")
            store.add_segment("goodbye", audio_existing)

            txt_path = os.path.join(store.transcripts_dir, "seg001.txt")
            with open(txt_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read().strip(), "goodbye")

            self.assertEqual(len(store.segments), 1)
            with open(store.full_transcript, "r", encoding="utf-8") as f:
                self.assertEqual(f.read().strip(), "goodbye")

            constants.DISCUSSIONS_DIR = old_dir


if __name__ == "__main__":
    unittest.main()
