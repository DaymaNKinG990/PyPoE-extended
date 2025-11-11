"""Tests for UI DI providers."""

import pytest

from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.shared.di import DIContainer

# Skip if PySide6 not available
pytest.importorskip("PySide6")

from PyPoE.ui.providers import create_ui_container, register_ui_providers


def test_register_ui_providers():
    """Test registering UI providers in container."""
    from PyPoE.poe.providers import register_core_providers
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    container = DIContainer()
    register_core_providers(container, version=VERSION.STABLE)
    register_ui_providers(container, version=VERSION.STABLE)

    # Check that UI providers are registered
    assert container.is_registered(GGPKViewModel)


def test_resolve_viewmodel_with_di():
    """Test resolving GGPKViewModel through DI."""
    from PyPoE.poe.providers import register_core_providers
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    container = DIContainer()
    register_core_providers(container, version=VERSION.STABLE)
    register_ui_providers(container, version=VERSION.STABLE)

    # Should be able to resolve viewmodel
    viewmodel = container.resolve(GGPKViewModel)
    assert viewmodel is not None
    assert hasattr(viewmodel, "factory")
    assert hasattr(viewmodel, "specification")


def test_viewmodel_with_factory():
    """Test creating viewmodel with factory method."""
    from PyPoE.poe.providers import register_core_providers
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    container = DIContainer()
    register_core_providers(container, version=VERSION.STABLE)

    # Get factory
    factory = container.resolve(FileParserFactory)

    # Create viewmodel with factory
    viewmodel = GGPKViewModel.with_factory(factory=factory)

    assert viewmodel is not None
    assert viewmodel.factory is factory
    assert viewmodel.specification is not None


def test_viewmodel_transient():
    """Test that viewmodel is transient (new instance each time)."""
    from PyPoE.poe.providers import register_core_providers
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    container = DIContainer()
    register_core_providers(container, version=VERSION.STABLE)
    register_ui_providers(container, version=VERSION.STABLE)

    # Resolve twice
    vm1 = container.resolve(GGPKViewModel)
    vm2 = container.resolve(GGPKViewModel)

    # Should be different instances (transient)
    assert vm1 is not vm2


def test_viewmodel_factory_singleton():
    """Test that viewmodel uses singleton factory."""
    from PyPoE.poe.providers import register_core_providers
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    container = DIContainer()
    register_core_providers(container, version=VERSION.STABLE)
    register_ui_providers(container, version=VERSION.STABLE)

    # Resolve viewmodels
    vm1 = container.resolve(GGPKViewModel)
    vm2 = container.resolve(GGPKViewModel)

    # Different viewmodels
    assert vm1 is not vm2

    # But same factory (singleton)
    assert vm1.factory is vm2.factory


def test_create_ui_container():
    """Test creating UI container with all providers."""
    container = create_ui_container(version=VERSION.STABLE)

    # Should have both core and UI providers
    assert container.is_registered(FileParserFactory)

    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    assert container.is_registered(GGPKViewModel)


def test_viewmodel_backward_compatibility():
    """Test that old viewmodel initialization still works."""
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    # Old way (without DI)
    viewmodel = GGPKViewModel(version=VERSION.STABLE)

    assert viewmodel is not None
    assert hasattr(viewmodel, "factory")
    assert hasattr(viewmodel, "specification")


def test_viewmodel_with_factory_equivalent():
    """Test that with_factory produces equivalent viewmodel."""
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    # Old way
    vm_old = GGPKViewModel(version=VERSION.STABLE)

    # New way with DI
    factory = FileParserFactory.default(VERSION.STABLE)
    vm_new = GGPKViewModel.with_factory(factory=factory)

    # Both should have same attributes
    assert hasattr(vm_old, "ggpk_file")
    assert hasattr(vm_new, "ggpk_file")
    assert hasattr(vm_old, "thread_pool")
    assert hasattr(vm_new, "thread_pool")
    assert hasattr(vm_old, "specification")
    assert hasattr(vm_new, "specification")


def test_viewmodel_specification_loaded():
    """Test that viewmodel has specification loaded."""
    from PyPoE.poe.providers import register_core_providers
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    container = DIContainer()
    register_core_providers(container, version=VERSION.STABLE)
    register_ui_providers(container, version=VERSION.STABLE)

    viewmodel = container.resolve(GGPKViewModel)

    # Specification should be loaded
    assert viewmodel.specification is not None
    assert len(viewmodel.specification) > 0  # Should have some specs


def test_ui_container_multiple_versions():
    """Test creating UI containers for different versions."""
    container_stable = create_ui_container(version=VERSION.STABLE)
    container_beta = create_ui_container(version=VERSION.BETA)

    # Different containers
    assert container_stable is not container_beta

    # Both should work
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    vm_stable = container_stable.resolve(GGPKViewModel)
    vm_beta = container_beta.resolve(GGPKViewModel)

    assert vm_stable is not vm_beta

