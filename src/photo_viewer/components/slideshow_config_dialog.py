"""
Configure Slideshow dialog for V-See.

Modal dialog to set slideshow options. Currently offers only the
interval in seconds (1–3600). More options (loop, shuffle, etc.)
can be added later. Uses QSpinBox for numeric input (similar to
HTML <input type="number"> with min/max/step).

Author: Photo Viewer Project
Date: 2025-02-10
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QWidget,
)

from photo_viewer.services.persistence import (
    get_slideshow_interval_seconds,
    set_slideshow_interval_seconds,
)


class SlideshowConfigDialog(QDialog):
    """
    Dialog to configure slideshow settings.

    For now only the interval in seconds is configurable via a
    QSpinBox (numeric input with up/down arrows and optional typing).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configure Slideshow")

        self._spin_seconds = QSpinBox(self)
        self._spin_seconds.setRange(1, 3600)
        self._spin_seconds.setSuffix(" s")
        self._spin_seconds.setValue(get_slideshow_interval_seconds())

        layout = QFormLayout(self)
        layout.addRow("Interval between slides:", self._spin_seconds)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self) -> None:
        """Save the chosen interval to persistence and close."""
        set_slideshow_interval_seconds(self._spin_seconds.value())
        super().accept()
