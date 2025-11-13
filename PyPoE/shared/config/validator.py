"""
Additional validators

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/shared/config/validator.py                                 |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Additional validators for configobj and validate.

Validator Function Generators
-------------------------------------------------------------------------------

.. autoclass:: IntEnumValidator

  .. automethod:: __call__

Validator Functions
-------------------------------------------------------------------------------

.. autofunction:: is_file

.. autofunction:: is_directory

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import os
from enum import IntEnum
from typing import Any

# 3rd Party
from validate import ValidateError, is_boolean  # type: ignore[import-untyped]

# =============================================================================
# Globals
# =============================================================================

__all__ = ["IntEnumValidator", "is_directory", "is_file", "functions"]


# =============================================================================
# Classes
# =============================================================================


class IntEnumValidator:
    """
    Validator for IntEnum classes.

    Creates a dynamic validator function for configobj that validates
    values against an IntEnum class.
    """

    def __init__(self, enum: type[IntEnum], default: IntEnum | int | None = None) -> None:
        """
        Initialize IntEnum validator.

        Args:
            enum: Base enum class for this validator
            default: Default attribute of the enum (IntEnum instance, int, or None)

        Raises:
            TypeError: If enum is not an IntEnum subclass
            TypeError: If default parameter is of invalid type
        """
        if not issubclass(enum, IntEnum):
            raise TypeError("enum must be an IntEnum subclass")
        self._enum = enum

        if default is None:
            self._default = None
        elif isinstance(default, enum):
            self._default = default
        elif isinstance(default, int):
            self._default = enum(int)
        else:
            raise TypeError("default must be a subtype of default")
        self._default = None

    def _get_enum_from_val(self, value: int | str) -> IntEnum:
        """
        Get IntEnum instance from value.

        Args:
            value: The value to pass to the enum class

        Returns:
            IntEnum instance based on the class

        Raises:
            ValidateError: If the value isn't a member of the IntEnum class
        """
        try:
            return self._enum(value)
        except ValueError as e:
            raise ValidateError(
                f"{self._enum.__name__} The value is not accepted by the enum."
            ) from e

    def __call__(self, value: int | str | IntEnum | None) -> IntEnum | None:
        """
        Validate value against IntEnum.

        Args:
            value: The value to validate (int, str, IntEnum instance, or None)

        Returns:
            IntEnum instance if successfully validated, or default if value is None

        Raises:
            ValidateError: If the value can't be validated
        """
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                # If the value was stored, it will be stored as
                # MyEnum.attribute
                #
                # This will get rid of the class portion for casting if present
                if value.startswith(self._enum.__name__ + "."):
                    value = value[len(self._enum.__name__) + 1 :]
                    try:
                        value = getattr(self._enum, value)
                    except AttributeError as e:
                        raise ValidateError(
                            f"The value is neither an integer or a valid {self._enum.__name__} "
                            "attribute"
                        ) from e
            else:
                value = self._get_enum_from_val(value)
        elif isinstance(value, int):
            value = self._get_enum_from_val(value)
        elif value is None:
            return self._default
        else:
            raise ValidateError("Invalid type")

        return value


# =============================================================================
# Functions
# =============================================================================


def _exists(value: str, exists: bool) -> None:
    """
    Check if path exists (internal helper).

    Args:
        value: Path to check
        exists: Whether path must exist

    Raises:
        ValidateError: If path doesn't exist when required
    """
    if not isinstance(exists, bool):
        # Raises VdtTypeError on fail
        exists = is_boolean(exists)
    if exists and not os.path.exists(value):
        raise ValidateError(f'Path "{value}" does not exist.')


def is_file(value: str, *args: Any, exists: bool = True, allow_empty: bool = False, **kwargs: Any) -> str:
    """
    Check whether the value is a valid file path.

    Optionally checks whether the file exists.

    Args:
        value: The value to validate
        *args: Additional positional arguments (unused)
        exists: Whether the file is required to exist to pass validation (default: True)
        allow_empty: Whether empty strings are allowed (default: False)
        **kwargs: Additional keyword arguments (unused)

    Returns:
        Validated file path string

    Raises:
        ValidateError: If the value can't be validated or is not a file
    """
    if allow_empty and value == "":
        return ""
    else:
        _exists(value, exists)
        if not os.path.isfile(value):
            raise ValidateError(f'"{value}" is not a file.')
        return value


def is_directory(value: str, *args: Any, exists: bool = True, allow_empty: bool = False, **kwargs: Any) -> str:
    """
    Check whether the value is a valid directory path.

    Optionally checks whether the directory exists.

    Args:
        value: The value to validate
        *args: Additional positional arguments (unused)
        exists: Whether the directory is required to exist to pass validation (default: True)
        allow_empty: Whether empty strings are allowed (default: False)
        **kwargs: Additional keyword arguments (unused)

    Returns:
        Validated directory path string

    Raises:
        ValidateError: If the value can't be validated or is not a directory
    """
    if allow_empty and value == "":
        return ""
    else:
        _exists(value, exists)
        if not os.path.isdir(value):
            raise ValidateError(f'"{value}" is not a directory.')
        return value


# =============================================================================
# Globals
# =============================================================================

functions = {
    "is_file": is_file,
    "is_directory": is_directory,
}
