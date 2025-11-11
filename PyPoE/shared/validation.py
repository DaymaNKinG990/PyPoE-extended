"""
Validation utilities - centralized data and file validation.

This module provides reusable validation functions to ensure data integrity
and eliminate code duplication.
"""

import os
from pathlib import Path
from typing import Any

from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_file_exists(file_path: str | Path, raise_error: bool = True) -> bool:
    """
    Validate that file exists.

    Args:
        file_path: Path to file
        raise_error: Whether to raise exception on failure

    Returns:
        True if file exists

    Raises:
        ValidationError: If file doesn't exist and raise_error is True
    """
    path = Path(file_path)
    exists = path.is_file()

    if not exists:
        msg = f"File does not exist: {path}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return exists


def validate_directory_exists(directory_path: str | Path, raise_error: bool = True) -> bool:
    """
    Validate that directory exists.

    Args:
        directory_path: Path to directory
        raise_error: Whether to raise exception on failure

    Returns:
        True if directory exists

    Raises:
        ValidationError: If directory doesn't exist and raise_error is True
    """
    path = Path(directory_path)
    exists = path.is_dir()

    if not exists:
        msg = f"Directory does not exist: {path}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return exists


def validate_file_extension(
    file_path: str | Path, expected_extensions: list[str] | str, raise_error: bool = True
) -> bool:
    """
    Validate file extension.

    Args:
        file_path: Path to file
        expected_extensions: Expected extension(s) (with or without dot, case-insensitive)
        raise_error: Whether to raise exception on failure

    Returns:
        True if extension matches

    Raises:
        ValidationError: If extension doesn't match and raise_error is True

    Example:
        validate_file_extension("file.dat", ".dat")
        validate_file_extension("file.ggpk", ["ggpk", ".ggpk"])
    """
    path = Path(file_path)
    actual_ext = path.suffix.lower()

    # Normalize expected extensions
    if isinstance(expected_extensions, str):
        expected_extensions = [expected_extensions]

    expected_extensions = [
        ext if ext.startswith(".") else f".{ext}" for ext in expected_extensions
    ]
    expected_extensions = [ext.lower() for ext in expected_extensions]

    valid = actual_ext in expected_extensions

    if not valid:
        msg = (
            f"Invalid file extension: {actual_ext} "
            f"(expected: {', '.join(expected_extensions)}) for {path}"
        )
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return valid


def validate_readable(file_path: str | Path, raise_error: bool = True) -> bool:
    """
    Validate that file is readable.

    Args:
        file_path: Path to file
        raise_error: Whether to raise exception on failure

    Returns:
        True if file is readable

    Raises:
        ValidationError: If file is not readable and raise_error is True
    """
    path = Path(file_path)

    if not path.exists():
        msg = f"File does not exist: {path}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)
        return False

    readable = os.access(path, os.R_OK)

    if not readable:
        msg = f"File is not readable: {path}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return readable


def validate_writable(directory_path: str | Path, raise_error: bool = True) -> bool:
    """
    Validate that directory is writable.

    Args:
        directory_path: Path to directory
        raise_error: Whether to raise exception on failure

    Returns:
        True if directory is writable

    Raises:
        ValidationError: If directory is not writable and raise_error is True
    """
    path = Path(directory_path)

    if not path.exists():
        msg = f"Directory does not exist: {path}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)
        return False

    writable = os.access(path, os.W_OK)

    if not writable:
        msg = f"Directory is not writable: {path}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return writable


def validate_not_empty(value: Any, name: str = "value", raise_error: bool = True) -> bool:
    """
    Validate that value is not empty.

    Args:
        value: Value to validate
        name: Name of the value for error message
        raise_error: Whether to raise exception on failure

    Returns:
        True if value is not empty

    Raises:
        ValidationError: If value is empty and raise_error is True
    """
    is_empty = value is None or (hasattr(value, "__len__") and len(value) == 0)

    if is_empty:
        msg = f"{name} cannot be empty"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return not is_empty


def validate_type(
    value: Any, expected_type: type | tuple[type, ...], name: str = "value", raise_error: bool = True
) -> bool:
    """
    Validate value type.

    Args:
        value: Value to validate
        expected_type: Expected type or tuple of types
        name: Name of the value for error message
        raise_error: Whether to raise exception on failure

    Returns:
        True if type matches

    Raises:
        ValidationError: If type doesn't match and raise_error is True

    Example:
        validate_type(x, int)
        validate_type(x, (int, float))
    """
    valid = isinstance(value, expected_type)

    if not valid:
        if isinstance(expected_type, tuple):
            type_names = " or ".join(t.__name__ for t in expected_type)
        else:
            type_names = expected_type.__name__

        msg = f"{name} must be {type_names}, got {type(value).__name__}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return valid


def validate_in_range(
    value: int | float,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    name: str = "value",
    raise_error: bool = True,
) -> bool:
    """
    Validate that value is in range.

    Args:
        value: Value to validate
        min_value: Minimum value (inclusive), None for no limit
        max_value: Maximum value (inclusive), None for no limit
        name: Name of the value for error message
        raise_error: Whether to raise exception on failure

    Returns:
        True if value is in range

    Raises:
        ValidationError: If value is out of range and raise_error is True
    """
    valid = True
    msg = ""

    if min_value is not None and value < min_value:
        valid = False
        msg = f"{name} must be >= {min_value}, got {value}"
    elif max_value is not None and value > max_value:
        valid = False
        msg = f"{name} must be <= {max_value}, got {value}"

    if not valid:
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return valid


def validate_in_list(
    value: Any, valid_values: list[Any], name: str = "value", raise_error: bool = True
) -> bool:
    """
    Validate that value is in list of valid values.

    Args:
        value: Value to validate
        valid_values: List of valid values
        name: Name of the value for error message
        raise_error: Whether to raise exception on failure

    Returns:
        True if value is in list

    Raises:
        ValidationError: If value is not in list and raise_error is True
    """
    valid = value in valid_values

    if not valid:
        msg = f"{name} must be one of {valid_values}, got {value}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)

    return valid


def validate_dict_keys(
    data: dict,
    required_keys: list[str],
    optional_keys: list[str] | None = None,
    raise_error: bool = True,
) -> bool:
    """
    Validate dictionary keys.

    Args:
        data: Dictionary to validate
        required_keys: List of required keys
        optional_keys: List of optional keys (None = allow any)
        raise_error: Whether to raise exception on failure

    Returns:
        True if all required keys present and no unexpected keys

    Raises:
        ValidationError: If validation fails and raise_error is True
    """
    missing_keys = set(required_keys) - set(data.keys())
    if missing_keys:
        msg = f"Missing required keys: {missing_keys}"
        logger.error(msg)
        if raise_error:
            raise ValidationError(msg)
        return False

    if optional_keys is not None:
        allowed_keys = set(required_keys) | set(optional_keys)
        unexpected_keys = set(data.keys()) - allowed_keys
        if unexpected_keys:
            msg = f"Unexpected keys: {unexpected_keys}"
            logger.error(msg)
            if raise_error:
                raise ValidationError(msg)
            return False

    return True


def validate_path_safe(path: str | Path, base_path: str | Path | None = None, raise_error: bool = True) -> bool:
    """
    Validate that path is safe (no directory traversal attacks).

    Args:
        path: Path to validate
        base_path: Base path to restrict to (None = no restriction)
        raise_error: Whether to raise exception on failure

    Returns:
        True if path is safe

    Raises:
        ValidationError: If path is unsafe and raise_error is True

    Example:
        validate_path_safe("../../etc/passwd")  # False
        validate_path_safe("data/file.dat", "data/")  # True
    """
    path = Path(path).resolve()

    # Check for absolute paths trying to escape
    if base_path is not None:
        base_path = Path(base_path).resolve()
        try:
            path.relative_to(base_path)
        except ValueError:
            msg = f"Path {path} is outside base path {base_path}"
            logger.error(msg)
            if raise_error:
                raise ValidationError(msg) from None
            return False

    # Check for suspicious patterns
    path_str = str(path)
    suspicious_patterns = ["../", "..\\"]
    for pattern in suspicious_patterns:
        if pattern in path_str:
            msg = f"Path contains suspicious pattern: {path}"
            logger.error(msg)
            if raise_error:
                raise ValidationError(msg)
            return False

    return True

