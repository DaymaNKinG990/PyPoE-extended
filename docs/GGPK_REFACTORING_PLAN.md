# 🏗️ GGPKFile Refactoring Plan

**Цель:** Разбить `GGPKFile` (854 строки) на специализированные классы с четкими ответственностями

**Приоритет:** ⭐ CRITICAL  
**Время:** ~40 часов  
**Статус:** 📋 Planning

---

## 📊 Текущая структура

### GGPKFile (854 строки) - God Object

**Ответственности:**
1. ✅ Чтение бинарного формата (`_read`, `_read_record`)
2. ✅ Управление записями (`records: dict[int, BaseRecord]`)
3. ✅ Построение дерева директорий (`build_directory`)
4. ✅ Доступ к файлам (`__getitem__`)
5. ✅ Сравнение GGPK файлов (`diff`)
6. ✅ Хранение состояния (`directory`, `records`)

**Проблемы:**
- ❌ Слишком много ответственностей (SRP violation)
- ❌ Сложно тестировать (все связано)
- ❌ Высокая связанность (tight coupling)
- ❌ Низкая cohesion

---

## 🎯 Целевая архитектура

### Разделение на специализированные классы:

```
GGPKFile (Facade)
├── GGPKReader          - чтение бинарного формата
├── GGPKRecordManager   - управление записями
├── GGPKDirectoryBuilder - построение дерева
└── GGPKDiffComparator  - сравнение файлов
```

---

## 📦 Новые классы

### 1. GGPKReader

**Ответственность:** Чтение и парсинг бинарного формата GGPK

**Методы:**
- `read_file(buffer: BinaryIO) -> dict[int, BaseRecord]`
- `read_record(buffer: BinaryIO, offset: int) -> BaseRecord`
- `find_next_record(buffer: BinaryIO, offset: int) -> int | None`

**Зависимости:**
- `BaseRecord`, `FileRecord`, `DirectoryRecord`, `FreeRecord`, `GGPKRecord`
- `InvalidTagError`

**Тестируемость:** ✅ Легко (только парсинг)

---

### 2. GGPKRecordManager

**Ответственность:** Управление коллекцией записей

**Методы:**
- `add_record(offset: int, record: BaseRecord) -> None`
- `get_record(offset: int) -> BaseRecord | None`
- `get_records() -> dict[int, BaseRecord]`
- `has_record(offset: int) -> bool`
- `clear() -> None`

**Состояние:**
- `records: dict[int, BaseRecord]`

**Тестируемость:** ✅ Очень легко (простой dict wrapper)

---

### 3. GGPKDirectoryBuilder

**Ответственность:** Построение дерева DirectoryNode из записей

**Методы:**
- `build_root(records: dict[int, BaseRecord]) -> DirectoryNode`
- `build_directory(parent: DirectoryNode, records: dict[int, BaseRecord]) -> DirectoryNode`
- `build_from_records(records: dict[int, BaseRecord]) -> DirectoryNode`

**Зависимости:**
- `GGPKRecordManager` (для получения записей)
- `DirectoryNode`, `DirectoryRecord`, `FileRecord`

**Тестируемость:** ✅ Легко (можно мокировать records)

---

### 4. GGPKDiffComparator

**Ответственность:** Сравнение двух GGPK файлов

**Методы:**
- `compare(ggpk1: GGPKFile, ggpk2: GGPKFile) -> tuple[list[str], list[str], list[str]]`
- `write_diff(new: list[str], deleted: list[str], changed: list[str], out_file: str) -> None`

**Зависимости:**
- `GGPKFile` (для доступа к directory)

**Тестируемость:** ✅ Легко (можно мокировать GGPKFile)

---

### 5. GGPKFile (Facade)

**Ответственность:** Публичный API, координация компонентов

**Методы:**
- `read(file_path_or_raw)` - использует GGPKReader
- `directory_build()` - использует GGPKDirectoryBuilder
- `__getitem__(path: str)` - доступ к directory
- `diff(other_ggpk)` - использует GGPKDiffComparator

**Состояние:**
- `directory: DirectoryNode | None`
- `_reader: GGPKReader`
- `_record_manager: GGPKRecordManager`
- `_directory_builder: GGPKDirectoryBuilder`
- `_diff_comparator: GGPKDiffComparator`

**DI:**
- Все компоненты инжектятся через конструктор
- Можно использовать DI контейнер

**Тестируемость:** ✅ Очень легко (все зависимости мокируемы)

---

## 🔄 План миграции

### Phase 1: Создать новые классы (без изменения GGPKFile)

1. ✅ Создать `GGPKReader`
2. ✅ Создать `GGPKRecordManager`
3. ✅ Создать `GGPKDirectoryBuilder`
4. ✅ Создать `GGPKDiffComparator`
5. ✅ Написать unit тесты для каждого класса

**Время:** ~8 часов

---

### Phase 2: Рефакторинг GGPKFile (постепенная замена)

1. ✅ Добавить DI в конструктор GGPKFile
2. ✅ Заменить `_read` на использование `GGPKReader`
3. ✅ Заменить `records` на использование `GGPKRecordManager`
4. ✅ Заменить `build_directory` на использование `GGPKDirectoryBuilder`
5. ✅ Заменить `diff` на использование `GGPKDiffComparator`
6. ✅ Обновить тесты

**Время:** ~12 часов

---

### Phase 3: Очистка и оптимизация

1. ✅ Удалить старые методы из GGPKFile
2. ✅ Обновить документацию
3. ✅ Обновить примеры использования
4. ✅ Проверить backward compatibility
5. ✅ Финальные тесты

**Время:** ~8 часов

---

### Phase 4: Интеграция с DI

1. ✅ Зарегистрировать новые классы в DI контейнере
2. ✅ Обновить providers
3. ✅ Обновить UI для использования DI
4. ✅ Финальная проверка

**Время:** ~4 часа

---

### Phase 5: Документация и примеры

1. ✅ Обновить API документацию
2. ✅ Создать примеры использования
3. ✅ Обновить REFACTORING_ROADMAP

**Время:** ~4 часа

---

## 📁 Структура файлов

```
PyPoE/poe/file/ggpk/
├── __init__.py              # Экспорт публичного API
├── file.py                  # GGPKFile (Facade)
├── reader.py                # GGPKReader
├── record_manager.py        # GGPKRecordManager
├── directory_builder.py     # GGPKDirectoryBuilder
├── diff_comparator.py       # GGPKDiffComparator
├── records.py               # BaseRecord, FileRecord, etc. (существующие)
└── nodes.py                 # DirectoryNode (существующий)
```

---

## ✅ Преимущества

1. **Single Responsibility Principle**
   - Каждый класс имеет одну четкую ответственность

2. **Testability**
   - Легко тестировать каждый компонент изолированно
   - Можно мокировать зависимости

3. **Maintainability**
   - Легче понимать и изменять код
   - Меньше связанности

4. **Reusability**
   - Компоненты можно использовать отдельно
   - Легко расширять функциональность

5. **DI Integration**
   - Все компоненты инжектятся через DI
   - Легко заменять реализации

---

## 🧪 Тестирование

### Unit Tests

- ✅ `test_ggpk_reader.py` - тесты парсинга
- ✅ `test_record_manager.py` - тесты управления записями
- ✅ `test_directory_builder.py` - тесты построения дерева
- ✅ `test_diff_comparator.py` - тесты сравнения
- ✅ `test_ggpk_file.py` - тесты фасада

### Integration Tests

- ✅ `test_ggpk_integration.py` - полный цикл работы
- ✅ `test_backward_compatibility.py` - обратная совместимость

---

## 📝 Backward Compatibility

**Важно:** Сохранить 100% обратную совместимость!

- ✅ Публичный API GGPKFile не изменится
- ✅ Все существующие методы работают как прежде
- ✅ Существующие тесты должны пройти без изменений
- ✅ CLI/GUI работают без изменений

---

## 🎯 Метрики успеха

- ✅ Снижение размера GGPKFile с 854 до ~200 строк
- ✅ Каждый новый класс < 200 строк
- ✅ Test coverage > 80% для новых классов
- ✅ Все существующие тесты проходят
- ✅ 0 MyPy errors
- ✅ 0 Ruff errors
- ✅ Backward compatibility 100%

---

## 📅 Timeline

**Week 1:**
- Phase 1: Создать новые классы (8h)
- Phase 2: Начать рефакторинг (6h)

**Week 2:**
- Phase 2: Завершить рефакторинг (6h)
- Phase 3: Очистка (8h)

**Week 3:**
- Phase 4: DI интеграция (4h)
- Phase 5: Документация (4h)

**Итого:** ~40 часов

---

**Статус:** 📋 Ready to start  
**Next Step:** Phase 1 - Create GGPKReader

