"""
Audio helpers for V-See.

``load_sound_files`` is always available (Qt-side scan in
``qt_music_player_widget``). Optional ``mp3_player`` (vio-python) adds the
``SoundPlayer`` API for programmatic playback outside the main UI.
"""

from __future__ import annotations

from photo_viewer.components.qt_music_player_widget import load_sound_files

try:
    from mp3_player import (
        SoundPlayer,
        format_seconds,
        get_audio_duration_seconds,
    )
except ImportError:
    SoundPlayer = None  # type: ignore[misc, assignment]
    format_seconds = None  # type: ignore[misc, assignment]
    get_audio_duration_seconds = None  # type: ignore[misc, assignment]

__all__ = [
    "SoundPlayer",
    "format_seconds",
    "get_audio_duration_seconds",
    "load_sound_files",
]
