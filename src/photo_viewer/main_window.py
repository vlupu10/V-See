"""
Main application window for V-See.

Defines the primary window shown at startup, implementing the Manage-mode
three-pane layout (folder tree, file list/thumbnails, preview/metadata).
All panes are built via private helpers and wired with QSplitters for
resizable layout. The folder tree mirrors the real filesystem (rooted at
the user's home directory) and is populated lazily as folders are expanded.
The center pane uses the ThumbnailGridWidget component; the preview pane
is still a placeholder.

Author: Photo Viewer Project
Date: 2025-02-10
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from photo_viewer.components.thumbnail_grid import ThumbnailGridWidget
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

        # Root for the folder browser: current user's home directory.
        # This gives quick access to common locations (Desktop, Documents, Pictures, etc.)
        self._folder_root_path = Path.home()
        self._folder_root_item: QStandardItem | None = None
        self._folder_model = self._build_folder_model()

        # Thumbnail service for the center pane; decoding runs on background threads.
        self._thumbnail_service = ThumbnailService(parent=self)
        # Center pane: thumbnail grid component (created in _create_right_pane).
        self._thumbnail_grid: ThumbnailGridWidget | None = None

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

    # --- Folder tree pane ------------------------------------------------

    def _create_folder_pane(self) -> QWidget:
        """
        Create the left pane: a labelled "Folders" header and a tree view.

        The tree is backed by a QStandardItemModel that mirrors the real
        filesystem starting from the user's home directory. Child directories
        for a node are only populated when that node is expanded, avoiding
        heavy upfront scanning.
        """
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Folders", container)
        header.setObjectName("folderHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        tree_view = QTreeView(container)
        tree_view.setObjectName("folderTree")
        tree_view.setHeaderHidden(True)
        tree_view.setUniformRowHeights(True)

        tree_view.setModel(self._folder_model)

        # Expand the home directory node by default to mimic typical
        # file browsers and to give immediate context.
        if self._folder_root_item is not None:
            root_index = self._folder_model.indexFromItem(self._folder_root_item)
            tree_view.expand(root_index)

        # When a folder is expanded, lazily populate its child directories.
        tree_view.expanded.connect(self._on_folder_expanded)

        # When the current folder selection changes, update the file list pane.
        selection_model = tree_view.selectionModel()
        if selection_model is not None:
            selection_model.currentChanged.connect(self._on_folder_selected)

        layout.addWidget(header)
        layout.addWidget(tree_view)

        return container

    def _build_folder_model(self) -> QStandardItemModel:
        """
        Create a model containing a single top-level node for the user's
        home directory. Each node initially has a placeholder child so it
        can be expanded; real children are populated on demand.
        """
        model = QStandardItemModel(self)
        model.setHorizontalHeaderLabels(["Folders"])

        root_item = model.invisibleRootItem()

        home_path = self._folder_root_path
        home_display = home_path.name or str(home_path)

        home_item = QStandardItem(home_display)
        home_item.setData(str(home_path), Qt.ItemDataRole.UserRole)

        # Add a dummy child so the view shows an expand arrow; real
        # children are inserted when the node is expanded.
        home_item.appendRow(QStandardItem("…"))

        root_item.appendRow(home_item)
        self._folder_root_item = home_item

        return model

    def _on_folder_expanded(self, index) -> None:
        """
        Slot called when a folder node is expanded. Ensures that the
        node's child directories are populated at this moment.
        """
        item = self._folder_model.itemFromIndex(index)
        if item is None:
            return
        self._ensure_folder_children_loaded(item)

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
            if not dir_path.is_dir():
                return

            try:
                children = sorted(
                    [p for p in dir_path.iterdir() if p.is_dir()],
                    key=lambda p: p.name.lower(),
                )
            except PermissionError:
                # Skip directories we cannot read.
                return

            for child_path in children:
                child_item = QStandardItem(child_path.name)
                child_item.setData(str(child_path), Qt.ItemDataRole.UserRole)
                # Add placeholder so this directory can be expanded later.
                child_item.appendRow(QStandardItem("…"))
                item.appendRow(child_item)

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
        self._thumbnail_grid.load_folder(self._folder_root_path)
        return self._thumbnail_grid

    def _create_preview_pane(self) -> QWidget:
        """
        Create the preview / metadata pane (placeholder).

        A simple frame with a header and explanatory label. Later this will
        show a larger preview of the selected file and basic EXIF data
        (camera, ISO, shutter speed, date taken).
        """
        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Preview / Metadata", frame)
        header.setObjectName("previewHeader")

        placeholder = QLabel(
            "Preview of selected file will appear here.\n"
            "EXIF data (camera, ISO, shutter speed, date taken) will be shown below.",
            frame,
        )
        placeholder.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        placeholder.setWordWrap(True)

        layout.addWidget(header)
        layout.addWidget(placeholder)

        return frame

    # --- File list behaviour ----------------------------------------------

    def _on_folder_selected(self, current, _previous) -> None:
        """
        Slot called when the selection in the folder tree changes.

        It resolves the selected item's path and reloads the file list
        pane with the contents of that directory.
        """
        item = self._folder_model.itemFromIndex(current)
        if item is None:
            return

        path_str = item.data(Qt.ItemDataRole.UserRole)
        if not path_str:
            return

        folder_path = Path(path_str)
        if self._thumbnail_grid is not None:
            self._thumbnail_grid.load_folder(folder_path)
