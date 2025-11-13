"""
Socket utility functions.

This module provides utility functions for working with socket file descriptors.
"""

import socket


def socket_fd_open(socket_fd: int) -> socket.socket:
    """
    Create a TCP/IP socket object from a socket file descriptor.

    Uses socket.fromfd to create a socket from a file descriptor.

    Args:
        socket_fd: File descriptor to build socket from

    Returns:
        Socket object
    """
    return socket.fromfd(socket_fd, socket.AF_INET, socket.SOCK_STREAM)


def socket_fd_close(sock: socket.socket) -> int:
    """
    Detach socket and return file descriptor.

    Args:
        sock: Socket to detach

    Returns:
        File descriptor
    """
    return sock.detach()

