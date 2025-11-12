"""
Connection management for patch server.

This module handles socket connections to the patch server.
"""

import contextlib
import io
import socket
import struct

from PyPoE.poe.patchserver.socket_utils import socket_fd_open


class PatchConnection:
    """
    Manages connection to the patch server.

    This class is responsible for:
    - Connecting to the master patch server
    - Obtaining patch URLs
    - Managing socket file descriptors
    - Sending and receiving data
    """

    _SERVER_IPV4 = "172.65.204.172"
    _SERVER_IPV6 = "2606:4700:90:0:7976:9369:8e00:f737"
    _PORT = 12995
    _PROTO = b"\x01\x04"  # patch proto 4

    def __init__(self, master_server: str = _SERVER_IPV4, master_port: int = _PORT) -> None:
        """
        Initialize PatchConnection.

        Args:
            master_server: Domain or IP address of the master patching server
            master_port: Port to use when connecting to the master patching server
        """
        self._master_server = (master_server, master_port)
        self.sock_fd: int | None = None
        self.patch_url: str = ""
        self.patch_cdn_url: str = ""

    def connect(self) -> None:
        """
        Connect to the patch server and obtain patch URLs.

        Opens a connection to the patchserver, gets webroot details,
        detaches from socket, and stores socket file descriptor.
        """
        with socket.socket(proto=socket.IPPROTO_TCP) as sock:
            sock.connect(self._master_server)
            sock.send(PatchConnection._PROTO)
            data = io.BytesIO(sock.recv(1024))

            struct.unpack("B", data.read(1))[0]
            struct.unpack("33s", data.read(33))[0]

            url_length = struct.unpack("B", data.read(1))[0]
            self.patch_url = data.read(url_length * 2).decode("utf-16")

            struct.unpack("B", data.read(1))[0]

            url2_length = struct.unpack("B", data.read(1))[0]
            self.patch_cdn_url = data.read(url2_length * 2).decode("utf-16")

            # Close this later!
            self.sock_fd = sock.detach()

    def disconnect(self) -> None:
        """
        Disconnect from the patch server and close socket.

        Closes the socket file descriptor if it exists.
        """
        if self.sock_fd is not None:
            sock = socket_fd_open(self.sock_fd)
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)
            try:
                sock.close()
            except OSError:
                pass
            self.sock_fd = None

    def get_socket(self) -> socket.socket:
        """
        Get socket object from file descriptor.

        Returns:
            Socket object

        Raises:
            ValueError: If not connected
        """
        if self.sock_fd is None:
            raise ValueError("Not connected. Call connect() first.")
        return socket_fd_open(self.sock_fd)

    def get_version(self) -> str:
        """
        Get game version from patch URL.

        Returns:
            Game version in x.x.x.x format
        """
        if not self.patch_url:
            raise ValueError("Patch URL not available. Call connect() first.")
        return self.patch_url.strip("/").rsplit("/", maxsplit=1)[-1]

    def __del__(self) -> None:
        """Automatically close connection on deletion."""
        self.disconnect()

