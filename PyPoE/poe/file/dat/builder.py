"""
Builder Pattern for DatFile.

This module provides a Builder class for creating DatFile instances
with optional custom components.
"""

from typing import TYPE_CHECKING

from typing_extensions import Self

if TYPE_CHECKING:
    from PyPoE.poe.file.dat.caster import DatCaster
    from PyPoE.poe.file.dat.indexer import DatIndexer
    from PyPoE.poe.file.dat.parser import DatParser

from PyPoE.poe.file.dat.file import DatFile


class DatFileBuilder:
    """
    Builder for creating DatFile instances with optional components.

    This builder allows for flexible construction of DatFile objects
    with custom components (Caster, Parser, Indexer).

    Example::

        # Simple usage
        dat_file = DatFileBuilder("path/to/file.dat").build()

        # With custom components
        custom_caster = DatCaster(use_dat_value=True, x64=True)
        custom_parser = DatParser(...)
        custom_indexer = DatIndexer(...)
        dat_file = (
            DatFileBuilder("path/to/file.dat")
            .with_caster(custom_caster)
            .with_parser(custom_parser)
            .with_indexer(custom_indexer)
            .build()
        )

        # Read and use
        with open("path/to/file.dat", "rb") as f:
            dat_file.read(f)
    """

    def __init__(self, file_path: str | None = None) -> None:
        """
        Initialize DatFileBuilder.

        Args:
            file_path: Path to the DAT file (optional, can be set later)
        """
        self._file_path = file_path
        self._caster: DatCaster | None = None
        self._parser: DatParser | None = None
        self._indexer: DatIndexer | None = None
        self._use_dat_value: bool = True
        self._x64: bool = False

    def with_file_path(self, file_path: str) -> Self:
        """
        Set the file path.

        Args:
            file_path: Path to the DAT file

        Returns:
            Self for method chaining
        """
        self._file_path = file_path
        return self

    def with_caster(self, caster: "DatCaster") -> Self:
        """
        Set a custom DatCaster.

        Args:
            caster: DatCaster instance

        Returns:
            Self for method chaining
        """
        self._caster = caster
        return self

    def with_parser(self, parser: "DatParser") -> Self:
        """
        Set a custom DatParser.

        Args:
            parser: DatParser instance

        Returns:
            Self for method chaining
        """
        self._parser = parser
        return self

    def with_indexer(self, indexer: "DatIndexer") -> Self:
        """
        Set a custom DatIndexer.

        Args:
            indexer: DatIndexer instance

        Returns:
            Self for method chaining
        """
        self._indexer = indexer
        return self

    def with_dat_value(self, use_dat_value: bool) -> Self:
        """
        Configure whether to use DatValue objects.

        Args:
            use_dat_value: If True, use DatValue objects; otherwise use plain values

        Returns:
            Self for method chaining
        """
        self._use_dat_value = use_dat_value
        return self

    def with_x64(self, x64: bool) -> Self:
        """
        Configure x64 mode.

        Args:
            x64: If True, use x64 mode; otherwise use x32 mode

        Returns:
            Self for method chaining
        """
        self._x64 = x64
        return self

    def build(self) -> DatFile:
        """
        Build and return a DatFile instance with configured components.

        Returns:
            DatFile instance

        Note:
            DatFile internally creates DatReader with the configured components.
            The builder parameters are passed to DatFile._read() method.
        """
        dat_file = DatFile(file_name=self._file_path or "")
        # Store builder parameters for use in _read()
        dat_file._builder_caster = self._caster  # type: ignore[assignment, attr-defined]
        dat_file._builder_parser = self._parser  # type: ignore[assignment, attr-defined]
        dat_file._builder_indexer = self._indexer  # type: ignore[assignment, attr-defined]
        dat_file._builder_use_dat_value = self._use_dat_value  # type: ignore[attr-defined]
        dat_file._builder_x64 = self._x64  # type: ignore[attr-defined]
        return dat_file

