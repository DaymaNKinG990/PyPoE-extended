"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/shared/cache.py                                   |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

All file caches classes will inherit :class:`AbstractFileCache`.

.. warning::
    None of the abstract classes found here should be instantiated directly.

See also:

* :mod:`PyPoE.poe.file.shared`
* :mod:`PyPoE.poe.file.shared.keyvalues`


Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

.. autoclass:: AbstractFileCache
    :private-members:
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from typing import Any

from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.shared import AbstractFileReadOnly
from PyPoE.poe.file.shared.protocols import IReadable

# 3rd-party
# self
from PyPoE.shared.mixins import ReprMixin

# =============================================================================
# Globals
# =============================================================================

__all__ = ["AbstractFileCache"]

# =============================================================================
# Classes
# =============================================================================


class AbstractFileCache(ReprMixin):
    """
    Abstract base class for file caches.

    Provides caching and lazy loading of file instances from the file system.

    Attributes:
        file_system: FileSystem instance
        files: Dictionary of loaded file instances and their related path
        instance_options: Options to pass to file's __init__ method
        read_options: Options to pass to file instance's read method
    """

    FILE_TYPE: type[AbstractFileReadOnly] | None = None

    def __init__(
        self,
        path_or_file_system: str | FileSystem | None = None,
        files: list[str] | None = None,
        files_shortcut: bool = True,
        instance_options: dict[str, Any] | None = None,
        read_options: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize file cache.

        Args:
            path_or_file_system: The root path (relative to content.ggpk) where
                the files are stored or a FileSystem instance
            files: Iterable of files that will be loaded right away
            files_shortcut: Whether to use the shortcut function (self.__getitem__)
            instance_options: Options to pass to the file's __init__ method
            read_options: Options to pass to the file instance's read method

        Raises:
            TypeError: If path_or_file_system is not specified or invalid type
            ValueError: If a FileSystem was passed, but it was not properly initialized
        """

        self.file_system: FileSystem
        if isinstance(path_or_file_system, FileSystem):
            self.file_system = path_or_file_system
        else:
            self.file_system = FileSystem(root_path=path_or_file_system)  # type: ignore[arg-type]

        self.instance_options: dict[str, Any] = {} if instance_options is None else instance_options
        self.read_options: dict[str, Any] = {} if read_options is None else read_options

        self.files: dict[str, AbstractFileReadOnly] = {}

        read_func = self.__getitem__ if files_shortcut else self.get_file

        if files is not None:
            for file in files:
                read_func(file)

    def __getitem__(self, item: str) -> IReadable:
        """
        Shortcut for get_file().

        Equivalent: AbstractFileCache[item] <==> AbstractFileCache.get_file(item)

        Args:
            item: Item to retrieve

        Returns:
            File instance (implements IReadable Protocol)
        """
        return self.get_file(item)

    def _get_file_instance_args(self, file_name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Get dictionary of keyword arguments to pass to file's __init__ method.

        Args:
            file_name: Name of the file
            *args: Additional positional arguments (unused)
            **kwargs: Additional keyword arguments (unused)

        Returns:
            Dictionary of keyword arguments
        """
        options = dict(self.instance_options)
        return options

    def _get_read_args(self, file_name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Get dictionary of keyword arguments to pass to file's read method.

        In particular it sets file_path_or_raw based on how the cache was
        instantiated.

        Args:
            file_name: Name of the file
            *args: Additional positional arguments (unused)
            **kwargs: Additional keyword arguments (unused)

        Returns:
            Dictionary of keyword arguments
        """
        options = dict(self.read_options)
        options["file_path_or_raw"] = self.file_system.get_file(file_name)

        return options

    def _create_instance(self, file_name: str, *args, **kwargs) -> Any:
        """
        Creates a new instance for the given file name

        Parameters
        ----------
        file_name :  str
            Name to the file to pass on


        Returns
        -------

            File instance
        """
        f = self.FILE_TYPE(  # type: ignore[misc]
            **self._get_file_instance_args(file_name=file_name, *args, **kwargs)  # type: ignore[misc]
        )
        f.read(**self._get_read_args(file_name=file_name, *args, **kwargs))  # type: ignore[misc]
        return f  # type: ignore[no-any-return]

    def get_file(self, file_name: str, *args, **kwargs) -> IReadable:
        """
        Returns the the specified file from the cache.

        If the file does not exist, read it from the path specified on cache
        creation, add it to the cache and then return it.

        Parameters
        ----------
        file_name :  str
            File to retrieve


        Returns
        -------
        IReadable
            read file instance (implements IReadable Protocol)

        Note:
            Returns IReadable Protocol instead of AbstractFileReadOnly
            for better Interface Segregation Principle (ISP) compliance.
            All returned instances are also AbstractFileReadOnly subclasses.
        """
        if file_name not in self.files:
            f = self._create_instance(file_name=file_name)
            self.files[file_name] = f
        else:
            f = self.files[file_name]

        return f  # type: ignore[no-any-return]
