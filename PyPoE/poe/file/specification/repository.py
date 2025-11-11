"""Specification repository implementations.

This module provides repository classes for loading .dat file specifications
from SQLite database instead of Python modules.

Example:
    >>> from PyPoE.poe.file.specification.repository import SQLiteSpecRepository
    >>> from PyPoE.poe.constants import VERSION
    >>> from pathlib import Path
    >>>
    >>> db_path = Path("data/specifications/stable.db")
    >>> repo = SQLiteSpecRepository(db_path)
    >>> spec = repo.get_spec(VERSION.STABLE)
    >>> file_spec = repo.get_file_spec("ActiveSkills.dat", VERSION.STABLE)
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Protocol

from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.specification.fields import Field, File, Specification, VirtualField
from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)


class SpecificationProvider(Protocol):
    """Protocol for specification providers."""

    def get_spec(self, version: VERSION) -> Specification:
        """Get complete specification for given version.

        Args:
            version: Game version (STABLE, BETA, ALPHA)

        Returns:
            Complete specification containing all .dat file specs
        """
        ...

    def get_file_spec(self, filename: str, version: VERSION) -> File:
        """Get specification for specific .dat file.

        Args:
            filename: Name of .dat file (e.g., 'ActiveSkills.dat')
            version: Game version

        Returns:
            File specification
        """
        ...


class SQLiteSpecRepository:
    """SQLite-based specification repository.

    Loads .dat file specifications from SQLite database instead of Python modules.
    This significantly reduces memory usage and import time compared to large
    Python files (27,000+ lines).

    Args:
        db_path: Path to SQLite database file

    Example:
        >>> repo = SQLiteSpecRepository(Path("data/specifications/stable.db"))
        >>> spec = repo.get_spec(VERSION.STABLE)
        >>> len(spec)  # Number of .dat files
        389
    """

    def __init__(self, db_path: Path):
        """Initialize repository.

        Args:
            db_path: Path to SQLite database file

        Raises:
            FileNotFoundError: If database file doesn't exist
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Specification database not found: {self.db_path}")

        self._conn: sqlite3.Connection | None = None
        logger.info("sqlite_spec_repository_initialized", db_path=str(db_path))

    @property
    def conn(self) -> sqlite3.Connection:
        """Lazy database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            logger.debug("sqlite_connection_established", db_path=str(self.db_path))
        return self._conn

    def get_spec(self, version: VERSION) -> Specification:
        """Load complete specification from database.

        Args:
            version: Game version (STABLE, BETA, ALPHA)

        Returns:
            Complete specification

        Example:
            >>> repo = SQLiteSpecRepository(Path("stable.db"))
            >>> spec = repo.get_spec(VERSION.STABLE)
            >>> 'ActiveSkills.dat' in spec
            True
        """
        version_str = version.name.lower()
        logger.info("loading_specification", version=version_str)

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT filename FROM files WHERE version = ? ORDER BY filename",
            (version_str,),
        )

        files = {}
        for row in cursor:
            filename = row["filename"]
            files[filename] = self.get_file_spec(filename, version)

        logger.info("specification_loaded", version=version_str, files_count=len(files))
        return Specification(files)

    def get_file_spec(self, filename: str, version: VERSION) -> File:
        """Load specification for specific .dat file.

        Args:
            filename: Name of .dat file (e.g., 'ActiveSkills.dat')
            version: Game version

        Returns:
            File specification

        Raises:
            ValueError: If file not found in database

        Example:
            >>> repo = SQLiteSpecRepository(Path("stable.db"))
            >>> file_spec = repo.get_file_spec("ActiveSkills.dat", VERSION.STABLE)
            >>> len(file_spec.fields)
            42
        """
        version_str = version.name.lower()

        cursor = self.conn.cursor()

        # Get file info
        cursor.execute(
            "SELECT id FROM files WHERE filename = ? AND version = ?",
            (filename, version_str),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"File {filename} not found for version {version_str}")

        file_id = row["id"]

        # Get fields
        cursor.execute(
            """
            SELECT name, type, key_field, key_id, key_offset, enum_name,
                   is_unique, file_path, file_ext, display, display_type, description
            FROM fields
            WHERE file_id = ?
            ORDER BY field_order
            """,
            (file_id,),
        )

        fields = []
        for field_row in cursor:
            field_kwargs = {
                "name": field_row["name"],
                "type": field_row["type"],
            }

            # Add optional fields if present
            if field_row["key_field"]:
                field_kwargs["key"] = field_row["key_field"]
            if field_row["key_id"]:
                field_kwargs["key_id"] = field_row["key_id"]
            if field_row["key_offset"]:
                field_kwargs["key_offset"] = field_row["key_offset"]
            if field_row["enum_name"]:
                field_kwargs["enum"] = field_row["enum_name"]
            if field_row["is_unique"]:
                field_kwargs["unique"] = bool(field_row["is_unique"])
            if field_row["file_path"]:
                field_kwargs["file_path"] = bool(field_row["file_path"])
            if field_row["file_ext"]:
                field_kwargs["file_ext"] = field_row["file_ext"]
            if field_row["display"]:
                field_kwargs["display"] = field_row["display"]
            if field_row["display_type"]:
                field_kwargs["display_type"] = field_row["display_type"]
            if field_row["description"]:
                field_kwargs["description"] = field_row["description"]

            fields.append(Field(**field_kwargs))

        # Get virtual fields
        cursor.execute(
            "SELECT name, fields, zip, description FROM virtual_fields WHERE file_id = ?",
            (file_id,),
        )

        virtual_fields = []
        for vf_row in cursor:
            vf_kwargs = {
                "name": vf_row["name"],
                "fields": json.loads(vf_row["fields"]),
                "zip": bool(vf_row["zip"]),
            }
            if vf_row["description"]:
                vf_kwargs["description"] = vf_row["description"]

            virtual_fields.append(VirtualField(**vf_kwargs))

        return File(
            fields=tuple(fields),
            virtual_fields=tuple(virtual_fields) if virtual_fields else None,
        )

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.debug("sqlite_connection_closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class CachedSpecRepository:
    """Caching wrapper for specification repositories.

    Wraps another repository and caches loaded specifications to avoid
    repeated database queries.

    Args:
        repository: Underlying specification repository

    Example:
        >>> sqlite_repo = SQLiteSpecRepository(Path("stable.db"))
        >>> cached_repo = CachedSpecRepository(sqlite_repo)
        >>> spec1 = cached_repo.get_spec(VERSION.STABLE)  # From DB
        >>> spec2 = cached_repo.get_spec(VERSION.STABLE)  # From cache
    """

    def __init__(self, repository: SpecificationProvider):
        self._repo = repository
        self._cache: dict[VERSION, Specification] = {}
        self._file_cache: dict[tuple[str, VERSION], File] = {}
        logger.debug("cached_spec_repository_initialized")

    def get_spec(self, version: VERSION) -> Specification:
        """Get specification with caching."""
        if version not in self._cache:
            logger.debug("cache_miss_spec", version=version.name)
            self._cache[version] = self._repo.get_spec(version)
        else:
            logger.debug("cache_hit_spec", version=version.name)
        return self._cache[version]

    def get_file_spec(self, filename: str, version: VERSION) -> File:
        """Get file specification with caching."""
        key = (filename, version)
        if key not in self._file_cache:
            logger.debug("cache_miss_file", filename=filename, version=version.name)
            self._file_cache[key] = self._repo.get_file_spec(filename, version)
        else:
            logger.debug("cache_hit_file", filename=filename, version=version.name)
        return self._file_cache[key]

    def clear_cache(self):
        """Clear all caches."""
        self._cache.clear()
        self._file_cache.clear()
        logger.info("cache_cleared")
