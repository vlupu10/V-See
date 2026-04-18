"""
Built-in music player using Qt Multimedia (QMediaPlayer + QAudioOutput).

Provides folder-based playlist playback for MP3 and other common formats
without the optional vio-python / mp3_player dependency.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)

AUDIO_FILE_EXTENSIONS = frozenset(
    {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
)


def load_sound_files(sound_dir: Path) -> dict[str, Path]:
    """
    Return a map of file stem -> path for recognised audio files in the folder.

    Same contract as mp3_player.load_sound_files: non-recursive, one level only.
    """
    try:
        if not sound_dir.exists() or not sound_dir.is_dir():
            return {}
    except OSError:
        return {}
    out: dict[str, Path] = {}
    try:
        for path in sorted(sound_dir.iterdir(), key=lambda p: p.name.lower()):
            if path.is_file() and path.suffix.lower() in AUDIO_FILE_EXTENSIONS:
                out[path.stem] = path
    except OSError:
        return {}
    return out


class QtMusicPlayerWidget(QWidget):
    """
    Transport controls + volume for sequential playback of a folder of audio files.

    API subset expected by MainWindow: set_playlist_from_folder, start_playback,
    stop_playback, is_playing.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.85)

        self._tracks: list[Path] = []
        self._index = 0
        self._folder: Path | None = None

        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)

        self._btn_play = QPushButton("Play", self)
        self._btn_play.setToolTip("Play or pause")
        self._btn_play.clicked.connect(self._on_play_clicked)
        self._btn_stop = QPushButton("Stop", self)
        self._btn_stop.setToolTip("Stop playback")
        self._btn_stop.clicked.connect(self.stop_playback)
        self._btn_next = QPushButton("Next", self)
        self._btn_next.setToolTip("Next track in folder")
        self._btn_next.clicked.connect(self._on_next_clicked)

        self._volume_slider = QSlider(Qt.Orientation.Horizontal, self)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(85)
        self._volume_slider.setMaximumWidth(140)
        self._volume_slider.setToolTip("Volume")
        self._volume_slider.valueChanged.connect(self._on_volume_changed)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 0)
        row.addWidget(self._btn_play)
        row.addWidget(self._btn_stop)
        row.addWidget(self._btn_next)
        row.addWidget(QLabel("Vol:", self))
        row.addWidget(self._volume_slider)
        row.addStretch(1)

    def set_playlist_from_folder(
        self,
        folder: Path,
        start_from_name: str | None = None,
    ) -> None:
        """Build ordered playlist from folder; optional stem to start from."""
        self.stop_playback()
        self._folder = folder
        try:
            paths = sorted(
                (
                    p
                    for p in folder.iterdir()
                    if p.is_file() and p.suffix.lower() in AUDIO_FILE_EXTENSIONS
                ),
                key=lambda p: p.name.lower(),
            )
        except OSError:
            self._tracks = []
            self._index = 0
            return
        self._tracks = paths
        self._index = 0
        if start_from_name and self._tracks:
            for i, p in enumerate(self._tracks):
                if p.stem == start_from_name:
                    self._index = i
                    break

    def start_playback(self) -> None:
        """Start or resume playback from the current playlist index."""
        if not self._tracks:
            return
        if self._index >= len(self._tracks):
            self._index = 0
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PausedState:
            self._player.play()
            return
        if state == QMediaPlayer.PlaybackState.PlayingState:
            return
        self._load_and_play_current()

    def stop_playback(self) -> None:
        """Stop the media player."""
        self._player.stop()

    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _load_and_play_current(self) -> None:
        if not self._tracks or self._index >= len(self._tracks):
            return
        path = self._tracks[self._index]
        try:
            url = QUrl.fromLocalFile(str(path.resolve()))
        except OSError:
            return
        self._player.setSource(url)
        self._player.play()

    def _on_play_clicked(self) -> None:
        if not self._tracks:
            return
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self._player.play()
        else:
            self.start_playback()

    def _on_next_clicked(self) -> None:
        if not self._tracks:
            return
        if self._index + 1 < len(self._tracks):
            self._index += 1
        else:
            self._index = 0
        self._load_and_play_current()

    def _on_volume_changed(self, value: int) -> None:
        self._audio_output.setVolume(max(0.0, min(1.0, value / 100.0)))

    def _on_playback_state_changed(self, _state: QMediaPlayer.PlaybackState) -> None:
        playing = self.is_playing()
        self._btn_play.setText("Pause" if playing else "Play")

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        if not self._tracks:
            return
        self._index += 1
        if self._index < len(self._tracks):
            self._load_and_play_current()
        else:
            self._index = 0
            self._player.stop()
