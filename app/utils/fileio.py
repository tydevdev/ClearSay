import os
import tempfile
from typing import Union


def atomic_write(path: str, data: Union[str, bytes]) -> None:
    """Write ``data`` to ``path`` atomically."""
    dir_name = os.path.dirname(path) or '.'
    mode = 'w'
    if isinstance(data, bytes):
        mode = 'wb'
    with tempfile.NamedTemporaryFile(mode, dir=dir_name, delete=False, encoding=None if isinstance(data, bytes) else 'utf-8') as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
    os.replace(tmp.name, path)

