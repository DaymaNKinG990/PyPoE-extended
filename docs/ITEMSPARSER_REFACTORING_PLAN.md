# ItemsParser Refactoring Plan

## Overview

ItemsParser is currently a God Object (1566 lines) that uses multiple inheritance from mixins. This plan outlines how to refactor it into specialized classes using composition instead of inheritance.

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

## Problems

1. **Multiple Inheritance Complexity**: ItemsParser inherits from 7 classes, making it hard to understand the method resolution order (MRO)
2. **Tight Coupling**: Mixins depend on ItemsParser attributes, creating circular dependencies
3. **Hard to Test**: Difficult to mock individual responsibilities
4. **God Object**: Too many responsibilities in one class

## Proposed Solution: Composition over Inheritance

### Phase 1: Create Specialized Classes

Extract mixins into standalone classes that can be used via composition:

1. **ItemTypeParser** (from TypesMixin + ExtrasMixin)
   - Parse item types (weapons, armor, currency, etc.)
   - Extract type-specific data
   - Map item classes to type handlers

2. **ItemConflictResolver** (from ConflictsMixin)
   - Resolve conflicts between items
   - Handle special cases (quest items, maps, etc.)
   - Format conflict messages

3. **ItemWikiExporter** (from ExportsMixin)
   - Export items to wiki format
   - Handle map exports
   - Process export filters

4. **ItemSkillHandler** (from SkillsMixin)
   - Handle skill-related items
   - Process skill gems
   - Extract skill data

5. **ItemDataExtractor** (from UtilsMixin)
   - Extract additional item data
   - Process item attributes
   - Handle item filtering

### Phase 2: Refactor ItemsParser as Facade

ItemsParser becomes a Facade that coordinates the specialized classes:

```python
class ItemsParser(BaseParser):
    def __init__(self, base_path, parsed_args, **kwargs):
        super().__init__(base_path, parsed_args, **kwargs)
        
        # Composition instead of inheritance
        self._type_parser = ItemTypeParser(self.rr, self.tc, self.file_system)
        self._conflict_resolver = ItemConflictResolver(self.rr, self.tc)
        self._wiki_exporter = ItemWikiExporter(self.rr, self.tc, self.file_system)
        self._skill_handler = ItemSkillHandler(self.rr, self.tc)
        self._data_extractor = ItemDataExtractor(self.rr, self.tc, self.file_system)
    
    def by_filter(self, parsed_args):
        # Delegate to appropriate handler
        items = self._data_extractor.filter_items(parsed_args)
        return self._wiki_exporter.export_items(items, parsed_args)
```

### Phase 3: Benefits

1. **Single Responsibility**: Each class has one clear purpose
2. **Testability**: Easy to mock individual components
3. **Maintainability**: Changes to one component don't affect others
4. **Reusability**: Components can be used independently
5. **DI Support**: Easy to inject dependencies

## Implementation Steps

### Step 1: Create ItemTypeParser

**File**: `PyPoE/cli/exporter/wiki/parsers/item/type_parser.py`

**Responsibilities**:
- Parse item types (weapons, armor, currency, etc.)
- Extract type-specific data
- Map item classes to type handlers

**Methods**:
- `parse_item_type(base_item_type) -> dict`
- `get_type_handlers(item_class) -> list[Callable]`
- `extract_type_data(item, item_type) -> dict`

### Step 2: Create ItemConflictResolver

**File**: `PyPoE/cli/exporter/wiki/parsers/item/conflict_resolver.py`

**Responsibilities**:
- Resolve conflicts between items
- Handle special cases
- Format conflict messages

**Methods**:
- `resolve_conflict(item_type, infobox, base_item_type) -> str | None`
- `handle_quest_items(infobox, base_item_type) -> str | None`
- `handle_maps(infobox, base_item_type) -> str | None`

### Step 3: Create ItemWikiExporter

**File**: `PyPoE/cli/exporter/wiki/parsers/item/wiki_exporter.py`

**Responsibilities**:
- Export items to wiki format
- Handle map exports
- Process export filters

**Methods**:
- `export_item(item, parsed_args) -> str`
- `export_map(map_item, parsed_args) -> str`
- `export_map_icons(parsed_args) -> None`

### Step 4: Create ItemSkillHandler

**File**: `PyPoE/cli/exporter/wiki/parsers/item/skill_handler.py`

**Responsibilities**:
- Handle skill-related items
- Process skill gems
- Extract skill data

**Methods**:
- `process_skill_gem(item) -> dict`
- `extract_skill_data(skill_gem) -> dict`
- `format_skill_info(skill_data) -> str`

### Step 5: Create ItemDataExtractor

**File**: `PyPoE/cli/exporter/wiki/parsers/item/data_extractor.py`

**Responsibilities**:
- Extract additional item data
- Process item attributes
- Handle item filtering

**Methods**:
- `filter_items(parsed_args) -> list`
- `extract_item_data(item) -> dict`
- `process_item_attributes(item) -> dict`

### Step 6: Refactor ItemsParser

**File**: `PyPoE/cli/exporter/wiki/parsers/item/parser.py`

**Changes**:
- Remove mixin inheritance
- Add composition of specialized classes
- Delegate methods to appropriate handlers
- Maintain backward compatibility

## Migration Strategy

1. **Phase 1**: Create specialized classes alongside existing mixins
2. **Phase 2**: Update ItemsParser to use composition (keep mixins for backward compatibility)
3. **Phase 3**: Update tests to use new structure
4. **Phase 4**: Remove mixins (optional, for cleaner code)

## Testing Strategy

1. **Unit Tests**: Test each specialized class independently
2. **Integration Tests**: Test ItemsParser with all components
3. **Backward Compatibility**: Ensure existing code still works

## Estimated Effort

- **Step 1-5**: 20-25 hours (creating specialized classes)
- **Step 6**: 10-15 hours (refactoring ItemsParser)
- **Testing**: 5-10 hours
- **Total**: 35-50 hours

## Risks

1. **Breaking Changes**: Existing code may break if not careful
2. **Performance**: Composition may have slight overhead
3. **Complexity**: Initial refactoring may increase complexity temporarily

## Success Criteria

1. ✅ ItemsParser reduced to <500 lines
2. ✅ Each specialized class <300 lines
3. ✅ All tests pass
4. ✅ Backward compatibility maintained
5. ✅ Code coverage >80%

## See Also

- `ARCHITECTURE_ANALYSIS.md` - Full architecture analysis
- `REFACTORING_ROADMAP.md` - Overall refactoring roadmap
- `GGPK_REFACTORING_PLAN.md` - Similar refactoring for GGPKFile

