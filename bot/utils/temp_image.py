# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path


def save_temp_png(data: bytes, *, prefix: str = "lq_") -> Path:
    fd, name = tempfile.mkstemp(suffix=".png", prefix=prefix)
    path = Path(name)
    with open(fd, "wb") as f:
        f.write(data)
    return path
