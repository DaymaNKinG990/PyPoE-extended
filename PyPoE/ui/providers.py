"""
Dependency Injection providers for PyPoE UI components.

This module provides DI registration for Qt UI components,
enabling testability and loose coupling.
"""

from typing import TYPE_CHECKING

from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.shared.di import DIContainer
from PyPoE.shared.logging import get_logger

if TYPE_CHECKING:
    from PySide6.QtCore import QObject

    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

logger = get_logger(__name__)


def register_ui_providers(
    container: DIContainer,
    version: VERSION = VERSION.STABLE,
    parent: "QObject | None" = None,
) -> None:
    """
    Register UI-specific providers in the DI container.

    Args:
        container: DI container instance
        version: Game version for specifications
        parent: Parent QObject for Qt components

    Example:
        >>> from PyPoE.shared.di import get_container
        >>> from PyPoE.ui.providers import register_ui_providers
        >>>
        >>> container = get_container()
        >>> register_ui_providers(container)
        >>>
        >>> # Now you can resolve UI components
        >>> viewmodel = container.resolve(GGPKViewModel)
    """
    logger.info("Registering UI providers", version=version.name)

    # Import here to avoid circular dependencies
    from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel

    # GGPKViewModel - transient (new instance for each window)
    # Uses factory from container for DI
    def create_viewmodel(c: DIContainer) -> "GGPKViewModel":
        factory = c.resolve(FileParserFactory)
        return GGPKViewModel.with_factory(factory=factory, parent=parent)

    container.register_factory(GGPKViewModel, create_viewmodel)

    logger.info("UI providers registered successfully")


def create_ui_container(
    version: VERSION = VERSION.STABLE,
    parent: "QObject | None" = None,
) -> DIContainer:
    """
    Create and configure a DI container for UI application.

    This is a convenience function that creates a container with both
    core and UI providers registered.

    Args:
        version: Game version for specifications
        parent: Parent QObject for Qt components

    Returns:
        Configured DIContainer with core + UI providers

    Example:
        >>> from PyPoE.ui.providers import create_ui_container
        >>> from PyPoE.ui.ggpk_viewer.viewmodel import GGPKViewModel
        >>>
        >>> container = create_ui_container()
        >>> viewmodel = container.resolve(GGPKViewModel)
    """
    from PyPoE.poe.providers import register_core_providers

    container = DIContainer()
    register_core_providers(container, version=version)
    register_ui_providers(container, version=version, parent=parent)

    logger.info("UI container created with all providers")
    return container

