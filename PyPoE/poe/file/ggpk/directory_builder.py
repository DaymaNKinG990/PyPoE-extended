"""
GGPK Directory Builder

Responsibility: Building DirectoryNode tree from GGPK records.
"""

from typing import TYPE_CHECKING

from PyPoE.poe.file.shared import ParserError

if TYPE_CHECKING:
    from PyPoE.poe.file.ggpk.nodes import DirectoryNode
    from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager
    from PyPoE.poe.file.ggpk.records import (
        BaseRecord,
    )

__all__ = ["GGPKDirectoryBuilder"]


class GGPKDirectoryBuilder:
    """
    Builds DirectoryNode tree from GGPK records.

    This class is responsible for:
    - Building root directory from GGPKRecord
    - Building directory tree recursively
    - Creating DirectoryNode instances

    Example:
        >>> builder = GGPKDirectoryBuilder()
        >>> root = builder.build_from_records(record_manager)
    """

    def build_from_records(
        self, record_manager: "GGPKRecordManager"
    ) -> "DirectoryNode":
        """
        Build root directory from records.

        Args:
            record_manager: Record manager with loaded records

        Returns:
            Root DirectoryNode

        Raises:
            ParserError: If records are invalid or missing
        """
        from PyPoE.poe.file.ggpk.nodes import DirectoryNode
        from PyPoE.poe.file.ggpk.records import DirectoryRecord, GGPKRecord

        records = record_manager.get_records()

        if not records:
            raise ParserError("No records - perform .read() first")

        # Get GGPKRecord at offset 0
        ggpk_record = records.get(0)
        if not isinstance(ggpk_record, GGPKRecord):
            raise ParserError(f"Expected GGPKRecord at offset 0, got {type(ggpk_record)}")

        # Find root DirectoryRecord
        root_record: DirectoryRecord | None = None
        for offset in ggpk_record.offsets:
            rec = records.get(offset)
            if isinstance(rec, DirectoryRecord):
                root_record = rec
                break

        if root_record is None:
            raise ParserError("GGPKRecord does not contain a DirectoryRecord")

        # Create root node
        root = DirectoryNode(
            parent=None,  # type: ignore[arg-type]
            is_file=False,
            record=root_record,
            hash="",  # Root has empty hash
        )

        # Build tree recursively
        self._build_directory_tree(root, records)

        return root

    def build_directory(
        self, parent: "DirectoryNode", record_manager: "GGPKRecordManager"
    ) -> "DirectoryNode":
        """
        Build directory tree for given parent node.

        Args:
            parent: Parent DirectoryNode
            record_manager: Record manager with loaded records

        Returns:
            Parent node (with children built)
        """
        records = record_manager.get_records()
        self._build_directory_tree(parent, records)
        return parent

    def _build_directory_tree(
        self, root: "DirectoryNode", records: dict[int, "BaseRecord"]
    ) -> None:
        """
        Build directory tree starting from root node.

        Args:
            root: Root DirectoryNode
            records: Dictionary of all records
        """
        from PyPoE.poe.file.ggpk.nodes import DirectoryNode
        from PyPoE.poe.file.ggpk.records import DirectoryRecord, FileRecord

        # Stack of (offset, hash, parent) tuples
        nodes_list: list[tuple[int, str, DirectoryNode]] = []

        # Initialize with root entries
        if isinstance(root.record, DirectoryRecord):
            for entry in root.record.entries:
                nodes_list.append((entry.offset, str(entry.hash), root))

        # Process all nodes
        while nodes_list:
            offset, hash_str, parent_node = nodes_list.pop()

            # Get record
            base_record = records.get(offset)
            if base_record is None:
                continue

            # Skip non-file/directory records
            if not isinstance(base_record, (DirectoryRecord, FileRecord)):
                continue

            # Create node
            node = DirectoryNode(
                parent=parent_node,
                is_file=isinstance(base_record, FileRecord),
                record=base_record,
                hash=hash_str,
            )

            # Add to parent's children
            parent_node.children[base_record.name] = node  # type: ignore[assignment]

            # If directory, add its entries to stack
            if node.is_directory and isinstance(base_record, DirectoryRecord):
                for entry in base_record.entries:
                    nodes_list.append((entry.offset, str(entry.hash), node))

