"""
Decorators

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/shared/decorators.py                                       |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utility decorators.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import functools
import warnings
from typing import Any

# 3rd-party

# self

# =============================================================================
# Globals
# =============================================================================

__all__ = ["deprecated", "doc"]


# =============================================================================
# Classes
# =============================================================================


class DeprecationDecorator:
    """
    Decorator for marking functions as deprecated.

    Applying this decorator will cause DeprecationWarnings to be emitted on
    function call and also adds a DEPRECATED notice to the docstring.

    Both message and doc_message accept format strings:
    - {version}: Version the function will be removed in
    - {func}: The name of the function (only in message)
    """

    _default_message = "Use of {func} is deprecated and will be removed in PyPoE {version}"
    _default_doc_message = "DEPRECATED. Will be removed in PyPoE {version}"

    def __init__(self, message: str | None = None, doc_message: str | None = None, version: str | None = None) -> None:
        """
        Initialize deprecation decorator.

        Args:
            message: Warning message on each call (uses {func} and {version})
            doc_message: Message to append to docstring (uses {version})
            version: Version the function will be removed in
        """
        self.message = message or self._default_message
        self.doc_message = doc_message or self._default_doc_message
        self.version = version or "unknown version"

    def __call__(self, function: Any) -> Any:
        """
        Apply deprecation decorator to function.

        Args:
            function: Function to deprecate

        Returns:
            Wrapped function that emits deprecation warnings
        """
        message_kwargs = {
            "version": self.version,
        }

        if hasattr(function, "__func__"):
            function = function.__func__

        if function.__doc__ is None:
            function.__doc__ = self.doc_message.format(**message_kwargs)
        else:
            function.__doc__ = self.doc_message.format(**message_kwargs) + "\n" + function.__doc__

        @functools.wraps(function)
        def deprecated_function(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                self.message.format(func=function.__name__, **message_kwargs),
                DeprecationWarning,
                stacklevel=2,
            )

            return function(*args, **kwargs)

        return deprecated_function


class DocStringDecorator:
    """
    Decorator for modifying docstrings.

    Modifies the docstring of a given object without wrapping it.
    This allows it to work with any type of object (functions, classes, etc.).
    """

    def __init__(self, prepend: str | Any | None = None, append: str | Any | None = None, doc: str | Any | None = None) -> None:
        """
        Initialize docstring decorator.

        All parameters accept either a string or an arbitrary object.
        If an object is specified, its docstring will be used.

        Args:
            prepend: String to prepend to the docstring (or object with docstring)
            append: String to append to the docstring (or object with docstring)
            doc: Docstring to use. If None, uses the object's docstring
        """
        self.append = self._get_str(append)
        self.prepend = self._get_str(prepend)
        self.doc = doc

    def _get_str(self, obj: str | Any | None) -> str:
        """
        Extract string from object.

        Args:
            obj: String, object with docstring, or None

        Returns:
            Extracted string or empty string
        """
        if obj is None:
            return ""
        elif isinstance(obj, str):
            return obj
        elif obj.__doc__:
            return obj.__doc__
        else:
            return ""

    def __call__(self, obj: Any) -> Any:
        """
        Apply docstring modification to object.

        Args:
            obj: Object to modify docstring for

        Returns:
            Object with modified docstring
        """
        docs = self._get_str(obj) if self.doc is None else self._get_str(self.doc)

        docs = self.prepend + docs + self.append

        if docs != "":
            if hasattr(obj, "__func__"):
                obj.__func__.__doc__ = docs
            else:
                obj.__doc__ = docs

        return obj


# =============================================================================
# Functions
# =============================================================================


def _make_callable(cls: type[Any]) -> Any:
    """
    Make decorator class callable as function.

    Allows using decorator classes both as @decorator() and @decorator.

    Args:
        cls: Decorator class to make callable

    Returns:
        Callable wrapper function
    """
    @functools.wraps(cls)
    def call(*args: Any, **kwargs: Any) -> Any:
        if len(args) == 1 and callable(args[0]):
            return cls()(args[0])
        else:
            return cls(*args, **kwargs)

    return call


# =============================================================================
# Init
# =============================================================================

deprecated = _make_callable(DeprecationDecorator)
doc = _make_callable(DocStringDecorator)
