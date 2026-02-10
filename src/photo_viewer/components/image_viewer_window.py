"""
Standalone image viewer window for V-See.

Shows a single image at a time with Next / Previous navigation that
wraps around within the current folder. Intended to be opened when the
user double-clicks a thumbnail in the Manage mode grid.

Author: Viorel LUPU
Date: 2025-02-10
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PyQt6.QtCore import QByteArray, Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from photo_viewer.components.slideshow_config_dialog import SlideshowConfigDialog
from photo_viewer.services.persistence import (
    get_slideshow_interval_seconds,
    get_viewer_window_geometry,
    set_viewer_window_geometry,
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
        # every N seconds (from persistence, default 3) with wrap-around.
        self._slideshow_timer = QTimer(self)
        self._slideshow_timer.timeout.connect(self._on_slideshow_tick)
        self._slideshow_interval_ms = get_slideshow_interval_seconds() * 1000

        self._slideshow_running = False

        self._image_label: QLabel
        self._filename_label: QLabel
        self._btn_prev: QPushButton
        self._btn_next: QPushButton
        self._btn_slideshow: QPushButton
        self._current_pixmap: QPixmap | None = None

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

        btn_config = QPushButton("Configure Slideshow", central)
        btn_config.clicked.connect(self._open_slideshow_config)

        controls_layout.addWidget(self._btn_prev)
        controls_layout.addWidget(self._btn_next)
        controls_layout.addSpacing(16)
        controls_layout.addWidget(self._btn_slideshow)
        controls_layout.addWidget(btn_config)
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

    def _open_slideshow_config(self) -> None:
        """
        Open the Configure Slideshow dialog. If the user accepts,
        update our interval and restart the timer if slideshow is running.
        """
        dialog = SlideshowConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._slideshow_interval_ms = get_slideshow_interval_seconds() * 1000
            if self._slideshow_running:
                self._slideshow_timer.setInterval(self._slideshow_interval_ms)

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
            self._current_pixmap = None
            return

        self._current_pixmap = pixmap
        self._apply_scaled_pixmap()
        self._image_label.setText("")
        self._filename_label.setText(path.name)

    def _apply_scaled_pixmap(self) -> None:
        """
        Scale the current pixmap to fit the label while preserving aspect.

        Called both when a new image is loaded and when the window is resized,
        so that the image always uses as much space as available.
        """
        if self._current_pixmap is None or self._current_pixmap.isNull():
            return

        target_size = self._image_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            target_size = self._current_pixmap.size()

        scaled = self._current_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)

    # ------------------------------------------------------------- Qt hooks

    def showEvent(self, event) -> None:  # type: ignore[override]
        """
        After the window is first shown, restore size/position from persistence
        (if any) and defer scaling so the first image is not displayed tiny.
        """
        super().showEvent(event)
        geo = get_viewer_window_geometry()
        if geo:
            ba = QByteArray.fromBase64(geo.encode("ascii"))
            if not ba.isEmpty():
                self.restoreGeometry(ba)
        QTimer.singleShot(0, self._apply_scaled_pixmap)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """
        When the window is resized, rescale the current image so that it
        fills the available space instead of staying at its original size.
        """
        super().resizeEvent(event)
        self._apply_scaled_pixmap()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Persist viewer window geometry when the window is closed."""
        geo = self.saveGeometry()
        if not geo.isEmpty():
            set_viewer_window_geometry(geo.toBase64().data().decode("ascii"))
        super().closeEvent(event)

