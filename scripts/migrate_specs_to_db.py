"""Migrate specifications from Python modules to SQLite database.

This script migrates .dat file specifications from large Python files
(27,000+ lines) to compact SQLite databases.

Usage:
    python scripts/migrate_specs_to_db.py

Output:
    - data/specifications/stable.db
    - data/specifications/beta.db
    - data/specifications/alpha.db
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

# Add PyPoE to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.specification import load
from PyPoE.shared.logging import configure_logging, get_logger

configure_logging(log_level="INFO")
logger = get_logger(__name__)


def create_database(db_path: Path):
    """Create database with schema.

    Args:
        db_path: Path to create database at
    """
    schema_path = Path(__file__).parent.parent / "data" / "specifications" / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    conn = sqlite3.connect(db_path)
    with open(schema_path, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

    logger.info("database_created", db_path=str(db_path))


def migrate_version(version: VERSION, output_db: Path):
    """Migrate one version to database.

    Args:
        version: Game version to migrate
        output_db: Output database path
    """
    logger.info("migration_started", version=version.name)

    # Load old specification from Python module
    logger.info("loading_python_specification", version=version.name)
    spec = load(version=version)
    logger.info(
        "python_specification_loaded",
        version=version.name,
        files_count=len(spec),
    )

    # Create database
    if output_db.exists():
        logger.warning("database_exists_overwriting", db_path=str(output_db))
        output_db.unlink()

    create_database(output_db)

    # Open connection
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()

    version_str = version.name.lower()
    files_migrated = 0
    fields_migrated = 0
    virtual_fields_migrated = 0

    # Insert files and fields
    for filename, file_spec in spec.items():
        # Insert file
        cursor.execute(
            "INSERT INTO files (filename, version) VALUES (?, ?)",
            (filename, version_str),
        )
        file_id = cursor.lastrowid
        files_migrated += 1

        # Insert fields
        for order, (field_name, field) in enumerate(file_spec.fields.items()):
            cursor.execute(
                """
                INSERT INTO fields
                (file_id, name, type, key_field, key_id, key_offset,
                 enum_name, is_unique, file_path, file_ext, display,
                 display_type, description, field_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    field.name,
                    field.type,
                    field.key if hasattr(field, "key") else None,
                    field.key_id if hasattr(field, "key_id") else None,
                    field.key_offset if hasattr(field, "key_offset") else 0,
                    field.enum if hasattr(field, "enum") else None,
                    1 if hasattr(field, "unique") and field.unique else 0,
                    1 if hasattr(field, "file_path") and field.file_path else 0,
                    field.file_ext if hasattr(field, "file_ext") else None,
                    field.display if hasattr(field, "display") else None,
                    field.display_type if hasattr(field, "display_type") else None,
                    field.description if hasattr(field, "description") else None,
                    order,
                ),
            )
            fields_migrated += 1

        # Insert virtual fields
        if hasattr(file_spec, "virtual_fields") and file_spec.virtual_fields:
            for vf_name, vf in file_spec.virtual_fields.items():
                cursor.execute(
                    """
                    INSERT INTO virtual_fields (file_id, name, fields, zip, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        file_id,
                        vf.name,
                        json.dumps(list(vf.fields)),
                        1 if vf.zip else 0,
                        vf.description if hasattr(vf, "description") else None,
                    ),
                )
                virtual_fields_migrated += 1

        # Commit every 10 files for progress
        if files_migrated % 10 == 0:
            conn.commit()
            logger.info(
                "migration_progress",
                version=version_str,
                files=files_migrated,
                fields=fields_migrated,
            )

    conn.commit()
    conn.close()

    logger.info(
        "migration_completed",
        version=version_str,
        db_path=str(output_db),
        files=files_migrated,
        fields=fields_migrated,
        virtual_fields=virtual_fields_migrated,
        size_mb=round(output_db.stat().st_size / 1024 / 1024, 2),
    )


def main():
    """Main migration script."""
    logger.info("migration_script_started")

    output_dir = Path("data/specifications")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Migrate all versions
    versions_to_migrate = [
        (VERSION.STABLE, "stable.db"),
        (VERSION.BETA, "beta.db"),
        (VERSION.ALPHA, "alpha.db"),
    ]

    for version, db_name in versions_to_migrate:
        try:
            migrate_version(version, output_dir / db_name)
        except Exception as e:
            logger.error(
                "migration_failed",
                version=version.name,
                error=str(e),
                exc_info=True,
            )
            raise

    logger.info(
        "all_migrations_completed",
        output_dir=str(output_dir.absolute()),
    )

    print("\n" + "=" * 80)
    print("[OK] All specifications migrated successfully!")
    print(f"Location: {output_dir.absolute()}")
    print("=" * 80)

    # Show file sizes
    print("\nFile sizes:")
    for version, db_name in versions_to_migrate:
        db_path = output_dir / db_name
        if db_path.exists():
            size_mb = db_path.stat().st_size / 1024 / 1024
            print(f"  - {db_name}: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
