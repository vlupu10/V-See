## V-See

A high-performance desktop photo viewer written in Python using PyQt6.
The design aims to closely follow the classic ACDSee "Manage" / "View" / "Slideshow" workflow,
with a strong focus on instant responsiveness and lazy loading.

### How to run: developer vs end user

| Who | How |
|-----|-----|
| **Developer** (with terminal) | Open a terminal, `conda activate v-see`, then `./run.sh` (or `python main.py`). No need to build. |
| **End user (Windows)** | Extract **V-See-Windows.zip**, then double‑click **V-See.exe**. No Python or build required. See [Installing V-See on Windows](docs/WINDOWS-SETUP.md#installing-v-see-end-users--no-build-required). |
| **End user (macOS/Linux)** | Build once with PyInstaller, then double‑click the app. See [Building install kits](docs/DISTRIBUTION.md). |

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

**Optional – music playback during slideshow:** With the same environment active that you use to run the app (e.g. `conda activate v-see` when using `run.sh`), from the Project-photo-viewer directory:  
`pip install -e "../vio-python[qt]"`  
(Requires ffmpeg on Windows/Linux; macOS uses built-in afplay.)

### What’s included

- **Manage mode:** Three-pane layout with split left panel: **Photos folder** and **Music folder** (independent trees), thumbnail grid, preview. Below the Music folder tree: playable-files list and MP3 player (requires `mp3-player[qt]`) with transport controls and volume slider. Lazy folder tree; async thumbnails. Last folders and main window geometry are restored on startup.
- **Display (View) window:** Open by double-clicking an image. Prev/Next with wrap-around; Slideshow ON/OFF; Stop music; Configure Slideshow (interval, music selection). Viewer geometry is saved when closed. Music auto-starts when slideshow runs if configured. Music stops when slideshow stops, when the viewer closes, or when the main window closes.
- **Configure Slideshow:** Interval (1–3600 s) and music options: "No music", "All songs in the selected music folder", or start from a specific song. All persisted.
- **Persistence:** SQLite store in `<app folder>/config/state.db` for last photos folder, last music folder, window geometries, slideshow interval, and slideshow music choice (travels with the app).
- **Robustness:** Invalid or disconnected folder paths (e.g. external drive unplugged) fall back to the tree root; slideshow music resets to "No music" to avoid crashes.

See `docs/ARCHITECTURE.md` for design, `docs/DISTRIBUTION.md` for building install kits (macOS, Windows, Linux), and `requirements/requirements.md` for full product requirements.

