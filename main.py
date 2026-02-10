"""
Application entry point for PhotoView Desktop.

Runs the PyQt6 application and shows the main window in Manage mode.
Ensures the src/ package root is on sys.path before importing the app.

Author: Viorel LUPU
Date: 2025-02-10
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication


def _configure_sys_path() -> None:
    """
    Ensure the src/ directory is on sys.path so that the
    `photo_viewer` package (and subpackages) can be imported.

    Required because the application is run from the project root (main.py)
    while the package lives under src/; without this, "from photo_viewer ..."
    would fail unless the user installs the package in development mode.
    """
    project_root = Path(__file__).resolve().parent
    src_dir = project_root / "src"
    src_str = str(src_dir)
    if src_dir.is_dir() and src_str not in sys.path:
        sys.path.insert(0, src_str)


def main() -> None:
    """
    Create the Qt application, show the main window, and run the event loop.

    Path configuration is done first so that imports of photo_viewer succeed;
    then the main window is instantiated and displayed.
    """
    _configure_sys_path()

    from photo_viewer.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
