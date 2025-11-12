"""
Indexer for DAT file columns.

This module handles building and managing indexes for DAT file columns
to enable fast lookups.
"""

from collections import OrderedDict, defaultdict
from collections.abc import Iterable
from typing import Any

from PyPoE.poe.file.dat.record import DatRecord


class DatIndexer:
    """
    Handles indexing of DAT file columns.

    This class is responsible for:
    - Building indexes for columns
    - Managing index storage
    - Providing fast lookups
    """

    def __init__(
        self,
        specification: Any,
        columns_unique: OrderedDict,
    ) -> None:
        """
        Initialize DatIndexer.

        Args:
            specification: File specification
            columns_unique: OrderedDict of unique columns
        """
        self.specification = specification
        self.columns_unique = columns_unique
        self.index: dict[
            str, dict[Any, DatRecord] | defaultdict[Any, list[DatRecord]]
        ] = {}

    def build_index(
        self,
        table_data: list[DatRecord],
        column: str | Iterable[str] | None = None,
    ) -> None:
        """
        Builds or rebuilds the index for the specified column.

        Indexed columns can be accessed though the instance variable index and
        will return a single value for unique columns and a list for non-unique
        columns.

        For example:
        self.index[column_name][indexed_value]

        .. warning::
            This method only works for columns that are marked as unique in the
            specification.

        Parameters
        ----------
        column : str or Iterable or None
            if specified the index will the built for the specified column
            or iterable of columns
            if not specified, the index will be build for any 'unique' columns
            by default
        table_data : list[DatRecord]
            List of DatRecord instances to index
        """
        columns = set()
        if column is None:
            for col in self.columns_unique:
                columns.add(col)
        elif isinstance(column, str):
            columns.add(column)
        elif isinstance(column, Iterable):
            for c in column:
                columns.add(c)

        columns_1to1 = set()
        columns_1to_n = set()
        columns_n_to_n = set()
        for col in columns:
            if col in self.columns_unique:
                self.index[col] = {}
                columns_1to1.add(col)
            elif self.specification.fields[col].type.startswith("ref|list"):  # type: ignore[union-attr]
                columns_n_to_n.add(col)
                self.index[col] = defaultdict(list)  # type: ignore[assignment]
            else:
                columns_1to_n.add(col)
                self.index[col] = defaultdict(list)  # type: ignore[assignment]

        # Second loop - build indexes
        for row in table_data:
            for col in columns_1to1:
                self.index[col][row[col]] = row  # type: ignore[index]
            for col in columns_1to_n:
                self.index[col][row[col]].append(row)  # type: ignore[index]
            for col in columns_n_to_n:
                for value in row[col]:
                    self.index[col][value].append(row)  # type: ignore[index]

    def get_index(self, column: str) -> dict[Any, DatRecord] | defaultdict[Any, list[DatRecord]]:
        """
        Get index for a column.

        Args:
            column: Column name

        Returns:
            Index dictionary for the column

        Raises:
            KeyError: If index not built for this column
        """
        if column not in self.index:
            raise KeyError(f"Index not built for column: {column}")
        return self.index[column]

    def has_index(self, column: str) -> bool:
        """
        Check if index exists for a column.

        Args:
            column: Column name

        Returns:
            True if index exists, False otherwise
        """
        return column in self.index

