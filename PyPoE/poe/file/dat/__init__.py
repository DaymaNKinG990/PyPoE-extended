"""
DAT file format support.

This module has been refactored into submodules for better organization:
- value.py: DatValue class
- record.py: DatRecord class
- caster.py: DatCaster for type casting
- parser.py: DatParser for parsing binary data
- indexer.py: DatIndexer for indexing
- reader.py: DatReader (simplified, uses composition)
- file.py: DatFile (main interface)
- relational.py: RelationalReader
"""

# Export constants
from PyPoE.poe.file.dat.file import DatFile
from PyPoE.poe.file.dat.parser import DAT_FILE_MAGIC_NUMBER
from PyPoE.poe.file.dat.relational import RelationalReader

__all__ = [
    "DatFile",
    "RelationalReader",
    "DAT_FILE_MAGIC_NUMBER",
]

