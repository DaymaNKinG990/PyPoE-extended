"""
GGPK Record Manager

Responsibility: Managing collection of GGPK records.
"""

from typing import TYPE_CHECKING

from PyPoE.poe.file.ggpk.records import BaseRecord

if TYPE_CHECKING:
    pass

__all__ = ["GGPKRecordManager"]


class GGPKRecordManager:
    """
    Manages collection of GGPK records.

    This class is responsible for:
    - Storing records in a dictionary (offset -> record)
    - Providing access to records
    - Managing record lifecycle

    Example:
        >>> manager = GGPKRecordManager()
        >>> manager.add_record(0, record)
        >>> record = manager.get_record(0)
    """

    def __init__(self):
        """Initialize record manager."""
        self._records: dict[int, BaseRecord] = {}

    def add_record(self, offset: int, record: BaseRecord) -> None:
        """
        Add a record to the collection.

        Args:
            offset: Record offset in file
            record: Record instance
        """
        self._records[offset] = record

    def get_record(self, offset: int) -> BaseRecord | None:
        """
        Get record by offset.

        Args:
            offset: Record offset

        Returns:
            Record instance or None if not found
        """
        return self._records.get(offset)

    def has_record(self, offset: int) -> bool:
        """
        Check if record exists at offset.

        Args:
            offset: Record offset

        Returns:
            True if record exists, False otherwise
        """
        return offset in self._records

    def get_records(self) -> dict[int, BaseRecord]:
        """
        Get all records.

        Returns:
            Dictionary mapping offset -> record
        """
        return self._records.copy()

    def clear(self) -> None:
        """Clear all records."""
        self._records.clear()

    def __len__(self) -> int:
        """Return number of records."""
        return len(self._records)

    def __contains__(self, offset: int) -> bool:
        """Check if record exists at offset."""
        return offset in self._records

    def __getitem__(self, offset: int) -> BaseRecord:
        """
        Get record by offset (raises KeyError if not found).

        Args:
            offset: Record offset

        Returns:
            Record instance

        Raises:
            KeyError: If record not found
        """
        return self._records[offset]

