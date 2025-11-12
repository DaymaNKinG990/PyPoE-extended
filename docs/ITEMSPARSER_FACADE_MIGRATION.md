# ItemsParser Facade Migration Guide

## Overview

This document describes the migration from the old mixin-based `ItemsParser` to the new Facade-based architecture using composition.

## What Changed

### Architecture

**Before (Multiple Inheritance):**
```python
class ItemsParser(
    SkillsMixin,
    TypesMixin,
    ExtrasMixin,
    ConflictsMixin,
    ExportsMixin,
    UtilsMixin,
    SkillParserShared,
):
    # 1567 lines of code
    # Methods inherited from 7 different classes
```

**After (Facade Pattern with Composition):**
```python
class ItemsParser(SkillParserShared):
    def __init__(self, base_path, parsed_args, **kwargs):
        super().__init__(base_path, parsed_args, **kwargs)
        
        # Composition instead of inheritance
        self._conflict_resolver = ItemConflictResolver(...)
        self._wiki_exporter = ItemWikiExporter(...)
        self._skill_handler = ItemSkillHandler(...)
        self._type_parser = ItemTypeParser(...)
        self._data_extractor = ItemDataExtractor(...)
    
    # ~1900 lines (includes class attributes and methods)
    # Methods delegate to specialized classes
```

### Specialized Classes

The functionality has been split into 5 specialized classes:

1. **ItemConflictResolver** (`conflict_resolver.py`)
   - Handles conflict resolution for items with duplicate names
   - Methods: `resolve_conflict()`

2. **ItemWikiExporter** (`wiki_exporter.py`)
   - Handles export of items to wiki format
   - Methods: `export_map_icons()`, `export_map()`

3. **ItemSkillHandler** (`skill_handler.py`)
   - Handles skill-related items (skill gems)
   - Methods: `process_skill_gem()`, `resolve_active_skill_gem_conflict()`

4. **ItemTypeParser** (`type_parser.py`)
   - Parses item types and extracts type-specific data
   - Methods: `parse_type_*()` for various item types

5. **ItemDataExtractor** (`data_extractor.py`)
   - Extracts and processes item data
   - Methods: `export_items()`, `process_name_conflicts()`, `format_map_name()`, `get_map_series()`

## API Changes

### Constructor

**Before:**
```python
parser = ItemsParser(base_path="output")
```

**After:**
```python
# parsed_args is now required
parsed_args = type("Args", (object,), {
    "store_images": False,
    "convert_images": False,
    "english_file_link": False,
})
parser = ItemsParser(base_path="output", parsed_args=parsed_args)
```

### Public Methods

All public methods remain the same:

- `by_rowid(parsed_args)` - Export items by row ID range
- `by_id(parsed_args)` - Export items by ID
- `by_name(parsed_args)` - Export items by name
- `by_filter(parsed_args)` - Export items by filter (regex)
- `export_map_icons(parsed_args)` - Export map icons
- `export_map(parsed_args)` - Export map data
- `export(parsed_args)` - Backward compatibility method (delegates to by_name/by_id)

### Internal Methods

Internal methods that are used by multiple components remain in `ItemsParser`:

- `_process_base_item_type()` - Process base item type information
- `_process_purchase_costs()` - Process purchase costs
- `_format_map_name()` - Format map name
- `_get_map_series()` - Get map series from parsed arguments
- `_type_map()` - Apply map-specific type information

## Migration Steps

### For Tests

1. **Update fixture to include `parsed_args`:**
```python
@pytest.fixture(scope="module")
def item_parser(poe_version, cli_config):
    path = config["Config"]["temp_dir"]
    parsed_args = type("Args", (object,), {
        "store_images": False,
        "convert_images": False,
        "english_file_link": False,
    })
    return item.ItemsParser(base_path=path, parsed_args=parsed_args)
```

2. **Tests should continue to work** - The `export()` method provides backward compatibility.

### For Code Using ItemsParser

1. **Update constructor calls:**
   - Add `parsed_args` parameter to `ItemsParser()` constructor
   - Ensure `parsed_args` has required attributes (`store_images`, `convert_images`, etc.)

2. **No changes needed for method calls** - All public methods work the same way.

### For Dependency Injection

The new architecture supports dependency injection:

```python
from PyPoE.shared.di import DIContainer
from PyPoE.poe.providers import register_core_providers

container = DIContainer()
register_core_providers(container)

# ItemsParser can now be created with injected dependencies
parser = ItemsParser(
    base_path="output",
    parsed_args=args,
    file_system=container.resolve(FileSystem),
    relational_reader=container.resolve(RelationalReader),
    # ... other dependencies
)
```

## Benefits

1. **Reduced Complexity**: ItemsParser is now a Facade (~1900 lines including attributes, was 1567)
2. **Better Testability**: Each specialized class can be tested independently
3. **Clear Responsibilities**: Each class has a single, well-defined purpose
4. **Easier Maintenance**: Changes to one component don't affect others
5. **DI Support**: All dependencies are injected, making testing easier

## Backward Compatibility

- ✅ All public methods work the same way
- ✅ `export()` method provides backward compatibility for tests
- ✅ Class attributes (`_type_*`, `_cls_map`, etc.) are preserved
- ✅ Properties (`_conflict_resolver_map`, `_cls_map`) work the same way

## Testing

Run tests to verify everything works:

```bash
pytest tests/PyPoE/cli/exporter/wiki/parser/test_wiki_item_parser.py -v
```

## Troubleshooting

### Issue: `ItemsParser() missing 1 required positional argument: 'parsed_args'`

**Solution**: Add `parsed_args` to constructor:
```python
parsed_args = type("Args", (object,), {"store_images": False})
parser = ItemsParser(base_path="output", parsed_args=parsed_args)
```

### Issue: `AttributeError: 'ItemsParser' object has no attribute '_conflict_resolver'`

**Solution**: This should not happen if `__init__` completed successfully. Check that all specialized classes are created in `__init__`.

### Issue: Tests fail with `TypeError` or `AttributeError`

**Solution**: Ensure `parsed_args` has all required attributes for the test scenario.

## Related Documentation

- `docs/ITEMSPARSER_REFACTORING_PLAN.md` - Original refactoring plan
- `docs/ITEMSPARSER_FACADE_REFACTORING.md` - Detailed Facade refactoring plan
- `docs/ARCHITECTURE_ANALYSIS.md` - Overall architecture analysis

