"""
Dependency Injection container for managing application dependencies.

This module provides a lightweight, type-safe DI container that supports:
- Singleton and transient lifecycles
- Lazy initialization
- Factory providers
- Automatic dependency resolution
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar, cast

from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class DIError(Exception):
    """Raised when DI operations fail."""

    pass


class Provider(ABC):
    """Abstract base class for dependency providers."""

    @abstractmethod
    def get(self) -> Any:
        """Get instance from provider."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset provider state."""
        pass


class SingletonProvider(Provider):
    """Provider that returns the same instance (singleton lifecycle)."""

    def __init__(self, factory: Callable[[], Any]):
        """
        Initialize singleton provider.

        Args:
            factory: Factory function that creates the instance
        """
        self.factory = factory
        self.instance: Any = None
        self._initialized = False

    def get(self) -> Any:
        """Get singleton instance (lazy initialization)."""
        if not self._initialized:
            logger.debug(f"Initializing singleton: {self.factory.__name__}")
            self.instance = self.factory()
            self._initialized = True
        return self.instance

    def reset(self) -> None:
        """Reset singleton instance."""
        logger.debug(f"Resetting singleton: {self.factory.__name__}")
        self.instance = None
        self._initialized = False


class TransientProvider(Provider):
    """Provider that returns new instance each time (transient lifecycle)."""

    def __init__(self, factory: Callable[[], Any]):
        """
        Initialize transient provider.

        Args:
            factory: Factory function that creates instances
        """
        self.factory = factory

    def get(self) -> Any:
        """Get new instance."""
        logger.debug(f"Creating transient instance: {self.factory.__name__}")
        return self.factory()

    def reset(self) -> None:
        """Reset transient provider (no-op)."""
        pass


class InstanceProvider(Provider):
    """Provider that returns pre-existing instance."""

    def __init__(self, instance: Any):
        """
        Initialize instance provider.

        Args:
            instance: Pre-existing instance to provide
        """
        self.instance = instance

    def get(self) -> Any:
        """Get instance."""
        return self.instance

    def reset(self) -> None:
        """Reset instance provider (no-op)."""
        pass


class FactoryProvider(Provider):
    """Provider that uses a factory function with dependencies."""

    def __init__(self, factory: Callable[..., Any], container: "DIContainer"):
        """
        Initialize factory provider.

        Args:
            factory: Factory function
            container: DI container for resolving dependencies
        """
        self.factory = factory
        self.container = container

    def get(self) -> Any:
        """Get instance from factory."""
        logger.debug(f"Creating instance via factory: {self.factory.__name__}")
        return self.factory(self.container)

    def reset(self) -> None:
        """Reset factory provider (no-op)."""
        pass


class DIContainer:
    """
    Dependency Injection container for managing object lifecycles.

    Example:
        >>> container = DIContainer()
        >>> container.register_singleton(Logger, lambda: FileLogger())
        >>> container.register_transient(Service, lambda: Service(container.resolve(Logger)))
        >>> service = container.resolve(Service)
    """

    def __init__(self):
        """Initialize DI container."""
        self._providers: dict[type, Provider] = {}
        logger.debug("DI Container initialized")

    def register_singleton(self, interface: type[T], factory: Callable[[], T]) -> None:
        """
        Register singleton provider (one instance for lifetime).

        Args:
            interface: Interface/class to register
            factory: Factory function that creates the instance

        Example:
            >>> container.register_singleton(Database, lambda: SQLiteDatabase())
        """
        if interface in self._providers:
            logger.warning(f"Overwriting existing provider for {interface.__name__}")

        self._providers[interface] = SingletonProvider(factory)
        logger.info(f"Registered singleton: {interface.__name__}")

    def register_transient(self, interface: type[T], factory: Callable[[], T]) -> None:
        """
        Register transient provider (new instance each time).

        Args:
            interface: Interface/class to register
            factory: Factory function that creates instances

        Example:
            >>> container.register_transient(Request, lambda: HttpRequest())
        """
        if interface in self._providers:
            logger.warning(f"Overwriting existing provider for {interface.__name__}")

        self._providers[interface] = TransientProvider(factory)
        logger.info(f"Registered transient: {interface.__name__}")

    def register_instance(self, interface: type[T], instance: T) -> None:
        """
        Register pre-existing instance.

        Args:
            interface: Interface/class to register
            instance: Pre-existing instance

        Example:
            >>> config = Config()
            >>> container.register_instance(Config, config)
        """
        if interface in self._providers:
            logger.warning(f"Overwriting existing provider for {interface.__name__}")

        self._providers[interface] = InstanceProvider(instance)
        logger.info(f"Registered instance: {interface.__name__}")

    def register_factory(
        self, interface: type[T], factory: Callable[["DIContainer"], T]
    ) -> None:
        """
        Register factory with access to container.

        Args:
            interface: Interface/class to register
            factory: Factory function that receives container

        Example:
            >>> container.register_factory(
            ...     Service,
            ...     lambda c: Service(c.resolve(Logger), c.resolve(Database))
            ... )
        """
        if interface in self._providers:
            logger.warning(f"Overwriting existing provider for {interface.__name__}")

        self._providers[interface] = FactoryProvider(factory, self)
        logger.info(f"Registered factory: {interface.__name__}")

    def resolve(self, interface: type[T]) -> T:
        """
        Resolve dependency from container.

        Args:
            interface: Interface/class to resolve

        Returns:
            Instance of the requested type

        Raises:
            DIError: If dependency is not registered

        Example:
            >>> logger = container.resolve(Logger)
        """
        if interface not in self._providers:
            raise DIError(
                f"No provider registered for {interface.__name__}. "
                f"Available: {list(self._providers.keys())}"
            )

        logger.debug(f"Resolving dependency: {interface.__name__}")
        return cast(T, self._providers[interface].get())

    def is_registered(self, interface: type) -> bool:
        """
        Check if interface is registered.

        Args:
            interface: Interface/class to check

        Returns:
            True if registered, False otherwise
        """
        return interface in self._providers

    def reset(self, interface: type | None = None) -> None:
        """
        Reset providers (useful for testing).

        Args:
            interface: Specific interface to reset, or None to reset all
        """
        if interface is None:
            logger.info("Resetting all providers")
            for provider in self._providers.values():
                provider.reset()
        elif interface in self._providers:
            logger.info(f"Resetting provider: {interface.__name__}")
            self._providers[interface].reset()
        else:
            logger.warning(f"Cannot reset unregistered provider: {interface.__name__}")

    def clear(self) -> None:
        """Clear all registered providers."""
        logger.info("Clearing DI container")
        self._providers.clear()

    def list_providers(self) -> list[str]:
        """
        List all registered providers.

        Returns:
            List of registered interface names
        """
        return [interface.__name__ for interface in self._providers]


# Global container instance
_global_container: DIContainer | None = None


def get_container() -> DIContainer:
    """
    Get global DI container (singleton pattern).

    Returns:
        Global DIContainer instance
    """
    global _global_container
    if _global_container is None:
        _global_container = DIContainer()
        logger.debug("Created global DI container")
    return _global_container


def reset_container() -> None:
    """Reset global DI container (useful for testing)."""
    global _global_container
    if _global_container is not None:
        _global_container.clear()
        _global_container = None
        logger.debug("Reset global DI container")

