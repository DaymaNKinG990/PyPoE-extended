# Protocol Interfaces Guide

## Overview

This guide explains how to use Protocol interfaces in PyPoE for better Interface Segregation Principle (ISP) compliance.

## Why Protocol Interfaces?

### Problem: Monolithic Abstract Base Classes

Before Protocol interfaces, all file classes had to inherit from `AbstractFileReadOnly`, which required implementing ALL methods, even if a class only needed some of them:

```python
# ❌ Old way: Must implement ALL methods
class GGPKFile(AbstractFileReadOnly):
    def read(self, ...): ...      # Needed
    def get_read_buffer(self, ...): ...  # Needed
    def write(self, ...): ...     # NOT needed (read-only format!)
    # ... 10+ more methods
```

### Solution: Protocol Interfaces

Protocol interfaces allow classes to implement only the interfaces they need:

```python
# ✅ New way: Implement only what you need
from PyPoE.poe.file.shared.protocols import IReadable, IBufferable

class GGPKFile(IReadable, IBufferable):  # NOT IWritable!
    def read(self, ...): ...
    def get_read_buffer(self, ...): ...
    # No write() method needed!
```

## Available Protocols

### IReadable

Protocol for classes that can read files.

```python
from PyPoE.poe.file.shared.protocols import IReadable

class MyReader(IReadable):
    def read(self, file_path_or_raw: str | bytes | BytesIO, *args, **kwargs) -> Any:
        # Read file data
        ...
```

**Implemented by:**
- `AbstractFileReadOnly`
- `AbstractFile`
- `GGPKFile`
- `DatFile`
- `BundleFile`
- All file classes

### IBufferable

Protocol for classes that can provide read buffers.

```python
from PyPoE.poe.file.shared.protocols import IBufferable

class MyBufferable(IBufferable):
    def get_read_buffer(
        self,
        file_path_or_raw: str | bytes | BytesIO,
        function: Callable,
        *args,
        **kwargs
    ) -> Any:
        # Get buffer and call function
        ...
```

**Implemented by:**
- `AbstractFileReadOnly`
- `AbstractFile`
- All file classes

### IWritable

Protocol for classes that can write files.

```python
from PyPoE.poe.file.shared.protocols import IWritable

class MyWriter(IWritable):
    def write(self, file_path: str, *args, **kwargs) -> Any:
        # Write file data
        ...
```

**Implemented by:**
- `AbstractFile` (and subclasses that support writing)
- `DatFile`
- `BundleFile`
- **NOT** `GGPKFile` (read-only format)

### ISeekable

Protocol for classes that support seeking in buffers.

```python
from PyPoE.poe.file.shared.protocols import ISeekable

class MySeekable(ISeekable):
    def seek(self, offset: int, whence: int = 0) -> int:
        # Seek to position
        ...
    
    def tell(self) -> int:
        # Get current position
        ...
```

### IDecompressable

Protocol for classes that can decompress data.

```python
from PyPoE.poe.file.shared.protocols import IDecompressable

class MyDecompressable(IDecompressable):
    def decompress(self, data: bytes) -> bytes:
        # Decompress data
        ...
```

### IFileSystemNode

Protocol for file system nodes (files and directories).

```python
from PyPoE.poe.file.shared.protocols import IFileSystemNode

class MyNode(IFileSystemNode):
    @property
    def name(self) -> str: ...
    
    @property
    def parent(self) -> IFileSystemNode | None: ...
    
    @property
    def children(self) -> dict[str, IFileSystemNode]: ...
    
    def get_path(self) -> str: ...
```

## Usage Examples

### Example 1: Creating a Read-Only File Class

```python
from PyPoE.poe.file.shared.protocols import IReadable, IBufferable

class MyReadOnlyFile(IReadable, IBufferable):
    """Read-only file that implements only reading protocols."""
    
    def read(self, file_path_or_raw: str | bytes | BytesIO, *args, **kwargs):
        # Read implementation
        ...
    
    def get_read_buffer(self, file_path_or_raw, function, *args, **kwargs):
        # Buffer implementation
        ...
```

### Example 2: Type Hints with Protocols

```python
from PyPoE.poe.file.shared.protocols import IReadable

def process_file(file: IReadable) -> None:
    """Process any file that implements IReadable."""
    file.read("path/to/file")
    # Works with GGPKFile, DatFile, BundleFile, etc.
```

### Example 3: Multiple Protocols

```python
from PyPoE.poe.file.shared.protocols import IReadable, IWritable, IBufferable

class MyReadWriteFile(IReadable, IWritable, IBufferable):
    """File that supports both reading and writing."""
    
    def read(self, ...): ...
    def write(self, ...): ...
    def get_read_buffer(self, ...): ...
```

### Example 4: Using with AbstractFileReadOnly (Backward Compatibility)

```python
from PyPoE.poe.file.shared import AbstractFileReadOnly
from PyPoE.poe.file.shared.protocols import IReadable

# AbstractFileReadOnly already implements IReadable and IBufferable
class MyFile(AbstractFileReadOnly):
    def _read(self, buffer, *args, **kwargs):
        # Implementation
        ...

# Can be used as IReadable
def process(file: IReadable):
    file.read("path")

my_file = MyFile()
process(my_file)  # ✅ Works!
```

## Migration Guide

### For New Code

**Use Protocols directly:**

```python
from PyPoE.poe.file.shared.protocols import IReadable, IBufferable

class MyNewFile(IReadable, IBufferable):
    def read(self, ...): ...
    def get_read_buffer(self, ...): ...
```

### For Existing Code

**Keep using AbstractFileReadOnly (backward compatible):**

```python
from PyPoE.poe.file.shared import AbstractFileReadOnly

class MyExistingFile(AbstractFileReadOnly):
    def _read(self, buffer, *args, **kwargs):
        # Implementation
        ...
```

**Or migrate to Protocols:**

```python
from PyPoE.poe.file.shared.protocols import IReadable, IBufferable

class MyExistingFile(IReadable, IBufferable):
    def read(self, ...): ...
    def get_read_buffer(self, ...): ...
```

## Benefits

1. **Interface Segregation Principle (ISP)**: Classes implement only what they need
2. **Type Safety**: MyPy checks Protocol compliance
3. **Flexibility**: Can use Protocols without inheritance
4. **Backward Compatibility**: AbstractFileReadOnly still works
5. **Better Documentation**: Clear interface contracts

## Best Practices

1. **Use Protocols for type hints**: `def process(file: IReadable): ...`
2. **Implement only needed Protocols**: Don't implement `IWritable` if you don't write
3. **Document Protocol usage**: Add comments about which Protocols your class implements
4. **Use AbstractFileReadOnly for convenience**: If you need default implementations

## See Also

- `PyPoE.poe.file.shared.protocols` - Protocol definitions
- `PyPoE.poe.file.shared` - Abstract base classes
- `ARCHITECTURE_ANALYSIS.md` - Architecture analysis

