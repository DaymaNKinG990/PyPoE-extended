"""
Patch server support.

This module has been refactored into submodules for better organization:
- connection.py: PatchConnection for socket management
- downloader.py: PatchDownloader for file downloads
- protocol.py: PatchProtocolParser for protocol parsing
- file_list.py: PatchFileListBuilder for building file lists
- hash_checker.py: PatchHashChecker for hash verification
- updater.py: PatchFileUpdater for updating files
- records.py: BaseRecordData, VirtualDirectoryRecord, VirtualFileRecord
- node.py: DirectoryNodeExtended
- patch.py: Patch (main interface, Facade)
- file_list.py: PatchFileList (main interface, Facade)
"""

from PyPoE.poe.patchserver.file_list_facade import PatchFileList

# Export utility functions
from PyPoE.poe.patchserver.hash_checker import node_check_hash, node_outdated_files
from PyPoE.poe.patchserver.patch import Patch
from PyPoE.poe.patchserver.socket_utils import socket_fd_close, socket_fd_open
from PyPoE.poe.patchserver.updater import node_update_files

__all__ = [
    "Patch",
    "PatchFileList",
    "node_check_hash",
    "node_outdated_files",
    "node_update_files",
    "socket_fd_open",
    "socket_fd_close",
]

