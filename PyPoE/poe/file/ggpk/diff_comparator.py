"""
GGPK Diff Comparator

Responsibility: Comparing two GGPK files and finding differences.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyPoE.poe.file.ggpk.nodes import DirectoryNode

__all__ = ["GGPKDiffComparator"]

# Forward reference for GGPKFile (will be defined in file.py)
if TYPE_CHECKING:
    from PyPoE.poe.file.ggpk.file import GGPKFile
else:
    GGPKFile = Any


class GGPKDiffComparator:
    """
    Compares two GGPK files and finds differences.

    This class is responsible for:
    - Comparing file trees of two GGPK files
    - Finding new, deleted, and changed files
    - Writing diff report to file

    Example:
        >>> comparator = GGPKDiffComparator()
        >>> new, deleted, changed = comparator.compare(ggpk1, ggpk2)
    """

    def compare(
        self,
        ggpk1: "GGPKFile",
        ggpk2: "GGPKFile",
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Compare two GGPK files.

        Args:
            ggpk1: First GGPK file
            ggpk2: Second GGPK file

        Returns:
            Tuple of (new_files, deleted_files, changed_files)

        Raises:
            TypeError: If arguments are not GGPKFile instances
            ValueError: If files are not parsed or directory not built
        """
        # Import here to avoid circular dependency
        from PyPoE.poe.file.ggpk.file import GGPKFile as GGPKFileType

        if not isinstance(ggpk1, GGPKFileType) or not isinstance(ggpk2, GGPKFileType):
            raise TypeError("Both arguments must be GGPKFile instances")

        if not ggpk1.is_parsed or not ggpk2.is_parsed:
            raise ValueError("Both ggpk files must be parsed and have their directory built")

        # Collect files from both GGPK files
        files1 = self._collect_files(ggpk1)
        files2 = self._collect_files(ggpk2)

        # Find differences
        set1 = set(files1.keys())
        set2 = set(files2.keys())

        new_files = sorted(set1.difference(set2))
        deleted_files = sorted(set2.difference(set1))
        changed_files = []

        # Find changed files (same path, different hash)
        for path in sorted(set1.intersection(set2)):
            if files1[path] != files2[path]:
                changed_files.append(path)

        return new_files, deleted_files, changed_files

    def compare_and_write(
        self,
        ggpk1: "GGPKFile",
        ggpk2: "GGPKFile",
        out_file: str,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Compare two GGPK files and write diff to file.

        Args:
            ggpk1: First GGPK file
            ggpk2: Second GGPK file
            out_file: Path to output file

        Returns:
            Tuple of (new_files, deleted_files, changed_files)
        """
        new_files, deleted_files, changed_files = self.compare(ggpk1, ggpk2)

        self._write_diff(out_file, new_files, deleted_files, changed_files)

        return new_files, deleted_files, changed_files

    def _collect_files(self, ggpk: "GGPKFile") -> dict[str, bytes]:
        """
        Collect all files from GGPK directory tree.

        Args:
            ggpk: GGPKFile instance

        Returns:
            Dictionary mapping file path -> hash
        """
        from PyPoE.poe.file.ggpk.records import FileRecord

        files: dict[str, bytes] = {}

        if ggpk.directory is None:
            return files

        def add_file(node: "DirectoryNode", depth: int) -> None:
            if not isinstance(node.record, FileRecord):
                return
            files[node.get_path()] = node.record.hash

        ggpk.directory.walk(add_file)

        return files

    def _write_diff(
        self,
        out_file: str,
        new_files: list[str],
        deleted_files: list[str],
        changed_files: list[str],
    ) -> None:
        """
        Write diff report to file.

        Args:
            out_file: Path to output file
            new_files: List of new file paths
            deleted_files: List of deleted file paths
            changed_files: List of changed file paths
        """
        with open(out_file, "w") as f:
            f.write("Diff between two ggpk files\n")
            f.write("\n")

            for header, file_list in (
                ("New files", new_files),
                ("Removed files", deleted_files),
                ("Changed files", changed_files),
            ):
                f.write("\n")
                f.write("=" * 80)
                f.write("\n")
                f.write(header)
                f.write("\n\n")
                for file_path in file_list:
                    f.write(file_path)
                    f.write("\n")

