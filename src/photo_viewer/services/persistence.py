"""
Persistence service for V-See using SQLite.

Stores application state (e.g. last visited folder path) so that on the next
launch the app can open the same folder. Uses the standard library sqlite3
module. The database is stored in a config subfolder next to the application
so it stays with the app and works the same on all OSes.

Author: Viorel LUPU
Date: 2025-02-10
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Keys in app_state table.
LAST_FOLDER_KEY = "last_folder"
MAIN_WINDOW_GEOMETRY_KEY = "main_window_geometry"
VIEWER_WINDOW_GEOMETRY_KEY = "viewer_window_geometry"
SLIDESHOW_INTERVAL_SECONDS_KEY = "slideshow_interval_seconds"

DEFAULT_SLIDESHOW_INTERVAL_SECONDS = 3

# Subfolder under the application directory where state is stored (recommended location).
CONFIG_SUBDIR = "config"
STATE_DB_FILENAME = "state.db"


def _application_dir() -> Path:
    """
    Return the directory containing the application (for portable state).

    - When run as a frozen bundle (e.g. PyInstaller): directory containing the executable.
    - When run from source: directory containing the main script (e.g. main.py).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(sys.argv[0]).resolve().parent


def _db_path() -> Path:
    """
    Return the path to the SQLite state file.

    Stored in a subfolder of the application directory so that state travels
    with the app and is the same on every OS. Recommended location:
    <application folder>/config/state.db
    """
    app_dir = _application_dir()
    config_dir = app_dir / CONFIG_SUBDIR
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / STATE_DB_FILENAME


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the app_state table if it does not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    conn.commit()


def _get_value(key: str) -> str | None:
    """Return the stored value for key, or None."""
    path = _db_path()
    if not path.exists():
        return None
    try:
        conn = sqlite3.connect(str(path))
        try:
            _ensure_schema(conn)
            row = conn.execute(
                "SELECT value FROM app_state WHERE key = ?",
                (key,),
            ).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    except Exception:
        return None


def _set_value(key: str, value: str) -> None:
    """Store a value for key. Creates config dir and DB if needed."""
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(str(path))
        try:
            _ensure_schema(conn)
            conn.execute(
                """
                INSERT INTO app_state (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def get_last_folder() -> str | None:
    """Return the last selected folder path, or None if none was stored."""
    return _get_value(LAST_FOLDER_KEY)


def set_last_folder(folder_path: str) -> None:
    """Persist the given folder path as the last selected folder."""
    _set_value(LAST_FOLDER_KEY, folder_path)


def get_main_window_geometry() -> str | None:
    """Return the last main window geometry (Qt base64), or None."""
    return _get_value(MAIN_WINDOW_GEOMETRY_KEY)


def set_main_window_geometry(geometry_base64: str) -> None:
    """Persist the main window geometry (Qt saveGeometry() as base64 string)."""
    _set_value(MAIN_WINDOW_GEOMETRY_KEY, geometry_base64)


def get_viewer_window_geometry() -> str | None:
    """Return the last viewer (display) window geometry (Qt base64), or None."""
    return _get_value(VIEWER_WINDOW_GEOMETRY_KEY)


def set_viewer_window_geometry(geometry_base64: str) -> None:
    """Persist the viewer window geometry (Qt saveGeometry() as base64 string)."""
    _set_value(VIEWER_WINDOW_GEOMETRY_KEY, geometry_base64)


def get_slideshow_interval_seconds() -> int:
    """Return the slideshow interval in seconds; default if not set."""
    raw = _get_value(SLIDESHOW_INTERVAL_SECONDS_KEY)
    if raw is None:
        return DEFAULT_SLIDESHOW_INTERVAL_SECONDS
    try:
        n = int(raw)
        return max(1, min(n, 3600))  # clamp 1–3600
    except ValueError:
        return DEFAULT_SLIDESHOW_INTERVAL_SECONDS


def set_slideshow_interval_seconds(seconds: int) -> None:
    """Persist the slideshow interval in seconds (1–3600)."""
    _set_value(SLIDESHOW_INTERVAL_SECONDS_KEY, str(max(1, min(seconds, 3600))))
