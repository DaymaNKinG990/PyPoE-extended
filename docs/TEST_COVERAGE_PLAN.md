# 📊 План увеличения тестового покрытия

**Дата:** 11 ноября 2024  
**Текущее покрытие:** ~35%  
**Целевое покрытие:** >80%

---

## 🎯 Модули БЕЗ тестов (приоритет 1)

### PyPoE/poe/file/dat/
- ❌ `caster.py` - 0% (DatCaster)
- ❌ `parser.py` - 0% (DatParser)
- ❌ `indexer.py` - 0% (DatIndexer)
- ❌ `value.py` - 0% (DatValue)
- ❌ `reader.py` - 0% (DatReader)
- ✅ `file.py` - есть тесты (test_dat.py)
- ✅ `record.py` - есть тесты (test_dat.py)
- ✅ `relational.py` - есть тесты (test_dat.py)
- ✅ `builder.py` - есть тесты (test_dat.py)

### PyPoE/poe/file/ggpk/
- ❌ `reader.py` - 0% (GGPKReader)
- ❌ `record_manager.py` - 0% (GGPKRecordManager)
- ❌ `nodes.py` - 0% (DirectoryNode)
- ❌ `directory_builder.py` - 0% (GGPKDirectoryBuilder)
- ❌ `diff_comparator.py` - 0% (GGPKDiffComparator)
- ❌ `records.py` - 0% (BaseRecord, FileRecord, etc.)
- ✅ `file.py` - есть тесты (test_new_ggpk_file.py)
- ✅ `builder.py` - есть тесты (test_builder.py)

### PyPoE/poe/patchserver/
- ❌ `connection.py` - 0% (PatchConnection)
- ❌ `downloader.py` - 0% (PatchDownloader)
- ❌ `protocol.py` - 0% (PatchProtocolParser)
- ❌ `file_list.py` - 0% (PatchFileListBuilder)
- ❌ `hash_checker.py` - 0% (node_check_hash)
- ❌ `updater.py` - 0% (node_update_files)
- ❌ `node.py` - 0% (DirectoryNodeExtended)
- ❌ `records.py` - 0% (BaseRecordData, etc.)
- ❌ `socket_utils.py` - 0% (socket_fd_open, socket_fd_close)
- ✅ `patch.py` - есть тесты (test_patchserver.py)
- ✅ `file_list_facade.py` - есть тесты (test_patchserver.py)

### PyPoE/poe/file/
- ❌ `psg.py` - 0% (PSGFile)
- ❌ `idt.py` - 0% (IDTFile)
- ❌ `idl.py` - 0% (IDLFile)
- ❌ `ot.py` - 0% (OTFileCache)
- ✅ `bundle.py` - есть тесты (test_dat.py)
- ✅ `file_system.py` - есть тесты (test_dat.py)

### PyPoE/shared/
- ❌ `error_utils.py` - 0% (Error utilities)
- ❌ `file_utils.py` - 0% (File utilities)
- ❌ `validation.py` - 0% (Validation utilities)
- ✅ `di.py` - есть тесты (test_di.py)
- ✅ `decorators.py` - есть тесты (test_decorators.py)
- ✅ `containers.py` - есть тесты (test_containers.py)
- ✅ `logging.py` - есть тесты (test_logging.py)
- ✅ `murmur2.py` - есть тесты (test_murmur2.py)
- ✅ `mixins.py` - есть тесты (test_mixins.py)

### PyPoE/cli/exporter/wiki/parsers/item/
- ❌ `conflict_resolver.py` - 0% (ItemConflictResolver)
- ❌ `wiki_exporter.py` - 0% (ItemWikiExporter)
- ❌ `skill_handler.py` - 0% (ItemSkillHandler)
- ❌ `type_parser.py` - 0% (ItemTypeParser)
- ❌ `data_extractor.py` - 0% (ItemDataExtractor)
- ✅ `parser.py` - есть тесты (test_wiki_item_parser.py)

### PyPoE/cli/exporter/dat/strategies/
- ✅ `json_strategy.py` - есть тесты (test_strategies.py)
- ✅ `csv_strategy.py` - есть тесты (test_strategies.py)
- ✅ `base.py` - есть тесты (test_strategies.py)

### PyPoE/poe/file/handlers/
- ✅ `base.py` - есть тесты (test_handlers.py)
- ✅ `ggpk_handler.py` - есть тесты (test_handlers.py)
- ✅ `dat_handler.py` - есть тесты (test_handlers.py)
- ✅ `bundle_handler.py` - есть тесты (test_handlers.py)
- ✅ `processor.py` - есть тесты (test_handlers.py)

---

## 📋 План действий

### Phase 1: Dat модули (высокий приоритет)
1. `tests/unit/poe/file/dat/test_caster.py` - DatCaster
2. `tests/unit/poe/file/dat/test_parser.py` - DatParser
3. `tests/unit/poe/file/dat/test_indexer.py` - DatIndexer
4. `tests/unit/poe/file/dat/test_value.py` - DatValue
5. `tests/unit/poe/file/dat/test_reader.py` - DatReader

### Phase 2: GGPK модули (высокий приоритет)
1. `tests/unit/poe/file/ggpk/test_reader.py` - GGPKReader
2. `tests/unit/poe/file/ggpk/test_record_manager.py` - GGPKRecordManager
3. `tests/unit/poe/file/ggpk/test_nodes.py` - DirectoryNode
4. `tests/unit/poe/file/ggpk/test_directory_builder.py` - GGPKDirectoryBuilder
5. `tests/unit/poe/file/ggpk/test_diff_comparator.py` - GGPKDiffComparator
6. `tests/unit/poe/file/ggpk/test_records.py` - Records

### Phase 3: PatchServer модули (средний приоритет)
1. `tests/unit/poe/patchserver/test_connection.py` - PatchConnection
2. `tests/unit/poe/patchserver/test_downloader.py` - PatchDownloader
3. `tests/unit/poe/patchserver/test_protocol.py` - PatchProtocolParser
4. `tests/unit/poe/patchserver/test_file_list.py` - PatchFileListBuilder
5. `tests/unit/poe/patchserver/test_hash_checker.py` - Hash checker
6. `tests/unit/poe/patchserver/test_updater.py` - Updater
7. `tests/unit/poe/patchserver/test_node.py` - DirectoryNodeExtended
8. `tests/unit/poe/patchserver/test_records.py` - Records
9. `tests/unit/poe/patchserver/test_socket_utils.py` - Socket utils

### Phase 4: Shared utilities (средний приоритет)
1. `tests/unit/shared/test_error_utils.py` - Error utilities
2. `tests/unit/shared/test_file_utils.py` - File utilities
3. `tests/unit/shared/test_validation.py` - Validation utilities

### Phase 5: Item parser модули (низкий приоритет)
1. `tests/unit/cli/exporter/wiki/parsers/item/test_conflict_resolver.py`
2. `tests/unit/cli/exporter/wiki/parsers/item/test_wiki_exporter.py`
3. `tests/unit/cli/exporter/wiki/parsers/item/test_skill_handler.py`
4. `tests/unit/cli/exporter/wiki/parsers/item/test_type_parser.py`
5. `tests/unit/cli/exporter/wiki/parsers/item/test_data_extractor.py`

### Phase 6: File модули (низкий приоритет)
1. `tests/unit/poe/file/test_psg.py` - PSGFile
2. `tests/unit/poe/file/test_idt.py` - IDTFile
3. `tests/unit/poe/file/test_idl.py` - IDLFile
4. `tests/unit/poe/file/test_ot.py` - OTFileCache

---

## 📊 Оценка трудоемкости

- **Phase 1 (Dat):** 15-20 часов (5 модулей)
- **Phase 2 (GGPK):** 18-24 часа (6 модулей)
- **Phase 3 (PatchServer):** 20-30 часов (9 модулей)
- **Phase 4 (Shared):** 6-8 часов (3 модуля)
- **Phase 5 (Item):** 15-20 часов (5 модулей)
- **Phase 6 (File):** 8-10 часов (4 модуля)

**Итого:** 82-112 часов для достижения >80% покрытия

---

## 🎯 Приоритизация

### Вариант 1: Полное покрытие (рекомендуется)
- Выполнить все 6 фаз
- Достичь >80% покрытия
- Время: 82-112 часов

### Вариант 2: Критичные модули
- Только Phase 1 и Phase 2 (Dat + GGPK)
- Достичь ~60% покрытия
- Время: 33-44 часа

### Вариант 3: Минимальное покрытие
- Только Phase 1 (Dat модули)
- Достичь ~45% покрытия
- Время: 15-20 часов

---

**Последнее обновление:** 11 ноября 2024

