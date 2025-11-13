"""
DatRecord class for representing rows in DAT files.

This module contains the DatRecord class which represents individual rows
in DAT files.
"""

from typing import TYPE_CHECKING

from PyPoE.poe.file.dat.value import DatValue

if TYPE_CHECKING:
    from PyPoE.poe.file.dat.reader import DatReader


class DatRecord(list):
    """
    Representation of a row in a DAT file.

    DatRecord is a list-like object that represents a single row in a DAT file.
    It provides dictionary-like access to columns by name and supports
    virtual fields defined in the specification.

    Attributes:
        parent: The parent DatReader instance this DatRecord belongs to
        rowid: The rowid of this DatRecord instance
    """

    __slots__ = ["parent", "rowid"]

    def __init__(self, parent: "DatReader", rowid: int) -> None:
        """
        Initialize DatRecord.

        Args:
            parent: The parent DatReader instance this DatRecord belongs to
            rowid: The rowid of this DatRecord instance
        """
        list.__init__(self)
        self.parent = parent
        self.rowid = rowid

    def __getitem__(self, item: str | int) -> Any:
        """
        Get item by column name or index.

        Args:
            item: Column name (str) or index (int)

        Returns:
            Value for the column/index

        Raises:
            KeyError: If column name not found
            IndexError: If index out of range
        """
        if isinstance(item, str):
            if item in self.parent.table_columns:
                value = list.__getitem__(self, self.parent.table_columns[item]["index"])
                if isinstance(value, DatValue):
                    value = value.get_value()
                return value
            elif item in self.parent.specification["virtual_fields"]:  # type: ignore[union-attr]
                field = self.parent.specification["virtual_fields"][item]  # type: ignore[union-attr]
                value = [self[fn] for fn in field["fields"]]
                if field["zip"]:
                    value = zip(*value, strict=False)
                return value
            else:
                raise KeyError(item)
        return list.__getitem__(self, item)

    def __repr__(self) -> str:
        """
        Return string representation of DatRecord.

        Returns:
            String representation showing all column values
        """
        stuff = [f"{{{k}: {self[i]}}}" for i, k in enumerate(self.parent.table_columns)]
        return "[{}]".format(", ".join(stuff))

    def __hash__(self) -> int:  # type: ignore[override]
        """
        Return hash of DatRecord.

        Returns:
            Hash based on file name and rowid
        """
        return hash((self.parent.file_name, self.rowid))

    def iter(self):
        """
        Iterate over the DatRecord and return key, value and index.

        Yields:
            Tuple of (key, value, index) for each column in the record
        """
        for index, key in enumerate(self.parent.table_columns):
            yield key, self[key], index

    def keys(self):
        """
        Return the keys (column names) of this record.

        Returns:
            Dictionary keys view of column names
        """
        return self.parent.table_columns.keys()

