"""
Prevent display sleep during slideshow (like YouTube keeps screen on during video).

Uses system APIs to tell the OS not to turn off the display while the slideshow
is running. macOS: caffeinate -d. Windows: SetThreadExecutionState.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any


class DisplaySleepPreventer:
    """
    Prevents the display from sleeping. Use when slideshow is running.

    Call start() when slideshow starts, stop() when it stops.
    On macOS uses caffeinate -d (built-in); on Windows uses SetThreadExecutionState.
    """

    def __init__(self) -> None:
        self._caffeinate_process: subprocess.Popen[Any] | None = None
        self._windows_prev_state: int | None = None

    def start(self) -> None:
        """Start preventing display sleep."""
        if sys.platform == "darwin":
            self._start_macos()
        elif sys.platform == "win32":
            self._start_windows()

    def stop(self) -> None:
        """Stop preventing display sleep; allow normal behavior."""
        if sys.platform == "darwin":
            self._stop_macos()
        elif sys.platform == "win32":
            self._stop_windows()

    def _start_macos(self) -> None:
        try:
            self._caffeinate_process = subprocess.Popen(
                ["caffeinate", "-d"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except FileNotFoundError:
            pass  # caffeinate should always exist on macOS

    def _stop_macos(self) -> None:
        if self._caffeinate_process is not None:
            try:
                self._caffeinate_process.terminate()
                self._caffeinate_process.wait(timeout=2)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    self._caffeinate_process.kill()
                except ProcessLookupError:
                    pass
            finally:
                self._caffeinate_process = None

    def _start_windows(self) -> None:
        try:
            import ctypes

            ES_CONTINUOUS = 0x80000000
            ES_DISPLAY_REQUIRED = 0x00000002
            ES_SYSTEM_REQUIRED = 0x00000001

            # Store previous state for reset (not required for ES_CONTINUOUS)
            prev = ctypes.windll.kernel32.SetThreadExecutionState(  # type: ignore[attr-defined]
                ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED
            )
            if prev != 0:
                self._windows_prev_state = prev
        except (AttributeError, OSError):
            pass

    def _stop_windows(self) -> None:
        try:
            import ctypes

            ES_CONTINUOUS = 0x80000000
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)  # type: ignore[attr-defined]
            self._windows_prev_state = None
        except (AttributeError, OSError):
            pass
