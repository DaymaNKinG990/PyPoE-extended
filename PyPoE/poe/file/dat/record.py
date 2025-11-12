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
    Attributes
    ----------
    parent :  DatReader
        The parent DatReader instance this DatRecord instance belongs to
    rowid :  int
        The rowid of this DatRecord instance
    """

    __slots__ = ["parent", "rowid"]

    def __init__(self, parent: "DatReader", rowid: int) -> None:
        """
        Parameters
        ----------
        parent :  DatReader
            The parent DatReader instance this DatRecord instance belongs to
        rowid :  int
            The rowid of this DatRecord instance
        """
        list.__init__(self)
        self.parent = parent
        self.rowid = rowid

    def __getitem__(self, item):
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

    def __repr__(self):
        stuff = [f"{{{k}: {self[i]}}}" for i, k in enumerate(self.parent.table_columns)]
        return "[{}]".format(", ".join(stuff))

    def __hash__(self):  # type: ignore[override]
        return hash((self.parent.file_name, self.rowid))

    def iter(self):
        """
        Iterates over the DatRecord and returns key, value and index

        Yields
        ------
        str
            key
        object
            the value
        int
            index
        """
        for index, key in enumerate(self.parent.table_columns):
            yield key, self[key], index

    def keys(self):
        """
        Returns the keys (column names) of this record.

        Returns
        -------
        dict_keys
            Keys of the record
        """
        return self.parent.table_columns.keys()

