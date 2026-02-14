## V-See

A high-performance desktop photo viewer written in Python using PyQt6. Browse photos, view full-screen, run slideshows with optional background music—with instant responsiveness and lazy loading.

### About

V-See follows the classic ACDSee-style workflow: **Manage** (browse folders and thumbnails), **View** (single-image full-screen), and **Slideshow** (auto-advance with optional music). It stays fast by loading only what you need and avoiding large database scans.

### Downloads

Pre-built releases (no Python required): [Releases](https://github.com/vlupu10/V-See/releases) — download `V-See-macOS.zip` or `V-See-Windows.zip`, extract, and run.

### How to run: developer vs end user

| Who | How |
|-----|-----|
| **Developer** (with terminal) | Open a terminal, `conda activate v-see`, then `./run.sh` (or `python main.py`). No need to build. |
| **End user (Windows)** | Extract **V-See-Windows.zip**, then double‑click **V-See.exe** or **Run V-See.bat**. No Python, conda, or build required. See [Installing V-See on Windows](docs/WINDOWS-SETUP.md#installing-v-see-end-users--no-build-required). |
| **End user (macOS)** | Extract **V-See-macOS.zip**, then double‑click **V-See.app**. No Python, conda, or build required. See [Building install kits](docs/DISTRIBUTION.md). |

**Important:** Conda, Python, vio-python, and mp3-player are required only for **developers** who build the app. End users simply download the zip, extract it, and run the app—no extra software needed.

### Quick start (development)

- **Create the conda environment** (recommended):

```bash
conda env create -f environment.yml
```

- **Run the app** (uses only the `v-see` conda env—no interference with other Python projects):

```bash
./run.sh
```

Alternatively, use a venv: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`, then `python main.py`.

**Optional – music playback during slideshow:** `pip install -e "../vio-python[qt]"` (from Project-photo-viewer). Requires ffmpeg on Windows/Linux; macOS uses built-in afplay.

**Video thumbnails and playback:** ffmpeg (for thumbnails—prefers embedded thumbnail when present, e.g. DJI/GoPro) and PyQt6-Multimedia (included in `requirements.txt`).

### What’s included

- **Manage mode:** Three-pane layout with split left panel: **Photos folder** and **Music folder** (independent trees), thumbnail grid, preview. Below the Music folder tree: playable-files list and MP3 player (requires `mp3-player[qt]`) with transport controls and volume slider. Lazy folder tree; async thumbnails for images and videos (MP4, MOV, etc.). Selecting a video thumbnail plays it in the preview pane until another item is selected. Last folders and main window geometry are restored on startup.
- **Display (View) window:** Open by double-clicking an image or video. Prev/Next with wrap-around; Slideshow ON/OFF; Stop music; Configure Slideshow (interval, music selection, video duration). Viewer geometry is saved when closed. Music auto-starts when slideshow runs if configured. Music stops when slideshow stops, when the viewer closes, or when the main window closes.
- **Video support:** Thumbnails for MP4, MOV, M4V, WebM. In Manage mode, selecting a video plays it in the preview pane. In slideshow, videos play automatically: either the first 5 seconds or the full video (configurable).
- **Configure Slideshow:** Interval (1–3600 s), music options, and video duration: "Display first 5 seconds of video" or "Display full video". All persisted.
- **Persistence:** SQLite store in `<app folder>/config/state.db` for last photos folder, last music folder, window geometries, slideshow interval, slideshow music choice, and slideshow video duration (travels with the app).
- **Robustness:** Invalid or disconnected folder paths (e.g. external drive unplugged) fall back to the tree root; slideshow music resets to "No music" to avoid crashes.

See `docs/ARCHITECTURE.md` for design, `docs/DISTRIBUTION.md` for building install kits (macOS, Windows, Linux) and creating releases, and `CONTRIBUTING.md` for how to contribute.

