## PhotoView Desktop

A high-performance desktop photo viewer written in Python using PyQt6.
The design aims to closely follow the classic ACDSee "Manage" / "View" / "Slideshow" workflow,
with a strong focus on instant responsiveness and lazy loading.

### Quick start (development)

- **Create a virtual environment** (recommended) and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

- **Run the app (early skeleton)**:

```bash
python main.py
```

At this stage, the application starts directly in the "Manage" mode with a
three‑pane layout (folder tree, file/thumbnail area, and preview/metadata pane),
using dummy data. Future iterations will add real filesystem browsing, high‑performance
thumbnailing, and the "View" and "Slideshow" modes.

