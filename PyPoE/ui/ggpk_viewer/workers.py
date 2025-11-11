"""
GGPK Viewer Async Workers

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/ui/ggpk_viewer/workers.py                                 |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Asynchronous workers for long-running GGPK operations using QThreadPool.
Prevents UI blocking during file loading and extraction.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import traceback
from pathlib import Path
from typing import Any

# Library
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

# Package
from PyPoE.poe.file import ggpk
from PyPoE.shared.logging import get_logger

# =============================================================================
# Globals
# =============================================================================

logger = get_logger(__name__)

# =============================================================================
# Classes
# =============================================================================


class WorkerSignals(QObject):
    """
    Signals for worker threads.

    Signals cannot be defined directly in QRunnable, so we use a separate QObject.
    """

    # GGPK Loading
    loading_started = Signal(str)  # file_path
    loading_progress = Signal(int, str)  # progress (0-100), message
    loading_finished = Signal(object)  # ggpk_file
    loading_failed = Signal(str, str)  # error_message, traceback

    # File Extraction
    extraction_started = Signal(str)  # file_name
    extraction_finished = Signal(bytes)  # data
    extraction_failed = Signal(str, str)  # error_message, traceback


class GGPKLoadWorker(QRunnable):
    """
    Worker for loading GGPK files asynchronously.

    Uses QThreadPool to avoid blocking the UI during large file loads.

    Example:
        >>> worker = GGPKLoadWorker(Path("content.ggpk"))
        >>> worker.signals.loading_finished.connect(on_loaded)
        >>> QThreadPool.globalInstance().start(worker)
    """

    def __init__(self, file_path: Path):
        """
        Initialize worker.

        Args:
            file_path: Path to GGPK file
        """
        super().__init__()
        self.file_path = file_path
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

        logger.debug("ggpk_load_worker_created", path=str(file_path))

    @Slot()
    def run(self):
        """Execute GGPK loading in background thread."""
        try:
            logger.info("ggpk_load_started", path=str(self.file_path))
            self.signals.loading_started.emit(str(self.file_path))

            # Phase 1: Read GGPK records (70%)
            self.signals.loading_progress.emit(10, "Reading GGPK records...")
            ggpk_file = ggpk.GGPKFile()

            # Hook progress updates if needed
            ggpk_file.read(self.file_path)
            self.signals.loading_progress.emit(70, "Read complete")

            # Phase 2: Build directory structure (30%)
            self.signals.loading_progress.emit(75, "Building directory tree...")
            ggpk_file.directory_build()
            self.signals.loading_progress.emit(100, "Complete")

            logger.info("ggpk_load_finished", path=str(self.file_path))
            self.signals.loading_finished.emit(ggpk_file)

        except Exception as e:
            error_msg = f"Failed to load GGPK: {str(e)}"
            tb = traceback.format_exc()
            logger.error("ggpk_load_failed", error=str(e), path=str(self.file_path))
            self.signals.loading_failed.emit(error_msg, tb)


class FileExtractionWorker(QRunnable):
    """
    Worker for extracting files from GGPK asynchronously.

    Used for large file extractions that could block the UI.

    Example:
        >>> worker = FileExtractionWorker(node.record)
        >>> worker.signals.extraction_finished.connect(on_extracted)
        >>> QThreadPool.globalInstance().start(worker)
    """

    def __init__(self, file_record: Any):
        """
        Initialize worker.

        Args:
            file_record: GGPK FileRecord to extract
        """
        super().__init__()
        self.file_record = file_record
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

        logger.debug("extraction_worker_created", file=file_record.name)

    @Slot()
    def run(self):
        """Execute file extraction in background thread."""
        try:
            logger.info("extraction_started", file=self.file_record.name)
            self.signals.extraction_started.emit(self.file_record.name)

            # Extract file data
            data = self.file_record.extract()

            logger.info("extraction_finished", file=self.file_record.name, size=len(data))
            self.signals.extraction_finished.emit(data)

        except Exception as e:
            error_msg = f"Failed to extract file: {str(e)}"
            tb = traceback.format_exc()
            logger.error("extraction_failed", error=str(e), file=self.file_record.name)
            self.signals.extraction_failed.emit(error_msg, tb)


__all__ = [
    "WorkerSignals",
    "GGPKLoadWorker",
    "FileExtractionWorker",
]
