# DatFile Refactoring Plan

## Overview

This document outlines the plan to refactor `dat.py` (988 lines) to improve architecture and maintainability.

## Current Structure

```
PyPoE/poe/file/dat.py (988 lines)
├── DatValue (~300 lines) - Value representation
├── DatRecord (~100 lines) - Row representation
├── DatReader (~400 lines) - Core reading logic
├── DatFile (~30 lines) - Main interface
└── RelationalReader (~200 lines) - Relational data access
```

## Analysis

### Current Problems

1. **DatReader is a God Object** (~400 lines)
   - Handles file reading
   - Handles data parsing
   - Handles type casting
   - Handles indexing
   - Handles column management

2. **Tight Coupling**
   - DatReader directly accesses file system
   - Hard to test in isolation
   - Difficult to mock dependencies

3. **Mixed Responsibilities**
   - Reading logic mixed with parsing logic
   - Type casting mixed with data extraction
   - Indexing logic mixed with column management

## Proposed Solution

### Phase 7.5.1: Extract Specialized Classes

Create specialized classes using composition:

```
PyPoE/poe/file/dat/
├── __init__.py              # Public API
├── file.py                  # DatFile (Facade, ~50 lines)
├── reader.py                # DatReader (simplified, ~150 lines)
├── parser.py                # DatParser (new, ~200 lines)
├── caster.py                # DatCaster (new, ~150 lines)
├── indexer.py               # DatIndexer (new, ~100 lines)
├── value.py                 # DatValue (~300 lines)
├── record.py                # DatRecord (~100 lines)
└── relational.py            # RelationalReader (~200 lines)
```

### Specialized Classes

1. **DatParser** (`parser.py`)
   - Parse binary data into structured format
   - Handle data section parsing
   - Methods: `parse_table()`, `parse_data_section()`, `parse_row()`

2. **DatCaster** (`caster.py`)
   - Type casting logic
   - Convert binary data to Python types
   - Methods: `cast_value()`, `cast_from_spec()`, `parse_cast_string()`

3. **DatIndexer** (`indexer.py`)
   - Index building and management
   - Column indexing
   - Methods: `build_index()`, `get_index()`, `add_to_index()`

4. **DatReader** (simplified, `reader.py`)
   - Coordinate parsing, casting, and indexing
   - Use composition: `DatParser`, `DatCaster`, `DatIndexer`
   - Methods: `read()`, `get_row()`, `get_column()`

5. **DatFile** (Facade, `file.py`)
   - Main interface
   - Delegates to `DatReader`
   - Methods: `read()`, `__getitem__()`, `__iter__()`

## Implementation Steps

### Step 1: Create DatParser

**File:** `PyPoE/poe/file/dat/parser.py`

**Responsibilities:**
- Parse binary data into structured format
- Handle data section parsing
- Extract table and data sections

**Methods:**
- `parse_table(buffer: bytes) -> list[dict]`
- `parse_data_section(buffer: bytes, offset: int) -> bytes`
- `parse_row(buffer: bytes, row_index: int) -> dict`

### Step 2: Create DatCaster

**File:** `PyPoE/poe/file/dat/caster.py`

**Responsibilities:**
- Type casting logic
- Convert binary data to Python types
- Handle pointer dereferencing

**Methods:**
- `cast_value(value: bytes, cast_type: str) -> Any`
- `cast_from_spec(specification, casts, offset: int) -> Any`
- `parse_cast_string(caststr: str) -> tuple[str, tuple]`

### Step 3: Create DatIndexer

**File:** `PyPoE/poe/file/dat/indexer.py`

**Responsibilities:**
- Index building and management
- Column indexing
- Fast lookups

**Methods:**
- `build_index(column_name: str) -> dict`
- `get_index(column_name: str) -> dict`
- `add_to_index(column_name: str, value: Any, row_index: int) -> None`

### Step 4: Refactor DatReader

**File:** `PyPoE/poe/file/dat/reader.py`

**Changes:**
- Use composition: `DatParser`, `DatCaster`, `DatIndexer`
- Simplify to coordination logic only
- Delegate parsing to `DatParser`
- Delegate casting to `DatCaster`
- Delegate indexing to `DatIndexer`

### Step 5: Refactor DatFile

**File:** `PyPoE/poe/file/dat/file.py`

**Changes:**
- Keep as Facade
- Delegate to `DatReader`
- Maintain backward compatibility

## Benefits

1. **Single Responsibility**: Each class has one clear purpose
2. **Testability**: Easy to mock individual components
3. **Maintainability**: Changes to one component don't affect others
4. **Reusability**: Components can be used independently
5. **DI Support**: Easy to inject dependencies

## Migration Strategy

1. Create new modules in `PyPoE/poe/file/dat/`
2. Move code from `dat.py` to specialized classes
3. Update `DatReader` to use composition
4. Update `DatFile` to use new structure
5. Update imports throughout codebase
6. Run tests to ensure compatibility
7. Remove old `dat.py` file

## Testing

- Unit tests for each specialized class
- Integration tests for `DatFile` and `DatReader`
- Backward compatibility tests
- Performance tests (ensure no regression)

## Timeline

- **Step 1-3**: 4-6 hours (create specialized classes)
- **Step 4**: 2-3 hours (refactor DatReader)
- **Step 5**: 1-2 hours (refactor DatFile)
- **Testing**: 2-3 hours
- **Total**: ~10-14 hours

