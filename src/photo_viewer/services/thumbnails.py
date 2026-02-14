"""
Thumbnail generation service for V-See.

Generates small preview images (thumbnails) for photo files on background
threads so that the Qt GUI thread remains responsive even when browsing
large folders. Loaded thumbnails are cached in memory and emitted back to
the UI via a Qt signal.

Author: Viorel LUPU
Date: 2025-02-10
"""

from __future__ import annotations

import io
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict

from PIL import Image

from photo_viewer.services.ffmpeg_paths import get_ffmpeg_paths
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
        Decode the image or video frame and turn it into a QIcon.

        For images: uses Pillow. For videos (.mp4): extracts first frame via ffmpeg.
        Returns None if the file cannot be opened or decoded.
        """
        if not path.is_file():
            return None

        suffix = path.suffix.lower()
        if suffix in (".mp4", ".mov", ".m4v", ".webm"):
            return self._build_video_icon(path)
        return self._build_image_icon(path)

    def _get_ffmpeg_paths(self) -> tuple[str, str]:
        """Resolve ffmpeg/ffprobe paths (bundled when frozen, else from PATH)."""
        return get_ffmpeg_paths()

    def _get_video_thumbnail_offset_seconds(self, path: Path) -> float:
        """
        Pick a good position for video thumbnails.
        Skip the first ~10% of the video (often black/intro) but cap at 2 seconds.
        Falls back to 1 second if ffprobe fails.
        """
        _, ffprobe = self._get_ffmpeg_paths()
        try:
            result = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                if duration > 0:
                    # Skip first ~10% (often black/intro), cap at 2s, min 0.5s
                    offset = min(2.0, max(0.5, duration * 0.1))
                    return offset
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        return 1.0  # Fallback: 1 second in (skips typical black start)

    def _extract_embedded_thumbnail(self, path: Path) -> QIcon | None:
        """
        Extract embedded thumbnail (attached pic) if present.
        Uses -map 0:v -map -0:V to select only attached-pic streams
        (DJI, GoPro, phones, etc. embed thumbnails this way).
        """
        ffmpeg, _ = self._get_ffmpeg_paths()
        try:
            result = subprocess.run(
                [
                    ffmpeg,
                    "-hwaccel", "none",
                    "-y",
                    "-i", str(path),
                    "-map", "0:v",
                    "-map", "-0:V",
                    "-c", "copy",
                    "-vframes", "1",
                    "-f", "image2pipe",
                    "-",
                ],
                capture_output=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0 or not result.stdout:
            return None
        try:
            img = Image.open(io.BytesIO(result.stdout))
            return self._pil_to_icon(img.convert("RGBA"))
        except Exception:
            return None

    def _extract_frame_at_offset(self, path: Path, offset_seconds: float) -> QIcon | None:
        """Extract a frame at the given time offset and build icon."""
        ffmpeg, _ = self._get_ffmpeg_paths()
        try:
            result = subprocess.run(
                [
                    ffmpeg,
                    "-hwaccel", "none",
                    "-y",
                    "-ss", str(offset_seconds),
                    "-i", str(path),
                    "-vf", "scale=320:-1",
                    "-vframes", "1",
                    "-f", "image2pipe",
                    "-vcodec", "png",
                    "-",
                ],
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0 or not result.stdout:
            return None
        try:
            img = Image.open(io.BytesIO(result.stdout)).convert("RGBA")
            return self._pil_to_icon(img)
        except Exception:
            return None

    def _build_video_icon(self, path: Path) -> QIcon | None:
        """
        Build video thumbnail. Prefer embedded thumbnail (attached pic from cameras
        like DJI, GoPro); fall back to extracting a frame at ~10% into the video.
        """
        icon = self._extract_embedded_thumbnail(path)
        if icon is not None:
            return icon
        offset = self._get_video_thumbnail_offset_seconds(path)
        return self._extract_frame_at_offset(path, offset)

    def _build_image_icon(self, path: Path) -> QIcon | None:
        """Decode image with Pillow and build icon."""
        try:
            with Image.open(path) as img:
                return self._pil_to_icon(img.convert("RGBA"))
        except Exception:
            return None

    def _pil_to_icon(self, img: Image.Image) -> QIcon:
        """Convert PIL Image to QIcon with frame."""
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

        margin = 4
        framed_width = width + margin * 2
        framed_height = height + margin * 2

        framed = QPixmap(framed_width, framed_height)
        framed.fill(Qt.GlobalColor.transparent)

        painter = QPainter(framed)
        try:
            painter.drawPixmap(margin, margin, base_pixmap)
            pen = QPen(QColor(220, 220, 220))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(0, 0, framed_width - 1, framed_height - 1)
        finally:
            painter.end()

        return QIcon(framed)

