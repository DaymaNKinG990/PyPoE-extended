"""
Tests for GGPK Async Workers

Tests asynchronous workers for loading GGPK files and extracting data.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import QThreadPool, QEventLoop, QTimer

from PyPoE.ui.ggpk_viewer.workers import (
    GGPKLoadWorker,
    FileExtractionWorker,
    WorkerSignals,
)


class TestWorkerSignals:
    """Test WorkerSignals."""

    def test_signals_exist(self):
        """Test that all required signals exist."""
        signals = WorkerSignals()
        
        assert hasattr(signals, 'loading_started')
        assert hasattr(signals, 'loading_progress')
        assert hasattr(signals, 'loading_finished')
        assert hasattr(signals, 'loading_failed')
        assert hasattr(signals, 'extraction_started')
        assert hasattr(signals, 'extraction_finished')
        assert hasattr(signals, 'extraction_failed')


class TestGGPKLoadWorker:
    """Test GGPKLoadWorker."""

    def test_init(self):
        """Test worker initialization."""
        file_path = Path("test.ggpk")
        worker = GGPKLoadWorker(file_path)
        
        assert worker.file_path == file_path
        assert worker.signals is not None
        assert worker.autoDelete() is True

    @patch('PyPoE.ui.ggpk_viewer.workers.ggpk.GGPKFile')
    def test_run_success(self, mock_ggpk_class):
        """Test successful GGPK loading."""
        # Setup
        file_path = Path("test.ggpk")
        worker = GGPKLoadWorker(file_path)
        
        mock_ggpk = MagicMock()
        mock_ggpk_class.return_value = mock_ggpk
        
        # Track signal emissions
        started_spy = Mock()
        progress_spy = Mock()
        finished_spy = Mock()
        failed_spy = Mock()
        
        worker.signals.loading_started.connect(started_spy)
        worker.signals.loading_progress.connect(progress_spy)
        worker.signals.loading_finished.connect(finished_spy)
        worker.signals.loading_failed.connect(failed_spy)
        
        # Execute
        worker.run()
        
        # Verify
        started_spy.assert_called_once()
        assert progress_spy.call_count >= 3  # At least 3 progress updates
        finished_spy.assert_called_once_with(mock_ggpk)
        failed_spy.assert_not_called()
        
        # Verify GGPK operations
        mock_ggpk.read.assert_called_once_with(file_path)
        mock_ggpk.directory_build.assert_called_once()

    @patch('PyPoE.ui.ggpk_viewer.workers.ggpk.GGPKFile')
    def test_run_failure(self, mock_ggpk_class):
        """Test GGPK loading failure."""
        # Setup
        file_path = Path("test.ggpk")
        worker = GGPKLoadWorker(file_path)
        
        # Simulate error
        mock_ggpk_class.side_effect = Exception("Test error")
        
        # Track signal emissions
        started_spy = Mock()
        finished_spy = Mock()
        failed_spy = Mock()
        
        worker.signals.loading_started.connect(started_spy)
        worker.signals.loading_finished.connect(finished_spy)
        worker.signals.loading_failed.connect(failed_spy)
        
        # Execute
        worker.run()
        
        # Verify
        started_spy.assert_called_once()
        finished_spy.assert_not_called()
        failed_spy.assert_called_once()
        
        # Check error details
        args = failed_spy.call_args[0]
        assert "Test error" in args[0]  # error_message
        assert len(args[1]) > 0  # traceback

    def test_worker_autoDelete_enabled(self):
        """Test that worker has autoDelete enabled."""
        file_path = Path("test.ggpk")
        worker = GGPKLoadWorker(file_path)
        
        # AutoDelete should be enabled for proper cleanup
        assert worker.autoDelete() is True


class TestFileExtractionWorker:
    """Test FileExtractionWorker."""

    def test_init(self):
        """Test worker initialization."""
        mock_record = MagicMock()
        mock_record.name = "test.dat"
        
        worker = FileExtractionWorker(mock_record)
        
        assert worker.file_record == mock_record
        assert worker.signals is not None
        assert worker.autoDelete() is True

    def test_run_success(self):
        """Test successful file extraction."""
        # Setup
        mock_record = MagicMock()
        mock_record.name = "test.dat"
        mock_record.extract.return_value = b"test data"
        
        worker = FileExtractionWorker(mock_record)
        
        # Track signal emissions
        started_spy = Mock()
        finished_spy = Mock()
        failed_spy = Mock()
        
        worker.signals.extraction_started.connect(started_spy)
        worker.signals.extraction_finished.connect(finished_spy)
        worker.signals.extraction_failed.connect(failed_spy)
        
        # Execute
        worker.run()
        
        # Verify
        started_spy.assert_called_once_with("test.dat")
        finished_spy.assert_called_once_with(b"test data")
        failed_spy.assert_not_called()
        mock_record.extract.assert_called_once()

    def test_run_failure(self):
        """Test file extraction failure."""
        # Setup
        mock_record = MagicMock()
        mock_record.name = "test.dat"
        mock_record.extract.side_effect = Exception("Extraction error")
        
        worker = FileExtractionWorker(mock_record)
        
        # Track signal emissions
        started_spy = Mock()
        finished_spy = Mock()
        failed_spy = Mock()
        
        worker.signals.extraction_started.connect(started_spy)
        worker.signals.extraction_finished.connect(finished_spy)
        worker.signals.extraction_failed.connect(failed_spy)
        
        # Execute
        worker.run()
        
        # Verify
        started_spy.assert_called_once()
        finished_spy.assert_not_called()
        failed_spy.assert_called_once()
        
        # Check error details
        args = failed_spy.call_args[0]
        assert "Extraction error" in args[0]  # error_message
        assert len(args[1]) > 0  # traceback


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

