"""
File utilities - centralized file operations with error handling.

This module provides reusable utilities for file operations throughout the project,
eliminating code duplication and providing consistent error handling.
"""

from collections.abc import Generator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)


class FileReadError(Exception):
    """Raised when file reading fails."""

    pass


class FileWriteError(Exception):
    """Raised when file writing fails."""

    pass


def read_file(file_path: str | Path) -> bytes:
    """
    Read file contents safely with centralized error handling.

    Args:
        file_path: Path to file to read

    Returns:
        File contents as bytes

    Raises:
        FileNotFoundError: If file doesn't exist
        FileReadError: If reading fails
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, "rb") as f:
            data = f.read()
            logger.debug(f"Successfully read {len(data)} bytes from {file_path}")
            return data
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise FileReadError(f"Permission denied: {file_path}") from e
    except OSError as e:
        logger.error(f"OS error reading file: {file_path} - {e}")
        raise FileReadError(f"Failed to read {file_path}: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error reading file: {file_path} - {e}")
        raise FileReadError(f"Unexpected error reading {file_path}: {e}") from e


def write_file(file_path: str | Path, data: bytes) -> None:
    """
    Write file contents safely with centralized error handling.

    Args:
        file_path: Path to file to write
        data: Binary data to write

    Raises:
        FileWriteError: If writing fails
    """
    file_path = Path(file_path)

    try:
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(data)
            logger.debug(f"Successfully wrote {len(data)} bytes to {file_path}")
    except PermissionError as e:
        logger.error(f"Permission denied writing file: {file_path}")
        raise FileWriteError(f"Permission denied: {file_path}") from e
    except OSError as e:
        logger.error(f"OS error writing file: {file_path} - {e}")
        raise FileWriteError(f"Failed to write {file_path}: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error writing file: {file_path} - {e}")
        raise FileWriteError(f"Unexpected error writing {file_path}: {e}") from e


def ensure_directory(directory_path: str | Path) -> Path:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        directory_path: Path to directory

    Returns:
        Path object for the directory

    Raises:
        FileWriteError: If directory creation fails
    """
    directory_path = Path(directory_path)

    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {directory_path}")
        return directory_path
    except PermissionError as e:
        logger.error(f"Permission denied creating directory: {directory_path}")
        raise FileWriteError(f"Permission denied: {directory_path}") from e
    except OSError as e:
        logger.error(f"OS error creating directory: {directory_path} - {e}")
        raise FileWriteError(f"Failed to create directory {directory_path}: {e}") from e


def file_exists(file_path: str | Path) -> bool:
    """
    Check if file exists.

    Args:
        file_path: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return Path(file_path).is_file()


def directory_exists(directory_path: str | Path) -> bool:
    """
    Check if directory exists.

    Args:
        directory_path: Path to check

    Returns:
        True if directory exists, False otherwise
    """
    return Path(directory_path).is_dir()


def get_file_size(file_path: str | Path) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path.stat().st_size


def create_buffer_from_file(file_path: str | Path) -> BytesIO:
    """
    Create BytesIO buffer from file contents.

    Args:
        file_path: Path to file

    Returns:
        BytesIO buffer containing file data

    Raises:
        FileNotFoundError: If file doesn't exist
        FileReadError: If reading fails
    """
    data = read_file(file_path)
    return BytesIO(data)


def create_buffer_from_bytes(data: bytes) -> BytesIO:
    """
    Create BytesIO buffer from bytes.

    Args:
        data: Binary data

    Returns:
        BytesIO buffer containing data
    """
    return BytesIO(data)


@contextmanager
def safe_open_read(
    file_path: str | Path, mode: str = "rb"
) -> Generator[BinaryIO, None, None]:
    """
    Context manager for safely opening files for reading.

    Args:
        file_path: Path to file
        mode: Open mode (default: "rb")

    Yields:
        File handle

    Raises:
        FileNotFoundError: If file doesn't exist
        FileReadError: If opening/reading fails
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, mode) as f:
            yield f  # type: ignore[misc]
    except PermissionError as e:
        logger.error(f"Permission denied: {file_path}")
        raise FileReadError(f"Permission denied: {file_path}") from e
    except OSError as e:
        logger.error(f"OS error: {file_path} - {e}")
        raise FileReadError(f"Failed to open {file_path}: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error: {file_path} - {e}")
        raise FileReadError(f"Unexpected error with {file_path}: {e}") from e


@contextmanager
def safe_open_write(
    file_path: str | Path, mode: str = "wb"
) -> Generator[BinaryIO, None, None]:
    """
    Context manager for safely opening files for writing.

    Args:
        file_path: Path to file
        mode: Open mode (default: "wb")

    Yields:
        File handle

    Raises:
        FileWriteError: If opening/writing fails
    """
    file_path = Path(file_path)

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, mode) as f:
            yield f  # type: ignore[misc]
    except PermissionError as e:
        logger.error(f"Permission denied: {file_path}")
        raise FileWriteError(f"Permission denied: {file_path}") from e
    except OSError as e:
        logger.error(f"OS error: {file_path} - {e}")
        raise FileWriteError(f"Failed to open {file_path}: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error: {file_path} - {e}")
        raise FileWriteError(f"Unexpected error with {file_path}: {e}") from e


def normalize_path(path: str | Path) -> str:
    """
    Normalize file path (resolve, absolute, forward slashes).

    Args:
        path: Path to normalize

    Returns:
        Normalized path string
    """
    return str(Path(path).resolve()).replace("\\", "/")


def get_file_extension(file_path: str | Path) -> str:
    """
    Get file extension (lowercase, without dot).

    Args:
        file_path: Path to file

    Returns:
        File extension (e.g., "dat", "ggpk")
    """
    return Path(file_path).suffix.lstrip(".").lower()


def join_paths(*parts: str | Path) -> str:
    """
    Join path parts safely.

    Args:
        *parts: Path parts to join

    Returns:
        Joined path
    """
    return str(Path(*[str(p) for p in parts]))

