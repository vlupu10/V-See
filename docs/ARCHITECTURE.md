<!-- Purpose: High-level architecture documentation for V-See. -->
<!-- Author: Viorel LUPU | Date: 2025-02-10 -->

## Architecture Overview

This document describes the high-level architecture of **V-See**, a desktop photo viewer built with Python and PyQt6. The design follows an ACDSee-style workflow with a clear split between UI components (widgets) and backend services.

---

### 1. Modes

The application has three main modes of operation:

| Mode       | Status    | Description |
|-----------|-----------|-------------|
| **Manage** | Implemented | Default view at startup. Three-pane browser: folder tree, thumbnail grid, preview/metadata. Double-click an image to open the Display (View) window. |
| **View**   | Implemented | Display window: single-image viewer with Prev/Next (wrap-around). Opened by double-clicking an image in Manage. Window geometry and last folder are persisted. |
| **Slideshow** | Partial | From the Display window: Slideshow ON/OFF (timer advances every N seconds). "Configure Slideshow" opens a dialog to set interval (1–3600 s); value is persisted. Loop, shuffle, transitions are planned. |

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
  - Implemented preview of the **currently selected thumbnail**.
  - When a folder is loaded, the first thumbnail is auto-selected; selecting a different thumbnail updates the preview.
  - The preview pane currently shows a scaled version of the image; EXIF and additional metadata will be added beneath it in a later iteration.

---

### 3. Layers (Components and Services)

Code is organised into **components** (UI widgets) and **services** (non-UI logic). Configuration lives under **config**.

#### 3.1 Components (`src/photo_viewer/components/`)

Reusable Qt widgets and views. Naming follows the same idea as “components” in Angular: self-contained UI units with a clear responsibility.

| Component | Purpose |
|-----------|---------|
| **ThumbnailGridWidget** | Center pane in Manage mode. Grid of image thumbnails for the selected folder; uses `ThumbnailService` and `load_folder(path)`. Emits `selection_changed(path_str)` and `activated(paths, index)` (double-click). |
| **ImageViewerWindow** | Display (View) window: shows one image, Prev/Next buttons, Slideshow ON/OFF, Configure Slideshow. Restores/saves window geometry and uses persisted slideshow interval. |
| **SlideshowConfigDialog** | Modal dialog for slideshow settings. Currently: interval in seconds (QSpinBox 1–3600). On OK, saves via persistence; viewer applies new interval if slideshow is running. |

Future components: folder tree widget (extracted from MainWindow), zoom/pan in viewer, more slideshow options in the config dialog.

#### 3.2 Services (`src/photo_viewer/services/`)

Backend logic that must not block the GUI thread. No Qt widgets; they expose signals or callbacks for the UI to react.

| Service | Purpose |
|---------|---------|
| **ThumbnailService** | Generates scaled, framed thumbnails for image files on a thread pool. Caches results in memory and emits `thumbnail_ready(path, QIcon)` so components can update item icons. Used by `ThumbnailGridWidget`. |
| **Persistence** (`persistence.py`) | Stores application state in SQLite so it survives restarts. Stores: **last_folder**, **main_window_geometry**, **viewer_window_geometry**, **slideshow_interval_seconds**. See §5 for the full API. |

Future services will include: filesystem browser (if the tree is moved out of MainWindow), metadata/EXIF extraction, and pre-fetching for View mode.

#### 3.3 Config (`src/photo_viewer/config/`)

Application-wide settings and path constants (e.g. project root, `docs/`, `tmp/`). Keeps the rest of the codebase independent of repository layout.

---

### 4. Main Window Composition

`MainWindow` (`src/photo_viewer/main_window.py`) is the top-level window. It:

- Builds the **folder tree** (left) with a lazy `QStandardItemModel` and connects selection changes to the center pane.
- Creates a **ThumbnailService** instance and a **ThumbnailGridWidget** (center), passing the service into the component. On folder selection, it calls `thumbnail_grid.load_folder(folder_path)`.
- Connects `ThumbnailGridWidget.selection_changed` to update the preview pane; connects `activated(paths, index)` to open an **ImageViewerWindow** with that image list and index.
- Builds the **preview pane** (bottom-right) with a `QLabel` that displays a scaled image preview for the currently selected file. EXIF/metadata display is still to be added.

No file-list or thumbnail logic remains inside MainWindow; the center pane is fully owned by the ThumbnailGridWidget component. On startup, MainWindow restores **last folder** and **main_window_geometry** from persistence; the tree is expanded to that path and the folder is selected. The folder tree uses `QTreeView.setEditTriggers(NoEditTriggers)` so double-click opens the viewer instead of renaming.

---

### 5. Persistence (SQLite)

Application state is persisted in a **SQLite** database so that preferences and context survive restarts. The implementation uses the Python standard library `sqlite3` (no extra dependency).

- **Location:** `~/.config/v-see/state.db` (directory created automatically).
- **Schema:** A single table `app_state (key TEXT PRIMARY KEY, value TEXT)` used as a key–value store.
- **Currently stored:**
  - **`last_folder`** — Path of the last folder selected in the folder tree. Restored on startup so the app reopens in the same place.
  - **`main_window_geometry`** — Main window size and position (Qt `saveGeometry` as base64). Restored on startup; saved when the main window is closed.
  - **`viewer_window_geometry`** — Display (viewer) window size and position. Restored when a viewer window is opened; saved when that window is closed.
  - **`slideshow_interval_seconds`** — Number of seconds between slides when slideshow is on (default 3, clamped 1–3600). Read when the viewer window is created; can be updated later via a “Config Slideshow” dialog.
- **Possible future keys:** loop on/off, shuffle, recent folders, splitter positions.

The persistence API lives in `photo_viewer.services.persistence`: `get_last_folder` / `set_last_folder`, `get_main_window_geometry` / `set_main_window_geometry`, `get_viewer_window_geometry` / `set_viewer_window_geometry`, `get_slideshow_interval_seconds` / `set_slideshow_interval_seconds`. New keys can be added with similar get/set helpers without changing the schema.

---

### 6. Performance Strategies

- **Lazy folder tree:** Only the children of an expanded node are read from disk; no full recursive scan on startup.
- **Asynchronous thumbnails:** Decoding and scaling are done on a `ThreadPoolExecutor` in `ThumbnailService`; the GUI thread only updates item icons when `thumbnail_ready` is emitted.
- **Planned:** Virtual scrolling / lazy loading for very large folders (e.g. 10,000+ images), and pre-fetching for instant switching in View mode.

---

### 7. Project Layout (Relevant Directories)

```
Project-photo-viewer/
├── main.py                 # Entry point; adds src to sys.path, launches QApplication
├── run.sh                  # Launcher: requires conda, activates env "v-see", runs main.py
├── environment.yml         # Conda env "v-see" (Python, Pillow, PyQt6 via pip)
├── requirements.txt       # Pip deps (for venv or conda pip section)
├── docs/
│   └── ARCHITECTURE.md     # This document
├── requirements/           # Product requirements and reference screenshots
└── src/photo_viewer/
    ├── __init__.py
    ├── main_window.py      # Main window, folder tree, layout composition
    ├── components/
    │   ├── __init__.py
    │   ├── thumbnail_grid.py       # ThumbnailGridWidget
    │   ├── image_viewer_window.py  # ImageViewerWindow (Display window)
    │   └── slideshow_config_dialog.py  # SlideshowConfigDialog
    ├── services/
    │   ├── __init__.py
    │   ├── persistence.py  # SQLite app state (§5)
    │   └── thumbnails.py   # ThumbnailService
    └── config/
        ├── __init__.py
        └── settings.py    # Paths and constants
```

### 8. Running the Application

The app is intended to run in an isolated conda environment so it does not interfere with other Python projects.

- **One-time setup:** `conda env create -f environment.yml` (creates env `v-see`).
- **Run:** `./run.sh` — the script checks for conda and the `v-see` env, activates it, then runs `python main.py`. It will not fall back to the base env or system Python.
- **Alternative:** Use a virtualenv and `pip install -r requirements.txt`, then run `python main.py` with that venv activated.

---

As the implementation evolves (zoom/pan, more slideshow options, further componentisation), this document will be updated to match.
