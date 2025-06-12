import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from utils.fileio import atomic_write


class TestAtomicWrite(unittest.TestCase):
    def test_atomic_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            atomic_write(path, "hello")
            with open(path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "hello")

            atomic_write(path, "goodbye")
            with open(path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "goodbye")


if __name__ == "__main__":
    unittest.main()
