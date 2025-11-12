"""
Record classes for patch server.

This module contains record classes used for representing patch server data.
"""

from typing import Any

from PyPoE.poe.file.ggpk import DirectoryRecord, FileRecord
from PyPoE.shared.mixins import ReprMixin


class BaseRecordData(ReprMixin):
    """
    Sibling to :class:`PyPoE.poe.file.ggpk.BaseRecord`.

    :attr:`PyPoE.poe.file.ggpk.DirectoryNode.record` item base class.
    Built from record data, rather than pointer details from GGPK file.

    Used for each item detailed by patchserver.

    Attributes
    ----------
    _name : str
        Name of item
    hash : int
        SHA256 hash of file contents
    """

    def __init__(self, name: str, hash: int) -> None:
        """
        Initialize BaseRecordData.

        Args:
            name: Name of item
            hash: SHA256 hash of file contents
        """
        self._name = name
        self.hash = hash


class VirtualDirectoryRecord(BaseRecordData, DirectoryRecord):
    """Virtual directory record from patch server."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize VirtualDirectoryRecord."""
        super().__init__(*args, **kwargs)


class VirtualFileRecord(BaseRecordData, FileRecord):
    """Virtual file record from patch server."""

    def __init__(self, name: str, hash: int, size: int) -> None:
        """
        Initialize VirtualFileRecord.

        Args:
            name: Name of file
            hash: SHA256 hash of file contents
            size: Size of file in bytes
        """
        self.data_length = size
        super().__init__(name, hash)

