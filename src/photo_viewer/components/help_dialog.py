"""
Help dialog for V-See.

Displays usage instructions in a modal dialog.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTextBrowser,
    QVBoxLayout,
)


HELP_HTML = """
<h2>V-See – Photo Viewer</h2>
<p>Manage, view, and slideshow photos with optional background music.</p>

<h3>Manage Mode (main window)</h3>
<ul>
<li><b>Photos folder</b> (top left) – Browse to select the folder of images to display.</li>
<li><b>Music folder</b> (bottom left) – Browse to select a folder of audio files for slideshow music.</li>
<li><b>Thumbnail grid</b> (center) – Shows images and videos (MP4, MOV, etc.) in the selected folder. Single-click to preview; double-click to open the viewer. Selecting a video plays it in the preview pane.</li>
<li><b>Preview pane</b> (right) – Shows a preview of the selected image, or plays the selected video until another thumbnail is chosen.</li>
<li><b>MP3 player</b> – Transport controls and volume slider. Music plays when you press Play or when the slideshow runs (if configured).</li>
</ul>

<h3>View Mode (viewer window)</h3>
<p>Opens when you double-click an image.</p>
<ul>
<li><b>Previous / Next</b> – Navigate between images in the folder.</li>
<li><b>Slideshow ON/OFF</b> – Start or stop automatic slideshow.</li>
<li><b>Stop music</b> – Stop background music.</li>
<li><b>Configure Slideshow</b> – Set interval (seconds between slides), music (No music, All songs, or start from a song), and video duration: first 5 seconds or full video.</li>
<li><b>Full Screen</b> – Toggle full screen. Press <b>Esc</b> to exit.</li>
</ul>

<h3>Tips</h3>
<ul>
<li>Videos in the slideshow play automatically: either the first 5 seconds or the full video, depending on Configure Slideshow.</li>
<li>Music auto-starts when the slideshow starts (if you chose music in Configure Slideshow).</li>
<li>Music stops when the slideshow stops, when you close the viewer, or when you close the main window.</li>
<li>Last folders and window positions are remembered on next run.</li>
<li>If a folder path becomes invalid (e.g. external drive disconnected), the app falls back to a safe location instead of crashing.</li>
</ul>
"""


class HelpDialog(QDialog):
    """Modal dialog displaying V-See usage instructions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("V-See – Help")
        self.setMinimumSize(480, 420)
        self.resize(520, 500)

        layout = QVBoxLayout(self)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(False)
        browser.setHtml(HELP_HTML)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok,
            parent=self,
        )
        button_box.accepted.connect(self.accept)

        layout.addWidget(browser)
        layout.addWidget(button_box)
