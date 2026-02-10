"""
Standalone image viewer window for V-See.

Shows a single image at a time with Next / Previous navigation that
wraps around within the current folder. Intended to be opened when the
user double-clicks a thumbnail in the Manage mode grid.

Author: Photo Viewer Project
Date: 2025-02-10
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class ImageViewerWindow(QMainWindow):
    """
    Separate window for viewing a single image with navigation controls.

    The window knows the ordered list of image paths in the current folder
    and the index of the image currently shown. Next/Previous buttons move
    through the list with wrap-around at both ends.
    """

    def __init__(
        self,
        image_paths: Sequence[Path],
        start_index: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        """
        Create a new viewer window.

        Parameters
        ----------
        image_paths:
            Ordered list of images from the folder that was active when
            the user double-clicked a thumbnail.
        start_index:
            Index into image_paths of the image to show initially.
        parent:
            Optional parent; the window is still top-level.
        """
        super().__init__(parent)
        self.setWindowTitle("V-See – Viewer")
        self.resize(1200, 800)

        self._image_paths = list(image_paths)
        self._current_index = max(0, min(start_index, len(self._image_paths) - 1))

        # Simple slideshow: when active, a timer advances to the next image
        # every few seconds with wrap-around.
        self._slideshow_timer = QTimer(self)
        self._slideshow_timer.timeout.connect(self._on_slideshow_tick)
        self._slideshow_interval_ms = 3000

        self._slideshow_running = False

        self._image_label: QLabel
        self._filename_label: QLabel
        self._btn_prev: QPushButton
        self._btn_next: QPushButton
        self._btn_slideshow: QPushButton

        self._init_ui()
        self._update_image()

    # ------------------------------------------------------------------ UI

    def _init_ui(self) -> None:
        """
        Build toolbar + central image area.

        The toolbar hosts navigation and slideshow controls. The central
        area hosts the image label and filename.
        """
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        # Top toolbar-style row for controls.
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self._btn_prev = QPushButton("◀ Previous", central)
        self._btn_prev.clicked.connect(self.show_previous)

        self._btn_next = QPushButton("Next ▶", central)
        self._btn_next.clicked.connect(self.show_next)

        self._btn_slideshow = QPushButton("Slideshow ON", central)
        self._btn_slideshow.clicked.connect(self._toggle_slideshow)

        controls_layout.addWidget(self._btn_prev)
        controls_layout.addWidget(self._btn_next)
        controls_layout.addSpacing(16)
        controls_layout.addWidget(self._btn_slideshow)
        controls_layout.addStretch(1)

        # Main image area.
        self._image_label = QLabel(central)
        self._image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self._image_label.setMinimumHeight(400)
        self._image_label.setText("No image.")

        self._filename_label = QLabel(central)
        self._filename_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )

        root_layout.addLayout(controls_layout)
        root_layout.addWidget(self._image_label, stretch=1)
        root_layout.addWidget(self._filename_label)

    # ---------------------------------------------------------- navigation

    def show_next(self) -> None:
        """Advance to the next image, wrapping around at the end."""
        if not self._image_paths:
            return
        self._current_index = (self._current_index + 1) % len(self._image_paths)
        self._update_image()

    def show_previous(self) -> None:
        """Move to the previous image, wrapping around to the end."""
        if not self._image_paths:
            return
        self._current_index = (self._current_index - 1) % len(self._image_paths)
        self._update_image()

    def _toggle_slideshow(self) -> None:
        """
        Start/stop slideshow.

        When running, the viewer automatically advances to the next image
        every few seconds. Stopping the slideshow leaves the viewer on the
        last-shown image, which is usually what users expect.
        """
        if self._slideshow_running:
            self._slideshow_timer.stop()
            self._slideshow_running = False
            self._btn_slideshow.setText("Slideshow ON")
        else:
            if not self._image_paths:
                return
            self._slideshow_timer.start(self._slideshow_interval_ms)
            self._slideshow_running = True
            self._btn_slideshow.setText("Slideshow OFF")

    def _on_slideshow_tick(self) -> None:
        """Timer callback: advance to the next image."""
        self.show_next()

    # --------------------------------------------------------------- image

    def _update_image(self) -> None:
        """Load and display the current image."""
        if not self._image_paths:
            self._image_label.setText("No images available.")
            self._image_label.setPixmap(QPixmap())
            self._filename_label.setText("")
            return

        path = self._image_paths[self._current_index]

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._image_label.setText("Cannot load image.")
            self._image_label.setPixmap(QPixmap())
            self._filename_label.setText(path.name)
            return

        target_size = self._image_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            target_size = pixmap.size()

        scaled = pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._image_label.setText("")
        self._filename_label.setText(path.name)

