"""
Shared Mixin Classes

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/shared/mixins.py                                           |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Shared Mixin classes.

Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

Classes
-------------------------------------------------------------------------------

.. autoclass:: ReprMixin

"""

# =============================================================================
# Imports
# =============================================================================

# Python
import inspect
from collections import OrderedDict
from typing import Any

# 3rd-party

# self

# =============================================================================
# Globals
# =============================================================================

__all__ = ["ReprMixin"]

# =============================================================================
# Classes
# =============================================================================


class ReprMixin:
    """
    Mixin to provide semi-universal __repr__ method.

    Generates repr of the form:
    ClassName<memoryaddr>(arg1=val1, ..., argn=valn, extrakey1=extraval1, ...,
    extrakeyn=extravaln)

    Class attributes for customization:
        _REPR_PRIVATE_ATTRIBUTES: If True, also consider attributes with _
        _REPR_ARGUMENTS_IGNORE_MISSING: If True, ignore missing attributes
            when _REPR_ARGUMENTS_TO_ATTRIBUTES is specified
        _REPR_ARGUMENTS_TO_ATTRIBUTES: Map argument names to attribute names
        _REPR_ARGUMENTS_IGNORE: Set of argument names to ignore
        _REPR_EXTRA_ATTRIBUTES: OrderedDict of extra attributes to include
            (keys are display names, values are attribute names or None to use key)
    """

    _REPR_PRIVATE_ATTRIBUTES = False
    _REPR_ARGUMENTS_IGNORE_MISSING = False
    _REPR_ARGUMENTS_TO_ATTRIBUTES: dict[str, str] = {}
    _REPR_ARGUMENTS_IGNORE: set[str] = set()
    _REPR_EXTRA_ATTRIBUTES: OrderedDict[str, Any] = OrderedDict()

    def __get_repr_obj(self, name: str, test_private: bool) -> str | None:
        """
        Get string representation of attribute.

        Args:
            name: Attribute name
            test_private: If True, try private attribute if public not found

        Returns:
            String representation or None if attribute not found
        """
        if not hasattr(self, name):
            if test_private and self._REPR_PRIVATE_ATTRIBUTES:
                name = "_" + name
                if not hasattr(self, name):
                    return None
            else:
                return None

        return repr(getattr(self, name))

    def __repr__(self) -> str:
        """
        Generate string representation of object.

        Returns:
            String representation in format: ClassName<addr>(args...)
        """
        args = []
        for name, parameter in inspect.signature(self.__init__).parameters.items():  # type: ignore[misc]
            if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
                continue

            if name in self._REPR_ARGUMENTS_IGNORE:
                continue

            test_private = True
            if self._REPR_ARGUMENTS_TO_ATTRIBUTES:
                if name in self._REPR_ARGUMENTS_TO_ATTRIBUTES:
                    name = self._REPR_ARGUMENTS_TO_ATTRIBUTES[name]
                    test_private = False
                elif self._REPR_ARGUMENTS_IGNORE_MISSING:
                    continue
            s = self.__get_repr_obj(name, test_private)

            if s is None:
                continue

            args.append(f"{parameter.name}={s}")

        for k, v in self._REPR_EXTRA_ATTRIBUTES.items():
            args.append(f"{k}={self.__get_repr_obj(v or k, False)}")

        return "{}<{}>({})".format(
            self.__class__.__name__,
            hex(id(self)),
            ", ".join(args),
        )


# =============================================================================
# Functions
# =============================================================================
