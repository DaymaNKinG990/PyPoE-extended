"""
GGPK Viewer ViewModel

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/ui/ggpk_viewer/viewmodel.py                               |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+

Description
===============================================================================

ViewModel layer for GGPK Viewer implementing MVVM pattern.
Separates business logic from UI, making code more testable and maintainable.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from pathlib import Path
from typing import Optional, List, Dict, Any
import re

# Library
from PySide6.QtCore import QObject, Signal, QThreadPool

# Package
from PyPoE.poe.constants import VERSION
from PyPoE.poe.file import ggpk
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.poe.file.specification.fields import Specification
from PyPoE.shared.logging import get_logger

# =============================================================================
# Globals
# =============================================================================

logger = get_logger(__name__)

# =============================================================================
# Classes
# =============================================================================


class GGPKViewModel(QObject):
    """
    ViewModel for GGPK Viewer.
    
    Handles all business logic and state management for the GGPK viewer,
    separated from UI concerns following MVVM pattern.
    
    Signals:
        ggpk_loaded: Emitted when GGPK file is successfully loaded
        ggpk_load_failed: Emitted when GGPK loading fails (error_message)
        node_selected: Emitted when a node is selected
        extraction_complete: Emitted when extraction finishes (success, path)
        specification_reloaded: Emitted when specification is reloaded
    
    Example:
        >>> vm = GGPKViewModel(version=VERSION.STABLE)
        >>> vm.load_ggpk_file(Path("content.ggpk"))
        >>> info = vm.get_node_info(node)
    """
    
    # Qt Signals for communication with View
    ggpk_loading_started = Signal(str)  # file_path
    ggpk_loading_progress = Signal(int, str)  # progress (0-100), message
    ggpk_loaded = Signal()
    ggpk_load_failed = Signal(str)  # error_message
    node_selected = Signal(object)  # node
    extraction_started = Signal(str)  # file_name
    extraction_complete = Signal(bool, str)  # success, path_or_error
    specification_reloaded = Signal()
    
    def __init__(self, version: VERSION = VERSION.STABLE, parent: Optional[QObject] = None):
        """
        Initialize ViewModel.
        
        Args:
            version: Game version for specifications
            parent: Parent QObject
        """
        super().__init__(parent)
        
        # State
        self.ggpk_file: Optional[ggpk.GGPKFile] = None
        self.current_node: Optional[Any] = None
        
        # Thread pool for async operations
        self.thread_pool: QThreadPool = QThreadPool.globalInstance()
        
        # Specification factory with dependency injection
        self.factory: FileParserFactory = FileParserFactory.default(version=version)
        self.specification: Specification = self.factory.get_specification()
        
        logger.info("ggpk_viewmodel_initialized", version=version.name)
    
    def load_ggpk_file(self, file_path: Path, async_mode: bool = True) -> None:
        """
        Load GGPK file asynchronously (non-blocking).
        
        Args:
            file_path: Path to .ggpk file
            async_mode: If True, load asynchronously (default). If False, load synchronously.
        
        Note:
            In async mode, this method returns immediately and emits signals:
            - ggpk_loading_started: When loading begins
            - ggpk_loading_progress: Progress updates (0-100)
            - ggpk_loaded: When loading completes successfully
            - ggpk_load_failed: If loading fails
        """
        if async_mode:
            # Use async worker to avoid blocking UI
            from PyPoE.ui.ggpk_viewer.workers import GGPKLoadWorker
            
            logger.info("starting_async_ggpk_load", path=str(file_path))
            
            worker = GGPKLoadWorker(file_path)
            
            # Connect worker signals to ViewModel signals
            worker.signals.loading_started.connect(self.ggpk_loading_started.emit)
            worker.signals.loading_progress.connect(self.ggpk_loading_progress.emit)
            worker.signals.loading_finished.connect(self._on_ggpk_loaded)
            worker.signals.loading_failed.connect(self._on_ggpk_load_failed)
            
            # Start worker in thread pool
            self.thread_pool.start(worker)
        else:
            # Synchronous loading (for backward compatibility/testing)
            try:
                logger.info("loading_ggpk_file_sync", path=str(file_path))
                self.ggpk_loading_started.emit(str(file_path))
                
                self.ggpk_file = ggpk.GGPKFile()
                self.ggpk_file.read(file_path)
                self.ggpk_loading_progress.emit(70, "Building directory...")
                self.ggpk_file.directory_build()
                self.ggpk_loading_progress.emit(100, "Complete")
                
                logger.info("ggpk_file_loaded", path=str(file_path))
                self.ggpk_loaded.emit()
                
            except Exception as e:
                error_msg = f"Failed to load GGPK file: {str(e)}"
                logger.error("ggpk_load_failed", error=str(e), path=str(file_path))
                self.ggpk_load_failed.emit(error_msg)
                self.ggpk_file = None
    
    def _on_ggpk_loaded(self, ggpk_file: ggpk.GGPKFile) -> None:
        """Handle successful GGPK loading from worker."""
        self.ggpk_file = ggpk_file
        logger.info("ggpk_file_loaded_async")
        self.ggpk_loaded.emit()
    
    def _on_ggpk_load_failed(self, error_msg: str, traceback: str) -> None:
        """Handle GGPK loading failure from worker."""
        logger.error("ggpk_load_failed_async", error=error_msg)
        self.ggpk_file = None
        self.ggpk_load_failed.emit(error_msg)
    
    def is_ggpk_loaded(self) -> bool:
        """
        Check if GGPK file is loaded.
        
        Returns:
            True if GGPK is loaded
        """
        return self.ggpk_file is not None
    
    def get_directory_tree(self) -> Optional[Any]:
        """
        Get root directory node.
        
        Returns:
            Root directory node or None if not loaded
        """
        if not self.is_ggpk_loaded():
            return None
        return self.ggpk_file.directory  # type: ignore[union-attr]
    
    def set_current_node(self, node: Any) -> None:
        """
        Set current selected node.
        
        Args:
            node: Selected node
        """
        self.current_node = node
        self.node_selected.emit(node)
        logger.debug("node_selected", node=str(node))
    
    def get_current_node(self) -> Optional[Any]:
        """
        Get current selected node.
        
        Returns:
            Current node or None
        """
        return self.current_node
    
    def get_node_info(self, node: Any) -> Dict[str, str]:
        """
        Get information about a node.
        
        Args:
            node: GGPK node
        
        Returns:
            Dictionary with node information
        """
        try:
            return {
                'name': node.record.name,
                'name_hash': node.record.name_hash,
                'hash': node.record.hash,
            }
        except AttributeError:
            return {
                'name': '',
                'name_hash': '',
                'hash': '',
            }
    
    def extract_node(self, node: Any, target_path: Path) -> bool:
        """
        Extract node to specified path.
        
        Args:
            node: Node to extract
            target_path: Target directory path
        
        Returns:
            True if extraction successful
        """
        try:
            logger.info("extracting_node", node=str(node), target=str(target_path))
            
            # Ensure target directory exists
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Extract file
            file_path = target_path / node.record.name
            with open(file_path, 'wb') as f:
                f.write(node.record.extract())
            
            logger.info("extraction_complete", path=str(file_path))
            self.extraction_complete.emit(True, str(file_path))
            return True
            
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            logger.error("extraction_failed", error=str(e))
            self.extraction_complete.emit(False, error_msg)
            return False
    
    def search_nodes(self, pattern: str) -> List[Any]:
        """
        Search for nodes matching pattern.
        
        Args:
            pattern: Search pattern (regex or plain text)
        
        Returns:
            List of matching nodes
        """
        if not self.is_ggpk_loaded():
            return []
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            # If invalid regex, treat as plain text
            regex = re.compile(re.escape(pattern), re.IGNORECASE)
        
        results = []
        for node in self.ggpk_file.directory.walk(function=lambda n: None):  # type: ignore[union-attr, call-arg]
            if regex.search(node.record.name):
                results.append(node)
        
        logger.debug("search_complete", pattern=pattern, results=len(results))
        return results
    
    def reload_specification(self, version: VERSION) -> None:
        """
        Reload specification with new version.
        
        Args:
            version: New game version
        """
        logger.info("reloading_specification", version=version.name)
        
        self.factory = FileParserFactory.default(version=version)
        self.specification = self.factory.get_specification()
        
        self.specification_reloaded.emit()
        logger.info("specification_reloaded", version=version.name)
    
    def get_specification(self) -> Specification:
        """
        Get current specification.
        
        Returns:
            Current specification
        """
        return self.specification


__all__ = ['GGPKViewModel']

