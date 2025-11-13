"""
GGPK Record Classes

This module contains all record types used in GGPK files:
- BaseRecord: Base class for all records
- GGPKRecord: Master record
- DirectoryRecord: Directory entry
- FileRecord: File entry
- FreeRecord: Free space marker
- DirectoryRecordEntry: Entry within directory record
"""

import io
import os
import struct
from typing import Any, BinaryIO

from PyPoE.shared.decorators import doc
from PyPoE.shared.mixins import ReprMixin

__all__ = [
    "GGPKError",
    "InvalidTagError",
    "BaseRecord",
    "MixinRecord",
    "GGPKRecord",
    "DirectoryRecord",
    "DirectoryRecordEntry",
    "FileRecord",
    "FreeRecord",
]


# =============================================================================
# Errors
# =============================================================================


class GGPKError(Exception):
    """Error raised when processing GGPK files."""

    pass


class InvalidTagError(GGPKError):
    """Error raised when an invalid tag is encountered in a GGPK file."""

    pass


# =============================================================================
# Base Classes
# =============================================================================


class BaseRecord(ReprMixin):
    """
    Base class for all GGPK record types.

    Attributes:
        _container: Parent GGPKFile instance
        length: Record length in bytes
        offset: Starting offset in GGPK file
        tag: Record tag (4 bytes, class attribute)
    """

    tag: str | None = None

    __slots__ = ["_container", "length", "offset"]

    def __init__(self, container: Any, length: int, offset: int) -> None:
        """
        Initialize base record.

        Args:
            container: Parent GGPKFile instance
            length: Record length in bytes
            offset: Starting offset in GGPK file
        """
        self._container = container
        self.length = length
        self.offset = offset

    def read(self, ggpkfile: BinaryIO) -> None:
        """
        Read this record's header from the GGPK file.

        Args:
            ggpkfile: Binary file stream
        """
        pass

    def write(self, ggpkfile: BinaryIO) -> None:
        """
        Write this record's header to the GGPK file.

        Args:
            ggpkfile: Binary file stream
        """
        ggpkfile.write(struct.pack("<i", self.length))
        ggpkfile.write(self.tag.encode() if isinstance(self.tag, str) else self.tag)


class MixinRecord:
    """
    Mixin for records that have a name.

    Provides name property with automatic length calculation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize mixin record.

        Args:
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self._name = ""
        self._name_length = 0

    @property
    def name(self) -> str:
        """
        Get the name of the file/directory.

        Returns:
            Name of the file/directory
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set the name of the file/directory.

        Automatically adjusts name_length to account for null bytes.

        Args:
            name: Name to set
        """
        self._name = name
        # Account for null bytes
        self._name_length = len(name) + 1


# =============================================================================
# Record Types
# =============================================================================


@doc(append=BaseRecord)
class GGPKRecord(BaseRecord):
    """
    The GGPKRecord is the master record of the file.

    It always contains two entries:
    - First is the root directory
    - Second is a FreeRecord

    Attributes:
        offsets: List of offsets for records referenced by this record
    """

    tag = "GGPK"

    __slots__ = BaseRecord.__slots__.copy() + ["offsets"]

    @doc(doc=BaseRecord.read)
    def read(self, ggpkfile: BinaryIO) -> None:
        """
        Read GGPK record from file.

        Args:
            ggpkfile: Binary file stream
        """
        # Should be 2, TODO?
        records = struct.unpack("<i", ggpkfile.read(4))[0]
        self.offsets = []
        for _i in range(0, records):
            self.offsets.append(struct.unpack("<q", ggpkfile.read(8))[0])

    @doc(doc=BaseRecord.write)
    def write(self, ggpkfile: BinaryIO) -> None:
        """
        Write GGPK record to file.

        Args:
            ggpkfile: Binary file stream
        """
        # Write length & tag
        super().write(ggpkfile)
        # Should always be 2
        ggpkfile.write(struct.pack("<i", 2))
        for offset in self.offsets:
            ggpkfile.write(struct.pack("<q", offset))


class DirectoryRecordEntry(ReprMixin):
    """
    Entry within a DirectoryRecord.

    Represents a single entry in a directory record, containing a hash
    and offset to the actual record.

    Attributes:
        hash: Murmur2 32-bit hash
        offset: Offset in GGPKFile
    """

    def __init__(self, hash: int, offset: int) -> None:
        """
        Initialize directory record entry.

        Args:
            hash: Murmur2 32-bit hash
            offset: Offset in GGPKFile
        """
        self.hash = hash
        self.offset = offset


@doc(append=BaseRecord)
class DirectoryRecord(MixinRecord, BaseRecord):
    """
    Represents a directory in the virtual GGPKFile file tree.

    Attributes:
        _name: Name of directory
        _name_length: Length of name (including null terminator)
        entries_length: Number of directory entries
        hash: SHA256 hash of directory contents (32 bytes)
        entries: List of DirectoryRecordEntry instances
    """

    tag = "PDIR"

    __slots__ = BaseRecord.__slots__.copy() + [
        "_name",
        "_name_length",
        "entries_length",
        "hash",
        "entries",
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize directory record.

        Args:
            *args: Additional positional arguments for BaseRecord
            **kwargs: Additional keyword arguments for BaseRecord
        """
        super().__init__(*args, **kwargs)

    @doc(doc=BaseRecord.read)
    def read(self, ggpkfile: BinaryIO) -> None:
        """
        Read directory record from file.

        Args:
            ggpkfile: Binary file stream
        """
        self._name_length = struct.unpack("<i", ggpkfile.read(4))[0]
        self.entries_length = struct.unpack("<i", ggpkfile.read(4))[0]
        self.hash = ggpkfile.read(32)
        # UTF-16 2-byte width
        self._name = ggpkfile.read(2 * (self._name_length - 1)).decode("UTF-16_LE")
        # Null Termination
        ggpkfile.seek(2, os.SEEK_CUR)
        self.entries = []
        for _i in range(0, self.entries_length):
            self.entries.append(
                DirectoryRecordEntry(
                    hash=struct.unpack("<I", ggpkfile.read(4))[0],
                    offset=struct.unpack("<q", ggpkfile.read(8))[0],
                )
            )

    @doc(doc=BaseRecord.write)
    def write(self, ggpkfile: BinaryIO) -> None:
        """
        Write directory record to file.

        Args:
            ggpkfile: Binary file stream

        Raises:
            ValueError: If hash is not 32 bytes or entries length mismatch
        """
        # Error Checking & variable preparation
        if len(self.hash) != 32:
            raise ValueError(f"Hash must be 32 bytes, was {len(self.hash)} bytes")
        if len(self.entries) != self.entries_length:
            raise ValueError("Numbers of entries must match with length")
        name_str = self._name.encode("UTF-16")
        # Write length & tag
        super().write(ggpkfile)
        ggpkfile.write(struct.pack("<i", self._name_length))
        ggpkfile.write(struct.pack("<i", self.entries_length))
        # Fixed 32-bytes
        ggpkfile.write(self.hash)
        ggpkfile.write(name_str)
        ggpkfile.write(struct.pack("<h", 0))
        # TODO: len(self.entries)
        for entry in self.entries:
            ggpkfile.write(struct.pack("<I", entry.hash))
            ggpkfile.write(struct.pack("<q", entry.offset))


@doc(append=BaseRecord)
class FileRecord(MixinRecord, BaseRecord):
    """
    Represents a file in the virtual GGPKFile file tree.

    Attributes:
        _name: Name of file
        _name_length: Length of name (including null terminator)
        hash: SHA256 hash of file contents (32 bytes)
        data_start: Starting offset of file data
        data_length: Length of file data in bytes
    """

    tag = "FILE"

    __slots__ = BaseRecord.__slots__.copy() + [
        "_name",
        "_name_length",
        "hash",
        "data_start",
        "data_length",
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize file record.

        Args:
            *args: Additional positional arguments for BaseRecord
            **kwargs: Additional keyword arguments for BaseRecord
        """
        super().__init__(*args, **kwargs)

    def extract(self, buffer: BinaryIO | None = None) -> io.BytesIO:
        """
        Extract this file contents into a memory file object.

        Args:
            buffer: GGPKFile buffer to use; if None, opens the parent
                GGPKFile and uses it as buffer

        Returns:
            BytesIO memory file buffer object containing file data
        """
        if buffer is None:
            return self._container.get_read_buffer(
                self._container._file_path_or_raw,
                self.extract,
            )

        # The buffer object is taken care of in get_read_buffer if it's a file
        buffer.seek(self.data_start)
        memfile = io.BytesIO()
        memfile.write(buffer.read(self.data_length))
        # Set the pointer to the beginning
        memfile.seek(0)
        return memfile

    def extract_to(self, directory: str, name: str | None = None) -> None:
        """
        Extract the file to the given directory.

        Args:
            directory: The directory to extract the file to
            name: The name of the file; if None, uses the file name as in the record
        """
        name = self._name if name is None else name
        path = os.path.join(directory, name)
        with open(path, "bw") as exfile:
            # TODO Mem leak?
            exfile.write(self.extract().read())

    @doc(doc=BaseRecord.read)
    def read(self, ggpkfile: BinaryIO) -> None:
        """
        Read file record from file.

        Args:
            ggpkfile: Binary file stream
        """
        self._name_length = struct.unpack("<i", ggpkfile.read(4))[0]
        self.hash = ggpkfile.read(32)
        # UTF-16 2-byte width
        self._name = ggpkfile.read(2 * (self._name_length - 1)).decode("UTF-16")
        # Null Termination
        ggpkfile.seek(2, os.SEEK_CUR)
        self.data_start = ggpkfile.tell()
        # Length 4B - Tag 4B - STRLen 4B - Hash 32B + STR ?B
        self.data_length = self.length - 44 - self._name_length * 2

        ggpkfile.seek(self.data_length, os.SEEK_CUR)

    @doc(doc=BaseRecord.write)
    def write(self, ggpkfile: BinaryIO) -> None:
        """
        Write file record to file.

        Args:
            ggpkfile: Binary file stream

        Raises:
            ValueError: If hash is not 32 bytes
        """
        # Error checking & variable preparation first
        if len(self.hash) != 32:
            raise ValueError(f"Hash must be 32 bytes, was {len(self.hash)} bytes")

        name_str = self._name.encode("UTF-16")
        # Write length & tag
        super().write(ggpkfile)
        ggpkfile.write(struct.pack("<i", self._name_length))
        # Fixed 32-bytes
        ggpkfile.write(self.hash)
        ggpkfile.write(name_str)
        ggpkfile.write(struct.pack("<h", 0))

        # TODO: Write File Contents here?


@doc(append=BaseRecord)
class FreeRecord(BaseRecord):
    """
    Represents free space in the GGPK file.

    Free records mark unused space in the GGPK file and can be reused
    for new records.

    Attributes:
        next_free: Offset of next FreeRecord in the chain
    """

    tag = "FREE"

    __slots__ = BaseRecord.__slots__.copy() + ["next_free"]

    @doc(doc=BaseRecord.read)
    def read(self, ggpkfile):
        self.next_free = struct.unpack("<q", ggpkfile.read(8))[0]
        ggpkfile.seek(self.length - 16, os.SEEK_CUR)

    @doc(doc=BaseRecord.write)
    def write(self, ggpkfile):
        # Write length & tag
        super().write(ggpkfile)
        ggpkfile.write(struct.pack("<q", self.next_free))

