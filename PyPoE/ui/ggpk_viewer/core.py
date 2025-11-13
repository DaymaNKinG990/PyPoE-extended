"""
GGPK User Interface Classes

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/ui/ggpk_viewer/core.py                                     |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Creates a qt User Interface to browse GGPK files.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

from __future__ import annotations

from typing import Any

# Default Imports
from collections import OrderedDict
from traceback import format_exc

# Library Imports
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
)

# Package Imports
from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.ggpk.records import DirectoryRecord
from PyPoE.ui.ggpk_viewer.menu import FileMenu, MiscMenu, ViewMenu
from PyPoE.ui.ggpk_viewer.toolbar import ContextToolbar
from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel
from PyPoE.ui.shared import SharedMainWindow
from PyPoE.ui.shared.file.manager import FileDataManager
from PyPoE.ui.shared.file.model import GGPKModel
from PyPoE.ui.shared.settings import BoolSetting, ComboBoxSetting, SettingFrame

# =============================================================================
# Classes
# =============================================================================


class GGPKViewerMainWindow(SharedMainWindow):
    """
    Main window for GGPK Viewer application.

    Implements MVVM pattern with ViewModel for business logic separation.
    Handles UI initialization, signal connections, and user interactions.

    Attributes:
        viewmodel: GGPKViewModel instance for business logic
        _file_data_manager: FileDataManager for file handling
        menu_file: File menu
        menu_view: View menu
        menu_misc: Miscellaneous menu
        context_toolbar: Context toolbar for actions
    """

    NAME = "GGPK Viewer"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize GGPK Viewer main window.

        Args:
            *args: Positional arguments passed to SharedMainWindow
            **kwargs: Keyword arguments passed to SharedMainWindow
        """
        super().__init__(*args, app_name=self.NAME, **kwargs)

        self.s_general = GeneralSettingsFrame(parent=self)

        # MVVM: Initialize ViewModel for business logic separation
        self.viewmodel = GGPKViewModel(version=self.s_general.version, parent=self)

        # Connect ViewModel signals to View slots
        self.viewmodel.ggpk_loading_started.connect(self._on_ggpk_loading_started)
        self.viewmodel.ggpk_loading_progress.connect(self._on_ggpk_loading_progress)
        self.viewmodel.ggpk_loaded.connect(self._on_ggpk_loaded)
        self.viewmodel.ggpk_load_failed.connect(self._on_ggpk_load_failed)
        self.viewmodel.node_selected.connect(self._on_node_selected)

        # Keep specification reference for FileDataManager (backward compatibility)
        self._specification = self.viewmodel.get_specification()

        self._file_data_manager = FileDataManager(self)

        # Menu Bar
        self.menu_file = FileMenu(parent=self)
        self.menu_view = ViewMenu(parent=self)
        self.menu_misc = MiscMenu(parent=self)
        self.menu_misc.addAction(self.settings_window.action_open)

        # Tool Bars
        self.context_toolbar = ContextToolbar(parent=self)

        # Central Widget
        self.master = QSplitter(parent=self)
        self.master.setOrientation(Qt.Vertical)
        self.work_area_splitter = QSplitter()
        self.master.addWidget(self.work_area_splitter)
        self.master.addWidget(self.notification)

        self.ggpk_view = QTreeView()
        self.ggpk_view.setModel(GGPKModel())
        self.ggpk_view.setColumnWidth(0, 200)
        self.ggpk_view.setColumnWidth(1, 75)
        self.ggpk_view.setColumnWidth(2, 80)
        # self.ggpk_view.setColumnWidth(3, 80)
        self.ggpk_view.setMinimumSize(370, 370)
        self.ggpk_view.clicked.connect(self._view_record)
        self.ggpk_view.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.ggpk_view.addAction(self.context_toolbar.action_extract)
        self.ggpk_view.addAction(self.context_toolbar.action_search)
        self.ggpk_view.addAction(self.context_toolbar.action_copy_path)
        self.work_area_splitter.addWidget(self.ggpk_view)

        self.work_area_frame = QFrame()
        self.work_area_frame.setContentsMargins(0, 0, 0, 0)
        self.file_layout = QVBoxLayout()
        self.file_layout.setContentsMargins(0, 0, 0, 0)
        self.work_area_frame.setLayout(self.file_layout)
        self.work_area_splitter.addWidget(self.work_area_frame)

        # Create Info bar
        self.file_infobar_layout = QHBoxLayout()
        self.file_infobar_layout.setAlignment(Qt.AlignLeft)
        self.file_infobar = QFrame()
        self.file_infobar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.file_infobar.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.file_infobar.setLayout(self.file_infobar_layout)

        self.file_infobar_layout.addWidget(QLabel(self.tr("Name Hash:")))
        self.file_infobar_name_hash = QLineEdit(readOnly=True)
        # self.file_infobar_name_hash.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        self.file_infobar_name_hash.setFixedWidth(70)
        self.file_infobar_layout.addWidget(self.file_infobar_name_hash)

        self.file_infobar_layout.addWidget(QLabel(self.tr("File Hash:")))
        self.file_infobar_file_hash = QLineEdit(readOnly=True)
        self.file_infobar_file_hash.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        self.file_infobar_file_hash.setMinimumWidth(405)
        self.file_infobar_layout.addWidget(self.file_infobar_file_hash)

        # Add to the info bar to general file layout
        self.file_layout.addWidget(self.file_infobar)

        # Create Frame
        # self.file_frame_scroll = QScrollArea()
        # self.file_frame_scroll.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        # self.file_layout.addWidget(self.file_frame_scroll)

        self.file_frame = QFrame()
        self.file_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.file_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.file_layout.addWidget(self.file_frame)

        self.file_frame_layout = QVBoxLayout()
        self.file_frame_layout.setAlignment(Qt.AlignTop)
        self.file_frame.setLayout(self.file_frame_layout)

        # self.file_frame_scroll.setWidget(self.file_frame)
        # self.file_frame_scroll.setLayout(self.file_frame_layout)
        # self.file_frame_scroll.show()

        #
        self.file_textbox = QTextEdit(self)
        self.file_textbox.setText(self.tr("No file selected."))
        self.file_textbox.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.file_frame_layout.addWidget(self.file_textbox)

        # Setup the main window
        self.setCentralWidget(self.master)
        self.statusBar()
        self.setWindowTitle(self.tr(self.NAME))

    def _reset_file_view(self, reset_hash=True):
        if reset_hash:
            self.file_infobar_file_hash.setText("")
            self.file_infobar_name_hash.setText("")
            self._last_node = None
        if hasattr(self, "file_view"):
            self.file_frame_layout.removeWidget(self.file_view)  # type: ignore[has-type]
            self.file_view.deleteLater()  # type: ignore[has-type]
            del self.file_view  # type: ignore[has-type]

    def _view_record(self, index=QModelIndex()):
        node = index.internalPointer()
        self.context_toolbar.enable_file_actions(node)

        # Do nothing if the user spams clicks the same...
        if node is self._last_node:
            return

        self._last_node = node

        self.file_infobar_file_hash.setText(hex(node.record.hash)[2:].upper())
        self.file_infobar_name_hash.setText(str(node.hash))

        if isinstance(node.record, DirectoryRecord):
            self.file_textbox.setText(self.tr("No file selected."))
            self.file_textbox.setVisible(True)
            if hasattr(self, "file_view"):
                self.file_view.setVisible(False)  # type: ignore[has-type]
            return

        # Avoid extracting data until we actually need
        obj = self._file_data_manager.get_handler(node.record.name)
        if obj is None:
            self.file_textbox.setText(self.tr("File view not supported for this file type."))
            self.file_textbox.setVisible(True)
            self._reset_file_view(reset_hash=False)
            return

        try:
            qwidget = obj.get_widget(node.record.extract(), file_name=node.record.name, parent=self)
        except Exception as e:
            msg = self.tr(f"{e.__class__.__name__} occurred when trying to open {node.record.name}")
            fullmsg = msg + ": \n\n" + format_exc()

            self.file_textbox.setText(fullmsg)
            self._write_log(fullmsg, msg)
            return

        self.file_textbox.setVisible(False)
        # Remove the old widget or we're heavily memory leaking
        self._reset_file_view(reset_hash=False)

        self.file_frame_layout.addWidget(qwidget)
        self.file_view = qwidget

        # Actually is a file record

    # =========================================================================
    # MVVM: ViewModel signal slots
    # =========================================================================

    def _on_ggpk_loading_started(self, file_path: str):
        """Handle GGPK loading start."""
        self._write_log(self.tr(f"Loading GGPK file: {file_path}..."))
        # Disable UI interactions during loading
        self.ggpk_view.setEnabled(False)

    def _on_ggpk_loading_progress(self, progress: int, message: str):
        """Handle GGPK loading progress updates."""
        self._write_log(self.tr(f"Progress: {progress}% - {message}"))

    def _on_ggpk_loaded(self):
        """Handle successful GGPK loading."""
        self._write_log(self.tr("GGPK file loaded successfully"))
        # Re-enable UI
        self.ggpk_view.setEnabled(True)
        # Update model with new GGPK
        model = self.ggpk_view.model()
        if isinstance(model, GGPKModel):
            model.set_ggpk(self.viewmodel.ggpk_file)

    def _on_ggpk_load_failed(self, error_message: str):
        """Handle GGPK loading failure."""
        self._write_log(error_message)
        # Re-enable UI
        self.ggpk_view.setEnabled(True)
        QMessageBox.warning(self, self.tr("Error"), error_message)

    def _on_node_selected(self, node):
        """Handle node selection from ViewModel."""
        # Update info bar
        info = self.viewmodel.get_node_info(node)
        self.file_infobar_name_hash.setText(info.get("name_hash", ""))
        self.file_infobar_file_hash.setText(info.get("hash", ""))


class GeneralSettingsFrame(SettingFrame):
    KEY = "general"  # type: ignore[assignment]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parent().settings_window.add_config_section(
            tr=self.tr("General"),
            qframe=self,
            order=-100,
        )

        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout)

        self._add_setting(SettingDDS(parent=self, settings=self.parent().settings, row=1))

        self._add_setting(
            SettingVersion(
                parent=self,
                settings=self.parent().settings,
                row=2,
            )
        )


class SettingDDS(BoolSetting):
    KEY = "uncompress_dds"  # type: ignore[assignment]
    DEFAULT = False  # type: ignore[assignment]

    def __init__(self, parent, settings, row, *args, **kwargs):
        super().__init__(parent, settings, *args, **kwargs)

        self.value = self.get()

        parent.main_layout.addWidget(
            QLabel(parent.tr("Uncompress DDS files after exporting them from the GGPK")), row, 1
        )
        parent.main_layout.addWidget(self.checkbox, row, 2)


class SettingVersion(ComboBoxSetting):
    KEY = "version"  # type: ignore[assignment]
    DEFAULT = VERSION.DEFAULT  # type: ignore[assignment]

    def __init__(self, parent, settings, row, *args, **kwargs):
        super().__init__(parent, settings, *args, **kwargs)
        self._set_data(
            OrderedDict(
                (
                    ("Stable", VERSION.STABLE),
                    ("Beta", VERSION.BETA),
                    ("Alpha", VERSION.ALPHA),
                )
            )
        )

        parent.layout.addWidget(QLabel(parent.tr("Version of the game")), row, 1)
        parent.layout.addWidget(self.combobox, row, 2)

    def _get_cast(self, value):
        # Handle both string names ('STABLE') and integer values (1)
        if isinstance(value, int):
            return VERSION(value)
        elif isinstance(value, str):
            # Try to get by name first
            try:
                return getattr(VERSION, value)
            except AttributeError:
                # If that fails, try to convert to int
                return VERSION(int(value))
        return VERSION(value)

    def _set_cast(self, value):
        # Save as the name of the enum member
        if isinstance(value, VERSION):
            return value.name
        return str(value)


# =============================================================================
# Functions
# =============================================================================
