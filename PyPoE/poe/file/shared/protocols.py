"""
Protocol interfaces for file operations.

This module defines Protocol interfaces that follow Interface Segregation Principle (ISP),
allowing classes to implement only the interfaces they need, rather than a monolithic
abstract base class.

Usage:
    from PyPoE.poe.file.shared.protocols import IReadable, IBufferable

    class MyFile(IReadable, IBufferable):
        def read(self, path: str) -> None: ...
        def get_read_buffer(self, path: str) -> BytesIO: ...
"""

from io import BytesIO
from typing import Any, Protocol, Union

__all__ = [
    "IReadable",
    "IBufferable",
    "IWritable",
    "ISeekable",
    "IDecompressable",
    "IFileSystemNode",
]


class IReadable(Protocol):
    """
    Protocol for classes that can read files.

    This protocol defines the interface for reading file data from a path or raw bytes.
    """

    def read(self, file_path_or_raw: str | bytes | BytesIO, *args: Any, **kwargs: Any) -> Any:
        """
        Read file data from path or raw bytes.

        Args:
            file_path_or_raw: File path, bytes, or BytesIO buffer
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Self (for method chaining) or None
        """
        ...


class IBufferable(Protocol):
    """
    Protocol for classes that can provide read buffers.

    This protocol defines the interface for getting a buffer from a file path or raw data.
    """

    def get_read_buffer(
        self,
        file_path_or_raw: str | bytes | BytesIO,
        function: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Get a read buffer from file path or raw data.

        Args:
            file_path_or_raw: File path, bytes, or BytesIO buffer
            function: Function to call with buffer
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Result of calling function with buffer
        """
        ...


class IWritable(Protocol):
    """
    Protocol for classes that can write files.

    This protocol defines the interface for writing file data to a path.
    """

    def write(self, file_path: str, *args: Any, **kwargs: Any) -> Any:
        """
        Write file data to path.

        Args:
            file_path: Path to write file
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Self (for method chaining) or None
        """
        ...


class ISeekable(Protocol):
    """
    Protocol for classes that support seeking in buffers.

    This protocol defines the interface for seeking and telling position in buffers.
    """

    def seek(self, offset: int, whence: int = 0) -> int:
        """
        Seek to position in buffer.

        Args:
            offset: Offset to seek to
            whence: Where to seek from (0=start, 1=current, 2=end)

        Returns:
            New position in buffer
        """
        ...

    def tell(self) -> int:
        """
        Get current position in buffer.

        Returns:
            Current position in buffer
        """
        ...


class IDecompressable(Protocol):
    """
    Protocol for classes that can decompress data.

    This protocol defines the interface for decompressing file data.
    """

    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data.

        Args:
            data: Compressed data

        Returns:
            Decompressed data
        """
        ...


class IFileSystemNode(Protocol):
    """
    Protocol for file system nodes (files and directories).

    This protocol defines the interface for nodes in a file system tree.
    """

    @property
    def name(self) -> str:
        """Get node name."""
        ...

    @property
    def parent(self) -> Union["IFileSystemNode", None]:
        """Get parent node."""
        ...

    @property
    def children(self) -> dict[str, "IFileSystemNode"]:
        """Get child nodes."""
        ...

    def get_path(self) -> str:
        """
        Get full path from root.

        Returns:
            Full path string
        """
        ...

