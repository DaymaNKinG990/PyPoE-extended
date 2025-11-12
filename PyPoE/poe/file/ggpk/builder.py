"""
Builder Pattern for GGPKFile.

This module provides a Builder class for creating GGPKFile instances
with optional custom components.
"""

from typing import TYPE_CHECKING

from typing_extensions import Self

if TYPE_CHECKING:
    from PyPoE.poe.file.ggpk.diff_comparator import GGPKDiffComparator
    from PyPoE.poe.file.ggpk.directory_builder import GGPKDirectoryBuilder
    from PyPoE.poe.file.ggpk.reader import GGPKReader
    from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager

from PyPoE.poe.file.ggpk.file import GGPKFile


class GGPKFileBuilder:
    """
    Builder for creating GGPKFile instances with optional components.

    This builder allows for flexible construction of GGPKFile objects
    with custom components (Reader, RecordManager, DirectoryBuilder, etc.).

    Example::

        # Simple usage
        ggpk = GGPKFileBuilder("path/to/content.ggpk").build()

        # With custom components
        custom_reader = GGPKReader(...)
        custom_manager = GGPKRecordManager(...)
        ggpk = (
            GGPKFileBuilder("path/to/content.ggpk")
            .with_reader(custom_reader)
            .with_record_manager(custom_manager)
            .build()
        )

        # Read and use
        with open("path/to/content.ggpk", "rb") as f:
            ggpk.read(f)
            ggpk.directory_build()
    """

    def __init__(self, file_path: str | None = None) -> None:
        """
        Initialize GGPKFileBuilder.

        Args:
            file_path: Path to the GGPK file (optional, can be set later)
        """
        self._file_path = file_path
        self._reader: GGPKReader | None = None
        self._record_manager: GGPKRecordManager | None = None
        self._directory_builder: GGPKDirectoryBuilder | None = None
        self._diff_comparator: GGPKDiffComparator | None = None

    def with_file_path(self, file_path: str) -> Self:
        """
        Set the file path.

        Args:
            file_path: Path to the GGPK file

        Returns:
            Self for method chaining
        """
        self._file_path = file_path
        return self

    def with_reader(self, reader: "GGPKReader") -> Self:
        """
        Set a custom GGPKReader.

        Args:
            reader: GGPKReader instance

        Returns:
            Self for method chaining
        """
        self._reader = reader
        return self

    def with_record_manager(self, manager: "GGPKRecordManager") -> Self:
        """
        Set a custom GGPKRecordManager.

        Args:
            manager: GGPKRecordManager instance

        Returns:
            Self for method chaining
        """
        self._record_manager = manager
        return self

    def with_directory_builder(self, builder: "GGPKDirectoryBuilder") -> Self:
        """
        Set a custom GGPKDirectoryBuilder.

        Args:
            builder: GGPKDirectoryBuilder instance

        Returns:
            Self for method chaining
        """
        self._directory_builder = builder
        return self

    def with_diff_comparator(self, comparator: "GGPKDiffComparator") -> Self:
        """
        Set a custom GGPKDiffComparator.

        Args:
            comparator: GGPKDiffComparator instance

        Returns:
            Self for method chaining
        """
        self._diff_comparator = comparator
        return self

    def build(self) -> GGPKFile:
        """
        Build and return a GGPKFile instance with configured components.

        Returns:
            GGPKFile instance

        Raises:
            ValueError: If file_path is required but not set
        """
        # GGPKFile can be created without file_path (set later via read())
        # Note: GGPKFile inherits from AbstractFileReadOnly which accepts file_path via kwargs
        return GGPKFile(
            file_path=self._file_path,
            reader=self._reader,
            record_manager=self._record_manager,
            directory_builder=self._directory_builder,
            diff_comparator=self._diff_comparator,
        )

