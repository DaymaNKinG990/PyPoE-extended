"""
File downloader for patch server.

This module handles downloading files from the patch server.
"""

import os
from urllib import request
from urllib.error import URLError

from PyPoE.poe.patchserver.connection import PatchConnection


class PatchDownloader:
    """
    Handles downloading files from the patch server.

    This class is responsible for:
    - Downloading files to disk
    - Downloading raw file bytes
    - Managing download paths
    """

    def __init__(self, connection: PatchConnection) -> None:
        """
        Initialize PatchDownloader.

        Args:
            connection: PatchConnection instance for accessing patch URLs
        """
        self._connection = connection

    def download(self, file_path: str, dst_dir: str | None = None, dst_file: str | None = None) -> None:
        """
        Download file from patch server to disk.

        Any intermediate directories for the write paths will be automatically
        created.

        Parameters
        ----------
        file_path : str
            Path of the file relative to the content.ggpk root directory
        dst_dir : str, optional
            Write the file to the specified directory.
            The target directory is seen as the root directory, thus the
            file will be written according to its ``file_path``
            Mutually exclusive with the ``dst_file`` argument.
        dst_file : str, optional
            Write the file to the specified location.
            Unlike dst_dir this will ignore any naming conventions from
            ``file_path``, so for example ``Data/Mods.dat`` could be written to
            ``C:/HelloWorld.txt``
            Mutually exclusive with the ``dst_dir`` argument.

        Raises
        ------
        ValueError
            if neither dst_dir or dst_file is set
        ValueError
            if the HTTP status code is not 200
        """
        if dst_dir:
            write_path = os.path.join(dst_dir, file_path)
        elif dst_file:
            write_path = dst_file
        else:
            raise ValueError("Either dst_dir or dst_file must be set")

        # Make any intermediate dirs to avoid errors
        os.makedirs(os.path.split(write_path)[0], exist_ok=True)

        # As per manual, writing should automatically find the optimal buffer
        with open(write_path, mode="wb") as f:
            f.write(self.download_raw(file_path))

    def download_raw(self, file_path: str) -> bytes:
        """
        Download raw bytes from patch server.

        Parameters
        ----------
        file_path : str
            Path of the file relative to the content.ggpk root directory

        Returns
        -------
        bytes
            The raw contents of the file in bytes

        Raises
        ------
        ValueError
            if the HTTP status code is not 200 (and it wasn't raised by urllib)
        URLError
            if connection fails
        """
        hosts = [self._connection.patch_url]
        for index, host in enumerate(hosts):
            try:
                with request.urlopen(url=f"{host}{file_path}") as robj:
                    if robj.getcode() != 200:
                        raise ValueError(f"HTTP response code: {robj.getcode()}")
                    result = robj.read()
                    if isinstance(result, bytes):
                        return result
                    return bytes(result)  # type: ignore[arg-type]
            except URLError as url_error:
                # try alternate patch url if connection refused
                if not isinstance(url_error.reason, ConnectionRefusedError) or not index < len(hosts):
                    raise url_error
        raise ValueError("Failed to download from all hosts")

