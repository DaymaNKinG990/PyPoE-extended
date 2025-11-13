"""
Patch class - Facade for patch server operations.

This module contains the Patch class which provides a simplified interface
for connecting to and downloading files from the patch server.
"""

from PyPoE.poe.patchserver.connection import PatchConnection
from PyPoE.poe.patchserver.downloader import PatchDownloader


class Patch:
    """
    Facade for patch server operations.

    This class provides a simplified interface for:
    - Connecting to the patch server
    - Downloading files
    - Getting version information

    Attributes:
        patch_url: Base patch url for the current PoE version
        patch_cdn_url: Load-balanced patching url including port
        sock_fd: Socket file descriptor
    """

    def __init__(self, master_server: str = PatchConnection._SERVER_IPV4, master_port: int = PatchConnection._PORT) -> None:
        """
        Initialize Patch and automatically fetch patching URLs.

        Args:
            master_server: Domain or IP address of the master patching server
            master_port: Port to use when connecting to the master patching server
        """
        self._connection = PatchConnection(master_server, master_port)
        self._connection.connect()
        self._downloader = PatchDownloader(self._connection)

        # Expose URLs for backward compatibility
        self.patch_url = self._connection.patch_url
        self.patch_cdn_url = self._connection.patch_cdn_url
        self.sock_fd = self._connection.sock_fd

    def __del__(self) -> None:
        """
        Automatically close connection on deletion.
        """
        self._connection.disconnect()

    def update_patch_urls(self) -> None:
        """
        Update patch URLs from master server.

        Disconnects and reconnects to fetch fresh URLs from the master server.
        Delegates to PatchConnection.
        """
        self._connection.disconnect()
        self._connection.connect()
        self.patch_url = self._connection.patch_url
        self.patch_cdn_url = self._connection.patch_cdn_url
        self.sock_fd = self._connection.sock_fd

    def download(self, file_path: str, dst_dir: str | None = None, dst_file: str | None = None) -> None:
        """
        Download file from patch server to disk.

        Delegates to PatchDownloader.

        Args:
            file_path: Path of the file relative to the content.ggpk root directory
            dst_dir: Write the file to the specified directory (optional)
            dst_file: Write the file to the specified location (optional)
        """
        self._downloader.download(file_path, dst_dir=dst_dir, dst_file=dst_file)

    def download_raw(self, file_path: str) -> bytes:
        """
        Download raw bytes from patch server.

        Delegates to PatchDownloader.

        Args:
            file_path: Path of the file relative to the content.ggpk root directory

        Returns:
            The raw contents of the file in bytes
        """
        return self._downloader.download_raw(file_path)

    @property
    def version(self) -> str:
        """
        Get game version from patch URL.

        Returns
        -------
        str
            Game version in x.x.x.x format
        """
        return self._connection.get_version()

