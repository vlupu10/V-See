<!-- Purpose: High-level architecture documentation for PhotoView Desktop. -->
<!-- Author: Photo Viewer Project | Date: 2025-02-10 -->

## Architecture Overview (Draft)

This document describes the high-level architecture of PhotoView Desktop.

Planned sections:

- **Modes**: Manage / View / Slideshow, and how they map to Qt widgets
- **Layers**:
  - `photo_viewer.components`: widgets, views, dialogs
  - `photo_viewer.services`: filesystem, thumbnailing, metadata, background workers
  - `photo_viewer.config`: configuration and constants
- **Performance strategies**:
  - Lazy filesystem loading
  - Asynchronous thumbnail generation
  - Virtual scrolling and item models

As the implementation evolves, we will keep this file up to date.

