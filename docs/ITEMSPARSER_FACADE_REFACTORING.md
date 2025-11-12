# ItemsParser Facade Refactoring Plan

## Overview

This document outlines the plan to refactor ItemsParser from using multiple inheritance (mixins) to using composition (Facade pattern) with specialized classes.

## Current Structure

```
ItemsParser (1566 lines)
├── SkillsMixin (186 lines)
├── TypesMixin (27 lines)
├── ExtrasMixin (238 lines)
├── ConflictsMixin (120 lines)
├── ExportsMixin (248 lines)
├── UtilsMixin (365 lines)
└── SkillParserShared (inherited)
```

## New Structure (Facade Pattern)

```
ItemsParser (Facade, ~300-400 lines)
├── ItemConflictResolver (composition)
├── ItemWikiExporter (composition)
├── ItemSkillHandler (composition)
├── ItemTypeParser (composition)
└── ItemDataExtractor (composition)
```

## Refactoring Steps

### Step 1: Create New ItemsParser Structure

1. Change inheritance from mixins to BaseParser + SkillParserShared only
2. Add composition of specialized classes in `__init__`
3. Keep all class attributes (they're needed for `_type_factory` and `_cls_map`)
4. Keep all properties (`_cls_map`, `_conflict_resolver_map`)

### Step 2: Delegate Methods

**Delegation Map:**

| Old Method (Mixin) | New Delegation |
|-------------------|----------------|
| `by_rowid()` | `self._data_extractor.export_items()` |
| `by_id()` | `self._data_extractor.export_items()` |
| `by_name()` | `self._data_extractor.export_items()` |
| `by_filter()` | `self._data_extractor.export_items()` |
| `export_map_icons()` | `self._wiki_exporter.export_map_icons()` |
| `export_map()` | `self._wiki_exporter.export_map()` |
| `_skill_gem()` | `self._skill_handler.process_skill_gem()` |
| `_conflict_*()` | `self._conflict_resolver.resolve_conflict()` |
| `_type_*()` | `self._type_parser.parse_*()` |
| `_process_name_conflicts()` | `self._data_extractor.process_name_conflicts()` |
| `_format_map_name()` | `self._data_extractor.format_map_name()` |
| `_get_map_series()` | `self._data_extractor.get_map_series()` |

### Step 3: Keep Internal Methods

Some methods should remain in ItemsParser:
- `_process_base_item_type()` - used by multiple components
- `_process_purchase_costs()` - used by multiple components
- `_image_init()` - BaseParser method
- `_write_dds()` - BaseParser method
- `_get_stats()` - SkillParserShared method
- `_item_column_index_filter()` - SkillParserShared method

### Step 4: Update Properties

Properties that reference methods need to be updated:
- `_conflict_resolver_map` - now uses `self._conflict_resolver.resolve_conflict()`
- `_cls_map` - now uses `self._type_parser` methods

## Implementation Details

### Constructor

```python
def __init__(self, base_path, parsed_args, **kwargs):
    super().__init__(base_path, parsed_args, **kwargs)
    
    # Create specialized classes via composition
    self._conflict_resolver = ItemConflictResolver(
        relational_reader=self.rr,
        language=self._language,
        lang_map=self._LANG,
        format_map_name=self._format_map_name,
    )
    
    self._wiki_exporter = ItemWikiExporter(
        relational_reader=self.rr,
        translation_cache=self.tc,
        file_system=self.file_system,
        language=self._language,
        lang_map=self._LANG,
        map_colors=self._MAP_COLORS,
        map_release_version=self._MAP_RELEASE_VERSION,
        relational_reader_english=self.rr2,
        image_init=self._image_init,
        write_dds=self._write_dds,
        format_map_name=self._format_map_name,
        get_map_series=self._get_map_series,
        process_base_item_type=self._process_base_item_type,
        process_purchase_costs=self._process_purchase_costs,
        type_map=self._type_map,
        img_path=self._img_path,
    )
    
    # ... other specialized classes
```

### Method Delegation Example

```python
def by_filter(self, parsed_args):
    # Delegate to ItemDataExtractor
    items = []
    for item in self.rr["BaseItemTypes.dat"]:
        if parsed_args.re_name and not parsed_args.re_name.match(item["Name"]):
            continue
        if parsed_args.re_id and not parsed_args.re_id.match(item["Id"]):
            continue
        items.append(item)
    
    return self._data_extractor.export_items(parsed_args, items)

def export_map(self, parsed_args):
    # Delegate to ItemWikiExporter
    return self._wiki_exporter.export_map(parsed_args)
```

## Benefits

1. **Reduced Complexity**: ItemsParser becomes a simple Facade (~300-400 lines)
2. **Better Testability**: Each component can be tested independently
3. **Clear Responsibilities**: Each class has a single, well-defined purpose
4. **Easier Maintenance**: Changes to one component don't affect others
5. **DI Support**: All dependencies are injected, making testing easier

## Migration Strategy

1. **Phase 1**: Create new ItemsParser alongside old one (parser_new.py)
2. **Phase 2**: Update tests to use new ItemsParser
3. **Phase 3**: Replace old ItemsParser with new one
4. **Phase 4**: Remove old mixins (optional, for cleaner code)

## Estimated Effort

- **Refactoring ItemsParser**: 15-20 hours
- **Updating Tests**: 5-10 hours
- **Total**: 20-30 hours

## Risks

1. **Breaking Changes**: Existing code may break if not careful
2. **Performance**: Composition may have slight overhead (negligible)
3. **Complexity**: Initial refactoring may increase complexity temporarily

## Success Criteria

1. ✅ ItemsParser reduced to <500 lines
2. ✅ All tests pass
3. ✅ No functionality lost
4. ✅ Code is more maintainable
5. ✅ All specialized classes are used via composition

