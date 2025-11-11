"""Tests for PyPoE DI providers."""

import pytest

from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.poe.file.ggpk import GGPKFile
from PyPoE.poe.file.specification.repository import SQLiteSpecRepository
from PyPoE.shared.di import DIContainer, DIError


def test_basic_container_registration():
    """Test basic provider registration without full setup."""
    container = DIContainer()

    # Register GGPK file provider
    container.register_transient(GGPKFile, lambda: GGPKFile())

    # Check registration
    assert container.is_registered(GGPKFile)
    assert not container.is_registered(FileParserFactory)


def test_ggpk_file_transient():
    """Test GGPK file is transient (new instance each time)."""
    container = DIContainer()
    container.register_transient(GGPKFile, lambda: GGPKFile())

    ggpk1 = container.resolve(GGPKFile)
    ggpk2 = container.resolve(GGPKFile)

    assert isinstance(ggpk1, GGPKFile)
    assert isinstance(ggpk2, GGPKFile)
    assert ggpk1 is not ggpk2  # Different instances


def test_manual_provider_registration():
    """Test manual registration of providers."""
    container = DIContainer()

    # Manually register a singleton
    container.register_singleton(
        FileParserFactory,
        lambda: FileParserFactory.default(VERSION.STABLE) if _spec_db_exists() else None,
    )

    # Check if registered
    assert container.is_registered(FileParserFactory)


def test_provider_lifecycle():
    """Test provider lifecycle management."""
    container = DIContainer()

    # Register transient
    container.register_transient(GGPKFile, lambda: GGPKFile())

    # Resolve multiple times
    instances = [container.resolve(GGPKFile) for _ in range(3)]

    # All should be different instances
    assert len({id(inst) for inst in instances}) == 3


def test_container_reset():
    """Test resetting container."""
    container = DIContainer()
    container.register_singleton(GGPKFile, lambda: GGPKFile())

    # Resolve
    instance1 = container.resolve(GGPKFile)

    # Reset
    container.reset(GGPKFile)

    # Resolve again - should be different instance
    instance2 = container.resolve(GGPKFile)
    assert instance1 is not instance2


def test_unregistered_provider():
    """Test resolving unregistered provider raises error."""
    container = DIContainer()

    with pytest.raises(DIError, match="No provider registered"):
        container.resolve(FileParserFactory)


def test_list_registered_providers():
    """Test listing registered providers."""
    container = DIContainer()
    container.register_transient(GGPKFile, lambda: GGPKFile())

    providers = container.list_providers()
    assert "GGPKFile" in providers


def test_is_registered():
    """Test checking if provider is registered."""
    container = DIContainer()

    assert not container.is_registered(GGPKFile)

    container.register_transient(GGPKFile, lambda: GGPKFile())

    assert container.is_registered(GGPKFile)


def test_clear_container():
    """Test clearing all providers."""
    container = DIContainer()
    container.register_transient(GGPKFile, lambda: GGPKFile())

    assert container.is_registered(GGPKFile)

    container.clear()

    assert not container.is_registered(GGPKFile)


def test_factory_provider():
    """Test factory provider with container access."""
    container = DIContainer()

    # Register a dependency
    container.register_singleton(GGPKFile, lambda: GGPKFile())

    # Register a factory that uses the dependency
    def create_with_deps(c):
        ggpk = c.resolve(GGPKFile)
        return {"ggpk": ggpk, "count": 1}

    container.register_factory(dict, create_with_deps)

    # Resolve
    result = container.resolve(dict)
    assert "ggpk" in result
    assert isinstance(result["ggpk"], GGPKFile)


# Helper function
def _spec_db_exists() -> bool:
    """Check if specification database exists."""
    from pathlib import Path
    db_path = Path(__file__).parent.parent.parent / "data" / "specifications" / "stable.db"
    return db_path.exists()


# Integration test (only runs if database exists)
@pytest.mark.skipif(not _spec_db_exists(), reason="Specification database not found")
def test_full_provider_registration():
    """Integration test with real database."""
    from PyPoE.poe.providers import register_core_providers

    container = DIContainer()
    register_core_providers(container, version=VERSION.STABLE)

    # Should have providers registered
    assert container.is_registered(SQLiteSpecRepository)
    assert container.is_registered(FileParserFactory)
    assert container.is_registered(GGPKFile)


@pytest.mark.skipif(not _spec_db_exists(), reason="Specification database not found")
def test_resolve_factory_integration():
    """Integration test resolving file parser factory."""
    from PyPoE.poe.providers import create_configured_container

    container = create_configured_container(version=VERSION.STABLE)

    # Should be able to resolve factory
    factory = container.resolve(FileParserFactory)
    assert isinstance(factory, FileParserFactory)

    # Can get specification
    spec = factory.get_specification()
    assert spec is not None
