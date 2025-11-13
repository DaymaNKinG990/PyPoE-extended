"""
Shared Python code

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/shared/__init__.py                                         |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================



Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python

# 3rd-party

# self

# =============================================================================
# Globals
# =============================================================================

__all__ = []

# =============================================================================
# Classes
# =============================================================================


class InheritedDocStringsMeta(type):
    """
    Metaclass for inheriting docstrings from parent classes.

    Automatically inherits docstrings from parent classes if a class or method
    doesn't have its own docstring. This is useful for reducing duplication
    when subclasses don't override documentation.

    Example:
        >>> class Base:
        ...     def method(self):
        ...         '''Base docstring'''
        ...
        >>> class Child(Base, metaclass=InheritedDocStringsMeta):
        ...     def method(self):
        ...         pass  # Will inherit docstring from Base
    """

    def __new__(cls, name: str, args: tuple, attrs: dict) -> type:
        """
        Create new class with inherited docstrings.

        Args:
            name: Name of the class
            args: Base classes tuple
            attrs: Class attributes dictionary

        Returns:
            New class with inherited docstrings
        """
        if not ("__doc__" in attrs and attrs["__doc__"]):
            for mro in cls.mro(cls):
                docstring = mro.__doc__
                if docstring is not None:
                    cls.__doc__ = docstring
                    # attrs['__doc__'] = docstring
                    break
        for attr, attribute in attrs.items():
            if attribute.__doc__:
                continue

            for mro in cls.mro(cls):
                if not hasattr(mro, attr):
                    break
                docstring = getattr(mro, attr).__doc__
                if docstring is not None:
                    attribute.__doc__ = docstring
                    break

        return type.__new__(cls, name, args, attrs)


# =============================================================================
# Functions
# =============================================================================
