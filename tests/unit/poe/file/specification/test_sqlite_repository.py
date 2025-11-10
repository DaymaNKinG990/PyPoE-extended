"""Unit tests for SQLiteSpecRepository.

These tests verify that specifications can be loaded from SQLite database
instead of Python modules.
"""

import pytest
import sqlite3
import json
from pathlib import Path
from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.specification.repository import (
    SQLiteSpecRepository,
    CachedSpecRepository,
)
from PyPoE.poe.file.specification.fields import Field, File, Specification, VirtualField


@pytest.fixture
def temp_spec_db(tmp_path):
    """Create a temporary specification database for testing."""
    db_path = tmp_path / "test_spec.db"

    # Create database with schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(filename, version)
        )
    """)

    cursor.execute("""
        CREATE TABLE fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            key_field TEXT,
            key_id TEXT,
            key_offset INTEGER DEFAULT 0,
            enum_name TEXT,
            is_unique BOOLEAN DEFAULT 0,
            file_path BOOLEAN DEFAULT 0,
            file_ext TEXT,
            display TEXT,
            display_type TEXT,
            description TEXT,
            field_order INTEGER NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE virtual_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            fields TEXT NOT NULL,
            zip BOOLEAN DEFAULT 0,
            description TEXT,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    # Insert test data
    cursor.execute(
        "INSERT INTO files (filename, version) VALUES (?, ?)",
        ("TestFile.dat", "stable"),
    )
    file_id = cursor.lastrowid

    # Insert fields
    cursor.execute(
        """
        INSERT INTO fields
        (file_id, name, type, key_field, key_id, is_unique, field_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (file_id, "Id", "ref|string", None, None, 1, 0),
    )

    cursor.execute(
        """
        INSERT INTO fields
        (file_id, name, type, field_order)
        VALUES (?, ?, ?, ?)
        """,
        (file_id, "Value", "int", 1),
    )

    # Insert virtual field
    cursor.execute(
        """
        INSERT INTO virtual_fields (file_id, name, fields, zip)
        VALUES (?, ?, ?, ?)
        """,
        (file_id, "Combined", json.dumps(["Id", "Value"]), 0),
    )

    conn.commit()
    conn.close()

    return db_path


def test_repository_initialization(temp_spec_db):
    """Test that repository can be initialized with database path."""
    repo = SQLiteSpecRepository(temp_spec_db)
    assert repo.db_path == temp_spec_db


def test_repository_initialization_nonexistent_file(tmp_path):
    """Test that initialization fails with non-existent database."""
    fake_path = tmp_path / "nonexistent.db"
    with pytest.raises(FileNotFoundError):
        SQLiteSpecRepository(fake_path)


def test_get_file_spec(temp_spec_db):
    """Test loading a single file specification."""
    repo = SQLiteSpecRepository(temp_spec_db)
    file_spec = repo.get_file_spec("TestFile.dat", VERSION.STABLE)

    assert isinstance(file_spec, File)
    assert len(file_spec.fields) == 2
    assert "Id" in file_spec.fields
    assert "Value" in file_spec.fields


def test_get_file_spec_fields(temp_spec_db):
    """Test that fields are loaded correctly."""
    repo = SQLiteSpecRepository(temp_spec_db)
    file_spec = repo.get_file_spec("TestFile.dat", VERSION.STABLE)

    id_field = file_spec.fields["Id"]
    assert id_field.name == "Id"
    assert id_field.type == "ref|string"
    assert id_field.unique is True

    value_field = file_spec.fields["Value"]
    assert value_field.name == "Value"
    assert value_field.type == "int"


def test_get_file_spec_virtual_fields(temp_spec_db):
    """Test that virtual fields are loaded correctly."""
    repo = SQLiteSpecRepository(temp_spec_db)
    file_spec = repo.get_file_spec("TestFile.dat", VERSION.STABLE)

    assert len(file_spec.virtual_fields) == 1
    assert "Combined" in file_spec.virtual_fields

    combined = file_spec.virtual_fields["Combined"]
    assert combined.name == "Combined"
    assert combined.fields == ["Id", "Value"]
    assert combined.zip is False


def test_get_file_spec_nonexistent(temp_spec_db):
    """Test that getting non-existent file raises error."""
    repo = SQLiteSpecRepository(temp_spec_db)
    with pytest.raises(ValueError):
        repo.get_file_spec("NonExistent.dat", VERSION.STABLE)


def test_get_spec(temp_spec_db):
    """Test loading complete specification."""
    repo = SQLiteSpecRepository(temp_spec_db)
    spec = repo.get_spec(VERSION.STABLE)

    assert isinstance(spec, Specification)
    assert "TestFile.dat" in spec
    assert isinstance(spec["TestFile.dat"], File)


def test_repository_context_manager(temp_spec_db):
    """Test that repository works as context manager."""
    with SQLiteSpecRepository(temp_spec_db) as repo:
        file_spec = repo.get_file_spec("TestFile.dat", VERSION.STABLE)
        assert isinstance(file_spec, File)


def test_cached_repository():
    """Test that caching repository works."""
    # Mock repository for testing
    class MockRepo:
        def __init__(self):
            self.get_spec_calls = 0
            self.get_file_spec_calls = 0

        def get_spec(self, version):
            self.get_spec_calls += 1
            return Specification({"Test.dat": File()})

        def get_file_spec(self, filename, version):
            self.get_file_spec_calls += 1
            return File()

    mock_repo = MockRepo()
    cached = CachedSpecRepository(mock_repo)

    # First call should hit the repository
    spec1 = cached.get_spec(VERSION.STABLE)
    assert mock_repo.get_spec_calls == 1

    # Second call should use cache
    spec2 = cached.get_spec(VERSION.STABLE)
    assert mock_repo.get_spec_calls == 1  # No additional calls

    # File spec caching
    file1 = cached.get_file_spec("Test.dat", VERSION.STABLE)
    assert mock_repo.get_file_spec_calls == 1

    file2 = cached.get_file_spec("Test.dat", VERSION.STABLE)
    assert mock_repo.get_file_spec_calls == 1  # Cached


def test_cached_repository_clear_cache():
    """Test that cache can be cleared."""
    class MockRepo:
        def __init__(self):
            self.calls = 0

        def get_spec(self, version):
            self.calls += 1
            return Specification({})

        def get_file_spec(self, filename, version):
            return File()

    mock_repo = MockRepo()
    cached = CachedSpecRepository(mock_repo)

    cached.get_spec(VERSION.STABLE)
    assert mock_repo.calls == 1

    cached.clear_cache()

    cached.get_spec(VERSION.STABLE)
    assert mock_repo.calls == 2  # Cache was cleared

