"""
Application-wide settings and path constants for PhotoView Desktop.

Defines project and source roots plus standard directories (docs, tmp)
so that components and services can resolve paths without hardcoding
the repository layout. Over time this module can grow to include
thumbnail sizes, worker limits, and cache locations.

Author: Viorel LUPU
Date: 2025-02-10
"""

from pathlib import Path

# Resolve project root: this file is src/photo_viewer/config/settings.py
# so parents[3] is the directory containing src/, docs/, tmp/, main.py.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
DOCS_ROOT = PROJECT_ROOT / "docs"
TMP_ROOT = PROJECT_ROOT / "tmp"
