"""
GGPK Directory Node

Represents a node in the GGPK file tree (file or directory).
"""

from typing import TYPE_CHECKING

from PyPoE.poe.file.shared import FILE_SYSTEM_TYPES, AbstractFileSystemNode

if TYPE_CHECKING:
    from PyPoE.poe.file.ggpk.records import DirectoryRecord, FileRecord

__all__ = ["DirectoryNode"]


class DirectoryNode(AbstractFileSystemNode):
    """
    Represents a node in the GGPK file tree.

    Can be either a file or a directory.

    Attributes
    ----------
    children : dict[str, DirectoryNode]
        Dictionary of child nodes (files and directories)
    parent : DirectoryNode | None
        Parent node, or None if this is the root node
    record : DirectoryRecord | FileRecord
        Associated record
    hash : str
        Hash value used by the game
    """

    __slots__ = ["record", "hash"] + AbstractFileSystemNode.__slots__

    _REPR_ARGUMENTS_IGNORE = {"parent"}

    def __init__(
        self,
        parent: "DirectoryNode | None",
        is_file: bool,
        record: "DirectoryRecord | FileRecord",
        hash: str,
    ):
        """
        Initialize directory node.

        Args:
            parent: Parent node (None for root)
            is_file: True if this is a file, False if directory
            record: Associated record
            hash: Hash value
        """
        super().__init__(
            parent=parent,  # type: ignore[arg-type]
            file_system_type=FILE_SYSTEM_TYPES.GGPK,
            is_file=is_file,
        )
        self.record: DirectoryRecord | FileRecord = record
        self.hash: str = hash

    @property
    def name(self) -> str:
        """Get node name from record."""
        return self.record.name  # type: ignore[no-any-return]

    @property
    def data(self) -> bytes:
        """
        Get file data (only for files).

        Returns:
            File contents as bytes

        Raises:
            ValueError: If node is not a file
            TypeError: If record is not a FileRecord
        """
        if self.is_file:
            from PyPoE.poe.file.ggpk.records import FileRecord

            if isinstance(self.record, FileRecord):
                return self.record.extract().read()  # type: ignore[no-any-return]
            raise TypeError("Expected FileRecord for file node")
        else:
            raise ValueError("Only files can have their data extracted")

