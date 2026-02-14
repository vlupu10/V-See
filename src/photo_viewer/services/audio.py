"""
Audio playback service using the shared mp3-player library.

Re-exports the MP3 player API from mp3_player so V-See can use a single
import from photo_viewer.services.audio. Requires the mp3-player package
to be installed (pip install -e /path/to/vldesign/vio-python).

Usage in a PyQt widget:
    from photo_viewer.services.audio import (
        SoundPlayer,
        format_seconds,
        get_audio_duration_seconds,
        load_sound_files,
    )
    player = SoundPlayer(path_to_mp3, loop=False)
    player.play()
    # ... pause, resume, stop, get_position(), play(start_at=...)
"""

from mp3_player import (
    SoundPlayer,
    format_seconds,
    get_audio_duration_seconds,
    load_sound_files,
)

__all__ = [
    "SoundPlayer",
    "format_seconds",
    "get_audio_duration_seconds",
    "load_sound_files",
]
