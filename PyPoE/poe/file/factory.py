"""Factory for creating file parsers with dependency injection.

This module provides factory classes that create file parsers with proper
dependencies injected, removing the need for global state.

Example:
    >>> from PyPoE.poe.file.factory import FileParserFactory
    >>> from PyPoE.poe.constants import VERSION
    >>>
    >>> # Create factory with default configuration
    >>> factory = FileParserFactory.default(VERSION.STABLE)
    >>>
    >>> # Get specification for loading .dat files
    >>> spec = factory.get_specification()
    >>>
    >>> # Or use in DatReader directly
    >>> from PyPoE.poe.file.dat import DatReader
    >>> reader = DatReader("ActiveSkills.dat", specification=spec)
"""

from __future__ import annotations

from pathlib import Path

from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.specification.fields import Specification
from PyPoE.poe.file.specification.repository import (
    CachedSpecRepository,
    SQLiteSpecRepository,
)
from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)


class FileParserFactory:
    """Factory for creating file parsers with proper dependencies.

    This factory manages specification repositories and provides
    specifications for file parsers, eliminating the need for global state.

    Args:
        spec_repository: Specification repository to use

    Example:
        >>> # Default factory with SQLite specs
        >>> factory = FileParserFactory.default(VERSION.STABLE)
        >>> spec = factory.get_specification()
        >>> print(len(spec))  # Number of .dat files
        801
    """

    def __init__(self, spec_repository: SQLiteSpecRepository):
        """Initialize factory.

        Args:
            spec_repository: Specification repository
        """
        self._spec_repo = CachedSpecRepository(spec_repository)
        logger.debug("file_parser_factory_initialized")

    @classmethod
    def default(cls, version: VERSION = VERSION.STABLE) -> FileParserFactory:
        """Create factory with default configuration.

        Args:
            version: Game version (STABLE, BETA, ALPHA)

        Returns:
            FileParserFactory instance

        Raises:
            FileNotFoundError: If specification database not found

        Example:
            >>> factory = FileParserFactory.default(VERSION.STABLE)
            >>> spec = factory.get_specification()
        """
        db_name = f"{version.name.lower()}.db"
        db_path = Path(__file__).parent.parent.parent / "data" / "specifications" / db_name

        if not db_path.exists():
            raise FileNotFoundError(
                f"Specification database not found: {db_path}\n"
                f"Run: python scripts/migrate_specs_to_db.py"
            )

        repo = SQLiteSpecRepository(db_path)
        logger.info("factory_created_with_default_specs", version=version.name)
        return cls(repo)

    @classmethod
    def from_db_path(cls, db_path: Path) -> FileParserFactory:
        """Create factory from custom database path.

        Args:
            db_path: Path to custom specification database

        Returns:
            FileParserFactory instance

        Example:
            >>> factory = FileParserFactory.from_db_path(Path("custom_specs.db"))
        """
        repo = SQLiteSpecRepository(db_path)
        logger.info("factory_created_with_custom_db", db_path=str(db_path))
        return cls(repo)

    def get_specification(self, version: VERSION = VERSION.STABLE) -> Specification:
        """Get complete specification for given version.

        Args:
            version: Game version

        Returns:
            Complete specification containing all .dat file specs

        Example:
            >>> factory = FileParserFactory.default()
            >>> spec = factory.get_specification(VERSION.STABLE)
            >>> file_spec = spec["ActiveSkills.dat"]
        """
        return self._spec_repo.get_spec(version)

    def clear_cache(self):
        """Clear specification cache.

        Useful if you want to force reload specifications from database.
        """
        self._spec_repo.clear_cache()
        logger.info("factory_cache_cleared")
