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

At this stage, the application starts directly in the "Manage" mode with a
three‑pane layout (folder tree, file/thumbnail area, and preview/metadata pane),
using dummy data. Future iterations will add real filesystem browsing, high‑performance
thumbnailing, and the "View" and "Slideshow" modes.

