"""
Tests for GGPK ViewModel

Tests the business logic layer separated from UI.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel
from PyPoE.poe.constants import VERSION


@pytest.fixture
def mock_factory():
    """Mock FileParserFactory for testing."""
    with patch('PyPoE.ui.ggpk_viewer.viewmodel.FileParserFactory') as mock:
        mock_instance = MagicMock()
        mock_instance.get_specification.return_value = MagicMock()
        mock.default.return_value = mock_instance
        yield mock


class TestGGPKViewModel:
    """Test GGPKViewModel business logic."""

    def test_init_default(self, mock_factory):
        """Test ViewModel initialization with defaults."""
        vm = GGPKViewModel()
        
        assert vm.ggpk_file is None
        assert vm.current_node is None
        assert vm.specification is not None
        assert vm.factory is not None

    def test_init_with_version(self, mock_factory):
        """Test ViewModel initialization with specific version."""
        vm = GGPKViewModel(version=VERSION.STABLE)
        
        assert vm.specification is not None

    def test_load_ggpk_file_success_sync(self, mock_factory):
        """Test loading GGPK file successfully (synchronous mode)."""
        vm = GGPKViewModel()
        mock_path = Path("test.ggpk")
        
        # Mock the file loading
        with patch('PyPoE.poe.file.ggpk.GGPKFile') as mock_ggpk:
            mock_instance = MagicMock()
            mock_ggpk.return_value = mock_instance
            
            # Use sync mode for testing
            vm.load_ggpk_file(mock_path, async_mode=False)
            
            assert vm.ggpk_file == mock_instance
            mock_instance.read.assert_called_once_with(mock_path)
            mock_instance.directory_build.assert_called_once()

    def test_load_ggpk_file_failure_sync(self, mock_factory):
        """Test loading GGPK file with error (synchronous mode)."""
        vm = GGPKViewModel()
        mock_path = Path("nonexistent.ggpk")
        
        with patch('PyPoE.poe.file.ggpk.GGPKFile') as mock_ggpk:
            mock_ggpk.side_effect = Exception("File not found")
            
            # Use sync mode for testing
            vm.load_ggpk_file(mock_path, async_mode=False)
            
            assert vm.ggpk_file is None
    
    def test_load_ggpk_file_async_mode(self, mock_factory):
        """Test loading GGPK file asynchronously."""
        vm = GGPKViewModel()
        vm.thread_pool = MagicMock()  # Mock thread pool
        mock_path = Path("test.ggpk")
        
        with patch('PyPoE.ui.ggpk_viewer.workers.GGPKLoadWorker') as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker
            
            # Use async mode (default)
            vm.load_ggpk_file(mock_path, async_mode=True)
            
            # Worker should be created and started
            mock_worker_class.assert_called_once_with(mock_path)
            vm.thread_pool.start.assert_called_once_with(mock_worker)

    def test_get_node_info(self, mock_factory):
        """Test getting node information."""
        vm = GGPKViewModel()
        mock_node = MagicMock()
        mock_node.record.name = "TestFile.dat"
        mock_node.record.name_hash = "ABC123"
        mock_node.record.hash = "DEF456"
        
        info = vm.get_node_info(mock_node)
        
        assert info['name'] == "TestFile.dat"
        assert info['name_hash'] == "ABC123"
        assert info['hash'] == "DEF456"

    def test_extract_node_to_path(self, mock_factory):
        """Test extracting node to specific path."""
        vm = GGPKViewModel()
        mock_node = MagicMock()
        mock_node.record.name = "test.txt"
        target_path = Path("/tmp/extracted")
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True):
            result = vm.extract_node(mock_node, target_path)
            
            # Should succeed
            assert result is True

    def test_search_nodes_by_name(self, mock_factory):
        """Test searching nodes by name pattern."""
        vm = GGPKViewModel()
        
        # Mock GGPK structure
        mock_ggpk = MagicMock()
        mock_node1 = MagicMock()
        mock_node1.record.name = "ActiveSkills.dat"
        mock_node2 = MagicMock()
        mock_node2.record.name = "PassiveSkills.dat"
        mock_node3 = MagicMock()
        mock_node3.record.name = "Items.dat"
        
        mock_ggpk.directory.walk.return_value = [
            mock_node1, mock_node2, mock_node3
        ]
        vm.ggpk_file = mock_ggpk
        
        results = vm.search_nodes("Skills")
        
        assert len(results) == 2
        assert mock_node1 in results
        assert mock_node2 in results
        assert mock_node3 not in results

    def test_get_directory_tree(self, mock_factory):
        """Test getting directory tree structure."""
        vm = GGPKViewModel()
        mock_ggpk = MagicMock()
        mock_ggpk.directory = MagicMock()
        vm.ggpk_file = mock_ggpk
        
        tree = vm.get_directory_tree()
        
        assert tree == mock_ggpk.directory

    def test_reload_specification(self, mock_factory):
        """Test reloading specification with new version."""
        vm = GGPKViewModel(version=VERSION.STABLE)
        
        # Create new mock for reloaded spec
        new_spec_mock = MagicMock()
        mock_factory.default.return_value.get_specification.return_value = new_spec_mock
        
        vm.reload_specification(VERSION.BETA)
        
        # Specification should be reloaded
        assert vm.specification is not None
        assert vm.specification == new_spec_mock

    def test_get_specification(self, mock_factory):
        """Test getting current specification."""
        vm = GGPKViewModel()
        
        spec = vm.get_specification()
        
        assert spec is not None
        assert spec == vm.specification

    def test_current_node_tracking(self, mock_factory):
        """Test tracking current selected node."""
        vm = GGPKViewModel()
        mock_node = MagicMock()
        
        vm.set_current_node(mock_node)
        
        assert vm.current_node == mock_node
        assert vm.get_current_node() == mock_node

    def test_is_ggpk_loaded(self, mock_factory):
        """Test checking if GGPK is loaded."""
        vm = GGPKViewModel()
        
        assert vm.is_ggpk_loaded() is False
        
        vm.ggpk_file = MagicMock()
        
        assert vm.is_ggpk_loaded() is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

