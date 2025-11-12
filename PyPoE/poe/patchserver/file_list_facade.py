"""
PatchFileList class - Facade for patch file list operations.

This module contains the PatchFileList class which provides a simplified
interface for retrieving and managing file lists from the patch server.
"""

from PyPoE.poe.patchserver.file_list import PatchFileListBuilder
from PyPoE.poe.patchserver.patch import Patch
from PyPoE.poe.patchserver.protocol import PatchProtocolParser


class PatchFileList:
    """
    Facade for patch file list operations.

    This class provides a simplified interface for:
    - Retrieving file lists from patch server
    - Managing directory structure
    - Updating file lists

    Attributes
    ----------
    patch : Patch
        Store patch server details
    directory : DirectoryNodeExtended
        Store patch file list data as DirectoryNode
    """

    def __init__(self, patch: Patch, socket_timeout: float = 1.0) -> None:
        """
        Initialize PatchFileList and automatically fetch root file list.

        Parameters
        ----------
        patch : Patch
            A Patch object
        socket_timeout : float
            Socket timeout value in seconds
        """
        self.patch = patch
        self._connection = patch._connection
        self._protocol = PatchProtocolParser(sock=self._connection.get_socket())
        self._builder = PatchFileListBuilder(
            connection=self._connection,
            protocol=self._protocol,
            socket_timeout=socket_timeout,
        )

        # Expose directory for backward compatibility
        self.directory = self._builder.directory

        # Get the root filelist
        self.update_filelist([""])

    def __del__(self) -> None:
        """Detach socket on instance deletion."""
        if hasattr(self, "_builder"):
            self._builder.__del__()

    def update_filelist(self, folders: list[str]) -> None:
        """
        Get file details for folders from the patch server.

        Delegates to PatchFileListBuilder.

        Parameters
        ----------
        folders : list[str]
            The list of folders to get details for
        """
        self._builder.update_filelist(folders)

