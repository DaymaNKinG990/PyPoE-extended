"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/file_system.py                                    |
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

Documentation
===============================================================================

Classes
-------------------------------------------------------------------------------

.. autoclass: FileSystem

.. autoclass: FileSystemNode
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import os

# 3rd-party
import brotli  # type: ignore[import-untyped]

from PyPoE.poe.file.bundle import Index
from PyPoE.poe.file.ggpk import FileRecord, GGPKFile

# self
from PyPoE.poe.file.shared import FILE_SYSTEM_TYPES, AbstractFileSystemNode, ParserError

# =============================================================================
# Globals
# =============================================================================

__all__ = ["FileSystem"]

# =============================================================================
# Classes
# =============================================================================


class FileSystemNode(AbstractFileSystemNode):
    """
    Node in the file system tree.

    Represents a file or directory in the game's file system,
    providing access to file data and path information.

    Attributes:
        file_system: FileSystem instance this node belongs to
        _name: Node name
    """

    _REPR_ARGUMENTS_IGNORE = {"parent"}

    __slots__ = ["file_system"] + AbstractFileSystemNode.__slots__

    def __init__(
        self,
        parent: "FileSystemNode | None",
        file_system_type: FILE_SYSTEM_TYPES,
        is_file: bool,
        file_system: "FileSystem",
        name: str,
    ) -> None:
        """
        Initialize file system node.

        Args:
            parent: Parent node (None for root)
            file_system_type: Type of file system (GGPK, DISK, BUNDLE)
            is_file: True if this is a file, False if directory
            file_system: FileSystem instance
            name: Node name
        """
        super().__init__(
            parent,  # type: ignore[arg-type]
            file_system_type,
            is_file,
        )

        self.file_system: FileSystem = file_system
        self._name: str = name

    @property
    def data(self) -> bytes:
        """
        Get file data.

        Returns:
            File contents as bytes

        Raises:
            ValueError: If this is a directory (not a file)
        """
        if self.is_file:
            return self.file_system.get_file(self.get_path())
        else:
            raise ValueError("Cannot get data from directory node")

    @property
    def name(self) -> str:
        """
        Get node name.

        Returns:
            Node name string
        """
        return self._name


class FileSystem:
    """
    Unified file system access for game files.

    Simplifies accessing files from the game by checking disk, GGPK, and bundles
    automatically. Upon initialization, the Index bundle and GGPK are automatically
    read if present. Further decompression or reading is done lazily when get_file()
    is called.

    Attributes:
        root_path: Root game directory path
        ggpk: GGPKFile instance (if Content.ggpk exists)
        index: Index instance (if available)
        directory: Root FileSystemNode (if built)
    """

    def __init__(self, root_path: str) -> None:
        """
        Initialize file system.

        Args:
            root_path: Root game directory path (where PathOfExile.exe is located)
        """
        self.directory: FileSystemNode | None = None

        self.root_path: str = root_path
        self.ggpk: GGPKFile | None = None

        ggpk_path = os.path.join(root_path, "Content.ggpk")
        if os.path.exists(os.path.join(root_path, "Content.ggpk")):
            self.ggpk = GGPKFile()
            self.ggpk.read(ggpk_path)
            self.ggpk.directory_build()

        self.index: Index | None = Index()
        try:
            if self.ggpk:
                node = self.ggpk[self.index.PATH]
                if isinstance(node.record, FileRecord):
                    self.index.read(node.record.extract())
                else:
                    raise ParserError("Index path does not point to a file")
            else:
                self.index.read(os.path.join(root_path, self.index.PATH))
        except FileNotFoundError:
            self.index = None

    def get_file(self, path: str) -> bytes:
        """
        Retrieve file contents as binary data.

        Searches for file in the following order:
        1. Index bundle (if available)
        2. GGPK file (if loaded)
        3. Disk (root_path)

        Args:
            path: Path relative to root game directory

        Returns:
            File contents as bytes

        Raises:
            FileNotFoundError: If file not found in any location
            ParserError: If path points to invalid file type
        """
        if self.index:
            try:
                fr = self.index.get_file_record(path)
            except FileNotFoundError:
                pass
            else:
                if self.ggpk:
                    node = self.ggpk[fr.bundle.ggpk_path]
                    if isinstance(node.record, FileRecord):
                        fr.bundle.read(node.record.extract())
                    else:
                        raise ParserError("Bundle path does not point to a file")
                else:
                    fr.bundle.read(os.path.join(self.root_path, fr.bundle.ggpk_path))
                return fr.get_file()

        # If the file is in the index, this section can't be reached
        if self.ggpk:
            try:
                node = self.ggpk[path]
                if isinstance(node.record, FileRecord):
                    return node.record.extract()  # type: ignore[no-any-return]
                else:
                    raise ParserError("Path does not point to a file")
            except FileNotFoundError:
                pass

        # If no GGPK is loaded or the file isn't within the GGPK, lastly the
        # root directory is tried
        from PyPoE.shared.file_utils import read_file

        try:
            return read_file(os.path.join(self.root_path, path))
        except FileNotFoundError as e:
            raise FileNotFoundError(
                "Specified file can not be found in the Index, content.ggpk or disk"
            ) from e

    def extract_dds(self, data: bytes) -> bytes:
        """
        Attempts to extract a .dds from the given data bytes.

        .dds files in the content.ggpk may be compressed with brotli or may be
        a reference to another .dds file.

        This function will take of those kind of files accordingly and try to return
        a file instead.
        If any problems arise an error will be raised instead.

        Parameters
        ----------
        data
            The raw data to extract the dds from.

        Returns
        -------
        bytes
            the uncompressed, dereferenced .dds file data

        Raises
        -------
        ValueError
            If the file data contains a reference, but path_or_ggpk is not specified
        TypeError
            If the file data contains a reference, but path_or_ggpk is of invalid
            type (i.e. not str or :class:`GGPKFile`
        ParserError
            If the uncompressed size does not match the size in the header
        brotli.error
            If whatever bytes were read were not brotli compressed
        """
        # Already a DDS file, so return it
        if data[:4] == b"DDS ":
            return data
        # Is this a reference?
        elif data[:1] == b"*":
            path = data[1:].decode()
            data = self.get_file(path)
            return self.extract_dds(data)
        else:
            size = int.from_bytes(data[:4], "little")
            dec = brotli.decompress(data[4:])
            if len(dec) != size:
                raise ParserError("Decompressed size does not match size in the header")
            return dec  # type: ignore[no-any-return]

    def build_directory(self) -> FileSystemNode:
        """
        Builds a joint directory from the files available on disk, in ggpk and
        in bundles.

        The directory is not required to retrieve files from the file system
        and serves more educational purposes.

        Returns
        -------
            The directory.
        """
        self.directory = FileSystemNode(
            file_system=self,
            name="",
            parent=None,
            file_system_type=FILE_SYSTEM_TYPES.ROOT,
            is_file=False,
        )

        for path, directories, files in os.walk(self.root_path):
            p = os.path.commonprefix([self.root_path, path])
            node = self.directory[path.replace(p, "")]
            for name in directories:
                node.children[name] = FileSystemNode(
                    parent=node,  # type: ignore[arg-type]
                    file_system_type=FILE_SYSTEM_TYPES.DISK,
                    is_file=False,
                    file_system=self,
                    name=name,
                )
            for name in files:
                node.children[name] = FileSystemNode(
                    parent=node,  # type: ignore[arg-type]
                    file_system_type=FILE_SYSTEM_TYPES.DISK,
                    is_file=True,
                    file_system=self,
                    name=name,
                )

        if self.ggpk:

            def add_to_directory(node, depth):
                # Return at depth 0? Root object

                root = self.directory[node.parent.get_path()] if node.parent else self.directory  # type: ignore[index]

                root.children[node.name] = FileSystemNode(  # type: ignore[assignment, union-attr]
                    parent=root,  # type: ignore[arg-type]
                    file_system_type=FILE_SYSTEM_TYPES.GGPK,
                    is_file=node.is_file,
                    file_system=self,
                    name=node.name,
                )

            if self.ggpk.directory:
                self.ggpk.directory.walk(function=add_to_directory)

        if self.index:  # type: ignore[union-attr]
            for dir_record in self.index.directories.values():
                parent = self.directory
                for directory in dir_record.path.split("/"):
                    try:
                        parent = parent.children[directory]  # type: ignore[assignment]
                    except KeyError:
                        node = FileSystemNode(
                            parent=parent,  # type: ignore[arg-type]
                            file_system_type=FILE_SYSTEM_TYPES.BUNDLE,
                            is_file=False,
                            file_system=self,
                            name=directory,
                        )
                        parent.children[directory] = node  # type: ignore[assignment]
                        parent = node  # type: ignore[assignment]

            for file_name in dir_record.files:
                node = FileSystemNode(
                    file_system=self,
                    name=file_name,
                    file_system_type=FILE_SYSTEM_TYPES.BUNDLE,
                    is_file=True,
                    parent=parent,
                )
                parent.children[file_name] = node

        return self.directory
