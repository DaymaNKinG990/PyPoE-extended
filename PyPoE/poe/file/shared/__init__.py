"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/shared/__init__.py                                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Shared classes & functions for the file API. Used for exposing the same basic
API.

All file classes inherit the base classes defined here or in the other shared
file modules.

.. warning::
    None of the abstract classes found here should be instantiated directly.

See also:

* :mod:`PyPoE.poe.file.shared.cache`
* :mod:`PyPoE.poe.file.shared.keyvalues`

Agreement
===============================================================================

See PyPoE/LICENSE

.. todo::

    The abstract classes should probably actually be using python abc api.

Documentation
===============================================================================

Abstract Classes
-------------------------------------------------------------------------------

.. autoclass:: AbstractFileReadOnly

.. autoclass:: AbstractFile

.. autoclass:: AbstractFileSystemNode


Enums
-------------------------------------------------------------------------------

.. autoclass:: FILE_SYSTEM_TYPES

Exceptions & Warnings
-------------------------------------------------------------------------------

.. autoclass:: ParserError

.. autoclass:: ParserWarning
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import abc
import os
import re
from collections.abc import Callable
from enum import IntEnum
from io import BytesIO
from typing import Any, Union

# self
from PyPoE.poe.file.shared.protocols import (
    IBufferable,
    IDecompressable,
    IFileSystemNode,
    IReadable,
    ISeekable,
    IWritable,
)
from PyPoE.shared.mixins import ReprMixin

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    "ParserError",
    "ParserWarning",
    "AbstractFileReadOnly",
    "AbstractFile",
    "FILE_SYSTEM_TYPES",
    "AbstractFileSystemNode",
    # Protocol interfaces (new in Phase 8.1)
    "IReadable",
    "IBufferable",
    "IWritable",
    "ISeekable",
    "IDecompressable",
    "IFileSystemNode",
]

# =============================================================================
# Exceptions
# =============================================================================


class ParserError(Exception):
    """
    Exception raised when general errors related to file parsing occur.

    This exception or subclasses of this exception are raised when general
    errors related to the parsing of files occur, such as malformed files.
    """

    pass


class ParserWarning(UserWarning):
    """
    Warning emitted during file parsing when issues are not severe enough to fail.

    This warning or subclasses of this warning are emitted when during the
    parsing process there are cases where issues are not severe enough to
    entirely fail the parsing, but could pose serious problems.
    """

    pass


# =============================================================================
# ABS
# =============================================================================


class AbstractFileReadOnly(ReprMixin):
    """
    Abstract Base Class for reading.

    It provides common methods as well as methods that implementing classes
    should override.

    This class implements the following Protocol interfaces:
    - IReadable: Provides read() method
    - IBufferable: Provides get_read_buffer() method

    Note: For new code, consider using Protocol interfaces directly
    (IReadable, IBufferable) instead of inheriting from this class.
    This allows better Interface Segregation Principle (ISP) compliance.

    See also:
        :mod:`PyPoE.poe.file.shared.protocols` for Protocol interfaces
    """

    def _read(self, buffer: BytesIO, *args: Any, **kwargs: Any) -> Any:
        """
        Read file from buffer (abstract method).

        Args:
            buffer: The file/byte buffer
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Result of the read operation

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError()

    def get_read_buffer(
        self, file_path_or_raw: BytesIO | bytes | str, function: Callable, *args: Any, **kwargs: Any
    ) -> Any:
        """
        Open file_path_or_raw in read mode and pass buffer to function.

        The function must accept at least one keyword argument called 'buffer'.

        Args:
            file_path_or_raw: File path, bytes or buffer to read from
            function: Function that will be called with the buffer keyword argument
            *args: Additional positional arguments to pass to the specified function
            **kwargs: Additional keyword arguments to pass to the specified function

        Returns:
            Result of the function

        Raises:
            TypeError: If file_path_or_raw has an invalid type
        """
        if isinstance(file_path_or_raw, BytesIO):
            return function(*args, buffer=file_path_or_raw, **kwargs)
        elif isinstance(file_path_or_raw, bytes):
            return function(*args, buffer=BytesIO(file_path_or_raw), **kwargs)
        elif isinstance(file_path_or_raw, str):
            with open(file_path_or_raw, "rb") as f:
                return function(*args, buffer=f, **kwargs)
        else:
            raise TypeError("file_path_or_raw must be a file path or bytes object")

    def read(self, file_path_or_raw: BytesIO | bytes | str, *args: Any, **kwargs: Any) -> Any:
        """
        Read file contents from specified path or buffer.

        Reads the file contents into the specified path or buffer. This will
        also reset any existing contents of the file.

        If a buffer or bytes was given, the data will be read from the buffer
        or bytes object. If a file path was given, the resulting data will be
        read from the specified file.

        Args:
            file_path_or_raw: File path, bytes or buffer to read from
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Result of the read operation, if any

        Raises:
            TypeError: If file_path_or_raw has an invalid type
        """
        return self.get_read_buffer(file_path_or_raw, self._read, *args, **kwargs)


class AbstractFile(AbstractFileReadOnly):
    """
    Abstract Base Class for reading and writing files.

    It provides common methods as well as methods that implementing classes
    should override.

    This class implements the following Protocol interfaces:
    - IReadable: Provides read() method (inherited from AbstractFileReadOnly)
    - IBufferable: Provides get_read_buffer() method (inherited)
    - IWritable: Provides write() method

    Note: For new code, consider using Protocol interfaces directly
    (IReadable, IBufferable, IWritable) instead of inheriting from this class.

    See also:
        :mod:`PyPoE.poe.file.shared.protocols` for Protocol interfaces
    """

    def _write(self, buffer: BytesIO, *args: Any, **kwargs: Any) -> Any:
        """
        Write file to buffer (abstract method).

        Args:
            buffer: The file/byte buffer
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Result of the write operation

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError()

    def get_write_buffer(
        self, file_path_or_raw: BytesIO | bytes | str, function: Callable, *args: Any, **kwargs: Any
    ) -> Any:
        """
        Open file_path_or_raw in write mode and pass buffer to function.

        The function must accept at least one keyword argument called 'buffer'.

        Args:
            file_path_or_raw: File path, bytes or buffer to write to
            function: Function that will be called with the buffer keyword argument
            *args: Additional positional arguments to pass to the specified function
            **kwargs: Additional keyword arguments to pass to the specified function

        Returns:
            Result of the function

        Raises:
            TypeError: If file_path_or_raw has an invalid type
        """
        if isinstance(file_path_or_raw, BytesIO):
            return function(*args, buffer=file_path_or_raw, **kwargs)
        elif isinstance(file_path_or_raw, bytes):
            return function(*args, buffer=BytesIO(file_path_or_raw), **kwargs)
        elif isinstance(file_path_or_raw, str):
            with open(file_path_or_raw, "wb") as f:
                return function(*args, buffer=f, **kwargs)
        else:
            raise TypeError("file_path_or_raw must be a file path or bytes object")

    def write(self, file_path_or_raw: BytesIO | bytes | str, *args: Any, **kwargs: Any) -> Any:
        """
        Write file contents to specified path or buffer.

        Write the contents of file to the specified path or buffer. If a buffer
        or bytes was given, a buffer object with the new data should be returned.
        If a file path was given, the resulting data should be written to the
        specified file.

        Args:
            file_path_or_raw: File path, bytes or buffer to write to
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Result of the write operation, if any

        Raises:
            TypeError: If file_path_or_raw has an invalid type
        """
        return self.get_write_buffer(file_path_or_raw, self._write, *args, **kwargs)


class FILE_SYSTEM_TYPES(IntEnum):
    """
    File system types for file system nodes.

    Attributes:
        ROOT: Root file system type (-1)
        DISK: Disk file system type (0)
        BUNDLE: Bundle file system type (1)
        GGPK: GGPK file system type (2)
    """

    ROOT = -1
    DISK = 0
    BUNDLE = 1
    GGPK = 2


class AbstractFileSystemNode(ReprMixin):
    """
    Abstract base class for file system nodes.

    Represents a file or directory in the file system tree structure.

    Attributes:
        parent: Parent node (None for root)
        file_system_type: Type of file system (FILE_SYSTEM_TYPES)
        is_file: True if this is a file, False if directory
        children: Dictionary of child nodes (keyed by name)
    """

    __slots__ = ["parent", "file_system_type", "is_file", "children"]

    def __init__(
        self, parent: "AbstractFileSystemNode | None", file_system_type: FILE_SYSTEM_TYPES, is_file: bool
    ) -> None:
        """
        Initialize file system node.

        Args:
            parent: Parent node (None for root)
            file_system_type: Type of file system (FILE_SYSTEM_TYPES)
            is_file: True if this is a file, False if directory
        """
        self.parent: AbstractFileSystemNode = parent
        self.file_system_type: FILE_SYSTEM_TYPES = file_system_type
        self.is_file: bool = is_file
        self.children: dict[str, AbstractFileSystemNode] = {}

    def __getitem__(self, item: str) -> "AbstractFileSystemNode":
        """
        Return the specified file or directory path.

        The path will accept valid paths for the current operating system,
        however forward slashes ( / ) are recommended as they are supported on
        both Windows and Linux.

        Since each node supports the same syntax, all these calls are equivalent:

        Example:
            >>> self['directory1']['directory2']['file.ext']
            >>> self['directory1']['directory2/file.ext']
            >>> self['directory1/directory2']['file.ext']
            >>> self['directory1/directory2/file.ext']

        Args:
            item: File path or file name

        Returns:
            AbstractFileSystemNode of the specified item

        Raises:
            FileNotFoundError: If the specified item is not found
        """
        item = item.strip("/\\")
        if not item:
            return self

        path: list[str] = []
        partial = item
        while partial:
            partial, result = os.path.split(partial)
            path.insert(0, result)

        obj = self
        while True:
            try:
                partial = path.pop(0)
            except IndexError:
                return obj

            for child in obj.children.values():
                if child.name == partial:
                    obj = child
                    break
            else:
                raise FileNotFoundError(f"{self.get_path()}/{item} not found")

    @property
    def data(self) -> bytes:
        """
        Get data contained within this object.

        Returns:
            File data as bytes

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        """
        Get name associated with the stored record.

        Returns:
            Name of the file/directory

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    @property
    def files(self) -> list["AbstractFileSystemNode"]:
        """
        Get list of child nodes which are files.

        Returns:
            List of AbstractFileSystemNode instances which reference a file
        """
        return [child for child in self.children.values() if child.is_file]

    @property
    def directories(self) -> list["AbstractFileSystemNode"]:
        """
        Get list of child nodes which are directories.

        Returns:
            List of AbstractFileSystemNode instances which reference a directory
        """
        return [child for child in self.children.values() if child.is_directory]

    @property
    def is_directory(self) -> bool:
        """
        Check if this node references a directory.

        Returns:
            True if this is a directory, False if it's a file
        """
        return not self.is_file

    def search(
        self, regex: re.Pattern[str] | str, search_files: bool = True, search_directories: bool = True
    ) -> list["AbstractFileSystemNode"]:
        """
        Search for nodes matching the given regex pattern.

        Args:
            regex: Compiled regular expression or string pattern to use
            search_files: Whether file instances should be searched (default: True)
            search_directories: Whether directory instances should be searched (default: True)

        Returns:
            List of matching AbstractFileSystemNode instances
        """
        if isinstance(regex, str):
            regex = re.compile(regex)

        nodes = []

        # func = lambda n: nodes.append(n) if re.search(regex, n.name) else None
        # self.walk(func)

        q = []
        q.append(self)

        while len(q) > 0:
            node = q.pop()
            if (
                search_files and node.is_file or search_directories and node.is_directory
            ) and re.search(regex, node.name):
                nodes.append(node)

            for child in node.children:
                q.append(child)  # type: ignore[arg-type]

        return nodes

    def get_path(self) -> str:
        """
        Get the full path from root to this node.

        Returns:
            Full path as a string (using forward slashes)
        """
        return "/".join([n.name for n in self.get_parent(make_list=True)])  # type: ignore[attr-defined]

    def get_parent(
        self,
        n: int = -1,
        stop_at: "AbstractFileSystemNode | None" = None,
        make_list: bool = False,
    ) -> "AbstractFileSystemNode | list[AbstractFileSystemNode]":
        """
        Get the n-th parent or return root parent if at top level.

        Negative values for n will iterate until the root is found.
        If the make_list keyword is set to True, a list of Nodes in the
        following form will be returned: [n-th parent, (n-1)-th parent, ..., self]

        Args:
            n: Up to which depth to go to (default: -1, goes to root)
            stop_at: AbstractFileSystemNode instance to stop the iteration at
            make_list: Return a list of AbstractFileSystemNode instances instead of parent

        Returns:
            Parent or root AbstractFileSystemNode instance, or list if make_list=True
        """
        nodes: list[AbstractFileSystemNode] = []
        node = self
        while n != 0:
            if node.parent is None:
                break

            if node is stop_at:
                break

            if make_list:
                nodes.insert(0, node)
            node = node.parent
            n -= 1

        return nodes if make_list else node  # type: ignore[return-value]

    def walk(self, function: Callable):
        """
        .. todo::
            function = None -> generator like os.walk (dir, [dirs], [files])

        Walks over the nodes and it's sub nodes and executes the specified
        function.

        The function will be called with the following dictionary arguments:

        * node - :class:`AbstractFileSystemNode`
        * depth - Depth

        Parameters
        ----------
        function
            function to call when walking
        """
        q = []
        q.append({"node": self, "depth": 0})

        while len(q) > 0:
            data = q.pop()
            function(**data)
            for child in data["node"].children.values():  # type: ignore[attr-defined]
                q.append({"node": child, "depth": data["depth"] + 1})  # type: ignore[operator]

        """for child in self.children:
            function(child)
            child.walk(function)"""

    def extract_to(self, target_directory: str):
        """
        Extracts the node and its contents (including sub-directories) to the
        specified target directory.

        Parameters
        ----------
        target_directory : str
            Path to directory where to extract to.
        """
        from PyPoE.shared.file_utils import ensure_directory, write_file

        dir_path = os.path.join(target_directory, self.name)
        if self.is_directory:
            ensure_directory(dir_path)

            for node in self.children.values():
                node.extract_to(dir_path)
        else:
            with open(dir_path, "wb") as f:
                f.write(bytes(self))  # type: ignore[call-overload]
