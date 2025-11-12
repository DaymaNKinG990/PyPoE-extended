"""
File list builder for patch server.

This module handles building the file list structure from patch server responses.
"""

import io
import struct
from typing import Any

from PyPoE.poe.file.ggpk import DirectoryRecord, FileRecord
from PyPoE.poe.patchserver.connection import PatchConnection
from PyPoE.poe.patchserver.node import DirectoryNodeExtended
from PyPoE.poe.patchserver.protocol import PatchProtocolParser
from PyPoE.poe.patchserver.records import VirtualDirectoryRecord, VirtualFileRecord
from PyPoE.poe.patchserver.socket_utils import socket_fd_open
from PyPoE.shared.murmur2 import murmur2_32


class PatchFileListBuilder:
    """
    Builds file list structure from patch server.

    This class is responsible for:
    - Querying patch server for folder details
    - Parsing protocol responses
    - Building directory tree structure
    """

    _PROTO_PRE = b"\x03\x00"

    def __init__(
        self,
        connection: PatchConnection,
        protocol: PatchProtocolParser | None = None,
        socket_timeout: float = 1.0,
    ) -> None:
        """
        Initialize PatchFileListBuilder.

        Args:
            connection: PatchConnection instance
            protocol: PatchProtocolParser instance (optional, created if None)
            socket_timeout: Socket timeout in seconds
        """
        self._connection = connection
        self._socket_timeout = socket_timeout
        self._sock = connection.get_socket()
        self._protocol = protocol if protocol is not None else PatchProtocolParser(sock=self._sock)
        self.directory = DirectoryNodeExtended(None, None, None)

    def update_filelist(self, folders: list[str]) -> None:
        """
        Get file details for folders from the patch server.

        Stores data in :attr:`.directory`.

        Patchserver works top down:
        PatchFileList().directory.children entries are not known
        until that directory is traversed.

        Once a directory level is traversed,
        patchserver can be queried for next directory.

        It will return item details for all items in queried directory.

        Parameters
        ----------
        folders : list[str]
            The list of folders to get details for
            Only one level at a time

        Raises
        ------
        ValueError
            If folders list contains repeated folders
        ValueError
            If root is requested alongside additional folders
        KeyError
            If the patch server sends data not understood
        """
        if len(set(folders)) != len(folders):
            raise ValueError("folder list contains non unique folder")

        folder_query = b""
        for folder in folders:
            if folder == "":
                if len(folders) > 1:
                    raise ValueError("if querying root, only root allowed")
                # query root folder (0 length folder name)
                folder_query = PatchFileListBuilder._PROTO_PRE + b"\x00"
            else:
                # test if folder is known
                try:
                    test_directory = self.directory[folder].record  # type: ignore[attr-defined]
                    if not isinstance(test_directory, DirectoryRecord):
                        raise ValueError("Must only query folders.")
                except FileNotFoundError as e:
                    raise ValueError(
                        "Queried folder unknown."
                        + " Must traverse patchserver"
                        + " top (root) to bottom"
                    ) from e

                query_folder_length = struct.pack("B", len(folder))
                query_folder_name = folder.encode("utf-16le")
                query_folder = PatchFileListBuilder._PROTO_PRE + query_folder_length + query_folder_name
                folder_query += query_folder

        self._sock.send(folder_query)
        self._sock.settimeout(self._socket_timeout)
        sock_data = self._sock.recv(2048)
        data = io.BytesIO(sock_data)
        # Set instance data, so that it can be modified by other methods
        self._protocol.data = data

        for folder in folders:
            # patch proto 4 decode
            folder_name, item_count = self._protocol.parse_file_list_header()

            print(f"{item_count} items in directory {folder_name}")

            parent = self.directory[folder]  # type: ignore[attr-defined]

            folder_directory_nodes = []

            for _item in range(0, item_count):
                header = struct.unpack("2s", self._protocol.read(2))[0]
                temp_record: VirtualFileRecord | VirtualDirectoryRecord
                if header == b"\x00\x00":
                    # File item
                    name, size, sha256sum = self._protocol.parse_file_item()
                    temp_record = VirtualFileRecord(name=name, hash=sha256sum, size=size)
                elif header == b"\x01\x00":
                    # Directory item
                    name, sha256sum = self._protocol.parse_directory_item()
                    temp_record = VirtualDirectoryRecord(name=name, hash=sha256sum)
                else:
                    raise KeyError(
                        "Unknown patch server"
                        + " item type:"
                        + f" {header!r} from query: {folder_query!r}"
                    )

                folder_directory_nodes.append(
                    DirectoryNodeExtended(
                        record=temp_record,
                        hash=murmur2_32(name.lower().encode("utf-16le")),
                        parent=parent,
                    )
                )

            parent.children = folder_directory_nodes  # type: ignore[assignment]

    def __del__(self) -> None:
        """Detach socket on instance deletion."""
        if hasattr(self, "_sock") and self._sock is not None:
            self._connection.sock_fd = self._sock.detach()

