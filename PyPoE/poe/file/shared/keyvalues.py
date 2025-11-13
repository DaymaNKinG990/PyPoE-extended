"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/shared/keyvalues.py                               |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Shared abstract classes for files that contain key-value pairs.

When implementing support for other file types that use the generic key-value
format GGG uses, the file should subclass the files found here and appropriately
change the logic.

The key value format is generally something like this:

.. code-block:: none

    SectionName
    {
        key = value
        key = "quoted value"
    }

.. warning::
    None of the abstract classes found here should be instantiated directly.

See also:

* :mod:`PyPoE.poe.file.shared`
* :mod:`PyPoE.poe.file.shared.cache`


Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

Abstract Classes
-------------------------------------------------------------------------------

.. autoclass:: AbstractKeyValueSection
    :private-members:
    :no-inherited-members:

.. autoclass:: AbstractKeyValueFile
    :exclude-members: write
    :private-members:
    :no-inherited-members:

    .. automethod:: read
    .. automethod:: get_read_buffer
    .. automethod:: write
    .. automethod:: get_write_buffer


.. autoclass:: AbstractKeyValueFileCache
    :private-members:

Exceptions & Warnings
-------------------------------------------------------------------------------

.. autoclass:: DuplicateKeyWarning

.. autoclass:: OverriddenKeyWarning
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import contextlib
import re
import warnings
from collections import OrderedDict, defaultdict
from typing import Union

from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.shared import AbstractFile, ParserError, ParserWarning
from PyPoE.poe.file.shared.cache import AbstractFileCache

# 3rd-party
# self
from PyPoE.shared.decorators import doc

# =============================================================================
# Globals
# =============================================================================

__all__ = ["AbstractKeyValueFile", "AbstractKeyValueFileCache", "AbstractKeyValueSection"]

# =============================================================================
# Classes
# =============================================================================


class DuplicateKeyWarning(ParserWarning):
    """
    Warning for keys that are not explicitly specified to be overridden.
    """

    pass


class OverriddenKeyWarning(ParserWarning):
    """
    Warning for keys that are overridden during a merge.
    """

    pass


class AbstractKeyValueSection(dict):
    """
    Abstract base class for key-value sections.

    Represents a section in a key-value file format. Handles special key types
    like APPEND_KEYS (for lists) and ORDERED_HASH_KEYS (for ordered dictionaries).

    Attributes:
        APPEND_KEYS: Set of keys that should be appended to (list behavior)
        ORDERED_HASH_KEYS: Set of keys that should use OrderedDict behavior
        NAME: Default name for this section type
        parent: Parent AbstractKeyValueFile instance
        name: Name of this section
    """

    APPEND_KEYS: set[str] = set()
    ORDERED_HASH_KEYS: set[str] = set()
    NAME = ""

    def __init__(self, parent: "AbstractKeyValueFile", name: str | None = None, *args: Any, **kwargs: Any) -> None:
        """
        Initialize key-value section.

        Args:
            parent: Parent AbstractKeyValueFile instance
            name: Name of the section (if None, uses NAME class attribute)
            *args: Additional positional arguments for dict
            **kwargs: Additional keyword arguments for dict

        Raises:
            ParserError: If name is not provided and NAME is empty
        """
        super().__init__(*args, **kwargs)
        self.parent: AbstractKeyValueFile = parent
        self.name: str
        if name:
            self.name = name
        elif self.NAME:
            self.name = self.NAME
        else:
            raise ParserError("Missing name for section")

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set item with special handling for APPEND_KEYS and ORDERED_HASH_KEYS.

        Args:
            key: Key name
            value: Value to set (handled specially for APPEND_KEYS and ORDERED_HASH_KEYS)
        """
        # Equals "override" behaviour
        if key in self.ORDERED_HASH_KEYS:
            if not isinstance(value, OrderedDict):
                if key in self:
                    self[key][value] = True
                    return
                else:
                    value = OrderedDict(((value, True),))
        elif key in self.APPEND_KEYS and not isinstance(value, list):
            if key in self:
                self[key].append(value)
                return
            else:
                value = [
                    value,
                ]
        super().__setitem__(key, value)

    def merge(self, other: "AbstractKeyValueSection") -> None:
        """
        Merge another section into this section.

        Handles special merging logic for APPEND_KEYS and ORDERED_HASH_KEYS.
        Keys in ORDERED_HASH_KEYS are merged into OrderedDict.
        Keys in APPEND_KEYS are appended to lists.

        Args:
            other: Another AbstractKeyValueSection to merge from

        Raises:
            TypeError: If other is not an AbstractKeyValueSection instance
        """
        if not isinstance(other, AbstractKeyValueSection):
            raise TypeError(
                f'Other must be a AbstractKeyValuesSection instance, got "{other.__class__.__name__}" '
                "instead."
            )

        for k, v in other.items():
            if k in self.ORDERED_HASH_KEYS:
                if isinstance(v, OrderedDict):
                    if k in self:
                        v = OrderedDict(list(self[k].items()) + list(v.items()))
                    else:
                        v = OrderedDict(v.items())
                else:
                    if k in self:
                        self[k][v] = True
                        continue
                    else:
                        v = OrderedDict(((v, True),))
            elif k in self.APPEND_KEYS:
                if isinstance(v, list):
                    if k in self:
                        v += self[k]
                    else:
                        pass
                else:
                    if k in self:
                        self[k].append(v)
                        continue
                    else:
                        v = [
                            v,
                        ]
            elif k in self:
                continue

            self[k] = v


class AbstractKeyValueFile(AbstractFile, defaultdict):
    """
    Abstract base class for key-value files.

    Represents a file in key-value format (e.g., .ot files). Supports file
    extension/inheritance and section-based structure.

    Attributes:
        SECTIONS: Dictionary mapping section names to section classes
        EXTENSION: File extension (if any) for this file class
        version: File format version number (None if not specified)
        extends: Name of file this extends (None if not extending)
        _parent_file: Parent AbstractKeyValueFile instance (if extending)
        _parent_file_system: Parent FileSystem instance (if using file system)
    """

    version: int | None = None
    extends: str | None = None

    SECTIONS: dict[str, type[AbstractKeyValueSection]] = {}

    EXTENSION = ""

    _re_header = re.compile(
        r"^"
        r"version (?P<version>[0-9]+)[\r\n]*"
        r'extends "(?P<extends>[\w\./_]+)"[\r\n]*'
        r"(?P<remainder>.*)"  # Match the rest
        r"$",
        re.UNICODE | re.MULTILINE | re.DOTALL,
    )

    _re_find_kv_sections = re.compile(
        r"^(?P<key>[\w]+)[\r\n]+"
        r"^{"
        r"(?P<contents>[^}]*)"
        r"^}",
        re.UNICODE | re.MULTILINE,
    )

    _re_find_kv_pairs = re.compile(
        r"^[\s]*"
        r"(?P<key>[\S]+)"
        r"[\s]*=[\s]*"
        r'(?P<value>"[^"]*"|[\S]+)'
        r"[\s]*$",
        re.UNICODE | re.MULTILINE,
    )

    def __init__(
        self,
        parent_or_file_system: "AbstractKeyValueFile | FileSystem | None" = None,
        version: int | None = None,
        extends: str | None = None,
        keys: Any = None,
    ) -> None:
        """
        Initialize key-value file.

        Args:
            parent_or_file_system: Parent file or file system instance
            version: File format version number
            extends: Name of file this extends
            keys: Default keys for defaultdict

        Raises:
            TypeError: If parent_or_file_system is of invalid type
        """
        AbstractFile.__init__(self)
        defaultdict.__init__(self, keys)

        self.version = version
        self.extends = extends

        self._parent_file: AbstractKeyValueFile | None = None
        self._parent_file_system: FileSystem | None = None

        if isinstance(parent_or_file_system, AbstractKeyValueFile):
            self._parent_file = parent_or_file_system
        elif isinstance(parent_or_file_system, FileSystem):
            self._parent_file_system = parent_or_file_system
        elif parent_or_file_system is not None:
            raise TypeError("parent_or_file_system is of invalid type.")

    #
    # Properties
    #
    @property
    def parent_or_file_system(self) -> "AbstractKeyValueFile | FileSystem":
        """
        Get parent file or file system.

        Returns:
            Parent AbstractKeyValueFile or FileSystem instance
        """
        return self._parent_file or self._parent_file_system  # type: ignore[return-value]

    #
    # Special
    #
    def __missing__(self, key: str) -> AbstractKeyValueSection:
        """
        Create section when accessed via dict interface.

        Args:
            key: Section name

        Returns:
            New or existing AbstractKeyValueSection instance
        """
        try:
            self[key] = self.SECTIONS[key](parent=self)
        except KeyError:
            self[key] = AbstractKeyValueSection(parent=self, name=key)

        return self[key]  # type: ignore[no-any-return]

    def __delitem__(self, key: str) -> None:
        """
        Delete item (not implemented).

        Raises:
            NotImplementedError: Always raised (deletion not supported)
        """
        raise NotImplementedError()

    def __repr__(self) -> str:
        """
        Return string representation.

        Returns:
            String representation of the key-value file
        """
        return f'{self.__class__.__name__}(extends="{self.extends}", version="{self.version}", keys={defaultdict.__repr__(self)}'

    def _read(self, buffer: Any, *args: Any, **kwargs: Any) -> None:
        """
        Read and parse key-value file from buffer.

        Parses file format, extracts sections and key-value pairs,
        handles file extension/inheritance.

        Args:
            buffer: File buffer to read from
            *args: Additional positional arguments (unused)
            **kwargs: Additional keyword arguments (unused)

        Raises:
            ParserError: If file format is invalid or parent file not found
        """
        data = buffer.read().decode("utf-16")

        match = self._re_header.match(data)
        if match is None:
            raise ParserError(f"File is not a valid {self.__class__.__name__} file.")

        self.version = int(match.group("version"))

        for section_match in self._re_find_kv_sections.finditer(match.group("remainder")):
            key = section_match.group("key")

            try:
                section = self[key]
            except KeyError:
                # print('Extra section:', key)
                section = AbstractKeyValueSection(parent=self, name=key)
                self[key] = section

            for kv_match in self._re_find_kv_pairs.finditer(section_match.group("contents")):
                value = kv_match.group("value").strip('"')
                if value == "true":
                    value = True
                elif value == "false":
                    value = False
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        with contextlib.suppress(ValueError):
                            value = float(value)

                section[kv_match.group("key")] = value

        extend = match.group("extends")

        if extend == "nothing":
            self.extends = None
        elif extend:
            if self._parent_file:
                self.merge(self._parent_file)
                if self._parent_file.name != extend:  # type: ignore[attr-defined]
                    warnings.warn(
                        f'Parent file name "{self._parent_file.name}" doesn\'t match extended file '  # type: ignore[attr-defined]
                        f'name "{extend}"',
                        ParserWarning,
                        stacklevel=2,
                    )
            elif self._parent_file_system:
                obj = self.__class__(parent_or_file_system=self._parent_file_system)
                obj.read(
                    file_path_or_raw=self._parent_file_system.get_file(extend + self.EXTENSION),
                )
                self.merge(obj)
            else:
                raise ParserError(
                    f'File extends "{extend}", but parent_or_file_system has not '
                    "been specified on class creation."
                )
            self.extends = extend

    def _write(self, buffer: Any, *args: Any, **kwargs: Any) -> None:
        """
        Write key-value file to buffer.

        Formats sections and key-value pairs into file format,
        including version and extends header.

        Args:
            buffer: File buffer to write to
            *args: Additional positional arguments (unused)
            **kwargs: Additional keyword arguments (unused)
        """
        lines = [
            f"version {self.version}",
            'extends "%s"' % (self.extends if self.extends else "nothing"),
        ]

        for section, keyvalues in self.items():
            lines.append("")
            lines.append(section)
            lines.append("{")
            for key, value in keyvalues.items():
                if isinstance(value, list):
                    for v in value:
                        lines.append(self._get_write_line(key, v))
                else:
                    lines.append(self._get_write_line(key, value))
            lines.append("}")

        buffer.write("\n".join(lines).encode("utf-16le"))

    @doc(prepend=AbstractFile.write)
    def write(self, *args: Any, **kwargs: Any) -> Any:
        """
        Write file to path or buffer.

        Warning:
            The current values held by the file instance will be written. This
            means values inherited from parent files will also be written.

        Args:
            *args: Additional positional arguments (passed to AbstractFile.write)
            **kwargs: Additional keyword arguments (passed to AbstractFile.write)

        Returns:
            Result of write operation
        """
        return super().write(*args, **kwargs)

    def _get_write_line(self, key: str, value: Any) -> str:
        """
        Format a key-value pair for writing.

        Args:
            key: Key name
            value: Value to format

        Returns:
            Formatted line string
        """
        return f'\t{key} = "{value}"'

    def merge(self, other: "AbstractKeyValueFile") -> None:
        """
        Merge with other file.

        Merges sections from another file into this file. If a section exists
        in both files, the sections are merged using AbstractKeyValueSection.merge().

        Args:
            other: Instance of the other file to merge with

        Raises:
            ValueError: If other has a different type than this instance
        """
        if not isinstance(other, self.__class__):
            raise ValueError(
                "Can't merge only with classes with the same base class, got "
                f'"{other.__class__.__name__}" instead'
            )

        for k, v in other.items():
            if k in self:
                self[k].merge(v)
            else:
                self[k] = v


class AbstractKeyValueFileCache(AbstractFileCache):
    FILE_TYPE = AbstractKeyValueFile  # type: ignore[assignment]

    @doc(doc=AbstractFileCache._get_file_instance_args)
    def _get_file_instance_args(self, file_name):
        options = super()._get_file_instance_args(file_name)
        options["parent_or_file_system"] = self.file_system

        return options


# =============================================================================
# Functions
# =============================================================================
