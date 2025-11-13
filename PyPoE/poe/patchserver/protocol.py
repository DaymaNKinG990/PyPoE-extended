"""
Protocol parser for patch server.

This module handles parsing of the patch server protocol.
"""

import io
import select
import socket
import struct


class PatchProtocolParser:
    """
    Parses patch server protocol messages.

    This class is responsible for:
    - Parsing protocol headers
    - Extracting variable-length strings
    - Parsing file and directory items
    """

    _PROTO_PRE = b"\x03\x00"
    _PROTO_HEADER2 = b"\x04\x00"

    def __init__(self, data: io.BytesIO | None = None, sock: socket.socket | None = None) -> None:
        """
        Initialize PatchProtocolParser.

        Args:
            data: BytesIO stream with protocol data
            sock: Socket for reading additional data if needed
        """
        self.data = data if data is not None else io.BytesIO()
        self.sock = sock

    def read(self, read_length: int) -> bytes:
        """
        Read length of data from data stream.

        Get and save more data from socket if length not met.

        Args:
            read_length: Length of data to read

        Returns:
            Requested data

        Raises:
            EOFError: If the TCP stream returned by the patch server ends unexpectedly
            ValueError: If socket is not available for reading
        """
        # The amount of data to pull from socket each recv
        # Amount recv will be < network MTU
        bufsize = 2048
        # Need to be able to set data, which is used by other methods
        data_stream = self.data
        # Need details of socket
        sock = self.sock
        if sock is None:
            raise ValueError("Socket not available for reading additional data")

        # Get the seek (cursor) position of data
        data_current = data_stream.tell()
        recv_attempts = 0
        while True:
            # no single value should be long enough to be broken
            # over more than 1 TCP packet
            if recv_attempts > 1:
                raise EOFError("Too many attempts to pull data when expecting more data")
            # Attempt to read length asked for
            data_read = data_stream.read(read_length)
            recv_attempts += 1
            # If less data than expected
            if len(data_read) < read_length:
                # Check if there is more data waiting in the socket
                # And that data waiting is not an empty TCP packet
                sockets_ready = select.select([sock], [], [], 0)
                if len(sockets_ready) < 1 or len(sock.recv(1, socket.MSG_PEEK)) < 1:
                    # If there is no more data, something is wrong
                    raise EOFError("Reached end of TCP stream when expecting more data")
                # Otherwise, create a new data stream with
                # all existing data + data pulled from socket
                data_stream.seek(0)
                data_all = data_stream.read() + sock.recv(bufsize)
                data_stream = io.BytesIO(data_all)
                data_stream.seek(data_current)
                # Set instance data, for access from other methods
                self.data = data_stream
            else:
                break
        return data_read

    def extract_varchar(self) -> str:
        """
        Extract variable length string from data stream.

        String length is first byte of data.

        Returns
        -------
        str
            Extracted variable length string
        """
        # First bytes tells length of string
        varchar_length = struct.unpack("B", self.read(1))[0]
        # String encoded utf-16 is 2*string length bytes
        varchar_length_blob = varchar_length * 2
        # Sometimes (root), length is 0, string is empty
        varchar_name = ""
        if varchar_length > 0:
            varchar_name = self.read(varchar_length_blob).decode("utf-16")
        return varchar_name

    def parse_file_list_header(self) -> tuple[str, int]:
        """
        Parse file list header from protocol.

        Returns
        -------
        tuple[str, int]
            Tuple of (folder_name, item_count)

        Raises
        ------
        KeyError
            If the patch server sends data not understood
        """
        query_header = struct.unpack("2s", self.read(2))[0]
        if query_header != PatchProtocolParser._PROTO_HEADER2:
            raise KeyError(f"Unknown patch server header: {query_header!r}")

        folder_name = self.extract_varchar()
        item_count = struct.unpack(">I", self.read(4))[0]

        return folder_name, item_count

    def parse_file_item(self) -> tuple[str, int, int]:
        """
        Parse a file item from protocol.

        Returns
        -------
        tuple[str, int, int]
            Tuple of (name, size, sha256sum)

        Raises
        ------
        KeyError
            If the patch server sends data not understood
        """
        header = struct.unpack("2s", self.read(2))[0]
        if header != b"\x00\x00":
            raise KeyError(f"Expected file item header, got: {header!r}")

        name = self.extract_varchar()

        # 4 byte unsigned int item size in bytes
        # 32 byte sha256 item checksum
        size, sha256sum = struct.unpack(">I32s", self.read(36))

        # store sha256sum as int
        sha256sum_int = int.from_bytes(sha256sum, byteorder="big")

        return name, size, sha256sum_int

    def parse_directory_item(self) -> tuple[str, int]:
        """
        Parse a directory item from protocol.

        Returns
        -------
        tuple[str, int]
            Tuple of (name, sha256sum)

        Raises
        ------
        KeyError
            If the patch server sends data not understood
        """
        header = struct.unpack("2s", self.read(2))[0]
        if header != b"\x01\x00":
            raise KeyError(f"Expected directory item header, got: {header!r}")

        name = self.extract_varchar()

        # 4 byte unsigned int item size in bytes (unused for directories)
        # 32 byte sha256 item checksum
        _size, sha256sum = struct.unpack(">I32s", self.read(36))

        # store sha256sum as int
        sha256sum_int = int.from_bytes(sha256sum, byteorder="big")

        return name, sha256sum_int

