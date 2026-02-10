"""
Non-UI services for PhotoView Desktop.

This package will host backend logic that must stay off the GUI thread:
- Filesystem browsing with lazy directory listing (no full recursive scan)
- Thumbnail generation on worker threads and optional disk cache
- Metadata/EXIF extraction for display in the preview pane

Author: Viorel LUPU
Date: 2025-02-10
"""
