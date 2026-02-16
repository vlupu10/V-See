"""
Main application window for V-See.

Defines the primary window shown at startup, implementing the Manage-mode
three-pane layout (folder tree, file list/thumbnails, preview/metadata).
All panes are built via private helpers and wired with QSplitters for
resizable layout. The folder tree mirrors the real filesystem (rooted at
the user's home directory on macOS/Linux, or drive root on Windows).
Child directories are populated lazily as folders are expanded.
The center pane uses the ThumbnailGridWidget component; the preview pane
is still a placeholder.

Author: Viorel LUPU
Date: 2025-02-10
"""

import os
import string
import sys
import time
from pathlib import Path

from PyQt6.QtCore import QByteArray, QEvent, Qt, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from photo_viewer.components.help_dialog import HelpDialog
from photo_viewer.components.image_viewer_window import ImageViewerWindow
from photo_viewer.components.slideshow_config_dialog import SlideshowConfigDialog

_mp3_import_error: str | None = None
try:
    from mp3_player import Mp3PlayerWidget, load_sound_files
except ImportError as e:
    Mp3PlayerWidget = None  # type: ignore[misc, assignment]
    _mp3_import_error = str(e)
    try:
        from photo_viewer.services.audio import load_sound_files
    except ImportError:
        load_sound_files = None  # type: ignore[assignment, misc]

# Fallback when neither mp3_player nor services.audio is available (list still populates)
AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")

# Video extensions for preview playback
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".m4v", ".webm"})

_video_available = False
try:
    from PyQt6.QtMultimedia import QMediaPlayer
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    _video_available = True
except ImportError:
    QMediaPlayer = None  # type: ignore[misc, assignment]
    QVideoWidget = None  # type: ignore[misc, assignment]


def _load_sound_files_fallback(sound_dir: Path) -> dict[str, Path]:
    """Scan folder for audio files when mp3_player is not installed."""
    try:
        if not sound_dir.exists() or not sound_dir.is_dir():
            return {}
    except OSError:
        return {}
    sound_files: dict[str, Path] = {}
    ext_lower = tuple(e.lower() for e in AUDIO_EXTENSIONS)
    try:
        for path in sorted(sound_dir.iterdir(), key=lambda p: p.name.lower()):
            if path.is_file() and path.suffix.lower() in ext_lower:
                sound_files[path.stem] = path
    except (PermissionError, OSError):
        pass
    return sound_files
from photo_viewer.components.thumbnail_grid import ThumbnailGridWidget
from photo_viewer.services.persistence import (
    get_last_folder,
    get_last_music_folder,
    get_main_window_geometry,
    get_slideshow_music,
    set_last_folder,
    set_last_music_folder,
    set_main_window_geometry,
)
from photo_viewer.services.thumbnails import ThumbnailService


class MainWindow(QMainWindow):
    """
    Main application window.

    Starts in "Manage" mode with an ACDSee-style three-pane layout:
    - Left:   Folder tree rooted at the user's home directory
    - Center: ThumbnailGridWidget component (grid of thumbnails with async loading)
    - Bottom-right: Preview / metadata pane (placeholder; will show selected image and EXIF)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the window and initialise the three-pane UI."""
        super().__init__(parent)
        self.setWindowTitle("V-See – Manage")
        self.resize(1400, 900)

        # Folder roots for the tree. Windows: all drive letters (C:\, D:\, etc).
        # macOS: Home + /Volumes (external drives). Linux: Home + /media/username.
        self._folder_root_paths = self._get_folder_roots()
        self._folder_root_path = (
            self._folder_root_paths[0][1] if self._folder_root_paths else Path.home()
        )
        self._folder_root_item: QStandardItem | None = None
        self._folder_model, self._folder_root_item = self._build_folder_model()
        self._music_folder_root_item: QStandardItem | None = None
        self._music_folder_model, self._music_folder_root_item = self._build_folder_model()

        # Thumbnail service for the center pane; decoding runs on background threads.
        self._thumbnail_service = ThumbnailService(parent=self)
        # Center pane: thumbnail grid component (created in _create_right_pane).
        self._thumbnail_grid: ThumbnailGridWidget | None = None

        # Preview pane widgets (created in _create_preview_pane).
        self._preview_image_label: QLabel | None = None
        self._preview_image_path: Path | None = None  # current image path, for resize re-scale
        # Folder tree views for photos and music.
        self._folder_tree_view: QTreeView | None = None
        self._music_folder_tree_view: QTreeView | None = None
        # Go-up buttons (Windows only) for navigating to parent folder.
        self._btn_go_up: QPushButton | None = None
        self._btn_music_go_up: QPushButton | None = None
        # Music section: file list and player.
        self._music_file_list: QListWidget | None = None
        self._mp3_player: Mp3PlayerWidget | None = None

        # Prevent viewer opens during init (avoids rapid spawn on Windows when
        # Qt emits spurious signals before main window is shown).
        self._main_window_ready = False
        self._last_thumbnail_activated_at = 0.0

        self._init_ui()

    # --- UI construction -------------------------------------------------

    def _init_ui(self) -> None:
        """
        Build the top-level layout: horizontal splitter with folder pane on the
        left and a vertical splitter (file list + preview) on the right.

        Stretch factors give roughly 20% width to the folder tree and 80% to
        the right side so the file list is the dominant area by default.
        """
        outer_splitter = QSplitter(Qt.Orientation.Horizontal, self)

        folder_pane = self._create_folder_pane()
        right_pane = self._create_right_pane()

        outer_splitter.addWidget(folder_pane)
        outer_splitter.addWidget(right_pane)

        outer_splitter.setStretchFactor(0, 1)
        outer_splitter.setStretchFactor(1, 4)

        self.setCentralWidget(outer_splitter)

        # Status bar with Help button on the right
        btn_help = QPushButton("Help", self)
        btn_help.setToolTip("Show usage instructions")
        btn_help.clicked.connect(self._on_help_clicked)
        self.statusBar().addPermanentWidget(btn_help)

        # Restore last main window size/position if stored.
        geo = get_main_window_geometry()
        if geo:
            ba = QByteArray.fromBase64(geo.encode("ascii"))
            if not ba.isEmpty():
                self.restoreGeometry(ba)

        # Restore last visited folder from persistence, or select home.
        self._restore_last_folder()
        # Defer so tree selection is fully applied before we read it
        QTimer.singleShot(0, self._update_music_file_list)

    # --- Folder tree pane ------------------------------------------------

    def _create_folder_pane(self) -> QWidget:
        """
        Create the left pane: vertically split into Photos folder (top) and
        Music folder (bottom). Each has a tree view for selecting a directory.
        """
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        vertical_splitter = QSplitter(Qt.Orientation.Vertical, container)

        # --- Top: Photos folder ---
        photos_section = QWidget(container)
        photos_layout = QVBoxLayout(photos_section)
        photos_layout.setContentsMargins(0, 0, 0, 0)
        photos_layout.setSpacing(4)

        if sys.platform == "win32":
            btn_go_up = QPushButton("↑", photos_section)
            btn_go_up.setObjectName("btnGoUp")
            btn_go_up.setToolTip("Go up one level (photos)")
            btn_go_up.setMaximumWidth(32)
            btn_go_up.clicked.connect(self._on_photos_go_up_clicked)
            self._btn_go_up = btn_go_up
            photos_layout.addWidget(btn_go_up)

        photos_header = QLabel("Photos folder", photos_section)
        photos_header.setObjectName("folderHeader")
        photos_header.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        photos_tree = QTreeView(photos_section)
        photos_tree.setObjectName("folderTree")
        photos_tree.setHeaderHidden(True)
        photos_tree.setUniformRowHeights(True)
        self._folder_tree_view = photos_tree
        photos_tree.setModel(self._folder_model)

        if self._folder_root_item is not None:
            root_index = self._folder_model.indexFromItem(self._folder_root_item)
            photos_tree.expand(root_index)

        photos_tree.expanded.connect(self._on_photos_folder_expanded)
        sel_model = photos_tree.selectionModel()
        if sel_model is not None:
            sel_model.currentChanged.connect(self._on_folder_selected)

        photos_layout.addWidget(photos_header)
        photos_layout.addWidget(photos_tree)

        # --- Bottom: Music folder ---
        music_section = QWidget(container)
        music_section.setMinimumHeight(200)
        music_layout = QVBoxLayout(music_section)
        music_layout.setContentsMargins(0, 0, 0, 0)
        music_layout.setSpacing(4)

        if sys.platform == "win32":
            btn_music_go_up = QPushButton("↑", music_section)
            btn_music_go_up.setObjectName("btnMusicGoUp")
            btn_music_go_up.setToolTip("Go up one level (music)")
            btn_music_go_up.setMaximumWidth(32)
            btn_music_go_up.clicked.connect(self._on_music_go_up_clicked)
            self._btn_music_go_up = btn_music_go_up
            music_layout.addWidget(btn_music_go_up)

        music_header = QLabel("Music folder", music_section)
        music_header.setObjectName("musicFolderHeader")
        music_header.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        music_tree = QTreeView(music_section)
        music_tree.setObjectName("musicFolderTree")
        music_tree.setHeaderHidden(True)
        music_tree.setUniformRowHeights(True)
        self._music_folder_tree_view = music_tree
        music_tree.setModel(self._music_folder_model)

        if self._music_folder_root_item is not None:
            root_index = self._music_folder_model.indexFromItem(
                self._music_folder_root_item
            )
            music_tree.expand(root_index)

        music_tree.expanded.connect(self._on_music_folder_expanded)
        music_sel = music_tree.selectionModel()
        if music_sel is not None:
            music_sel.currentChanged.connect(self._on_music_folder_selected)

        music_layout.addWidget(music_header)
        music_layout.addWidget(music_tree)

        # Music files list (vertical) - populated when folder is selected
        music_files_label = QLabel("Playable files:", music_section)
        music_files_list = QListWidget(music_section)
        music_files_list.setObjectName("musicFileList")
        music_files_list.setMinimumHeight(80)
        music_files_list.itemDoubleClicked.connect(self._on_music_file_double_clicked)
        self._music_file_list = music_files_list
        music_layout.addWidget(music_files_label)
        music_layout.addWidget(music_files_list)

        # MP3 player controls
        if Mp3PlayerWidget is not None:
            self._mp3_player = Mp3PlayerWidget(music_section)
            music_layout.addWidget(self._mp3_player)
        else:
            hint = "pip install -e \"../vio-python[qt]\" (from Project-photo-viewer)"
            if _mp3_import_error:
                hint = f"{_mp3_import_error} — {hint}"
            no_player = QLabel(f"Install mp3-player[qt] for playback\n{hint}", music_section)
            no_player.setStyleSheet("color: gray; font-size: 11px;")
            no_player.setWordWrap(True)
            music_layout.addWidget(no_player)

        vertical_splitter.addWidget(photos_section)
        vertical_splitter.addWidget(music_section)
        vertical_splitter.setStretchFactor(0, 1)
        vertical_splitter.setStretchFactor(1, 1)

        layout.addWidget(vertical_splitter)
        return container

    def _get_selected_folder_path(self) -> Path | None:
        """Return the path of the currently selected photos folder, or None."""
        if self._folder_tree_view is None or self._folder_model is None:
            return None
        index = self._folder_tree_view.currentIndex()
        item = self._folder_model.itemFromIndex(index)
        if item is None:
            return None
        path_str = item.data(Qt.ItemDataRole.UserRole)
        if not path_str:
            return None
        return Path(path_str)

    def _get_selected_music_folder_path(self) -> Path | None:
        """Return the path of the currently selected music folder, or None."""
        if self._music_folder_tree_view is None or self._music_folder_model is None:
            return None
        index = self._music_folder_tree_view.currentIndex()
        item = self._music_folder_model.itemFromIndex(index)
        if item is None:
            return None
        path_str = item.data(Qt.ItemDataRole.UserRole)
        if not path_str:
            return None
        return Path(path_str)

    def _on_photos_go_up_clicked(self) -> None:
        """
        Navigate to the parent of the currently selected folder.

        Windows only. Disabled when at drive root (parent equals self).
        """
        current = self._get_selected_folder_path()
        if current is None:
            return
        try:
            if not current.is_dir():
                return
            parent = current.resolve().parent
            # At drive root, parent equals current (e.g. C:\ parent is C:\).
            if parent == current or not parent.is_dir():
                return
        except (OSError, PermissionError):
            return  # e.g. drive disconnected
        try:
            set_last_folder(str(parent))
            self._expand_and_select_path(
                parent, self._folder_tree_view, self._folder_model, self._folder_root_item
            )
        except (OSError, PermissionError):
            return
        self._update_go_up_button_state()

    def _on_music_go_up_clicked(self) -> None:
        """Navigate to the parent of the currently selected music folder."""
        current = self._get_selected_music_folder_path()
        if current is None:
            return
        try:
            if not current.is_dir():
                return
            parent = current.resolve().parent
            if parent == current or not parent.is_dir():
                return
        except (OSError, PermissionError):
            return  # e.g. drive disconnected
        try:
            set_last_music_folder(str(parent))
            self._expand_and_select_path(
                parent,
                self._music_folder_tree_view,
                self._music_folder_model,
                self._music_folder_root_item,
            )
        except (OSError, PermissionError):
            return
        self._update_go_up_button_state()

    def _update_go_up_button_state(self) -> None:
        """Enable or disable the Go up buttons based on current selections."""
        if self._btn_go_up is not None:
            current = self._get_selected_folder_path()
            try:
                if current is None or not current.is_dir():
                    self._btn_go_up.setEnabled(False)
                else:
                    parent = current.resolve().parent
                    self._btn_go_up.setEnabled(parent != current and parent.is_dir())
            except (OSError, PermissionError):
                self._btn_go_up.setEnabled(False)
        if self._btn_music_go_up is not None:
            current = self._get_selected_music_folder_path()
            try:
                if current is None or not current.is_dir():
                    self._btn_music_go_up.setEnabled(False)
                else:
                    parent = current.resolve().parent
                    self._btn_music_go_up.setEnabled(
                        parent != current and parent.is_dir()
                    )
            except (OSError, PermissionError):
                self._btn_music_go_up.setEnabled(False)

    def _get_folder_roots(self) -> list[tuple[str, Path]]:
        """
        Return list of (display_name, path) for top-level folder roots.
        Includes external drives/volumes so temporarily attached devices appear.
        """
        roots: list[tuple[str, Path]] = []
        if sys.platform == "win32":
            # All logical drives (C:\, D:\, etc.) including external USB drives.
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                try:
                    if os.path.exists(drive):
                        roots.append((drive, Path(drive)))
                except OSError:
                    pass
        elif sys.platform == "darwin":
            # Home directory + /Volumes (includes external drives, network mounts).
            roots.append(("Home", Path.home()))
            volumes = Path("/Volumes")
            if volumes.is_dir():
                roots.append(("Volumes", volumes))
        else:
            # Linux: Home + /media/username (typical mount point for removable media).
            roots.append(("Home", Path.home()))
            media_user = Path("/media") / os.environ.get("USER", "user")
            if media_user.is_dir():
                roots.append(("Media", media_user))
            # Also add /mnt in case user mounts there.
            if Path("/mnt").is_dir():
                roots.append(("mnt", Path("/mnt")))
        return roots if roots else [("Home", Path.home())]

    def _build_folder_model(self) -> tuple[QStandardItemModel, QStandardItem]:
        """
        Create a model with top-level nodes for each folder root (drives/volumes).
        Each node has a placeholder child; real children are loaded on expand.
        Returns (model, first_root_item).
        """
        model = QStandardItemModel(self)
        model.setHorizontalHeaderLabels(["Folders"])

        invisible_root = model.invisibleRootItem()
        first_item: QStandardItem | None = None

        for display_name, path in self._folder_root_paths:
            try:
                if not path.exists() or not path.is_dir():
                    continue
            except (OSError, PermissionError):
                continue
            item = QStandardItem(display_name)
            item.setData(str(path), Qt.ItemDataRole.UserRole)
            item.appendRow(QStandardItem("…"))
            invisible_root.appendRow(item)
            if first_item is None:
                first_item = item

        if first_item is None:
            fallback = QStandardItem("Home")
            fallback.setData(str(Path.home()), Qt.ItemDataRole.UserRole)
            fallback.appendRow(QStandardItem("…"))
            invisible_root.appendRow(fallback)
            first_item = fallback

        return model, first_item

    def _on_photos_folder_expanded(self, index) -> None:
        """Slot called when a photos folder node is expanded."""
        item = self._folder_model.itemFromIndex(index)
        if item is None:
            return
        self._ensure_folder_children_loaded(item)

    def _on_music_folder_expanded(self, index) -> None:
        """Slot called when a music folder node is expanded."""
        item = self._music_folder_model.itemFromIndex(index)
        if item is None:
            return
        self._ensure_folder_children_loaded(item)

    def _on_music_folder_selected(self, current, _previous) -> None:
        """Slot called when the music folder selection changes."""
        item = self._music_folder_model.itemFromIndex(current)
        if item is None:
            return
        path_str = item.data(Qt.ItemDataRole.UserRole)
        if not path_str:
            return
        if not self._is_path_valid_folder(path_str):
            self._expand_and_select_path(
                self._folder_root_path,
                self._music_folder_tree_view,
                self._music_folder_model,
                self._music_folder_root_item,
            )
            set_slideshow_music(SlideshowConfigDialog.NO_MUSIC)
            self._update_go_up_button_state()
            self._update_music_file_list()
            return
        set_last_music_folder(path_str)
        self._update_go_up_button_state()
        self._update_music_file_list()

    def _on_music_file_double_clicked(self, item: QListWidgetItem) -> None:
        """Double-click on a song: jump to it and start playback immediately."""
        folder = self._get_selected_music_folder_path()
        if folder is None or self._mp3_player is None:
            return
        song_name = item.text()
        if not song_name:
            return
        try:
            self._mp3_player.set_playlist_from_folder(folder, start_from_name=song_name)
            self._mp3_player.start_playback()
        except (OSError, PermissionError):
            pass

    def _update_music_file_list(self) -> None:
        """Populate the music file list and MP3 player from the selected music folder."""
        folder = self._get_selected_music_folder_path()
        if self._music_file_list is None:
            return
        self._music_file_list.clear()
        if folder is None:
            return
        if not self._is_path_valid_folder(str(folder)):
            return
        loader = load_sound_files if load_sound_files is not None else _load_sound_files_fallback
        try:
            songs = loader(folder)
        except (OSError, PermissionError):
            return
        for name in sorted(songs.keys()):
            self._music_file_list.addItem(QListWidgetItem(name))
        if self._mp3_player is not None:
            try:
                self._mp3_player.set_playlist_from_folder(folder)
            except (OSError, PermissionError):
                pass

    def _ensure_folder_children_loaded(self, item: QStandardItem) -> None:
        """
        Populate the given item's child directories if they have not
        been loaded yet (lazy loading).
        """
        # If the only child has no path data, treat it as a placeholder
        # and replace it with real children.
        if item.rowCount() == 1 and not item.child(0).data(Qt.ItemDataRole.UserRole):
            item.removeRows(0, item.rowCount())

            dir_path = Path(item.data(Qt.ItemDataRole.UserRole))
            try:
                if not dir_path.is_dir():
                    return
                children = sorted(
                    [p for p in dir_path.iterdir() if p.is_dir()],
                    key=lambda p: p.name.lower(),
                )
            except (PermissionError, OSError):
                return

            for child_path in children:
                child_item = QStandardItem(child_path.name)
                child_item.setData(str(child_path), Qt.ItemDataRole.UserRole)
                # Add placeholder so this directory can be expanded later.
                child_item.appendRow(QStandardItem("…"))
                item.appendRow(child_item)

    def _is_path_valid_folder(self, path_str: str) -> bool:
        """
        Return True if the path exists, is a directory, and is under any tree root.
        Handles disconnected external drives, deleted folders, etc.
        """
        if not path_str or not path_str.strip():
            return False
        try:
            path = Path(path_str).resolve()
            if not path.is_dir():
                return False
            for _name, root in self._folder_root_paths:
                try:
                    path.relative_to(root.resolve())
                    return True
                except ValueError:
                    continue
            return False
        except (OSError, RuntimeError):
            return False

    def _get_root_item_for_path(
        self, path: Path, model: QStandardItemModel | None = None
    ) -> QStandardItem | None:
        """Return the top-level tree item that contains the given path, or None."""
        try:
            path = path.resolve()
        except (OSError, RuntimeError):
            return None
        m = model if model is not None else self._folder_model
        invisible = m.invisibleRootItem()
        for row in range(invisible.rowCount()):
            item = invisible.child(row)
            if item is None:
                continue
            root_str = item.data(Qt.ItemDataRole.UserRole)
            if not root_str:
                continue
            try:
                root = Path(root_str).resolve()
                path.relative_to(root)
                return item
            except ValueError:
                continue
        return None

    def _restore_last_folder(self) -> None:
        """
        Restore the last visited photos and music folders from persistence.

        If persisted paths are invalid (e.g. deleted folders, disconnected
        external drives), fall back to the tree root. When the music folder
        cannot be restored, the slideshow music dropdown is reset to "No music".
        """
        root = self._folder_root_path.resolve()

        # Photos folder
        last = get_last_folder()
        use_last = self._is_path_valid_folder(last) if last else False
        if use_last:
            try:
                path = Path(last).resolve()
                self._expand_and_select_path(
                    path,
                    self._folder_tree_view,
                    self._folder_model,
                    self._folder_root_item,
                )
            except (ValueError, OSError, RuntimeError):
                use_last = False
        if not use_last:
            self._expand_and_select_path(
                self._folder_root_path,
                self._folder_tree_view,
                self._folder_model,
                self._folder_root_item,
            )

        # Music folder
        last_music = get_last_music_folder()
        use_last_music = self._is_path_valid_folder(last_music) if last_music else False
        if use_last_music:
            try:
                path = Path(last_music).resolve()
                self._expand_and_select_path(
                    path,
                    self._music_folder_tree_view,
                    self._music_folder_model,
                    self._music_folder_root_item,
                )
            except (ValueError, OSError, RuntimeError):
                use_last_music = False
        if not use_last_music:
            self._expand_and_select_path(
                self._folder_root_path,
                self._music_folder_tree_view,
                self._music_folder_model,
                self._music_folder_root_item,
            )
            set_slideshow_music(SlideshowConfigDialog.NO_MUSIC)

        self._update_go_up_button_state()

    def _expand_and_select_path(
        self,
        path: Path,
        tree_view: QTreeView | None,
        model: QStandardItemModel,
        root_item: QStandardItem | None,
    ) -> None:
        """
        Expand the folder tree along the given path and select the final node.
        On OSError (e.g. disconnected drive), falls back to selecting root.
        Supports multiple roots (drives/volumes); finds the correct root for the path.
        """
        if tree_view is None or root_item is None:
            return

        root_item = self._get_root_item_for_path(path, model) or root_item
        root_str = root_item.data(Qt.ItemDataRole.UserRole)
        if not root_str:
            return

        try:
            path = path.resolve()
            root = Path(root_str).resolve()
        except (OSError, PermissionError):
            root_index = model.indexFromItem(root_item)
            tree_view.setCurrentIndex(root_index)
            return

        if path == root:
            root_index = model.indexFromItem(root_item)
            tree_view.expand(root_index)
            tree_view.setCurrentIndex(root_index)
            return

        try:
            relative = path.relative_to(root)
        except ValueError:
            root_index = model.indexFromItem(root_item)
            tree_view.expand(root_index)
            tree_view.setCurrentIndex(root_index)
            return

        parts = relative.parts
        current_item = root_item
        current_path = root

        for part in parts:
            current_path = current_path / part
            try:
                self._ensure_folder_children_loaded(current_item)
            except (OSError, PermissionError):
                break
            index = model.indexFromItem(current_item)
            tree_view.expand(index)

            found = None
            for row in range(current_item.rowCount()):
                child = current_item.child(row)
                if child.data(Qt.ItemDataRole.UserRole) == str(current_path):
                    found = child
                    break
            if found is None:
                break
            current_item = found

        target_index = model.indexFromItem(current_item)
        tree_view.setCurrentIndex(target_index)

    # --- Help ------------------------------------------------------------

    def _on_help_clicked(self) -> None:
        """Show the Help dialog with usage instructions."""
        HelpDialog(self).exec()

    # --- Slideshow music (auto-start when slideshow runs) ----------------

    def start_slideshow_music_if_configured(self) -> None:
        """
        Start music playback if a music folder is selected and the persisted
        dropdown is not "No music". Called by the viewer when slideshow starts.
        Skips if the folder is invalid (e.g. disconnected external drive).
        If music is already playing, leaves it playing (does not restart).
        """
        folder = self._get_selected_music_folder_path()
        if folder is None or not self._is_path_valid_folder(str(folder)):
            return
        if self._mp3_player is None:
            return
        if self._mp3_player.is_playing():
            return  # Already playing; don't restart
        music_choice = get_slideshow_music()
        if music_choice == SlideshowConfigDialog.NO_MUSIC:
            return
        start_from = None
        if music_choice not in (SlideshowConfigDialog.NO_MUSIC, SlideshowConfigDialog.ALL_SONGS):
            start_from = music_choice
        loader = load_sound_files if load_sound_files else _load_sound_files_fallback
        try:
            songs = loader(folder)
        except (OSError, PermissionError):
            self.statusBar().showMessage("Music: could not read folder.", 5000)
            return
        if not songs:
            self.statusBar().showMessage("Music: no audio files in folder.", 5000)
            return
        try:
            self._mp3_player.set_playlist_from_folder(folder, start_from_name=start_from)
            self._mp3_player.start_playback()
        except (OSError, PermissionError, FileNotFoundError) as e:
            self.statusBar().showMessage(
                f"Music: could not start — {e}",
                5000,
            )

    def stop_slideshow_music(self) -> None:
        """Stop music playback. Called by the viewer when slideshow stops."""
        if self._mp3_player is not None:
            self._mp3_player.stop_playback()

    # --- Right side: file list + preview --------------------------------

    def _create_right_pane(self) -> QWidget:
        """
        Create the right-hand area as a vertical splitter.

        Top widget: file list / thumbnail pane (main content area).
        Bottom widget: preview / metadata pane. Stretch factors favour the
        file list (3) over the preview (1) so the grid/list is the primary view.
        """
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 4, 4)
        layout.setSpacing(4)

        vertical_splitter = QSplitter(Qt.Orientation.Vertical, container)

        file_list_pane = self._create_thumbnail_grid_pane()
        preview_pane = self._create_preview_pane()

        vertical_splitter.addWidget(file_list_pane)
        vertical_splitter.addWidget(preview_pane)

        vertical_splitter.setStretchFactor(0, 3)
        vertical_splitter.setStretchFactor(1, 1)

        layout.addWidget(vertical_splitter)
        return container

    def _create_thumbnail_grid_pane(self) -> QWidget:
        """
        Create the central pane using the ThumbnailGridWidget component.

        The component owns the list model, path-to-item mapping, and
        thumbnail updates; we only pass the folder path when selection changes.
        """
        self._thumbnail_grid = ThumbnailGridWidget(
            self._thumbnail_service,
            parent=self,
        )
        # React to selection changes in the grid to update the preview pane.
        self._thumbnail_grid.selection_changed.connect(self._on_thumbnail_selected)
        # React to double-click activation to open the external viewer.
        self._thumbnail_grid.activated.connect(self._on_thumbnail_activated)
        return self._thumbnail_grid

    def _create_preview_pane(self) -> QWidget:
        """
        Create the preview / metadata pane.

        Shows a scaled preview of the selected image, or plays the selected
        video. Uses QStackedWidget to switch between image and video views.
        """
        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Preview / Metadata", frame)
        header.setObjectName("previewHeader")

        self._preview_stacked = QStackedWidget(frame)

        image_label = QLabel(frame)
        image_label.setObjectName("previewImage")
        image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        image_label.setMinimumHeight(200)
        image_label.setText("No image selected.")
        image_label.installEventFilter(self)

        self._preview_image_label = image_label
        self._preview_stacked.addWidget(image_label)

        self._preview_media_player = None
        self._preview_video_widget = None
        if _video_available and QVideoWidget is not None and QMediaPlayer is not None:
            video_widget = QVideoWidget(frame)
            video_widget.setMinimumHeight(200)
            self._preview_video_widget = video_widget
            self._preview_stacked.addWidget(video_widget)
            self._preview_media_player = QMediaPlayer()
            self._preview_media_player.setVideoOutput(video_widget)

        layout.addWidget(header)
        layout.addWidget(self._preview_stacked)

        return frame

    # --- File list behaviour ----------------------------------------------

    def _on_folder_selected(self, current, _previous) -> None:
        """
        Slot called when the selection in the folder tree changes.

        It resolves the selected item's path and reloads the file list
        pane with the contents of that directory. Falls back to root if
        the path is invalid (e.g. disconnected drive).
        """
        item = self._folder_model.itemFromIndex(current)
        if item is None:
            return

        path_str = item.data(Qt.ItemDataRole.UserRole)
        if not path_str:
            return

        if not self._is_path_valid_folder(path_str):
            self._expand_and_select_path(
                self._folder_root_path,
                self._folder_tree_view,
                self._folder_model,
                self._folder_root_item,
            )
            self._update_go_up_button_state()
            return

        folder_path = Path(path_str)
        set_last_folder(path_str)
        if self._thumbnail_grid is not None:
            self._thumbnail_grid.load_folder(folder_path)
        self._update_go_up_button_state()

    def _on_thumbnail_selected(self, path_str: str) -> None:
        """
        Slot called when the user selects a thumbnail in the center pane.

        Loads the corresponding image and displays a scaled preview in
        the preview pane.
        """
        if not path_str:
            return
        self._update_preview(Path(path_str))

    def _on_thumbnail_activated(self, paths: list[str], index: int) -> None:
        """
        Slot called when the user double-clicks a thumbnail in the grid.

        Opens a separate viewer window that can navigate within the list
        using Next/Previous controls and an optional slideshow.

        Guard: ignore activations before main window is shown (avoids rapid
        viewer spawn on Windows from spurious Qt signals during init).
        Debounce: ignore repeated activations within 400ms.
        """
        if not self._main_window_ready:
            return
        now = time.monotonic()
        if now - self._last_thumbnail_activated_at < 0.4:
            return
        self._last_thumbnail_activated_at = now

        image_paths = [Path(p) for p in paths]
        music_folder = self._get_selected_music_folder_path()
        viewer = ImageViewerWindow(
            image_paths,
            start_index=index,
            music_folder=music_folder,
            main_window=self,
            parent=self,
        )
        viewer.show()

    def _update_preview(self, path: Path | None) -> None:
        """Show the selected image or play the selected video in the preview pane."""
        if self._preview_image_label is None:
            return

        # Stop any playing video
        if self._preview_media_player is not None:
            self._preview_media_player.stop()

        if path is None:
            self._preview_image_path = None
            self._preview_stacked.setCurrentWidget(self._preview_image_label)
            self._preview_image_label.setText("No image selected.")
            self._preview_image_label.setPixmap(QPixmap())
            return

        try:
            if not path.is_file():
                self._preview_image_path = None
                self._preview_stacked.setCurrentWidget(self._preview_image_label)
                self._preview_image_label.setText("Selected item is not a file.")
                self._preview_image_label.setPixmap(QPixmap())
                return
        except OSError:
            self._preview_image_path = None
            self._preview_stacked.setCurrentWidget(self._preview_image_label)
            self._preview_image_label.setText("Cannot load (device disconnected?).")
            self._preview_image_label.setPixmap(QPixmap())
            return

        # Video: play in video widget
        if path.suffix.lower() in VIDEO_EXTENSIONS and self._preview_media_player is not None:
            self._preview_image_path = None
            self._preview_stacked.setCurrentWidget(self._preview_video_widget)
            self._preview_media_player.setSource(QUrl.fromLocalFile(str(path.resolve())))
            self._preview_media_player.play()
            return

        # Image: show scaled pixmap
        try:
            pixmap = QPixmap(str(path))
        except (OSError, PermissionError):
            self._preview_image_path = None
            self._preview_stacked.setCurrentWidget(self._preview_image_label)
            self._preview_image_label.setText("Cannot load image.")
            self._preview_image_label.setPixmap(QPixmap())
            return
        if pixmap.isNull():
            self._preview_image_path = None
            self._preview_stacked.setCurrentWidget(self._preview_image_label)
            self._preview_image_label.setText("Cannot load image.")
            self._preview_image_label.setPixmap(QPixmap())
            return

        self._preview_image_path = path
        self._preview_stacked.setCurrentWidget(self._preview_image_label)

        target_size = self._preview_image_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            target_size = pixmap.size()

        scaled = pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview_image_label.setPixmap(scaled)
        self._preview_image_label.setText("")

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        """Re-scale the preview image when the preview pane is resized (e.g. splitter moved)."""
        if (
            event.type() == QEvent.Type.Resize
            and watched is self._preview_image_label
            and self._preview_image_path is not None
        ):
            self._update_preview(self._preview_image_path)
        return super().eventFilter(watched, event)

    def showEvent(self, event) -> None:  # type: ignore[override]
        """Mark main window as ready so thumbnail activations can open viewer windows."""
        super().showEvent(event)
        self._main_window_ready = True

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Stop music, stop preview video, and persist geometry when the window is closed."""
        self.stop_slideshow_music()
        if self._preview_media_player is not None:
            self._preview_media_player.stop()
        geo = self.saveGeometry()
        if not geo.isEmpty():
            set_main_window_geometry(geo.toBase64().data().decode("ascii"))
        super().closeEvent(event)
