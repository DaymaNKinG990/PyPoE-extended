"""
special containers

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/shared/containers.py                                       |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

special containers

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from collections.abc import Iterable
from typing import Any

# =============================================================================
# Globals
# =============================================================================

__all__ = ["Record", "TypedContainerMeta", "TypedContainerMixin", "TypedList"]

# =============================================================================
# Classes
# =============================================================================


class Record:
    """
    Base class for record-like objects with __slots__.

    Provides string representation and equality comparison based on
    __slots__ attributes. Subclasses should define __slots__ with
    attribute names.

    Example:
        >>> class Point(Record):
        ...     __slots__ = ("x", "y")
        ...     def __init__(self, x, y):
        ...         self.x = x
        ...         self.y = y
        >>> p = Point(1, 2)
        >>> str(p)
        "Point(x=1, y=2)"
    """

    __slots__: tuple[str, ...] = ()

    def __str__(self) -> str:
        """
        Return string representation.

        Returns:
            String representation using repr()
        """
        return repr(self)

    def __repr__(self) -> str:
        """
        Return detailed string representation.

        Returns:
            String in format: ClassName(attr1=val1, attr2=val2, ...)
        """
        out = []
        for attr in self.__slots__:
            out.append(f"{attr}={repr(getattr(self, attr))}")

        return "{}({})".format(self.__class__.__name__, ", ".join(out))

    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another Record.

        Args:
            other: Other object to compare

        Returns:
            True if all __slots__ attributes are equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return object.__eq__(self, other)

        return all(getattr(self, attr) == getattr(other, attr) for attr in self.__slots__)

    def __ne__(self, other: Any) -> bool:
        """
        Check inequality with another Record.

        Args:
            other: Other object to compare

        Returns:
            True if any __slots__ attributes differ, False otherwise
        """
        if not isinstance(other, self.__class__):
            return object.__eq__(self, other)

        return all(getattr(self, attr) != getattr(other, attr) for attr in self.__slots__)


class TypedContainerMeta(type):
    """
    Metaclass for typed containers.

    Validates that ACCEPTED_TYPES is defined and converts single types
    to tuples for consistent handling.

    Raises:
        ValueError: If ACCEPTED_TYPES is missing, None, or invalid
    """

    def __new__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        """
        Create new typed container class.

        Args:
            name: Class name
            bases: Base classes
            attrs: Class attributes

        Returns:
            New class with validated ACCEPTED_TYPES

        Raises:
            ValueError: If ACCEPTED_TYPES is missing, None, or invalid
        """
        if "ACCEPTED_TYPES" not in attrs:
            raise ValueError("ACCEPTED_TYPES is required.")

        if attrs["ACCEPTED_TYPES"] is None:
            raise ValueError("ACCEPTED_TYPES must not be None.")

        if isinstance(attrs["ACCEPTED_TYPES"], type):
            attrs["ACCEPTED_TYPES"] = (attrs["ACCEPTED_TYPES"],)
        elif isinstance(attrs["ACCEPTED_TYPES"], Iterable):
            for t in attrs["ACCEPTED_TYPES"]:
                if not isinstance(t, type):
                    raise ValueError("Every type in ACCEPTED_TYPES Iterable must be a type")
        else:
            raise ValueError("ACCEPTED_TYPES must be a type or Iterable of types")

        return type.__new__(cls, name, bases, attrs)


class TypedContainerMixin:
    """
    Mixin for containers that only accept specific types.

    Provides validation methods to ensure only acceptable types
    are added to the container. Requires ACCEPTED_TYPES to be defined
    (typically via TypedContainerMeta).

    Attributes:
        ACCEPTED_TYPES: Tuple of accepted types (set by metaclass)
    """

    ACCEPTED_TYPES: tuple[type, ...] | None = None

    def _is_cls(self, obj: Any) -> None:
        """
        Validate that object is same class instance.

        Args:
            obj: Object to validate

        Raises:
            TypeError: If object is not same class instance
        """
        if not isinstance(obj, self.__class__):
            raise TypeError(
                f'"{self.__class__.__name__}" instance can only be added to another "{self.__class__.__name__}" instance.'
            )

    def _is_acceptable(self, obj: Any) -> None:
        """
        Validate that object is of accepted type.

        Args:
            obj: Object to validate

        Raises:
            TypeError: If object is not of accepted type
        """
        if not isinstance(obj, self.ACCEPTED_TYPES):  # type: ignore[arg-type]
            raise TypeError(
                '"{}" instance only accepts "{}" instances.'.format(
                    self.__class__.__name__,
                    ", ".join([t.__name__ for t in self.ACCEPTED_TYPES]),  # type: ignore[attr-defined]
                )
            )


class TypedList(list, TypedContainerMixin):
    """
    List that only accepts specific types.

    Extends list with type checking. Only items of ACCEPTED_TYPES
    can be added. Requires ACCEPTED_TYPES to be defined via metaclass.

    Example:
        >>> class IntList(TypedList, metaclass=TypedContainerMeta):
        ...     ACCEPTED_TYPES = int
        >>> lst = IntList()
        >>> lst.append(1)  # OK
        >>> lst.append("str")  # Raises TypeError
    """

    def __add__(self, other: Any) -> Any:
        """
        Concatenate with another TypedList of same type.

        Args:
            other: Another TypedList instance

        Returns:
            New TypedList with concatenated items

        Raises:
            TypeError: If other is not same class instance
        """
        self._is_cls(other)
        return list.__add__(self, other)

    def __iadd__(self, other: Any) -> Any:
        """
        In-place concatenation with another TypedList.

        Args:
            other: Another TypedList instance

        Returns:
            Self with items added

        Raises:
            TypeError: If other is not same class instance
        """
        self._is_cls(other)
        return list.__iadd__(self, other)

    def __setitem__(self, key: int | slice, value: Any) -> None:
        """
        Set item at index with type checking.

        Args:
            key: Index or slice
            value: Value to set (must be of accepted type)

        Raises:
            TypeError: If value is not of accepted type
        """
        self._is_acceptable(value)
        list.__setitem__(self, key, value)

    def append(self, p_object: Any) -> None:
        """
        Append item to list with type checking.

        Args:
            p_object: Item to append (must be of accepted type)

        Raises:
            TypeError: If item is not of accepted type
        """
        self._is_acceptable(p_object)
        list.append(self, p_object)

    def extend(self, iterable: Iterable[Any]) -> None:
        """
        Extend list with items from iterable with type checking.

        Args:
            iterable: Iterable of items (all must be of accepted type)

        Raises:
            TypeError: If any item is not of accepted type
        """
        for item in iterable:
            self._is_acceptable(item)
        list.extend(self, iterable)

    def insert(self, index: int, p_object: Any) -> None:
        """
        Insert item at index with type checking.

        Args:
            index: Index to insert at
            p_object: Item to insert (must be of accepted type)

        Raises:
            TypeError: If item is not of accepted type
        """
        self._is_acceptable(p_object)
        list.insert(self, index, p_object)
