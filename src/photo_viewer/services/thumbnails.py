"""
Thumbnail generation service for V-See.

Generates small preview images (thumbnails) for photo files on background
threads so that the Qt GUI thread remains responsive even when browsing
large folders. Loaded thumbnails are cached in memory and emitted back to
the UI via a Qt signal.

Author: Photo Viewer Project
Date: 2025-02-10
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict

from PIL import Image
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap


class ThumbnailService(QObject):
    """
    Asynchronous thumbnail generator with an in-memory cache.

    Usage:
    - Connect to the `thumbnail_ready` signal to be notified when a thumbnail
      has been generated for a file path.
    - Call `request_thumbnail(path)` from the GUI thread whenever you add a
      file to the view. If the thumbnail is already cached, the signal is
      emitted immediately; otherwise the work is scheduled on a background
      thread and the signal fires when ready.
    """

    thumbnail_ready = pyqtSignal(str, QIcon)

    def __init__(
        self,
        max_workers: int = 4,
        size: int = 160,
        parent: QObject | None = None,
    ) -> None:
        """
        Create the thumbnail service.

        Parameters
        ----------
        max_workers:
            Maximum number of worker threads used for decoding and scaling.
        size:
            Target edge size (pixels) for both width and height. Thumbnails
            preserve aspect ratio and fit inside this square.
        parent:
            Optional Qt parent object for ownership.
        """
        super().__init__(parent)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._target_size = size
        self._cache: Dict[str, QIcon] = {}

    # ------------------------------------------------------------------ API

    def request_thumbnail(self, path: Path) -> None:
        """
        Request a thumbnail for the given file path.

        If the thumbnail is cached, the `thumbnail_ready` signal is emitted
        immediately. Otherwise, decoding and scaling are performed on a
        background thread and the signal will fire when complete.
        """
        path_str = str(path)

        if path_str in self._cache:
            self.thumbnail_ready.emit(path_str, self._cache[path_str])
            return

        # Schedule work on a background thread. The callback will emit the
        # signal from the worker thread; Qt will deliver it to the GUI thread
        # using a queued connection.
        self._executor.submit(self._load_and_emit, path_str)

    # ----------------------------------------------------------------- intern

    def _load_and_emit(self, path_str: str) -> None:
        """Worker: load, scale, cache, and emit icon for a single path."""
        try:
            icon = self._build_icon(Path(path_str))
        except Exception:
            # On failure (unsupported file, decode error, etc.), skip quietly.
            return

        if icon is None:
            return

        self._cache[path_str] = icon
        self.thumbnail_ready.emit(path_str, icon)

    def _build_icon(self, path: Path) -> QIcon | None:
        """
        Decode the image using Pillow and turn it into a QIcon.

        Returns None if the file cannot be opened or decoded.
        """
        if not path.is_file():
            return None

        with Image.open(path) as img:
            # Use a copy of the image resized in-place to the thumbnail size
            img = img.convert("RGBA")
            img.thumbnail((self._target_size, self._target_size))

            width, height = img.size
            data = img.tobytes("raw", "RGBA")

            qimage = QImage(
                data,
                width,
                height,
                QImage.Format.Format_RGBA8888,
            )
            base_pixmap = QPixmap.fromImage(qimage)

            # Add a subtle frame around the thumbnail to visually separate it
            # from the background and neighbouring thumbnails.
            margin = 4
            framed_width = width + margin * 2
            framed_height = height + margin * 2

            framed = QPixmap(framed_width, framed_height)
            framed.fill(Qt.GlobalColor.transparent)

            painter = QPainter(framed)
            try:
                # Draw the image centered inside the frame.
                painter.drawPixmap(margin, margin, base_pixmap)

                # Draw a light border.
                pen = QPen(QColor(220, 220, 220))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawRect(0, 0, framed_width - 1, framed_height - 1)
            finally:
                painter.end()

            return QIcon(framed)

