"""
Menus for GGPKViewer

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/ui/ggpk_viewer/menu.py                                     |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Contains the Menus and related actions for the GGPKViewer

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python

# 3rd Party
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

# self
from PyPoE.poe.file.ggpk import FileRecord
from PyPoE.ui.shared.file.ggpk import GGPKOpenAction
from PyPoE.ui.shared.file.model import GGPKModel

# =============================================================================
# Globals
# =============================================================================

__all__ = ["FileMenu", "MiscMenu", "ViewMenu"]

# =============================================================================
# Classes
# =============================================================================


class CustomOpenAction(GGPKOpenAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thread = None

    def _get_version(self):
        return self._main_window().s_general.version

    def _main_window(self):
        return self.parent().parent()

    def _open_ggpk(self):
        self._thread = super()._open_ggpk()

        # User cancelled
        if self._thread is None:
            return

        # Destroy the old object or we're massively memory-leaking
        # TODO for some reason 2 objects are still kept in memory
        p = self._main_window()
        p._reset_file_view(reset_hash=True)
        p.ggpk_view.model().deleteLater()
        p.ggpk_view.setModel(GGPKModel())

        self._thread.finished.connect(self._update_ggpk_model)
        self._thread.start()

    def _ggpk_sort(self, node, depth, **kwargs):
        def sorter(obj):
            return (
                    isinstance(getattr(obj, "record", None), FileRecord),
                    getattr(obj, "name", str(obj)),
                )
        # Check if children is a dict or list and sort accordingly
        if isinstance(node.children, dict):
            # Keep as dict after sorting
            sorted_items = sorted(node.children.items(), key=lambda item: sorter(item[1]))
            node.children = dict(sorted_items)
        elif isinstance(node.children, list):
            node.children = sorted(node.children, key=sorter)

    def _update_ggpk_model(self):
        p = self._main_window()

        p._write_log(self.tr("Sorting GGPK directory..."))
        self._thread.ggpk_file.directory.walk(self._ggpk_sort)  # type: ignore[union-attr]

        p._write_log(self.tr("Viewing GGPK contents..."))

        p.ggpk_view.setModel(GGPKModel(self._thread.ggpk_file.directory))  # type: ignore[union-attr]
        p.ggpk_view.show()

        p._write_log(self.tr("Done."))


class FileMenu(QMenu):
    """
    Create file menu and handle related actions
    """

    def __init__(self, *args, **kwargs):
        QMenu.__init__(self, *args, **kwargs)

        self.action_open = CustomOpenAction(self)
        self.addAction(self.action_open)

        self.setTitle(self.tr("File"))
        self.parent().menuBar().addMenu(self)


class ViewMenu(QMenu):
    """
    Create view menu and handle related actions
    """

    def __init__(self, *args, **kwargs):
        QMenu.__init__(self, *args, **kwargs)

        self.action_toggle_toolbar = QAction(
            self, text=self.tr("File Viewer Toolbar"), checkable=True
        )
        self.action_toggle_toolbar.setStatusTip(self.tr("Toggle file viewer toolbar"))
        self.action_toggle_toolbar.triggered.connect(self._toggle_view_toolbar)
        self.action_toggle_toolbar.setChecked(True)
        self.addAction(self.action_toggle_toolbar)

        self.setTitle(self.tr("View"))
        self.parent().menuBar().addMenu(self)

    def _toggle_view_toolbar(self):
        tb = self.parent().context_toolbar
        tb.setVisible(not tb.isVisible())


class MiscMenu(QMenu):
    """
    Create misc menu and handle related actions
    """

    def __init__(self, *args, **kwargs):
        QMenu.__init__(self, *args, **kwargs)

        self.action_reload_specifications = QAction(
            self, text=self.tr("Reload .dat specifications")
        )
        self.action_reload_specifications.setStatusTip(
            self.tr("Reloads the default .dat specifications.")
        )
        self.action_reload_specifications.triggered.connect(self._reload_specifications)
        self.addAction(self.action_reload_specifications)

        self.setTitle(self.tr("Misc"))
        self.parent().menuBar().addMenu(self)

    def _reload_specifications(self):
        p = self.parent()

        v = p.s_general.version

        p._write_log(self.tr(f"Reloading default specification... ({v})"))
        # MVVM: Use ViewModel to reload specification
        p.viewmodel.reload_specification(v)
        # Update reference for backward compatibility
        p._specification = p.viewmodel.get_specification()
        p._write_log("Done.")
