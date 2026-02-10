"""
UI components (widgets) for V-See.

This package hosts reusable widgets and views for:
- Manage mode: folder tree, thumbnail grid, preview pane
- View mode: image canvas, zoom/pan controls
- Slideshow: configuration dialogs and playback UI

Author: Viorel LUPU
Date: 2025-02-10
"""

from photo_viewer.components.image_viewer_window import ImageViewerWindow
from photo_viewer.components.slideshow_config_dialog import SlideshowConfigDialog
from photo_viewer.components.thumbnail_grid import ThumbnailGridWidget

__all__ = ["ThumbnailGridWidget", "ImageViewerWindow", "SlideshowConfigDialog"]
