"""
Thumbnail grid widget (component) for V-See.

Displays a grid of image thumbnails for the currently selected folder.
Uses a ThumbnailService for asynchronous thumbnail generation; each item
shows a framed thumbnail and filename. Designed to be embedded in the
Manage-mode center pane.

Author: Viorel LUPU
Date: 2025-02-10
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QListView,
    QVBoxLayout,
    QWidget,
)

from photo_viewer.services.thumbnails import ThumbnailService


# Supported image extensions for the file list (lowercase).
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"})


class ThumbnailGridWidget(QFrame):
    """
    Widget that displays a grid of image thumbnails for a given folder.

    Uses an injected ThumbnailService to load thumbnails asynchronously.
    Call load_folder(path) whenever the user selects a different folder;
    the grid clears and repopulates with image files from that directory,
    and thumbnails fill in as they are generated.
    """

    # Emitted when the current selection changes to a specific file path.
    selection_changed = pyqtSignal(str)
    # Emitted when the user activates (double-clicks) a thumbnail.
    # Carries the full ordered list of paths in the current folder and the
    # index of the activated item so a viewer window can navigate.
    activated = pyqtSignal(list, int)

    def __init__(
        self,
        thumbnail_service: ThumbnailService,
        parent: QWidget | None = None,
    ) -> None:
        """
        Create the thumbnail grid component.

        Parameters
        ----------
        thumbnail_service
            Service used to request and receive thumbnails; must outlive
            this widget. thumbnail_ready signal will be connected.
        parent
            Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("thumbnailGrid")

        self._thumbnail_service = thumbnail_service
        self._model = QStandardItemModel(self)
        self._file_items_by_path: dict[str, QStandardItem] = {}
        self._current_paths: list[str] = []
        self._list_view: QListView | None = None

        self._build_ui()
        self._thumbnail_service.thumbnail_ready.connect(self._on_thumbnail_ready)

    def _build_ui(self) -> None:
        """Build the layout: header label and icon-mode list view."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Files", self)
        header.setObjectName("fileHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        list_view = QListView(self)
        list_view.setObjectName("fileList")

        # Configure as a grid of thumbnails. We rely on Qt's built-in
        # size calculations based on iconSize and text instead of a
        # fixed gridSize to avoid the \"first load\" truncation issue.
        list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        list_view.setViewMode(QListView.ViewMode.IconMode)
        list_view.setWrapping(True)
        list_view.setMovement(QListView.Movement.Static)
        list_view.setResizeMode(QListView.ResizeMode.Adjust)

        list_view.setIconSize(QSize(128, 128))
        list_view.setSpacing(8)
        list_view.setModel(self._model)

        self._list_view = list_view

        # Propagate selection changes to listeners as file paths.
        selection_model = list_view.selectionModel()
        if selection_model is not None:
            selection_model.currentChanged.connect(self._on_current_changed)
            list_view.doubleClicked.connect(self._on_double_clicked)

        layout.addWidget(header)
        layout.addWidget(list_view)

    def load_folder(self, folder_path: Path) -> None:
        """
        Replace the grid contents with image files from the given folder.

        Clears the current list, enumerates image files in the directory
        (by supported extension), adds one item per file, and requests
        a thumbnail for each from the ThumbnailService. Thumbnails
        appear as they complete.
        """
        self._model.removeRows(0, self._model.rowCount())
        self._file_items_by_path.clear()
        self._current_paths.clear()

        try:
            if not folder_path.is_dir():
                return
        except OSError:
            return

        try:
            entries = sorted(
                [p for p in folder_path.iterdir() if p.is_file()],
                key=lambda p: p.name.lower(),
            )
        except (PermissionError, OSError):
            return

        for path in entries:
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            path_str = str(path)
            item = QStandardItem(path.name)
            item.setData(path_str, Qt.ItemDataRole.UserRole)
            self._model.appendRow(item)
            self._file_items_by_path[path_str] = item
            self._thumbnail_service.request_thumbnail(path)

            self._current_paths.append(path_str)

        # Auto-select the first item (if any) so that callers can show a
        # preview immediately when a folder is loaded.
        if self._list_view is not None and self._model.rowCount() > 0:
            index0 = self._model.index(0, 0)
            self._list_view.setCurrentIndex(index0)

    def _on_thumbnail_ready(self, path_str: str, icon: QIcon) -> None:
        """
        Slot called when the ThumbnailService has produced a thumbnail.

        If the path still belongs to an item in the current grid (user
        has not switched folder), the item's icon is updated.
        """
        item = self._file_items_by_path.get(path_str)
        if item is None:
            return

        item.setIcon(icon)

        # Force the view to recompute item geometry now that real icons
        # are available. Without this, the first load can display icons
        # in rows that were initially laid out assuming text-only items,
        # causing visible overlap until the folder is reloaded.
        if self._list_view is not None:
            self._list_view.doItemsLayout()

    def _on_current_changed(self, current, _previous) -> None:
        """Emit selection_changed with the newly selected file path."""
        item = self._model.itemFromIndex(current)
        if item is None:
            return
        path_str = item.data(Qt.ItemDataRole.UserRole)
        if not path_str:
            return
        self.selection_changed.emit(str(path_str))

    def _on_double_clicked(self, index) -> None:
        """
        Emit activated with the full set of paths and the clicked index.

        The receiver (e.g. MainWindow) can then create a viewer window
        that knows how to navigate within the folder.
        """
        if not self._current_paths:
            return
        row = index.row()
        if row < 0 or row >= len(self._current_paths):
            return
        self.activated.emit(list(self._current_paths), row)
