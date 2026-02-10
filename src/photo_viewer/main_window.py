"""
Main application window for PhotoView Desktop.

Defines the primary window shown at startup, implementing the Manage-mode
three-pane layout (folder tree, file list/thumbnails, preview/metadata).
All panes are built via private helpers and wired with QSplitters for
resizable layout. Uses dummy data for the tree and file list until
real filesystem and thumbnail services are integrated.

Author: Photo Viewer Project
Date: 2025-02-10
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QMainWindow,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """
    Main application window.

    Starts in "Manage" mode with an ACDSee-style three-pane layout:
    - Left:   Folder tree (dummy data for now; will become filesystem tree)
    - Center: File list / thumbnail area (placeholder; will support grid and details view)
    - Bottom-right: Preview / metadata pane (placeholder; will show selected image and EXIF)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the window and initialise the three-pane UI."""
        super().__init__(parent)
        self.setWindowTitle("PhotoView Desktop – Manage")
        self.resize(1400, 900)

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

        The tree uses a dummy model for now to validate layout and splitter
        behaviour; it will be replaced by a lazily-loaded filesystem model.
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

        model = self._create_dummy_folder_model(tree_view)
        tree_view.setModel(model)
        tree_view.expandAll()

        layout.addWidget(header)
        layout.addWidget(tree_view)

        return container

    def _create_dummy_folder_model(self, parent: QWidget) -> QStandardItemModel:
        """
        Build a dummy hierarchical model for the folder tree.

        Used only to validate the layout. Provides a small tree (Pictures,
        Camera Roll, Downloads) with nested items. Will be replaced by
        QFileSystemModel (or similar) for lazy, on-expand directory loading.
        """
        model = QStandardItemModel(parent)
        root_item = model.invisibleRootItem()

        pictures = QStandardItem("Pictures")
        camera = QStandardItem("Camera Roll")
        downloads = QStandardItem("Downloads")

        holidays = QStandardItem("2024-Holidays")
        city = QStandardItem("City")
        mountains = QStandardItem("Mountains")
        holidays.appendRow(city)
        holidays.appendRow(mountains)
        pictures.appendRow(holidays)

        raw = QStandardItem("RAW")
        jpeg = QStandardItem("JPEG")
        camera.appendRow(raw)
        camera.appendRow(jpeg)

        root_item.appendRow(pictures)
        root_item.appendRow(camera)
        root_item.appendRow(downloads)

        return model

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

        file_list_pane = self._create_file_list_pane()
        preview_pane = self._create_preview_pane()

        vertical_splitter.addWidget(file_list_pane)
        vertical_splitter.addWidget(preview_pane)

        vertical_splitter.setStretchFactor(0, 3)
        vertical_splitter.setStretchFactor(1, 1)

        layout.addWidget(vertical_splitter)
        return container

    def _create_file_list_pane(self) -> QWidget:
        """
        Create the central file list / thumbnail pane (placeholder).

        Currently a QListView with dummy image filenames (IMG_0001.jpg …)
        to confirm sizing and scroll behaviour. Will be replaced by a
        virtualised thumbnail grid and/or details list with async loading.
        """
        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Files (Thumbnails / Details view placeholder)", frame)
        header.setObjectName("fileHeader")

        list_view = QListView(frame)
        list_view.setObjectName("fileList")

        model = QStandardItemModel(list_view)
        for i in range(1, 21):
            item = QStandardItem(f"IMG_{i:04d}.jpg")
            model.appendRow(item)
        list_view.setModel(model)

        layout.addWidget(header)
        layout.addWidget(list_view)

        return frame

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
