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

from PyPoE.poe.patchserver.patch import Patch
from PyPoE.poe.patchserver.file_list import PatchFileList

__all__ = [
    "Patch",
    "PatchFileList",
]

