"""
Toolbars for GGPKViewer

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/ui/ggpk_viewer/toolbar.py                                  |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Contains various toolbars for use in the GGPKViewer application.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import os
from typing import Any

# 3rd Party
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QFileDialog, QToolBar

# self
from PyPoE.poe.file.ggpk.records import DirectoryRecord, FileRecord
from PyPoE.ui.shared.dialog import RegExSearchDialog

# =============================================================================
# Globals
# =============================================================================

__all__ = ["ContextToolbar"]

# =============================================================================
# Classes
# =============================================================================


class ContextToolbar(QToolBar):
    """
    Context toolbar for GGPK Viewer.

    Provides actions for file extraction, search, and path copying.
    Actions are enabled/disabled based on selection state.

    Attributes:
        action_extract: Action for extracting selected files/folders
        action_search: Action for searching in selected folder
        action_copy_path: Action for copying file path
        regex_search: Dialog for regex search functionality
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize context toolbar.

        Args:
            *args: Positional arguments passed to QToolBar
            **kwargs: Keyword arguments passed to QToolBar
        """
        QToolBar.__init__(self, *args, **kwargs)

        # self.setAllowedAreas(Qt.LeftToolBarArea | Qt.RightToolBarArea)
        self.action_extract = QAction(self, text=self.tr("Extract"))
        self.action_extract.setStatusTip(self.tr("Extract currently selected file or folder"))
        self.action_extract.triggered.connect(self._toolbar_extract)
        self.action_extract.setDisabled(True)
        self.addAction(self.action_extract)

        self.action_search = QAction(self, text=self.tr("Search"))
        self.action_search.setStatusTip(self.tr("Search currently selected folder"))
        self.action_search.triggered.connect(self._toolbar_search)
        self.action_search.setDisabled(True)
        self.addAction(self.action_search)

        self.action_copy_path = QAction(self, text=self.tr("Copy path"))
        self.action_copy_path.setStatusTip(
            self.tr(
                "Copy the file path relative to content.ggpk root for the "
                "currently selected file or folder"
            )
        )
        self.action_copy_path.triggered.connect(self._toolbar_copy_path)
        self.action_copy_path.setDisabled(True)
        # self.addAction(self.action_copy_path)

        self.setWindowTitle(self.tr("File Viewer Toolbar"))
        self.setOrientation(Qt.Horizontal)
        self.parent().addToolBar(Qt.TopToolBarArea, self)
        self.visibilityChanged.connect(self._adjust_view)

        self.regex_search = RegExSearchDialog(self)

    def _adjust_view(self, visibility: bool) -> None:
        """
        Adjust view when toolbar visibility changes.

        Args:
            visibility: Whether toolbar is visible
        """
        self.parent().menu_view.action_toggle_toolbar.setChecked(visibility)

    def _get_node(self) -> Any | None:
        """
        Get currently selected node from GGPK view.

        Returns:
            DirectoryNode or FileRecord node, or None if nothing selected
        """
        # returns list of columns
        indexes = self.parent().ggpk_view.selectedIndexes()
        # Shouldn't happen... TODO log
        if not indexes:
            return None
        return indexes[0].internalPointer()

    def _toolbar_extract_dds(self, path: str, node: Any) -> None:
        """
        Extract and decompress DDS file.

        Args:
            path: Path to DDS file
            node: DirectoryNode or FileRecord node
        """
        from PyPoE.shared.file_utils import read_file, write_file

        self.parent()._write_log(path)
        data = read_file(path)
        if data[:4] == b"DDS ":
            return

        try:
            # Extract DDS using FileSystem method
            if node.record._container:
                from PyPoE.cli.core import get_content_path
                from PyPoE.poe.file.file_system import FileSystem
                fs = FileSystem(root_path=get_content_path())
                data = fs.extract_dds(data)
        except FileNotFoundError as e:
            self.parent()._write_log(f"Broken symbolic link.\n{e}")

        write_file(path, data)

    def _toolbar_extract(self) -> None:
        """
        Extract selected file or folder to directory.

        Prompts user for target directory and extracts files.
        Optionally decompresses DDS files if enabled in settings.
        """
        node = self._get_node()
        if node is None:
            return

        p = self.parent()
        target_dir = QFileDialog.getExistingDirectory(
            self, self.tr("Select directory to extract to")
        )
        if not target_dir:
            return
        p._write_log(self.tr(f'Extracting file(s) to "{target_dir}"...'))
        node.extract_to(target_dir)

        # TODO Fix double writing
        if self.parent().s_general.uncompress_dds:
            if isinstance(node.record, DirectoryRecord):
                p._write_log(self.tr("Uncompressing DDS Files..."))
                for root, _dirs, files in os.walk(os.path.join(target_dir, node.name)):
                    for file_name in files:
                        if file_name.endswith(".dds"):
                            self._toolbar_extract_dds(os.path.join(root, file_name), node)
            elif isinstance(node.record, FileRecord) and node.name.endswith(".dds"):
                p._write_log(self.tr("Uncompressing DDS File..."))
                self._toolbar_extract_dds(os.path.join(target_dir, node.name), node)

        p._write_log(self.tr("Done."))

    def _toolbar_search(self) -> None:
        """
        Search for files in selected directory using regex.

        Opens regex search dialog and searches for matching files.
        Results are displayed in the log area.
        """
        node = self._get_node()
        if node is None:
            return

        if not isinstance(node.record, DirectoryRecord):
            return

        ok = self.regex_search.exec_()

        # User canceled or (custom) regex error
        if not ok:
            return

        sdir = self.regex_search.option_search_directories.isChecked()

        self.parent()._write_log(self.tr("Started searching..."))
        result = node.search(self.regex_search.regex_compiled, search_directories=sdir)
        if result:
            out = []
            stop = None if self.regex_search.option_full_path.isChecked() else node
            for item in result:
                p = item.get_parent(stop_at=stop, make_list=True)
                p = [n.name for n in p]
                out.append("/".join(p))
            out.sort()
            outtext = "\n".join(out)
        else:
            outtext = self.tr("No items found.")

        self.parent()._write_log(self.tr("Finished searching."))

        self.parent().file_textbox.setText(outtext)

    def _toolbar_copy_path(self) -> None:
        """
        Copy file path to clipboard.

        Copies the path of the selected file or folder relative to
        content.ggpk root to the system clipboard.
        """
        node = self._get_node()
        if node is None:
            return

        QApplication.clipboard().setText(node.get_path())

    def enable_file_actions(self, node: Any) -> None:
        """
        Enable or disable file actions based on node type.

        Args:
            node: DirectoryNode or FileRecord node
        """
        if isinstance(node.record, DirectoryRecord):
            self.action_search.setEnabled(True)
        else:
            self.action_search.setEnabled(False)
        self.action_extract.setEnabled(True)
        self.action_copy_path.setEnabled(True)
