"""
Resolve ffmpeg and ffprobe executable paths.

When running as a PyInstaller bundle, uses bundled binaries from the app bundle.
On macOS .app: binaries live in Contents/Frameworks or Contents/Resources.
Otherwise: uses system PATH (shutil.which).
"""

from __future__ import annotations

import os
import shutil
import sys
from typing import Tuple


def _bundled_ffmpeg_paths() -> Tuple[str, str] | None:
    """Locate bundled ffmpeg/ffprobe when running as a frozen PyInstaller app."""
    if not getattr(sys, "frozen", False):
        return None

    exe_dir = os.path.dirname(sys.executable)
    # Search order: same dir as exe (onedir), then common bundle locations
    candidates = [exe_dir]
    # macOS .app: Contents/MacOS has exe; ffmpeg is in Contents/Frameworks or Contents/Resources
    if "Contents" in exe_dir:
        contents = os.path.dirname(exe_dir)
        candidates.extend([
            os.path.join(contents, "Frameworks"),
            os.path.join(contents, "Resources"),
        ])
    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, sys._MEIPASS)

    for base in candidates:
        ffmpeg = os.path.join(base, "ffmpeg")
        ffprobe = os.path.join(base, "ffprobe")
        if os.path.isfile(ffmpeg) and os.path.isfile(ffprobe):
            return (ffmpeg, ffprobe)
    return None


def get_ffmpeg_paths() -> Tuple[str, str]:
    """
    Return (ffmpeg_path, ffprobe_path) for subprocess calls.

    When frozen: uses bundled ffmpeg/ffprobe from the app bundle.
    Otherwise: uses shutil.which, falling back to bare 'ffmpeg'/'ffprobe'.
    """
    bundled = _bundled_ffmpeg_paths()
    if bundled:
        return bundled
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    ffprobe = shutil.which("ffprobe") or "ffprobe"
    return (ffmpeg, ffprobe)
