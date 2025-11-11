"""
Dependency Injection providers for PyPoE core components.

This module provides factory functions and registration helpers for core
components, enabling dependency injection throughout the application.
"""

from pathlib import Path

from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.ggpk import GGPKFile
from PyPoE.poe.file.ggpk.diff_comparator import GGPKDiffComparator
from PyPoE.poe.file.ggpk.directory_builder import GGPKDirectoryBuilder
from PyPoE.poe.file.ggpk.reader import GGPKReader
from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager
from PyPoE.poe.file.specification.repository import SQLiteSpecRepository
from PyPoE.shared.di import DIContainer
from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)


def register_core_providers(
    container: DIContainer,
    game_path: str | None = None,
    version: VERSION = VERSION.STABLE,
) -> None:
    """
    Register all core PyPoE providers in the DI container.

    Args:
        container: DI container instance
        game_path: Path to game installation (optional, for FileSystem)
        version: Game version for specifications

    Example:
        >>> from PyPoE.shared.di import get_container
        >>> from PyPoE.poe.providers import register_core_providers
        >>>
        >>> container = get_container()
        >>> register_core_providers(container, game_path="C:/PoE")
        >>>
        >>> # Now you can resolve dependencies
        >>> factory = container.resolve(FileParserFactory)
    """
    logger.info("Registering core providers", version=version.name)

    # Specification Repository (singleton)
    container.register_factory(
        SQLiteSpecRepository,
        lambda c: _create_spec_repository(version),
    )

    # File Parser Factory (singleton)
    container.register_factory(
        FileParserFactory,
        lambda c: FileParserFactory(c.resolve(SQLiteSpecRepository)),
    )

    # File System (singleton, if game_path provided)
    if game_path:
        container.register_singleton(
            FileSystem,
            lambda: FileSystem(root_path=game_path),
        )
        logger.info("FileSystem registered", game_path=game_path)

    # GGPK Components (transient - stateless, can be reused)
    container.register_transient(
        GGPKReader,
        lambda: GGPKReader(),
    )
    container.register_transient(
        GGPKRecordManager,
        lambda: GGPKRecordManager(),
    )
    container.register_transient(
        GGPKDirectoryBuilder,
        lambda: GGPKDirectoryBuilder(),
    )
    container.register_transient(
        GGPKDiffComparator,
        lambda: GGPKDiffComparator(),
    )

    # GGPK File (transient - each usage creates new instance)
    # Uses DI to inject all components
    container.register_factory(
        GGPKFile,
        lambda c: GGPKFile(
            reader=c.resolve(GGPKReader),
            record_manager=c.resolve(GGPKRecordManager),
            directory_builder=c.resolve(GGPKDirectoryBuilder),
            diff_comparator=c.resolve(GGPKDiffComparator),
        ),
    )

    logger.info("Core providers registered successfully")


def _create_spec_repository(version: VERSION) -> SQLiteSpecRepository:
    """
    Create specification repository for given version.

    Args:
        version: Game version

    Returns:
        SQLiteSpecRepository instance

    Raises:
        FileNotFoundError: If specification database not found
    """
    db_name = f"{version.name.lower()}.db"
    db_path = Path(__file__).parent.parent / "data" / "specifications" / db_name

    if not db_path.exists():
        raise FileNotFoundError(
            f"Specification database not found: {db_path}\n"
            f"Run: python scripts/migrate_specs_to_db.py"
        )

    logger.debug("Creating spec repository", version=version.name, db_path=str(db_path))
    return SQLiteSpecRepository(db_path)


def create_configured_container(
    game_path: str | None = None,
    version: VERSION = VERSION.STABLE,
) -> DIContainer:
    """
    Create and configure a DI container with all core providers.

    This is a convenience function that creates a new container and registers
    all core providers in one call.

    Args:
        game_path: Path to game installation (optional)
        version: Game version for specifications

    Returns:
        Configured DIContainer instance

    Example:
        >>> from PyPoE.poe.providers import create_configured_container
        >>> from PyPoE.poe.file.factory import FileParserFactory
        >>>
        >>> container = create_configured_container()
        >>> factory = container.resolve(FileParserFactory)
        >>> spec = factory.get_specification()
    """
    from PyPoE.shared.di import DIContainer

    container = DIContainer()
    register_core_providers(container, game_path=game_path, version=version)
    logger.info("Configured container created")
    return container

