"""
DatReader class for reading DAT files.

This module contains the DatReader class which coordinates parsing, casting,
and indexing of DAT files using composition of specialized classes.
"""

from collections.abc import Iterable
from io import BytesIO
from typing import Any

from PyPoE.poe.file.dat.caster import DatCaster
from PyPoE.poe.file.dat.indexer import DatIndexer
from PyPoE.poe.file.dat.parser import DatParser
from PyPoE.poe.file.dat.record import DatRecord
from PyPoE.poe.file.specification.errors import SpecificationError
from PyPoE.poe.file.specification.fields import Specification
from PyPoE.shared.mixins import ReprMixin


class DatReader(ReprMixin):
    """
    Reader for DAT files using composition of specialized classes.

    This class coordinates:
    - DatParser: Parsing binary data
    - DatCaster: Type casting
    - DatIndexer: Index building

    Attributes:
        file_name: File name
        table_data: List of rows containing DatRecord entries
        index: Indexes for columns (built if auto_build_index is True)
        specification: File specification
        parser: DatParser instance
        caster: DatCaster instance
        indexer: DatIndexer instance
    """

    def __init__(
        self,
        file_name: str,
        *args: Any,
        use_dat_value: bool = True,
        specification: Specification | None = None,
        auto_build_index: bool = False,
        x64: bool = False,
    ) -> None:
        """
        Initialize DatReader.

        Args:
            file_name: Name of the dat file
            *args: Additional positional arguments (unused)
            use_dat_value: Whether to use DatValue instances or values
            specification: Specification to use
            auto_build_index: Whether to automatically build the index for
                unique columns after reading
            x64: Whether the reader should run in 64 bit mode for dat64 files

        Raises:
            SpecificationError: If the dat file is not in the specification
        """
        self.file_name = file_name
        self.auto_build_index = auto_build_index
        self.x64 = x64

        # Fix for the look up
        _file_name = file_name.replace(".dat64", ".dat") if x64 else file_name

        # Process specification
        if specification is None:
            raise SpecificationError(
                SpecificationError.ERRORS.RUNTIME_MISSING_SPECIFICATION,
                "No specification provided. Use FileParserFactory.default().get_specification() "
                "or load specification manually.",
            )
        else:
            specification = specification[_file_name]  # type: ignore[index]
        self.specification = specification

        # Store use_dat_value for backward compatibility
        self.use_dat_value = use_dat_value

        # Create specialized components via composition
        self.caster = DatCaster(use_dat_value=use_dat_value, x64=x64)
        self.parser = DatParser(
            file_name=file_name,
            specification=specification,
            caster=self.caster,
            x64=x64,
        )

        # Get column information from specification
        for var in ("columns", "columns_all", "columns_zip", "columns_data", "columns_unique"):
            setattr(self, var, getattr(specification, var))

        # Create indexer
        self.indexer = DatIndexer(
            specification=specification,
            columns_unique=self.columns_unique,  # type: ignore[attr-defined]
        )

        # File structure (set by read())
        self.file_length: int = 0
        self.data_offset: int = 0
        self.table_length: int = 0
        self.table_record_length: int = 0
        self.table_rows: int = 0
        self.table_data: list[DatRecord] = []

        # Expose index from indexer
        self.index = self.indexer.index

        # Expose table_columns from parser
        self.table_columns = self.parser.table_columns

    def __iter__(self) -> Any:
        """
        Iterate over table data.

        Returns:
            Iterator over DatRecord instances
        """
        return iter(self.table_data)

    def __getitem__(self, item: int) -> Any:
        """
        Get row by index.

        Args:
            item: Row index

        Returns:
            DatRecord instance at the specified index
        """
        return self.table_data[item]

    def read(self, raw: bytes | BytesIO) -> list[DatRecord]:
        """
        Read and parse DAT file.

        Args:
            raw: Raw file bytes or BytesIO

        Returns:
            List of DatRecord instances
        """
        # Parse file structure
        file_raw, file_length, data_offset, table_rows, table_record_length = (
            self.parser.parse_file(raw)
        )

        # Store file structure
        self.file_length = file_length
        self.data_offset = data_offset
        self.table_rows = table_rows
        self.table_length = data_offset - 4
        self.table_record_length = table_record_length

        # Parse all rows
        self.table_data = []
        for i in range(0, table_rows):
            row = self.parser.parse_row(
                file_raw=file_raw,
                data_offset=data_offset,
                rowid=i,
                table_record_length=table_record_length,
                parent=self,
            )
            self.table_data.append(row)

        # Build index if requested
        if self.auto_build_index:
            self.build_index()

        return self.table_data

    def build_index(self, column: str | Iterable[str] | None = None) -> None:
        """
        Build or rebuild index for specified column(s).

        Delegates to DatIndexer. If column is not specified, builds index
        for all unique columns.

        Args:
            column: Column name(s) to build index for, or None for all unique columns
        """
        self.indexer.build_index(self.table_data, column=column)

    def row_iter(self) -> Any:
        """
        Return iterator over rows.

        Returns:
            Iterator over DatRecord instances
        """
        return iter(self.table_data)

    def column_iter(self) -> Any:
        """
        Iterate over columns.

        Yields:
            List of values for each column
            Values per column
        """
        for ci, _column in enumerate(self.table_columns):
            yield [item[ci] for item in self]

