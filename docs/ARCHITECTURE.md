<!-- Purpose: High-level architecture documentation for V-See. -->
<!-- Author: Photo Viewer Project | Date: 2025-02-10 -->

## Architecture Overview

This document describes the high-level architecture of **V-See**, a desktop photo viewer built with Python and PyQt6. The design follows an ACDSee-style workflow with a clear split between UI components (widgets) and backend services.

---

### 1. Modes

The application has three main modes of operation:

| Mode       | Status    | Description |
|-----------|-----------|-------------|
| **Manage** | Implemented | Default view at startup. Three-pane browser: folder tree, thumbnail grid, preview/metadata. |
| **View**   | Planned    | Single-image full-screen viewer (zoom, pan, next/previous). Activated by double-clicking an image in Manage. |
| **Slideshow** | Planned | Configurable slideshow from the current folder (duration, transitions, loop, shuffle). |

---

### 2. Manage Mode Layout

When the app launches, the main window shows **Manage** mode with a resizable three-pane layout:

- **Left pane — Folder tree**
  - Hierarchical view of the filesystem rooted at the user’s home directory.
  - Implemented in `MainWindow` with a `QStandardItemModel`; child directories are loaded **lazily** when a node is expanded (no upfront recursive scan).
  - Selection in the tree drives the content of the center pane.

- **Center pane — Thumbnail grid**
  - Implemented by the **`ThumbnailGridWidget`** component (`photo_viewer.components.thumbnail_grid`).
  - Displays image files from the currently selected folder in icon mode (grid of thumbnails with filenames).
  - Thumbnails are generated **asynchronously** by `ThumbnailService`; icons appear as they complete. Each thumbnail is drawn with a light frame for separation.

- **Right/bottom pane — Preview / Metadata**
  - Placeholder for a larger preview of the selected file and basic EXIF data (camera, ISO, date taken). Not yet implemented.

---

### 3. Layers (Components and Services)

Code is organised into **components** (UI widgets) and **services** (non-UI logic). Configuration lives under **config**.

#### 3.1 Components (`src/photo_viewer/components/`)

Reusable Qt widgets and views. Naming follows the same idea as “components” in Angular: self-contained UI units with a clear responsibility.

| Component | Purpose |
|-----------|---------|
| **ThumbnailGridWidget** | Center pane in Manage mode. Shows a grid of image thumbnails for a given folder; takes a `ThumbnailService` in the constructor and calls `load_folder(path)` when the user selects a folder. |

Future components will include: folder tree widget (extracted from MainWindow), preview pane widget, View-mode canvas, and slideshow dialogs.

#### 3.2 Services (`src/photo_viewer/services/`)

Backend logic that must not block the GUI thread. No Qt widgets; they expose signals or callbacks for the UI to react.

| Service | Purpose |
|---------|---------|
| **ThumbnailService** | Generates scaled, framed thumbnails for image files on a thread pool. Caches results in memory and emits `thumbnail_ready(path, QIcon)` so components can update item icons. Used by `ThumbnailGridWidget`. |

Future services will include: filesystem browser (if the tree is moved out of MainWindow), metadata/EXIF extraction, and pre-fetching for View mode.

#### 3.3 Config (`src/photo_viewer/config/`)

Application-wide settings and path constants (e.g. project root, `docs/`, `tmp/`). Keeps the rest of the codebase independent of repository layout.

---

### 4. Main Window Composition

`MainWindow` (`src/photo_viewer/main_window.py`) is the top-level window. It:

- Builds the **folder tree** (left) with a lazy `QStandardItemModel` and connects selection changes to the center pane.
- Creates a **ThumbnailService** instance and a **ThumbnailGridWidget** (center), passing the service into the component. On folder selection, it calls `thumbnail_grid.load_folder(folder_path)`.
- Builds the **preview pane** (bottom-right) as a placeholder.

No file-list or thumbnail logic remains inside MainWindow; the center pane is fully owned by the ThumbnailGridWidget component.

---

### 5. Performance Strategies

- **Lazy folder tree:** Only the children of an expanded node are read from disk; no full recursive scan on startup.
- **Asynchronous thumbnails:** Decoding and scaling are done on a `ThreadPoolExecutor` in `ThumbnailService`; the GUI thread only updates item icons when `thumbnail_ready` is emitted.
- **Planned:** Virtual scrolling / lazy loading for very large folders (e.g. 10,000+ images), and pre-fetching for instant switching in View mode.

---

### 6. Project Layout (Relevant Directories)

```
src/photo_viewer/
├── __init__.py
├── main_window.py          # Main window, folder tree, layout composition
├── components/
│   ├── __init__.py
│   └── thumbnail_grid.py  # ThumbnailGridWidget
├── services/
│   ├── __init__.py
│   └── thumbnails.py       # ThumbnailService
└── config/
    ├── __init__.py
    └── settings.py         # Paths and constants

docs/                       # Architecture and design docs
requirements/               # Product requirements and reference screenshots
tmp/                        # Temporary / cache files (gitignored except .gitkeep)
```

---

As the implementation evolves (View mode, Slideshow, further componentisation), this document will be updated to match.
