# GGPK Module Guide

## Overview

The GGPK module provides a refactored, modular architecture for working with Path of Exile's `.ggpk` files. The module follows SOLID principles and uses Dependency Injection for better testability and maintainability.

## Architecture

The GGPK module is split into specialized components:

```
PyPoE/poe/file/ggpk/
├── __init__.py              # Public API exports
├── file.py                   # GGPKFile (Facade)
├── reader.py                 # GGPKReader (binary parsing)
├── record_manager.py         # GGPKRecordManager (record collection)
├── directory_builder.py      # GGPKDirectoryBuilder (tree building)
├── diff_comparator.py         # GGPKDiffComparator (file comparison)
├── nodes.py                  # DirectoryNode (tree structure)
└── records.py                # Record classes (FileRecord, DirectoryRecord, etc.)
```

### Component Responsibilities

- **GGPKFile** (Facade): Main entry point, coordinates all components
- **GGPKReader**: Reads and parses binary GGPK format
- **GGPKRecordManager**: Manages collection of GGPK records
- **GGPKDirectoryBuilder**: Builds DirectoryNode tree from records
- **GGPKDiffComparator**: Compares two GGPK files for differences
- **DirectoryNode**: Represents nodes in the file system tree
- **Records**: BaseRecord, FileRecord, DirectoryRecord, etc.

## Quick Start

### Basic Usage

```python
from PyPoE.poe.file.ggpk import GGPKFile

# Create GGPKFile instance
ggpk = GGPKFile()

# Read GGPK file
ggpk.read("Content.ggpk")

# Build directory tree
ggpk.directory_build()

# Access files
node = ggpk["Metadata/StatDescriptions/stat_descriptions.txt"]
print(f"File: {node.name}")
print(f"Size: {node.record.length} bytes")
```

### Using Dependency Injection

```python
from PyPoE.poe.providers import create_configured_container
from PyPoE.poe.file.ggpk import GGPKFile

# Create DI container with all providers
container = create_configured_container()

# Resolve GGPKFile (components are automatically injected)
ggpk = container.resolve(GGPKFile)

# Use as normal
ggpk.read("Content.ggpk")
ggpk.directory_build()
```

### Manual Component Injection

```python
from PyPoE.poe.file.ggpk import GGPKFile
from PyPoE.poe.file.ggpk.reader import GGPKReader
from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager
from PyPoE.poe.file.ggpk.directory_builder import GGPKDirectoryBuilder
from PyPoE.poe.file.ggpk.diff_comparator import GGPKDiffComparator

# Create components manually
reader = GGPKReader()
record_manager = GGPKRecordManager()
directory_builder = GGPKDirectoryBuilder()
diff_comparator = GGPKDiffComparator()

# Inject into GGPKFile
ggpk = GGPKFile(
    reader=reader,
    record_manager=record_manager,
    directory_builder=directory_builder,
    diff_comparator=diff_comparator,
)

# Use as normal
ggpk.read("Content.ggpk")
```

## API Reference

### GGPKFile

Main facade class for working with GGPK files.

#### Methods

- `read(file_path_or_raw)`: Read GGPK file from path or binary data
- `directory_build()`: Build directory tree from records
- `diff(other_ggpk)`: Compare with another GGPK file
- `__getitem__(path)`: Access node by path (e.g., `ggpk["path/to/file"]`)

#### Properties

- `directory`: Root DirectoryNode (None until `directory_build()` is called)
- `records`: Dictionary mapping offset -> BaseRecord (backward compatibility)
- `is_parsed`: True if directory tree is built

#### Example

```python
ggpk = GGPKFile()
ggpk.read("Content.ggpk")
ggpk.directory_build()

# Access root directory
root = ggpk.directory

# Access file by path
file_node = ggpk["Metadata/StatDescriptions/stat_descriptions.txt"]

# Check if parsed
if ggpk.is_parsed:
    print("Directory tree is built")
```

### GGPKReader

Reads and parses binary GGPK format.

#### Methods

- `read_file(buffer)`: Read all records from binary stream
- `read_record(records, buffer, offset)`: Read single record

#### Example

```python
from PyPoE.poe.file.ggpk.reader import GGPKReader

reader = GGPKReader()
with open("Content.ggpk", "rb") as f:
    records = reader.read_file(f)
    print(f"Read {len(records)} records")
```

### GGPKRecordManager

Manages collection of GGPK records.

#### Methods

- `add_record(offset, record)`: Add record to collection
- `get_record(offset)`: Get record by offset
- `clear()`: Clear all records

#### Example

```python
from PyPoE.poe.file.ggpk.record_manager import GGPKRecordManager
from PyPoE.poe.file.ggpk.records import FileRecord

manager = GGPKRecordManager()
record = FileRecord(None, 100, 0)
manager.add_record(0, record)

retrieved = manager.get_record(0)
assert retrieved is record
```

### GGPKDirectoryBuilder

Builds DirectoryNode tree from GGPK records.

#### Methods

- `build_directory(records)`: Build directory tree from records dictionary

#### Example

```python
from PyPoE.poe.file.ggpk.directory_builder import GGPKDirectoryBuilder

builder = GGPKDirectoryBuilder()
directory = builder.build_directory(records)
```

### GGPKDiffComparator

Compares two GGPK files for differences.

#### Methods

- `compare(old_ggpk, new_ggpk)`: Compare two GGPK files

#### Returns

Dictionary with keys:
- `new_files`: List of new file paths
- `deleted_files`: List of deleted file paths
- `changed_files`: List of changed file paths

#### Example

```python
from PyPoE.poe.file.ggpk.diff_comparator import GGPKDiffComparator

old_ggpk = GGPKFile()
old_ggpk.read("Content.ggpk.old")
old_ggpk.directory_build()

new_ggpk = GGPKFile()
new_ggpk.read("Content.ggpk")
new_ggpk.directory_build()

comparator = GGPKDiffComparator()
diff = comparator.compare(old_ggpk, new_ggpk)

print(f"New files: {len(diff['new_files'])}")
print(f"Deleted files: {len(diff['deleted_files'])}")
print(f"Changed files: {len(diff['changed_files'])}")
```

## Record Classes

### BaseRecord

Base class for all GGPK record types.

### FileRecord

Represents a file entry in the GGPK.

#### Attributes

- `name`: File name
- `length`: File size in bytes
- `offset`: Starting offset in GGPK file
- `hash`: File hash

### DirectoryRecord

Represents a directory entry in the GGPK.

#### Attributes

- `name`: Directory name
- `entries`: List of DirectoryRecordEntry

### DirectoryNode

Represents a node in the file system tree.

#### Attributes

- `name`: Node name
- `record`: Associated BaseRecord
- `parent`: Parent DirectoryNode
- `children`: Dictionary of child nodes
- `files`: List of file nodes
- `directories`: List of directory nodes

#### Methods

- `get_path()`: Get full path from root
- `gen_walk(max_depth=-1)`: Walk tree recursively

## Migration from Old API

### Old Code

```python
from PyPoE.poe.file.ggpk import GGPKFile

ggpk = GGPKFile()
ggpk.read("Content.ggpk")
ggpk.directory_build()
```

### New Code (Same API!)

```python
from PyPoE.poe.file.ggpk import GGPKFile

ggpk = GGPKFile()
ggpk.read("Content.ggpk")
ggpk.directory_build()
```

The public API remains the same! The refactoring is internal.

## Dependency Injection

All GGPK components are registered in the DI container:

```python
from PyPoE.poe.providers import register_core_providers
from PyPoE.shared.di import DIContainer

container = DIContainer()
register_core_providers(container)

# All components are available
ggpk = container.resolve(GGPKFile)
reader = container.resolve(GGPKReader)
# etc.
```

## Error Handling

### GGPKError

Base exception for all GGPK-related errors.

### InvalidTagError

Raised when an invalid tag is encountered in the GGPK file.

```python
from PyPoE.poe.file.ggpk import GGPKFile, InvalidTagError

try:
    ggpk = GGPKFile()
    ggpk.read("Content.ggpk")
except InvalidTagError as e:
    print(f"Invalid tag encountered: {e}")
```

## Best Practices

1. **Use DI for production code**: Register components in DI container
2. **Manual injection for testing**: Inject mock components in tests
3. **Always call `directory_build()`**: After reading, build directory tree
4. **Check `is_parsed`**: Before accessing `directory` property
5. **Use path access**: `ggpk["path/to/file"]` is cleaner than walking tree

## Examples

See `examples/di_usage_example.py` for complete examples.

## See Also

- `docs/DI_INTEGRATION_GUIDE.md`: Dependency Injection guide
- `docs/GGPK_REFACTORING_PLAN.md`: Refactoring plan and architecture

