"""Tests for Dependency Injection container."""

import pytest

from PyPoE.shared.di import (
    DIContainer,
    DIError,
    FactoryProvider,
    InstanceProvider,
    SingletonProvider,
    TransientProvider,
    get_container,
    reset_container,
)


# Test classes
class Logger:
    """Mock logger class."""

    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        """Log message."""
        self.messages.append(message)


class Database:
    """Mock database class."""

    def __init__(self):
        self.connected = False

    def connect(self) -> None:
        """Connect to database."""
        self.connected = True


class Service:
    """Mock service class with dependencies."""

    def __init__(self, logger: Logger, database: Database):
        self.logger = logger
        self.database = database


# Tests for Providers
def test_singleton_provider():
    """Test singleton provider returns same instance."""
    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return Logger()

    provider = SingletonProvider(factory)

    instance1 = provider.get()
    instance2 = provider.get()

    assert instance1 is instance2
    assert call_count == 1


def test_singleton_provider_reset():
    """Test singleton provider can be reset."""
    provider = SingletonProvider(lambda: Logger())

    instance1 = provider.get()
    provider.reset()
    instance2 = provider.get()

    assert instance1 is not instance2


def test_transient_provider():
    """Test transient provider returns new instance each time."""
    provider = TransientProvider(lambda: Logger())

    instance1 = provider.get()
    instance2 = provider.get()

    assert instance1 is not instance2


def test_instance_provider():
    """Test instance provider returns same pre-existing instance."""
    logger = Logger()
    provider = InstanceProvider(logger)

    instance1 = provider.get()
    instance2 = provider.get()

    assert instance1 is logger
    assert instance2 is logger


def test_factory_provider():
    """Test factory provider with container access."""
    container = DIContainer()
    container.register_singleton(Logger, lambda: Logger())

    provider = FactoryProvider(lambda c: Service(c.resolve(Logger), Database()), container)

    instance = provider.get()
    assert isinstance(instance, Service)
    assert isinstance(instance.logger, Logger)


# Tests for DIContainer
def test_container_register_and_resolve_singleton():
    """Test registering and resolving singleton."""
    container = DIContainer()
    container.register_singleton(Logger, lambda: Logger())

    logger1 = container.resolve(Logger)
    logger2 = container.resolve(Logger)

    assert isinstance(logger1, Logger)
    assert logger1 is logger2


def test_container_register_and_resolve_transient():
    """Test registering and resolving transient."""
    container = DIContainer()
    container.register_transient(Logger, lambda: Logger())

    logger1 = container.resolve(Logger)
    logger2 = container.resolve(Logger)

    assert isinstance(logger1, Logger)
    assert logger1 is not logger2


def test_container_register_and_resolve_instance():
    """Test registering and resolving pre-existing instance."""
    container = DIContainer()
    logger = Logger()
    container.register_instance(Logger, logger)

    resolved = container.resolve(Logger)

    assert resolved is logger


def test_container_register_and_resolve_factory():
    """Test registering and resolving with factory."""
    container = DIContainer()
    container.register_singleton(Logger, lambda: Logger())
    container.register_singleton(Database, lambda: Database())
    container.register_factory(
        Service, lambda c: Service(c.resolve(Logger), c.resolve(Database))
    )

    service = container.resolve(Service)

    assert isinstance(service, Service)
    assert isinstance(service.logger, Logger)
    assert isinstance(service.database, Database)


def test_container_resolve_unregistered():
    """Test resolving unregistered dependency raises error."""
    container = DIContainer()

    with pytest.raises(DIError, match="No provider registered for Logger"):
        container.resolve(Logger)


def test_container_is_registered():
    """Test checking if interface is registered."""
    container = DIContainer()

    assert not container.is_registered(Logger)

    container.register_singleton(Logger, lambda: Logger())

    assert container.is_registered(Logger)


def test_container_reset_specific():
    """Test resetting specific provider."""
    container = DIContainer()
    container.register_singleton(Logger, lambda: Logger())

    logger1 = container.resolve(Logger)
    container.reset(Logger)
    logger2 = container.resolve(Logger)

    assert logger1 is not logger2


def test_container_reset_all():
    """Test resetting all providers."""
    container = DIContainer()
    container.register_singleton(Logger, lambda: Logger())
    container.register_singleton(Database, lambda: Database())

    logger1 = container.resolve(Logger)
    db1 = container.resolve(Database)

    container.reset()

    logger2 = container.resolve(Logger)
    db2 = container.resolve(Database)

    assert logger1 is not logger2
    assert db1 is not db2


def test_container_clear():
    """Test clearing all providers."""
    container = DIContainer()
    container.register_singleton(Logger, lambda: Logger())

    container.clear()

    assert not container.is_registered(Logger)
    with pytest.raises(DIError):
        container.resolve(Logger)


def test_container_list_providers():
    """Test listing registered providers."""
    container = DIContainer()
    container.register_singleton(Logger, lambda: Logger())
    container.register_transient(Database, lambda: Database())

    providers = container.list_providers()

    assert "Logger" in providers
    assert "Database" in providers
    assert len(providers) == 2


def test_container_overwrite_provider():
    """Test overwriting existing provider."""
    container = DIContainer()
    logger1 = Logger()
    logger2 = Logger()

    container.register_instance(Logger, logger1)
    container.register_instance(Logger, logger2)

    resolved = container.resolve(Logger)

    assert resolved is logger2


def test_global_container():
    """Test global container singleton."""
    reset_container()

    container1 = get_container()
    container2 = get_container()

    assert container1 is container2


def test_reset_global_container():
    """Test resetting global container."""
    reset_container()

    container1 = get_container()
    reset_container()
    container2 = get_container()

    assert container1 is not container2


def test_complex_dependency_chain():
    """Test resolving complex dependency chain."""
    container = DIContainer()

    # Register dependencies
    container.register_singleton(Logger, lambda: Logger())
    container.register_singleton(Database, lambda: Database())
    container.register_factory(
        Service, lambda c: Service(c.resolve(Logger), c.resolve(Database))
    )

    # Resolve
    service = container.resolve(Service)
    logger = container.resolve(Logger)

    # Verify
    assert isinstance(service, Service)
    assert service.logger is logger
    assert isinstance(service.database, Database)


def test_singleton_lifecycle():
    """Test singleton lifecycle across multiple resolves."""
    container = DIContainer()
    container.register_singleton(Logger, lambda: Logger())

    logger = container.resolve(Logger)
    logger.log("test message")

    # Resolve again - should get same instance with message
    logger2 = container.resolve(Logger)

    assert logger2.messages == ["test message"]
    assert logger is logger2


def test_transient_lifecycle():
    """Test transient lifecycle creates new instances."""
    container = DIContainer()
    container.register_transient(Logger, lambda: Logger())

    logger1 = container.resolve(Logger)
    logger1.log("message 1")

    logger2 = container.resolve(Logger)

    assert logger2.messages == []
    assert logger1 is not logger2

