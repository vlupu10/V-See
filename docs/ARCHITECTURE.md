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
| **Slideshow** | Partial | From the Display window: Slideshow ON/OFF (timer advances every N seconds for images; videos play for 5 s or full length per config). "Configure Slideshow" sets interval, music, and video duration (first 5 seconds or full video). Music auto-starts when slideshow runs if configured. Loop, shuffle, transitions are planned. |

---

### 2. Manage Mode Layout

When the app launches, the main window shows **Manage** mode with a resizable three-pane layout:

- **Left pane — Folder trees (Photos + Music)**
  - Split vertically into **Photos folder** (top) and **Music folder** (bottom). Each has its own tree for independent selection.
  - Hierarchical view of the filesystem rooted at drive root (e.g. `C:\`) on Windows—or home directory on macOS/Linux.
  - **Windows only:** a "↑" (Go up) button for each tree navigates to the parent folder; disabled when at drive root.
  - Implemented in `MainWindow` with two `QStandardItemModel` instances; child directories are loaded **lazily** when a node is expanded.
  - **Photos folder** selection drives the center pane (thumbnail grid).
  - **Music folder** selection drives the playable-files list and MP3 player below it; also used for the slideshow music dropdown and auto-start when slideshow runs.

- **Center pane — Thumbnail grid**
  - Implemented by the **`ThumbnailGridWidget`** component (`photo_viewer.components.thumbnail_grid`).
  - Displays image and video files (jpg, png, mp4, mov, etc.) from the currently selected folder in icon mode.
  - Thumbnails are generated **asynchronously** by `ThumbnailService`. Images use Pillow. For videos: prefers the **embedded thumbnail** (attached pic) when present (e.g. DJI, GoPro); otherwise extracts a frame at ~10% into the video via ffmpeg/ffprobe. Each thumbnail is drawn with a light frame for separation.

- **Left pane (Music section) — Playable files + MP3 player**
  - Below the Music folder tree: a vertical list of audio files (mp3, wav, m4a, aac, ogg, flac) in the selected folder, by filename without extension.
  - MP3 player controls (first, previous, stop, pause, play, next, last) and a volume slider when `mp3-player[qt]` is installed. Music can be played manually or auto-starts when slideshow runs (if configured). Music stops when slideshow stops, when the viewer closes, or when the main window closes.

- **Right/bottom pane — Preview / Metadata**
  - Implemented preview of the **currently selected thumbnail**.
  - When a folder is loaded, the first thumbnail is auto-selected; selecting a different thumbnail updates the preview.
  - **Images:** Shows a scaled version of the image.
  - **Videos:** Plays the selected video in the preview pane; playback continues until another thumbnail is selected.

---

### 3. Layers (Components and Services)

Code is organised into **components** (UI widgets) and **services** (non-UI logic). Configuration lives under **config**.

#### 3.1 Components (`src/photo_viewer/components/`)

Reusable Qt widgets and views. Naming follows the same idea as “components” in Angular: self-contained UI units with a clear responsibility.

| Component | Purpose |
|-----------|---------|
| **ThumbnailGridWidget** | Center pane in Manage mode. Grid of image thumbnails for the selected folder; uses `ThumbnailService` and `load_folder(path)`. Emits `selection_changed(path_str)` and `activated(paths, index)` (double-click). |
| **ImageViewerWindow** | Display (View) window: shows one image, Prev/Next buttons, Slideshow ON/OFF, Stop music, Configure Slideshow. Restores/saves window geometry and uses persisted slideshow interval. Music is controlled from the main window; auto-starts when slideshow runs if configured; Stop music button and window close trigger music stop. |
| **SlideshowConfigDialog** | Modal dialog for slideshow settings: interval (QSpinBox 1–3600 s), music (QComboBox), and video duration (QRadioButton: "Display first 5 seconds of video" or "Display full video"). All persisted; viewer applies new settings if slideshow is running. |

Future components: folder tree widget (extracted from MainWindow), zoom/pan in viewer, more slideshow options in the config dialog.

#### 3.2 Services (`src/photo_viewer/services/`)

Backend logic that must not block the GUI thread. No Qt widgets; they expose signals or callbacks for the UI to react.

| Service | Purpose |
|---------|---------|
| **ThumbnailService** | Generates scaled, framed thumbnails on a thread pool. Images: Pillow. Videos: (1) embedded thumbnail (attached pic) via ffmpeg when present; (2) fallback to frame at ~10% of duration via ffmpeg/ffprobe. Requires ffmpeg for video thumbnails. Caches results, emits `thumbnail_ready(path, QIcon)`. |
| **Persistence** (`persistence.py`) | Stores application state in SQLite. Keys: **last_folder**, **last_music_folder**, **main_window_geometry**, **viewer_window_geometry**, **slideshow_interval_seconds**, **slideshow_music**, **slideshow_video_duration** (5_seconds | full). See §5 for the full API. |

Future services will include: filesystem browser (if the tree is moved out of MainWindow), metadata/EXIF extraction, and pre-fetching for View mode.

#### 3.3 Config (`src/photo_viewer/config/`)

Application-wide settings and path constants (e.g. project root, `docs/`, `tmp/`). Keeps the rest of the codebase independent of repository layout.

---

### 4. Main Window Composition

`MainWindow` (`src/photo_viewer/main_window.py`) is the top-level window. It:

- Builds the **left pane** with two folder trees (Photos, Music) and the Music file list + MP3 player. Music folder selection populates the playable-files list and configures the slideshow music dropdown.
- Creates a **ThumbnailService** instance and a **ThumbnailGridWidget** (center), passing the service into the component. On Photos folder selection, it calls `thumbnail_grid.load_folder(folder_path)`.
- Connects `ThumbnailGridWidget.selection_changed` to update the preview pane; connects `activated(paths, index)` to open an **ImageViewerWindow** with that image list, index, and the selected Music folder path.
- Provides `start_slideshow_music_if_configured()` and `stop_slideshow_music()` for the viewer to auto-start/stop music when slideshow turns on/off. Calls `stop_slideshow_music()` in `closeEvent` so music stops when the main window is closed.
- Builds the **preview pane** (bottom-right) with a `QStackedWidget`: image preview (QLabel) or video playback (QVideoWidget). Selecting a video plays it in the preview until another item is selected. EXIF/metadata display is still to be added.

No file-list or thumbnail logic remains inside MainWindow; the center pane is fully owned by the ThumbnailGridWidget component. On startup, MainWindow restores **last_folder**, **last_music_folder**, and **main_window_geometry** from persistence. If persisted paths are invalid (e.g. disconnected external drive), it falls back to the tree root and resets slideshow music to "No music". The folder trees use `QTreeView.setEditTriggers(NoEditTriggers)` so double-click opens the viewer instead of renaming.

---

### 5. Persistence (SQLite)

Application state is persisted in a **SQLite** database so that preferences and context survive restarts. The implementation uses the Python standard library `sqlite3` (no extra dependency).

- **Location:** In a `config` subfolder next to the application: `<app dir>/config/state.db`. When run from source this is the project root (directory containing `main.py`); when run as a frozen bundle it is the directory containing the executable. The directory is created automatically.
- **Schema:** A single table `app_state (key TEXT PRIMARY KEY, value TEXT)` used as a key–value store.
- **Currently stored:**
  - **`last_folder`** — Path of the last Photos folder selected. Restored on startup so the app reopens in the same place.
  - **`last_music_folder`** — Path of the last Music folder selected. Restored on startup.
  - **`main_window_geometry`** — Main window size and position (Qt `saveGeometry` as base64). Restored on startup; saved when the main window is closed.
  - **`viewer_window_geometry`** — Display (viewer) window size and position. Restored when a viewer window is opened; saved when that window is closed.
  - **`slideshow_interval_seconds`** — Number of seconds between slides when slideshow is on (default 3, clamped 1–3600). Read when the viewer window is created; can be updated later via "Configure Slideshow".
  - **`slideshow_music`** — Music choice: "No music", "All songs in the selected music folder", or a song name (start from that song). Persisted and used for auto-start when slideshow runs.
  - **`slideshow_video_duration`** — Video playback in slideshow: `"5_seconds"` (default) or `"full"`. Configurable via Configure Slideshow dialog.
- **Invalid paths:** If persisted folders no longer exist (deleted or on a disconnected external drive), the app falls back to the tree root and resets the slideshow music dropdown to "No music" to avoid crashes.
- **Possible future keys:** loop on/off, shuffle, recent folders, splitter positions.

The persistence API lives in `photo_viewer.services.persistence`: `get_last_folder` / `set_last_folder`, `get_last_music_folder` / `set_last_music_folder`, `get_main_window_geometry` / `set_main_window_geometry`, `get_viewer_window_geometry` / `set_viewer_window_geometry`, `get_slideshow_interval_seconds` / `set_slideshow_interval_seconds`, `get_slideshow_music` / `set_slideshow_music`, `get_slideshow_video_duration` / `set_slideshow_video_duration`. New keys can be added with similar get/set helpers without changing the schema.

---

### 6. Performance Strategies

- **Lazy folder tree:** Only the children of an expanded node are read from disk; no full recursive scan on startup.
- **Asynchronous thumbnails:** Decoding and scaling are done on a `ThreadPoolExecutor` in `ThumbnailService`; the GUI thread only updates item icons when `thumbnail_ready` is emitted.
- **Planned:** Virtual scrolling / lazy loading for very large folders (e.g. 10,000+ images), and pre-fetching for instant switching in View mode.

### 7. Defensive Handling for Invalid Paths and Disconnected Drives

Persisted folder paths (photos and music) may become invalid if the user deletes folders or disconnects external storage. To avoid crashes:

- **On startup:** Before restoring persisted paths, the app validates each path (exists, is directory, under tree root). Invalid paths fall back to the tree root; when the music folder is invalid, the slideshow music dropdown is reset to "No music".
- **During use:** If the user selects a folder that has become invalid (e.g. drive disconnected after expansion), selection is redirected to root; for the music folder, the dropdown is also reset to "No music".
- **Thumbnail grid and music file list:** Path access is wrapped in try/except for `OSError` and `PermissionError` so disconnected drives do not crash the app.
- **Unexpected disconnection:** Go-up buttons, path resolution in `_expand_and_select_path`, image loading (preview pane and viewer), and the thumbnail service catch `OSError`/`PermissionError` so the app continues to run if an external device is disconnected mid-session. The user sees a fallback (e.g. "Cannot load image (device disconnected?)") instead of a crash.

---

### 8. Project Layout (Relevant Directories)

```
Project-photo-viewer/
├── main.py                 # Entry point; adds src to sys.path, launches QApplication
├── run.sh                  # Launcher: requires conda, activates env "v-see", runs main.py
├── environment.yml         # Conda env "v-see" (Python, Pillow, PyQt6, ffmpeg, PyQt6-Multimedia)
├── requirements.txt       # Pip deps (for venv or conda pip section)
├── docs/
│   └── ARCHITECTURE.md     # This document
├── requirements/           # Product requirements and reference screenshots
└── src/photo_viewer/
    ├── __init__.py
    ├── main_window.py      # Main window, folder trees (Photos+Music), layout, MP3 player
    ├── components/
    │   ├── __init__.py
    │   ├── thumbnail_grid.py       # ThumbnailGridWidget
    │   ├── image_viewer_window.py  # ImageViewerWindow (Display window)
    │   └── slideshow_config_dialog.py  # SlideshowConfigDialog
    ├── services/
    │   ├── __init__.py
    │   ├── persistence.py   # SQLite app state (§5)
    │   ├── thumbnails.py    # ThumbnailService (images + videos)
    │   ├── display_sleep.py # Prevent display sleep during slideshow
    │   └── audio.py         # Re-exports mp3-player for playback
    └── config/
        ├── __init__.py
        └── settings.py    # Paths and constants
```

### 9. Running the Application

The app is intended to run in an isolated conda environment so it does not interfere with other Python projects.

- **One-time setup:** `conda env create -f environment.yml` (creates env `v-see`).
- **Run:** `./run.sh` — the script checks for conda and the `v-see` env, activates it, then runs `python main.py`. It will not fall back to the base env or system Python.
- **Alternative:** Use a virtualenv and `pip install -r requirements.txt`, then run `python main.py` with that venv activated.

---

As the implementation evolves (zoom/pan, more slideshow options, further componentisation), this document will be updated to match.
