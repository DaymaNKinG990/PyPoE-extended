"""
Socket utility functions.

This module provides utility functions for working with socket file descriptors.
"""

import socket


def socket_fd_open(socket_fd: int) -> socket.socket:
    """
    Create a TCP/IP socket object from a socket file descriptor.

    Uses :func:`socket.fromfd`.

    Parameters
    ----------
    socket_fd : int
        File descriptor to build socket from.

    Returns
    -------
    socket.socket
        Socket object
    """
    return socket.fromfd(socket_fd, socket.AF_INET, socket.SOCK_STREAM)


def socket_fd_close(sock: socket.socket) -> int:
    """
    Detach socket and return file descriptor.

    Parameters
    ----------
    sock : socket.socket
        Socket to detach

    Returns
    -------
    int
        File descriptor
    """
    return sock.detach()

