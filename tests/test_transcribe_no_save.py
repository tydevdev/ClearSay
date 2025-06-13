import os
import sys
import tempfile
import asyncio
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

# Provide minimal 'fastapi' stub to import server without dependencies
import types
fastapi_stub = types.ModuleType("fastapi")
class _FakeApp:
    def add_middleware(self, *a, **k):
        pass
    def post(self, *a, **k):
        def wrapper(f):
            return f
        return wrapper
    def get(self, *a, **k):
        def wrapper(f):
            return f
        return wrapper
fastapi_stub.FastAPI = lambda *a, **k: _FakeApp()
fastapi_stub.HTTPException = type("HTTPException", (Exception,), {})
fastapi_stub.Request = object
fastapi_stub.__version__ = "0"
cors_module = types.ModuleType("fastapi.middleware.cors")
cors_module.CORSMiddleware = object
middleware_module = types.ModuleType("fastapi.middleware")
middleware_module.cors = cors_module
fastapi_stub.middleware = middleware_module
sys.modules.setdefault("fastapi", fastapi_stub)
sys.modules.setdefault("fastapi.middleware", middleware_module)
sys.modules.setdefault("fastapi.middleware.cors", cors_module)

# Stub heavy dependencies so server module can be imported
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sd_stub = types.ModuleType("sounddevice")
sd_stub.InputStream = object
sys.modules.setdefault("sounddevice", sd_stub)
sys.modules.setdefault("torch", types.ModuleType("torch"))
sys.modules.setdefault("whisper", types.ModuleType("whisper"))

import server
import constants
from storage import DiscussionStorage


class TestTranscribeNoSave(unittest.TestCase):
    def test_no_save_does_not_modify_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rec_dir = os.path.join(tmpdir, "rec")
            disc_dir = os.path.join(tmpdir, "disc")
            os.makedirs(rec_dir, exist_ok=True)
            os.makedirs(disc_dir, exist_ok=True)

            constants.RECORDING_DIR = rec_dir
            constants.DISCUSSIONS_DIR = disc_dir
            server.RECORDING_DIR = rec_dir
            server.DISCUSSIONS_DIR = disc_dir

            server.transcript_buffer = DiscussionStorage()

            audio_path = os.path.join(rec_dir, "a.wav")
            with open(audio_path, "wb") as f:
                f.write(b"data")

            with patch("server.run_model", return_value="hello"):
                result = asyncio.run(server.transcribe(file="a.wav", save=False))

            self.assertEqual(result["transcript"], "hello")
            self.assertEqual(server.transcript_buffer.segments, [])


if __name__ == "__main__":
    unittest.main()
