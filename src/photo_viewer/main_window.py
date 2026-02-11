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

import sys
from pathlib import Path

from PyQt6.QtCore import QByteArray, QEvent, Qt
from PyQt6.QtGui import QPixmap, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from photo_viewer.components.image_viewer_window import ImageViewerWindow
from photo_viewer.components.thumbnail_grid import ThumbnailGridWidget
from photo_viewer.services.persistence import (
    get_last_folder,
    get_main_window_geometry,
    set_last_folder,
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

        # Root for the folder browser. On Windows: drive root (C:\) so users can
        # navigate to C:\Projects, C:\Users, etc. On macOS/Linux: home directory.
        if sys.platform == "win32":
            self._folder_root_path = Path(Path.home().anchor)  # e.g. C:\
        else:
            self._folder_root_path = Path.home()
        self._folder_root_item: QStandardItem | None = None
        self._folder_model = self._build_folder_model()

        # Thumbnail service for the center pane; decoding runs on background threads.
        self._thumbnail_service = ThumbnailService(parent=self)
        # Center pane: thumbnail grid component (created in _create_right_pane).
        self._thumbnail_grid: ThumbnailGridWidget | None = None

        # Preview pane widgets (created in _create_preview_pane).
        self._preview_image_label: QLabel | None = None
        self._preview_image_path: Path | None = None  # current image path, for resize re-scale
        # Folder tree view reference so we can expand/select by path on restore.
        self._folder_tree_view: QTreeView | None = None
        # Go-up button (Windows only) for navigating to parent folder.
        self._btn_go_up: QPushButton | None = None

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

        # Restore last main window size/position if stored.
        geo = get_main_window_geometry()
        if geo:
            ba = QByteArray.fromBase64(geo.encode("ascii"))
            if not ba.isEmpty():
                self.restoreGeometry(ba)

        # Restore last visited folder from persistence, or select home.
        self._restore_last_folder()

    # --- Folder tree pane ------------------------------------------------

    def _create_folder_pane(self) -> QWidget:
        """
        Create the left pane: a labelled "Folders" header and a tree view.

        On Windows, a "↑" (Go up) button is shown at the top to navigate to
        the parent folder. The tree is backed by a QStandardItemModel that
        mirrors the real filesystem, rooted at drive root (Windows) or home
        (macOS/Linux). Child directories are populated lazily when expanded.
        """
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Windows only: "Go up" button to navigate to parent folder.
        if sys.platform == "win32":
            btn_go_up = QPushButton("↑", container)
            btn_go_up.setObjectName("btnGoUp")
            btn_go_up.setToolTip("Go up one level")
            btn_go_up.setMaximumWidth(32)
            btn_go_up.clicked.connect(self._on_go_up_clicked)
            self._btn_go_up = btn_go_up
            layout.addWidget(btn_go_up)

        header = QLabel("Folders", container)
        header.setObjectName("folderHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        tree_view = QTreeView(container)
        tree_view.setObjectName("folderTree")
        tree_view.setHeaderHidden(True)
        tree_view.setUniformRowHeights(True)
        self._folder_tree_view = tree_view

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

    def _get_selected_folder_path(self) -> Path | None:
        """Return the path of the currently selected folder, or None."""
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

    def _on_go_up_clicked(self) -> None:
        """
        Navigate to the parent of the currently selected folder.

        Windows only. Disabled when at drive root (parent equals self).
        """
        current = self._get_selected_folder_path()
        if current is None or not current.is_dir():
            return
        parent = current.resolve().parent
        # At drive root, parent equals current (e.g. C:\ parent is C:\).
        if parent == current or not parent.is_dir():
            return
        set_last_folder(str(parent))
        self._expand_and_select_path(parent)
        self._update_go_up_button_state()

    def _update_go_up_button_state(self) -> None:
        """Enable or disable the Go up button based on current selection."""
        if self._btn_go_up is None:
            return
        current = self._get_selected_folder_path()
        if current is None or not current.is_dir():
            self._btn_go_up.setEnabled(False)
            return
        parent = current.resolve().parent
        # Disable when at drive root (parent equals current).
        self._btn_go_up.setEnabled(parent != current and parent.is_dir())

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

    def _restore_last_folder(self) -> None:
        """
        Restore the last visited folder from persistence and select it,
        so the thumbnail grid loads that folder. Only use the stored path if it
        exists on this machine and is under the tree root (drive root on Windows,
        home on macOS/Linux). Paths from another OS or user are ignored.
        """
        last = get_last_folder()
        root = self._folder_root_path.resolve()
        use_last = False
        if last:
            try:
                path = Path(last).resolve()
                if path.is_dir():
                    path.relative_to(root)  # raises ValueError if not under root
                    use_last = True
                    self._expand_and_select_path(path)
            except (ValueError, OSError):
                pass
        if not use_last:
            self._expand_and_select_path(self._folder_root_path)
        self._update_go_up_button_state()

    def _expand_and_select_path(self, path: Path) -> None:
        """
        Expand the folder tree along the given path and select the final node.

        Used on startup to open the last folder, or to fall back to root.
        The tree is lazy so we expand each segment and find the matching child.
        """
        if self._folder_tree_view is None or self._folder_root_item is None:
            return

        path = path.resolve()
        root = self._folder_root_path.resolve()

        if path == root:
            root_index = self._folder_model.indexFromItem(self._folder_root_item)
            self._folder_tree_view.expand(root_index)
            self._folder_tree_view.setCurrentIndex(root_index)
            return

        try:
            relative = path.relative_to(root)
        except ValueError:
            # Path not under root (e.g. different drive on Windows); select root.
            root_index = self._folder_model.indexFromItem(self._folder_root_item)
            self._folder_tree_view.expand(root_index)
            self._folder_tree_view.setCurrentIndex(root_index)
            return

        parts = relative.parts
        current_item = self._folder_root_item
        current_path = root

        for part in parts:
            current_path = current_path / part
            # Ensure children are loaded so we can find the next segment.
            self._ensure_folder_children_loaded(current_item)
            index = self._folder_model.indexFromItem(current_item)
            self._folder_tree_view.expand(index)

            found = None
            for row in range(current_item.rowCount()):
                child = current_item.child(row)
                if child.data(Qt.ItemDataRole.UserRole) == str(current_path):
                    found = child
                    break
            if found is None:
                break
            current_item = found

        target_index = self._folder_model.indexFromItem(current_item)
        self._folder_tree_view.setCurrentIndex(target_index)

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

        Currently shows a scaled preview of the selected image; EXIF and
        other metadata will be added underneath in a later iteration.
        """
        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Preview / Metadata", frame)
        header.setObjectName("previewHeader")

        image_label = QLabel(frame)
        image_label.setObjectName("previewImage")
        image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        image_label.setMinimumHeight(200)
        image_label.setText("No image selected.")
        image_label.installEventFilter(self)  # re-scale image when pane is resized (e.g. splitter)

        self._preview_image_label = image_label

        layout.addWidget(header)
        layout.addWidget(image_label)

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
        """
        image_paths = [Path(p) for p in paths]
        viewer = ImageViewerWindow(image_paths, start_index=index, parent=self)
        viewer.show()

    def _update_preview(self, image_path: Path | None) -> None:
        """Load the given image path into the preview label, scaled to fit available space."""
        if self._preview_image_label is None:
            return

        if image_path is None or not image_path.is_file():
            self._preview_image_path = None
            self._preview_image_label.setText(
                "No image selected." if image_path is None else "Selected item is not a file."
            )
            self._preview_image_label.setPixmap(QPixmap())
            return

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self._preview_image_path = None
            self._preview_image_label.setText("Cannot load image.")
            self._preview_image_label.setPixmap(QPixmap())
            return

        self._preview_image_path = image_path

        # Scale to fit the label while preserving aspect ratio (uses current widget size).
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

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Persist main window geometry when the window is closed."""
        geo = self.saveGeometry()
        if not geo.isEmpty():
            set_main_window_geometry(geo.toBase64().data().decode("ascii"))
        super().closeEvent(event)
