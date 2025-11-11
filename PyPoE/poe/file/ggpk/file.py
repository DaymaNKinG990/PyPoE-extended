"""
GGPK File (Facade)

Main facade class for working with GGPK files.
Uses specialized classes for different responsibilities.
"""

from typing import Any, BinaryIO

from PyPoE.poe.file.ggpk.diff_comparator import GGPKDiffComparator
from PyPoE.poe.file.ggpk.directory_builder import GGPKDirectoryBuilder
from PyPoE.poe.file.ggpk.nodes import DirectoryNode
from PyPoE.poe.file.ggpk.reader import GGPKReader
from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager
from PyPoE.poe.file.ggpk.records import BaseRecord
from PyPoE.poe.file.shared import AbstractFileReadOnly
from PyPoE.shared import InheritedDocStringsMeta
from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)

__all__ = ["GGPKFile"]


class GGPKFile(AbstractFileReadOnly, metaclass=InheritedDocStringsMeta):
    """
    Representation of a .ggpk file (Facade pattern).

    This class coordinates specialized components:
    - GGPKReader: Reading binary format
    - GGPKRecordManager: Managing records
    - GGPKDirectoryBuilder: Building directory tree
    - GGPKDiffComparator: Comparing files

    Attributes
    ----------
    directory : DirectoryNode | None
        Root DirectoryNode instance
    records : dict[int, BaseRecord]
        Mapping of offset -> record instances (deprecated, use record_manager)

    Example:
        >>> ggpk = GGPKFile()
        >>> ggpk.read("Content.ggpk")
        >>> ggpk.directory_build()
        >>> node = ggpk["Metadata/StatDescriptions/stat_descriptions.txt"]
    """

    EXTENSION = ".ggpk"

    def __init__(
        self,
        reader: GGPKReader | None = None,
        record_manager: GGPKRecordManager | None = None,
        directory_builder: GGPKDirectoryBuilder | None = None,
        diff_comparator: GGPKDiffComparator | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize GGPKFile.

        Args:
            reader: GGPKReader instance (created if None)
            record_manager: GGPKRecordManager instance (created if None)
            directory_builder: GGPKDirectoryBuilder instance (created if None)
            diff_comparator: GGPKDiffComparator instance (created if None)
            *args: Additional arguments for AbstractFileReadOnly
            **kwargs: Additional keyword arguments for AbstractFileReadOnly
        """
        super().__init__(*args, **kwargs)

        # Initialize components (DI pattern)
        # Use 'is None' instead of 'or' because empty managers are falsy
        self._reader = reader if reader is not None else GGPKReader(container=self)
        self._record_manager = (
            record_manager if record_manager is not None else GGPKRecordManager()
        )
        self._directory_builder = (
            directory_builder if directory_builder is not None else GGPKDirectoryBuilder()
        )
        self._diff_comparator = (
            diff_comparator if diff_comparator is not None else GGPKDiffComparator()
        )

        # State
        self.directory: DirectoryNode | None = None
        self._file_path_or_raw: str | bytes | BinaryIO | None = None

        # Backward compatibility: expose records as property
        self._records: dict[int, BaseRecord] = {}

    @property
    def records(self) -> dict[int, BaseRecord]:
        """
        Get all records (backward compatibility).

        Returns:
            Dictionary mapping offset -> record
        """
        return self._record_manager.get_records()

    @records.setter
    def records(self, value: dict[int, BaseRecord]) -> None:
        """
        Set records (backward compatibility).

        Args:
            value: Dictionary of records
        """
        self._record_manager.clear()
        for offset, record in value.items():
            self._record_manager.add_record(offset, record)
        self._records = value

    def __getitem__(self, item: str) -> DirectoryNode:
        """
        Get node by file path.

        Args:
            item: File path or "ROOT"

        Returns:
            DirectoryNode instance

        Raises:
            ValueError: If directory is not built
            FileNotFoundError: If file was not found
            TypeError: If result is not a DirectoryNode
        """
        if self.directory is None:
            raise ValueError("Directory not build")
        if item == "ROOT":
            return self.directory

        result = self.directory[item]
        if not isinstance(result, DirectoryNode):
            raise TypeError(f"Expected DirectoryNode, got {type(result)}")
        return result

    def _is_parsed(self) -> bool:
        """
        Check if directory has been built.

        Returns:
            True if directory is built, False otherwise
        """
        return self.directory is not None

    is_parsed = property(fget=_is_parsed)

    def _read(self, buffer: BinaryIO, *args: Any, **kwargs: Any) -> None:
        """
        Read records from file into record manager.

        Args:
            buffer: Binary file stream
            *args: Additional arguments (unused)
            **kwargs: Additional keyword arguments (unused)
        """
        # Use GGPKReader to read all records
        records = self._reader.read_file(buffer)

        # Store in record manager
        self._record_manager.clear()
        for offset, record in records.items():
            self._record_manager.add_record(offset, record)

        # Backward compatibility: also store in _records
        self._records = records

        logger.info("ggpk_file_read", records_count=len(records))

    def read(self, file_path_or_raw: str | bytes | BinaryIO, *args: Any, **kwargs: Any) -> None:
        """
        Read GGPK file.

        Args:
            file_path_or_raw: File path, bytes, or file-like object
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        super().read(file_path_or_raw, *args, **kwargs)  # type: ignore[arg-type]
        self._file_path_or_raw = file_path_or_raw

    def build_directory(self, parent: DirectoryNode | None = None) -> DirectoryNode:
        """
        Build directory tree from records.

        Args:
            parent: Parent DirectoryNode (None for root)

        Returns:
            Root or parent DirectoryNode

        Raises:
            ParserError: If records are invalid or missing
        """
        from PyPoE.poe.file.shared import ParserError

        if not self._record_manager.get_records():
            raise ParserError("No records - perform .read() first")

        if parent is None:
            # Build root directory
            root = self._directory_builder.build_from_records(self._record_manager)
            self.directory = root
            logger.info("ggpk_directory_built", root=root.name)
            return root
        else:
            # Build directory for given parent
            return self._directory_builder.build_directory(parent, self._record_manager)

    directory_build = build_directory

    def diff(
        self,
        other_ggpk: "GGPKFile",
        out_file: str | None = None,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Compare this GGPK file with another.

        Args:
            other_ggpk: Other GGPKFile instance
            out_file: Optional output file for diff report

        Returns:
            Tuple of (new_files, deleted_files, changed_files)

        Raises:
            TypeError: If other_ggpk is not a GGPKFile instance
            ValueError: If files are not parsed or directory not built
        """
        if out_file:
            return self._diff_comparator.compare_and_write(self, other_ggpk, out_file)
        else:
            return self._diff_comparator.compare(self, other_ggpk)

