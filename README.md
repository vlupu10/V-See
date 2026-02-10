## V-See

A high-performance desktop photo viewer written in Python using PyQt6.
The design aims to closely follow the classic ACDSee "Manage" / "View" / "Slideshow" workflow,
with a strong focus on instant responsiveness and lazy loading.

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

### What’s included

- **Manage mode:** Three-pane layout (folder tree, thumbnail grid, preview). Lazy folder tree; async thumbnails. Last folder and main window geometry are restored on startup.
- **Display (View) window:** Open by double-clicking an image. Prev/Next with wrap-around; Slideshow ON/OFF; Configure Slideshow (interval in seconds, persisted). Viewer geometry is saved when closed.
- **Persistence:** SQLite store under `~/.config/v-see/` for last folder, window geometries, and slideshow interval.

See `docs/ARCHITECTURE.md` for design and `requirements/requirements.md` for full product requirements.

