# Phase 9: Additional Design Patterns

**Дата:** 11 ноября 2024  
**Цель:** Добавить дополнительные паттерны проектирования для улучшения архитектуры  
**Приоритет:** 🟡 MEDIUM (опциональные улучшения)

---

## 📋 Обзор

Phase 9 включает внедрение дополнительных паттернов проектирования, которые улучшат гибкость и расширяемость кодовой базы.

### Планируемые паттерны:

1. **Builder Pattern** - для сложных объектов (GGPKFile, DatFile)
2. **Command Pattern** - для CLI команд
3. **Chain of Responsibility** - для обработки файлов
4. **Strategy Pattern** - расширение существующего использования

---

## 🎯 Phase 9.1: Builder Pattern

**Цель:** Упростить создание сложных объектов (GGPKFile, DatFile)

**Трудоемкость:** 5-8 часов  
**Impact:** 🟢 НИЗКИЙ (но улучшает читаемость)

### Задачи:

#### 9.1.1: GGPKFile Builder

**Файл:** `PyPoE/poe/file/ggpk/builder.py`

```python
class GGPKFileBuilder:
    """Builder для создания GGPKFile с опциональными компонентами."""
    
    def __init__(self, file_path: str):
        self._file_path = file_path
        self._reader: GGPKReader | None = None
        self._record_manager: GGPKRecordManager | None = None
        self._directory_builder: GGPKDirectoryBuilder | None = None
        self._diff_comparator: GGPKDiffComparator | None = None
    
    def with_reader(self, reader: GGPKReader) -> Self:
        """Установить кастомный GGPKReader."""
        self._reader = reader
        return self
    
    def with_record_manager(self, manager: GGPKRecordManager) -> Self:
        """Установить кастомный GGPKRecordManager."""
        self._record_manager = manager
        return self
    
    def with_directory_builder(self, builder: GGPKDirectoryBuilder) -> Self:
        """Установить кастомный GGPKDirectoryBuilder."""
        self._directory_builder = builder
        return self
    
    def with_diff_comparator(self, comparator: GGPKDiffComparator) -> Self:
        """Установить кастомный GGPKDiffComparator."""
        self._diff_comparator = comparator
        return self
    
    def build(self) -> GGPKFile:
        """Создать GGPKFile с настроенными компонентами."""
        return GGPKFile(
            file_path=self._file_path,
            reader=self._reader,
            record_manager=self._record_manager,
            directory_builder=self._directory_builder,
            diff_comparator=self._diff_comparator,
        )
```

**Пример использования:**
```python
# Старый способ
ggpk = GGPKFile("path/to/content.ggpk")
ggpk.read(file_handle)

# Новый способ (Builder)
ggpk = (
    GGPKFileBuilder("path/to/content.ggpk")
    .with_reader(custom_reader)
    .with_record_manager(custom_manager)
    .build()
)
ggpk.read(file_handle)
```

#### 9.1.2: DatFile Builder

**Файл:** `PyPoE/poe/file/dat/builder.py`

Аналогично для DatFile с DatCaster, DatParser, DatIndexer.

---

## 🎯 Phase 9.2: Command Pattern для CLI

**Цель:** Инкапсулировать CLI команды в объекты

**Трудоемкость:** 12-15 часов  
**Impact:** 🟢 НИЗКИЙ (но улучшает тестируемость)

### Задачи:

#### 9.2.1: Создать базовый Command интерфейс

**Файл:** `PyPoE/cli/commands/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any

class Command(ABC):
    """Базовый интерфейс для CLI команд."""
    
    @abstractmethod
    def execute(self, args: Any) -> int:
        """Выполнить команду. Возвращает exit code."""
        pass
    
    @abstractmethod
    def validate(self, args: Any) -> bool:
        """Проверить валидность аргументов."""
        pass
```

#### 9.2.2: Рефакторить существующие команды

**Файлы:**
- `PyPoE/cli/commands/export_dat.py` - ExportDatCommand
- `PyPoE/cli/commands/export_wiki.py` - ExportWikiCommand
- `PyPoE/cli/commands/export_translations.py` - ExportTranslationsCommand

**Пример:**
```python
class ExportDatCommand(Command):
    def __init__(self, handler: DatHandler):
        self._handler = handler
    
    def execute(self, args: Any) -> int:
        if not self.validate(args):
            return 1
        self._handler.export(args)
        return 0
    
    def validate(self, args: Any) -> bool:
        return hasattr(args, 'output_dir') and args.output_dir
```

#### 9.2.3: Создать CommandInvoker

**Файл:** `PyPoE/cli/commands/invoker.py`

```python
class CommandInvoker:
    """Выполняет команды и поддерживает undo/redo (опционально)."""
    
    def __init__(self):
        self._history: list[Command] = []
    
    def execute(self, command: Command, args: Any) -> int:
        """Выполнить команду и добавить в историю."""
        result = command.execute(args)
        if result == 0:
            self._history.append(command)
        return result
```

---

## 🎯 Phase 9.3: Chain of Responsibility для файлов

**Цель:** Обработка файлов через цепочку обработчиков

**Трудоемкость:** 10-12 часов  
**Impact:** 🟢 НИЗКИЙ (но улучшает расширяемость)

### Задачи:

#### 9.3.1: Создать базовый FileHandler

**Файл:** `PyPoE/poe/file/handlers/base.py`

```python
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyPoE.poe.file.shared import AbstractFileReadOnly

class FileHandler(ABC):
    """Базовый обработчик файлов в цепочке."""
    
    def __init__(self):
        self._next_handler: FileHandler | None = None
    
    def set_next(self, handler: "FileHandler") -> "FileHandler":
        """Установить следующий обработчик в цепочке."""
        self._next_handler = handler
        return handler
    
    @abstractmethod
    def can_handle(self, file: "AbstractFileReadOnly") -> bool:
        """Проверить, может ли обработчик обработать файл."""
        pass
    
    @abstractmethod
    def handle(self, file: "AbstractFileReadOnly") -> None:
        """Обработать файл."""
        pass
    
    def _next(self, file: "AbstractFileReadOnly") -> None:
        """Передать файл следующему обработчику."""
        if self._next_handler:
            self._next_handler.handle(file)
```

#### 9.3.2: Создать конкретные обработчики

**Файлы:**
- `PyPoE/poe/file/handlers/ggpk_handler.py` - GGPKFileHandler
- `PyPoE/poe/file/handlers/dat_handler.py` - DatFileHandler
- `PyPoE/poe/file/handlers/bundle_handler.py` - BundleHandler

**Пример:**
```python
class GGPKFileHandler(FileHandler):
    def can_handle(self, file: AbstractFileReadOnly) -> bool:
        return isinstance(file, GGPKFile)
    
    def handle(self, file: AbstractFileReadOnly) -> None:
        if self.can_handle(file):
            # Обработка GGPK файла
            file.directory_build()
        else:
            self._next(file)
```

#### 9.3.3: Создать FileProcessor

**Файл:** `PyPoE/poe/file/handlers/processor.py`

```python
class FileProcessor:
    """Обрабатывает файлы через цепочку обработчиков."""
    
    def __init__(self):
        self._chain: FileHandler | None = None
    
    def add_handler(self, handler: FileHandler) -> None:
        """Добавить обработчик в цепочку."""
        if self._chain is None:
            self._chain = handler
        else:
            # Найти последний обработчик
            current = self._chain
            while current._next_handler:
                current = current._next_handler
            current.set_next(handler)
    
    def process(self, file: AbstractFileReadOnly) -> None:
        """Обработать файл через цепочку."""
        if self._chain:
            self._chain.handle(file)
```

---

## 🎯 Phase 9.4: Расширение Strategy Pattern

**Цель:** Улучшить существующее использование Strategy

**Трудоемкость:** 3-5 часов  
**Impact:** 🟢 НИЗКИЙ

### Задачи:

#### 9.4.1: Создать Strategy интерфейсы

**Файл:** `PyPoE/poe/file/strategies/base.py`

```python
from abc import ABC, abstractmethod

class ParsingStrategy(ABC):
    """Стратегия парсинга файлов."""
    
    @abstractmethod
    def parse(self, data: bytes) -> Any:
        """Парсить данные."""
        pass

class CompressionStrategy(ABC):
    """Стратегия сжатия/распаковки."""
    
    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """Сжать данные."""
        pass
    
    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """Распаковать данные."""
        pass
```

#### 9.4.2: Реализовать конкретные стратегии

**Файлы:**
- `PyPoE/poe/file/strategies/brotli_strategy.py` - BrotliCompressionStrategy
- `PyPoE/poe/file/strategies/zlib_strategy.py` - ZlibCompressionStrategy

---

## 📊 План выполнения

```
Phase 9.1 (Builder):        ⏳ PENDING - 5-8 часов
Phase 9.2 (Command):        ⏳ PENDING - 12-15 часов
Phase 9.3 (Chain of Resp):  ⏳ PENDING - 10-12 часов
Phase 9.4 (Strategy):       ⏳ PENDING - 3-5 часов
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Итого Phase 9:              ⏳ PENDING - 30-40 часов
```

---

## ✅ Критерии успеха

- [ ] Builder Pattern реализован для GGPKFile и DatFile
- [ ] Command Pattern реализован для всех CLI команд
- [ ] Chain of Responsibility реализован для обработки файлов
- [ ] Strategy Pattern расширен
- [ ] Все паттерны покрыты unit тестами
- [ ] Документация создана
- [ ] MyPy: 0 errors
- [ ] Ruff: 0 errors

---

## 📝 Примечания

- Все паттерны опциональны и могут быть реализованы по мере необходимости
- Приоритет: Builder > Command > Chain of Responsibility > Strategy
- Каждый паттерн должен быть полностью протестирован перед интеграцией

