"""
GGPK File Module

This module provides classes for reading and working with GGPK files.

Public API:
- GGPKFile: Main facade class
- GGPKReader: Reading binary format
- GGPKRecordManager: Managing records
- GGPKDirectoryBuilder: Building directory tree
- GGPKDiffComparator: Comparing GGPK files

Internal API:
- Records: BaseRecord, FileRecord, DirectoryRecord, etc.
- Nodes: DirectoryNode
"""

from PyPoE.poe.file.ggpk.builder import GGPKFileBuilder
from PyPoE.poe.file.ggpk.file import GGPKFile
from PyPoE.poe.file.ggpk.nodes import DirectoryNode
from PyPoE.poe.file.ggpk.records import (
    BaseRecord,
    DirectoryRecord,
    DirectoryRecordEntry,
    FileRecord,
    FreeRecord,
    GGPKError,
    GGPKRecord,
    InvalidTagError,
)

__all__ = [
    "GGPKFile",
    "GGPKFileBuilder",
    "DirectoryNode",
    "BaseRecord",
    "DirectoryRecord",
    "DirectoryRecordEntry",
    "FileRecord",
    "FreeRecord",
    "GGPKError",
    "GGPKRecord",
    "InvalidTagError",
]

