"""
Video playback diagnostics logger.

Writes timestamped log lines to a file with immediate flush (line buffering)
so that data is persisted before an OS-level crash. Use for debugging
video player freezes and crashes.

Log file: <app config dir>/video_playback.log

Author: Viorel LUPU
Date: 2025-02
"""

from __future__ import annotations

import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import TextIO

# Config dir: same location as persistence (config subfolder)
_CONFIG_SUBDIR = "config"
_LOG_FILENAME = "video_playback.log"
_file: TextIO | None = None
_log_path_printed = False
_lock = threading.Lock()


def _log_path() -> Path:
    """Return path to the video playback log file."""
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).resolve().parent
    else:
        app_dir = Path(sys.argv[0]).resolve().parent
    config_dir = app_dir / _CONFIG_SUBDIR
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / _LOG_FILENAME


def _ensure_open() -> TextIO | None:
    """Open log file with line buffering (each write is flushed)."""
    global _file, _log_path_printed
    with _lock:
        if _file is not None:
            return _file
        try:
            path = _log_path()
            _file = open(path, "a", buffering=1, encoding="utf-8")
            if not _log_path_printed:
                print(f"V-See video log: {path}", flush=True)
                _log_path_printed = True
            return _file
        except OSError:
            return None


def log(source: str, message: str, **kwargs: str | int | float) -> None:
    """
    Append a timestamped log line and flush immediately.

    source: Where the log originates (e.g. "viewer", "preview").
    message: Short description.
    **kwargs: Additional key=value pairs to append.
    """
    f = _ensure_open()
    if f is None:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    line = f"{ts} [{source}] {message}"
    if extra:
        line += f" {extra}"
    line += "\n"
    try:
        f.write(line)
        f.flush()
    except OSError:
        pass


def close() -> None:
    """Close the log file. Safe to call multiple times."""
    global _file
    if _file is not None:
        try:
            _file.close()
        except OSError:
            pass
        _file = None


def get_log_path() -> Path:
    """Return the path to the log file (for user reference)."""
    return _log_path()
