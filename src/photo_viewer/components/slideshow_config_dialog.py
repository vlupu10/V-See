"""
Configure Slideshow dialog for V-See.

Modal dialog to set slideshow options: interval in seconds (1–3600) and
music selection (No music, or any mp3/wav/etc. from the folder's music subfolder).
Uses QSpinBox for numeric input and QComboBox for music.

Author: Viorel LUPU
Date: 2025-02-10
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSizePolicy,
    QSpinBox,
    QWidget,
)

from photo_viewer.services.persistence import (
    get_slideshow_interval_seconds,
    get_slideshow_music,
    set_slideshow_interval_seconds,
    set_slideshow_music,
)

try:
    from mp3_player import load_sound_files
except ImportError:
    try:
        from photo_viewer.services.audio import load_sound_files
    except ImportError:
        load_sound_files = None  # type: ignore[assignment, misc]


class SlideshowConfigDialog(QDialog):
    """
    Dialog to configure slideshow settings.

    Offers interval in seconds via QSpinBox and music selection via QComboBox.
    Music options:
    - "No music" - no background music
    - "All songs in the selected music folder" - play all songs in order
    - Individual song names - play all songs starting from the selected one
    """

    NO_MUSIC = "No music"
    ALL_SONGS = "All songs in the selected music folder"

    def __init__(
        self,
        parent: QWidget | None = None,
        music_folder: Path | None = None,
    ) -> None:
        """
        Create the dialog.

        Parameters
        ----------
        parent
            Parent widget (e.g. ImageViewerWindow).
        music_folder
            Path to the music folder (e.g. images_folder / "music").
            If None or folder has no audio files, only "No music" is shown.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure Slideshow")
        self.setMinimumWidth(420)

        self._spin_seconds = QSpinBox(self)
        self._spin_seconds.setRange(1, 3600)
        self._spin_seconds.setSuffix(" s")
        self._spin_seconds.setValue(get_slideshow_interval_seconds())

        self._combo_music = QComboBox(self)
        self._combo_music.setMinimumWidth(320)
        self._combo_music.setMinimumContentsLength(35)
        self._combo_music.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._combo_music.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._combo_music.addItem(self.NO_MUSIC)
        self._combo_music.addItem(self.ALL_SONGS)
        if music_folder is not None and load_sound_files is not None:
            songs = load_sound_files(music_folder)
            for name in sorted(songs.keys()):
                self._combo_music.addItem(name)
        self._set_combo_to_saved()

        layout = QFormLayout(self)
        layout.addRow("Interval between slides:", self._spin_seconds)
        layout.addRow("Music:", self._combo_music)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _set_combo_to_saved(self) -> None:
        saved = get_slideshow_music()
        idx = self._combo_music.findText(saved)
        if idx >= 0:
            self._combo_music.setCurrentIndex(idx)
        else:
            self._combo_music.setCurrentIndex(0)

    def accept(self) -> None:
        """Save the chosen interval and music to persistence and close."""
        set_slideshow_interval_seconds(self._spin_seconds.value())
        set_slideshow_music(self._combo_music.currentText())
        super().accept()
