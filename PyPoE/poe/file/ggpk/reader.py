"""
GGPK File Reader

Responsibility: Reading and parsing binary GGPK file format.
"""

import os
import struct
from typing import BinaryIO

from PyPoE.poe.file.ggpk.records import (
    BaseRecord,
    DirectoryRecord,
    FileRecord,
    FreeRecord,
    GGPKRecord,
    InvalidTagError,
)
from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)


class GGPKReader:
    """
    Reads and parses binary GGPK file format.

    This class is responsible for:
    - Reading records from binary stream
    - Parsing record headers (length, tag)
    - Creating appropriate record instances
    - Handling invalid tags and seeking next record

    Example:
        >>> reader = GGPKReader()
        >>> with open("Content.ggpk", "rb") as f:
        ...     records = reader.read_file(f)
        >>> print(f"Read {len(records)} records")
    """

    # Record tags in binary format
    TAG_FILE = b"FILE"
    TAG_FREE = b"FREE"
    TAG_PDIR = b"PDIR"
    TAG_GGPK = b"GGPK"

    # All known tags for seeking
    KNOWN_TAGS = (TAG_FILE, TAG_FREE, TAG_PDIR, TAG_GGPK)

    def __init__(self, container=None) -> None:
        """
        Initialize GGPK reader.

        Args:
            container: Optional GGPKFile container (for backward compatibility)
        """
        self._container = container

    def read_file(self, buffer: BinaryIO) -> dict[int, BaseRecord]:
        """
        Read all records from GGPK file.

        Args:
            buffer: Binary file stream

        Returns:
            Dictionary mapping offset -> BaseRecord

        Raises:
            InvalidTagError: If invalid tag encountered and cannot recover
        """
        records: dict[int, BaseRecord] = {}
        offset = 0
        size = buffer.seek(0, os.SEEK_END)

        # Reset pointer
        buffer.seek(0, os.SEEK_SET)

        while offset < size:
            try:
                self.read_record(records=records, buffer=buffer, offset=offset)
            except InvalidTagError as e:
                logger.warning("invalid_tag_seeking_next", tag=str(e.args), offset=offset)
                buffer.seek(offset)

                # Try to find next valid record
                next_offset = self._find_next_record(buffer, offset)
                if next_offset is None:
                    # No more records found
                    break
                offset = next_offset
            else:
                offset = buffer.tell()

        return records

    def read_record(
        self,
        records: dict[int, BaseRecord],
        buffer: BinaryIO,
        offset: int,
    ) -> None:
        """
        Read a single record from buffer at given offset.

        Args:
            records: Dictionary to store records in
            buffer: Binary file stream
            offset: Offset to read from

        Raises:
            InvalidTagError: If tag is not recognized
        """
        buffer.seek(offset)
        length = struct.unpack("<i", buffer.read(4))[0]
        tag = buffer.read(4)

        # Create appropriate record instance
        record = self._create_record(tag, length, offset)
        record.read(buffer)
        records[offset] = record

    def _create_record(self, tag: bytes, length: int, offset: int) -> BaseRecord:
        """
        Create record instance based on tag.

        Args:
            tag: Record tag (4 bytes)
            length: Record length
            offset: Record offset

        Returns:
            BaseRecord instance

        Raises:
            InvalidTagError: If tag is not recognized
        """
        if tag == self.TAG_FILE:
            return FileRecord(self._container, length, offset)
        elif tag == self.TAG_FREE:
            return FreeRecord(self._container, length, offset)
        elif tag == self.TAG_PDIR:
            return DirectoryRecord(self._container, length, offset)
        elif tag == self.TAG_GGPK:
            return GGPKRecord(self._container, length, offset)
        else:
            raise InvalidTagError(tag)

    def _find_next_record(self, buffer: BinaryIO, start_offset: int) -> int | None:
        """
        Find next valid record tag in buffer.

        Searches for known tags (FILE, FREE, PDIR, GGPK) starting from
        given offset. Used for recovery when invalid tag is encountered.

        Args:
            buffer: Binary file stream
            start_offset: Offset to start searching from

        Returns:
            Offset of next record, or None if not found
        """
        buffer.seek(start_offset)

        # Offset by 3 to capture things in the middle of chunks
        offset = start_offset - 3
        buffer.seek(offset)

        while True:
            chunk = buffer.read(4096)
            if not chunk:
                return None

            # Search for known tags
            for tag in self.KNOWN_TAGS:
                index = chunk.find(tag)
                if index != -1:
                    # Tag is preceded by u32 length
                    found_offset = buffer.tell() - len(chunk) + index - 4
                    buffer.seek(found_offset)
                    return found_offset

            # Move forward
            offset += 4093
            buffer.seek(offset)

            if len(chunk) < 4096:
                break

        return None

