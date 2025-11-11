"""Tests for GGPKViewModel DI integration (without spec database)."""

import pytest

pytest.importorskip("PySide6")

from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel


def test_viewmodel_with_factory_method_exists():
    """Test that GGPKViewModel has with_factory class method."""
    assert hasattr(GGPKViewModel, "with_factory")
    assert callable(getattr(GGPKViewModel, "with_factory"))


def test_viewmodel_with_factory_signature():
    """Test with_factory signature."""
    import inspect

    sig = inspect.signature(GGPKViewModel.with_factory)

    # Should accept factory and optional parent
    params = list(sig.parameters.keys())
    assert "factory" in params
    assert "parent" in params


def test_viewmodel_traditional_init():
    """Test traditional initialization still works (backward compatibility)."""
    from PyPoE.poe.constants import VERSION

    # Should not raise
    try:
        vm = GGPKViewModel(version=VERSION.STABLE)
    except FileNotFoundError:
        # Expected if spec DB not found, that's OK
        pytest.skip("Specification database not found")

    # If we get here, initialization worked
    assert vm is not None


def test_viewmodel_has_required_attributes():
    """Test that viewmodel instance has required attributes."""
    from PyPoE.poe.constants import VERSION

    try:
        vm = GGPKViewModel(version=VERSION.STABLE)
    except FileNotFoundError:
        pytest.skip("Specification database not found")

    # Check required attributes
    assert hasattr(vm, "ggpk_file")
    assert hasattr(vm, "current_node")
    assert hasattr(vm, "thread_pool")
    assert hasattr(vm, "factory")
    assert hasattr(vm, "specification")


def test_viewmodel_with_factory_creates_instance():
    """Test with_factory creates proper instance (with mock factory)."""

    # Create a mock factory
    class MockFactory:
        def get_specification(self):
            return {}

    mock_factory = MockFactory()

    # Create viewmodel with mock factory
    vm = GGPKViewModel.with_factory(factory=mock_factory)  # type: ignore[arg-type]

    assert vm is not None
    assert hasattr(vm, "ggpk_file")
    assert hasattr(vm, "thread_pool")
    assert vm.factory is mock_factory


def test_viewmodel_with_factory_uses_injected_factory():
    """Test that with_factory actually uses the injected factory."""

    class MockFactory:
        called = False

        def get_specification(self):
            MockFactory.called = True
            return {"test": "spec"}

    mock_factory = MockFactory()

    vm = GGPKViewModel.with_factory(factory=mock_factory)  # type: ignore[arg-type]

    # Factory should have been called
    assert MockFactory.called
    assert vm.specification == {"test": "spec"}


def test_ui_providers_module_exists():
    """Test that UI providers module exists."""
    try:
        from PyPoE.ui import providers

        assert providers is not None
    except ImportError as e:
        pytest.fail(f"UI providers module not found: {e}")


def test_ui_providers_exports():
    """Test that UI providers exports expected functions."""
    from PyPoE.ui import providers

    assert hasattr(providers, "register_ui_providers")
    assert hasattr(providers, "create_ui_container")
    assert callable(providers.register_ui_providers)
    assert callable(providers.create_ui_container)

