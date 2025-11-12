# PatchServer Refactoring Plan

## Обзор

**Файл:** `PyPoE/poe/patchserver.py`  
**Размер:** 991 строка  
**Проблема:** God Object - классы `Patch` и `PatchFileList` содержат слишком много ответственностей

## Анализ текущей структуры

### Класс `Patch` (~185 строк)
**Ответственности:**
1. Подключение к патч-серверу (socket management)
2. Получение URL патч-сервера (protocol parsing)
3. Загрузка файлов (HTTP download)
4. Управление версией

**Методы:**
- `__init__()` - инициализация, получение URL
- `__del__()` - закрытие сокета
- `update_patch_urls()` - получение URL с сервера
- `download()` - загрузка файла на диск
- `download_raw()` - загрузка сырых байтов
- `version` (property) - получение версии

### Класс `PatchFileList` (~350 строк)
**Ответственности:**
1. Управление сокетом для запросов
2. Парсинг протокола патч-сервера
3. Парсинг списка файлов
4. Управление структурой директорий

**Методы:**
- `__init__()` - инициализация, получение root
- `__del__()` - закрытие сокета
- `read()` - чтение данных из сокета
- `extract_varchar()` - извлечение строки
- `update_filelist()` - обновление списка файлов

### Вспомогательные классы
- `BaseRecordData` - базовый класс для записей
- `VirtualDirectoryRecord` - виртуальная директория
- `VirtualFileRecord` - виртуальный файл
- `DirectoryNodeExtended` - расширенный узел директории

### Функции
- `socket_fd_open()` - открытие сокета из FD
- `socket_fd_close()` - закрытие сокета
- `node_check_hash()` - проверка хеша узла
- `node_outdated_files()` - поиск устаревших файлов
- `node_update_files()` - обновление файлов

## Проблемы

1. **Нарушение SRP:** Классы делают слишком много
2. **Тесная связанность:** Смешаны сетевые операции, парсинг, управление файлами
3. **Сложность тестирования:** Невозможно мокировать отдельные части
4. **Дублирование:** Логика работы с сокетами разбросана

## Предлагаемое решение

### Разбиение на специализированные классы

#### 1. `PatchConnection` (`connection.py`)
**Ответственность:** Управление подключением к патч-серверу

**Методы:**
- `connect()` - подключение к серверу
- `disconnect()` - отключение
- `send()` - отправка данных
- `receive()` - получение данных
- `get_patch_urls()` - получение URL патч-сервера

**Атрибуты:**
- `sock_fd` - file descriptor сокета
- `master_server` - адрес сервера
- `timeout` - таймаут

#### 2. `PatchDownloader` (`downloader.py`)
**Ответственность:** Загрузка файлов с патч-сервера

**Методы:**
- `download()` - загрузка файла на диск
- `download_raw()` - загрузка сырых байтов
- `download_to_path()` - загрузка в указанный путь

**Зависимости:**
- `PatchConnection` (для получения URL)

#### 3. `PatchProtocolParser` (`protocol.py`)
**Ответственность:** Парсинг протокола патч-сервера

**Методы:**
- `parse_patch_urls()` - парсинг URL из ответа
- `parse_file_list_header()` - парсинг заголовка списка файлов
- `parse_file_item()` - парсинг одного файла
- `parse_directory_item()` - парсинг директории
- `extract_varchar()` - извлечение строки

**Константы:**
- `PROTO_PRE` - префикс протокола
- `PROTO_HEADER2` - заголовок ответа
- `PROTO_VERSION` - версия протокола

#### 4. `PatchFileListBuilder` (`file_list.py`)
**Ответственность:** Построение структуры списка файлов

**Методы:**
- `update_filelist()` - обновление списка файлов
- `add_folder()` - добавление папки
- `add_file()` - добавление файла
- `get_directory()` - получение структуры директорий

**Зависимости:**
- `PatchConnection` (для запросов)
- `PatchProtocolParser` (для парсинга)

#### 5. `PatchHashChecker` (`hash_checker.py`)
**Ответственность:** Проверка хешей файлов и директорий

**Методы:**
- `check_hash()` - проверка хеша узла
- `check_file_hash()` - проверка хеша файла
- `check_directory_hash()` - проверка хеша директории
- `find_outdated_files()` - поиск устаревших файлов

#### 6. `PatchFileUpdater` (`updater.py`)
**Ответственность:** Обновление файлов

**Методы:**
- `update_files()` - обновление файлов
- `update_file()` - обновление одного файла
- `update_directory()` - обновление директории

**Зависимости:**
- `PatchDownloader` (для загрузки)
- `PatchHashChecker` (для проверки)

### Рефакторинг существующих классов

#### `Patch` → Facade
**Новая структура:**
```python
class Patch:
    def __init__(self):
        self._connection = PatchConnection()
        self._downloader = PatchDownloader(self._connection)
        self._version = None
    
    def download(self, file_path, dst_dir=None, dst_file=None):
        return self._downloader.download(file_path, dst_dir, dst_file)
    
    @property
    def version(self):
        if self._version is None:
            self._version = self._connection.get_version()
        return self._version
```

#### `PatchFileList` → Facade
**Новая структура:**
```python
class PatchFileList:
    def __init__(self, patch):
        self._connection = patch._connection
        self._protocol = PatchProtocolParser()
        self._builder = PatchFileListBuilder(self._connection, self._protocol)
        self.directory = self._builder.get_directory()
    
    def update_filelist(self, folders):
        return self._builder.update_filelist(folders)
```

## Структура модулей

```
PyPoE/poe/patchserver/
├── __init__.py
├── connection.py      # PatchConnection
├── downloader.py      # PatchDownloader
├── protocol.py         # PatchProtocolParser
├── file_list.py       # PatchFileListBuilder
├── hash_checker.py    # PatchHashChecker
├── updater.py         # PatchFileUpdater
├── records.py         # BaseRecordData, VirtualDirectoryRecord, VirtualFileRecord
├── node.py            # DirectoryNodeExtended
├── patch.py           # Patch (Facade)
└── file_list.py       # PatchFileList (Facade)
```

## План реализации

### Phase 7.6.1: Create Specialized Classes
1. Создать `PatchConnection` (connection.py)
2. Создать `PatchDownloader` (downloader.py)
3. Создать `PatchProtocolParser` (protocol.py)
4. Создать `PatchFileListBuilder` (file_list.py)
5. Создать `PatchHashChecker` (hash_checker.py)
6. Создать `PatchFileUpdater` (updater.py)
7. Переместить вспомогательные классы (records.py, node.py)

### Phase 7.6.2: Refactor Patch and PatchFileList
1. Рефакторить `Patch` как Facade
2. Рефакторить `PatchFileList` как Facade
3. Обновить импорты

### Phase 7.6.3: Update Tests and Documentation
1. Обновить тесты
2. Обновить документацию
3. Проверить backward compatibility

## Преимущества

1. **Single Responsibility:** Каждый класс отвечает за одну задачу
2. **Testability:** Легко мокировать и тестировать отдельные компоненты
3. **Maintainability:** Изменения в одном компоненте не влияют на другие
4. **Reusability:** Компоненты можно использовать независимо
5. **DI Support:** Легко внедрять зависимости

## Оценка времени

- Phase 7.6.1: 6-8 часов
- Phase 7.6.2: 2-3 часа
- Phase 7.6.3: 1-2 часа
**Итого:** 9-13 часов

## Риски

1. **Сложность протокола:** Протокол патч-сервера может быть сложным для парсинга
2. **Socket management:** Управление сокетами требует аккуратности
3. **Backward compatibility:** Нужно сохранить совместимость API

## Следующие шаги

После завершения Phase 7.6:
- Phase 7.7: Другие God Objects (если есть)
- Phase 9: Additional Patterns

