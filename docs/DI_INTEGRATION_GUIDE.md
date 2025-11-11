# 🏗️ Dependency Injection Integration Guide

**Руководство по использованию DI контейнера в PyPoE**

---

## 📋 Обзор

PyPoE теперь поддерживает Dependency Injection (DI) для управления зависимостями и упрощения тестирования. Этот гайд покажет, как использовать DI контейнер в вашем коде.

---

## 🚀 Быстрый старт

### 1. Базовое использование

```python
from PyPoE.poe.providers import create_configured_container
from PyPoE.poe.file.ggpk import GGPKFile
from PyPoE.poe.file.factory import FileParserFactory

# Создать настроенный контейнер
container = create_configured_container()

# Получить GGPKFile (transient - новый каждый раз)
ggpk = container.resolve(GGPKFile)
ggpk.read("Content.ggpk")

# Получить FileParserFactory (singleton - один для всех)
factory = container.resolve(FileParserFactory)
spec = factory.get_specification()
```

### 2. Использование с game path

```python
from PyPoE.poe.providers import create_configured_container
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.constants import VERSION

# Создать контейнер с указанием пути к игре
container = create_configured_container(
    game_path="C:/Program Files/Path of Exile",
    version=VERSION.STABLE
)

# Теперь можно резолвить FileSystem
fs = container.resolve(FileSystem)
file_data = fs.get_file("Data/Passive.dat")
```

---

## 🎯 Зарегистрированные компоненты

### Core Components

| Component | Lifecycle | Description |
|-----------|-----------|-------------|
| `GGPKFile` | **Transient** | Новый экземпляр каждый раз |
| `FileParserFactory` | **Singleton** | Один экземпляр на контейнер |
| `SQLiteSpecRepository` | **Singleton** | Один экземпляр на контейнер |
| `FileSystem` | **Singleton** | Если указан `game_path` |

---

## 📦 Примеры использования

### Пример 1: Чтение GGPK файла через DI

```python
from PyPoE.shared.di import get_container
from PyPoE.poe.providers import register_core_providers
from PyPoE.poe.file.ggpk import GGPKFile

# Получить глобальный контейнер
container = get_container()
register_core_providers(container)

# Resolve GGPKFile
ggpk = container.resolve(GGPKFile)

# Использовать как обычно
ggpk.read("Content.ggpk")
ggpk.directory_build()

# Экстракция файла
node = ggpk["Metadata/StatDescriptions/stat_descriptions.txt"]
content = node.record.extract()
```

### Пример 2: Работа со спецификациями

```python
from PyPoE.poe.providers import create_configured_container
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.poe.file.dat import DatFile

# Создать контейнер
container = create_configured_container()

# Получить factory
factory = container.resolve(FileParserFactory)

# Получить спецификацию
spec = factory.get_specification()

# Использовать для чтения DAT файлов
dat = DatFile()
dat.read("Data/ActiveSkills.dat", specification=spec["ActiveSkills.dat"])

print(f"Loaded {len(dat.reader)} rows")
```

### Пример 3: Custom компоненты в DI

```python
from PyPoE.shared.di import DIContainer
from PyPoE.poe.providers import register_core_providers

# Создать свой контейнер
container = DIContainer()

# Зарегистрировать core компоненты
register_core_providers(container)

# Зарегистрировать свои компоненты
class MyService:
    def __init__(self, ggpk: GGPKFile):
        self.ggpk = ggpk

# Зарегистрировать с зависимостью
container.register_factory(
    MyService,
    lambda c: MyService(c.resolve(GGPKFile))
)

# Использовать
service = container.resolve(MyService)
```

---

## 🧪 Тестирование с DI

### Пример теста с моком

```python
import pytest
from PyPoE.shared.di import DIContainer
from PyPoE.poe.file.ggpk import GGPKFile

def test_my_function_with_mock():
    """Test using mock GGPK file."""
    # Создать контейнер для теста
    container = DIContainer()
    
    # Создать mock
    class MockGGPK:
        def read(self, path):
            pass
        
        def directory_build(self):
            self.directory = MockDirectory()
    
    # Зарегистрировать mock
    container.register_instance(GGPKFile, MockGGPK())
    
    # Использовать в тесте
    ggpk = container.resolve(GGPKFile)
    ggpk.read("test.ggpk")
    assert ggpk.directory is not None
```

### Пример теста с reset

```python
import pytest
from PyPoE.shared.di import get_container, reset_container
from PyPoE.poe.providers import register_core_providers

def test_with_container_reset():
    """Test with container reset."""
    # Reset перед тестом
    reset_container()
    
    container = get_container()
    register_core_providers(container)
    
    # Ваш тест
    factory = container.resolve(FileParserFactory)
    assert factory is not None
    
    # Reset после теста
    reset_container()
```

---

## 🎨 Best Practices

### ✅ DO

1. **Используйте глобальный контейнер для production кода**
   ```python
   from PyPoE.shared.di import get_container
   container = get_container()
   ```

2. **Создавайте новый контейнер для каждого теста**
   ```python
   container = DIContainer()
   ```

3. **Регистрируйте зависимости один раз при старте**
   ```python
   from PyPoE.poe.providers import register_core_providers
   register_core_providers(container)
   ```

4. **Используйте factory для компонентов с зависимостями**
   ```python
   container.register_factory(
       MyClass,
       lambda c: MyClass(c.resolve(Dependency))
   )
   ```

### ❌ DON'T

1. **Не создавайте зависимости напрямую, если они в DI**
   ```python
   # ❌ Плохо
   ggpk = GGPKFile()
   
   # ✅ Хорошо
   ggpk = container.resolve(GGPKFile)
   ```

2. **Не регистрируйте провайдеры повторно**
   ```python
   # ❌ Плохо
   register_core_providers(container)
   register_core_providers(container)  # Duplicate!
   
   # ✅ Хорошо
   if not container.is_registered(GGPKFile):
       register_core_providers(container)
   ```

3. **Не смешивайте singleton и transient lifecycle неправильно**
   ```python
   # ❌ Плохо - GGPKFile должен быть transient
   container.register_singleton(GGPKFile, lambda: GGPKFile())
   
   # ✅ Хорошо
   container.register_transient(GGPKFile, lambda: GGPKFile())
   ```

---

## 🔧 Продвинутое использование

### Custom версии спецификаций

```python
from PyPoE.poe.providers import create_configured_container
from PyPoE.poe.constants import VERSION

# Stable version
container_stable = create_configured_container(version=VERSION.STABLE)

# Beta version
container_beta = create_configured_container(version=VERSION.BETA)

# Alpha version
container_alpha = create_configured_container(version=VERSION.ALPHA)
```

### Множественные контейнеры

```python
from PyPoE.shared.di import DIContainer
from PyPoE.poe.providers import register_core_providers

# Контейнер для production
prod_container = DIContainer()
register_core_providers(prod_container, game_path="C:/PoE")

# Контейнер для dev
dev_container = DIContainer()
register_core_providers(dev_container, game_path="D:/PoE_Dev")

# Использовать разные контейнеры
prod_fs = prod_container.resolve(FileSystem)
dev_fs = dev_container.resolve(FileSystem)
```

### Lazy initialization

```python
from PyPoE.poe.providers import create_configured_container

# Контейнер создается, но компоненты не инициализируются
container = create_configured_container()

# Инициализация происходит только при первом resolve
factory = container.resolve(FileParserFactory)  # Здесь инициализация
```

---

## 📚 API Reference

### DIContainer

```python
class DIContainer:
    def register_singleton(self, interface: type[T], factory: Callable[[], T]) -> None
    def register_transient(self, interface: type[T], factory: Callable[[], T]) -> None
    def register_instance(self, interface: type[T], instance: T) -> None
    def register_factory(self, interface: type[T], factory: Callable[[DIContainer], T]) -> None
    def resolve(self, interface: type[T]) -> T
    def is_registered(self, interface: type) -> bool
    def reset(self, interface: type | None = None) -> None
    def clear(self) -> None
    def list_providers(self) -> list[str]
```

### Providers

```python
def register_core_providers(
    container: DIContainer,
    game_path: str | None = None,
    version: VERSION = VERSION.STABLE,
) -> None

def create_configured_container(
    game_path: str | None = None,
    version: VERSION = VERSION.STABLE,
) -> DIContainer
```

---

## 🐛 Troubleshooting

### Ошибка: "No provider registered"

```python
# Проблема
ggpk = container.resolve(GGPKFile)  # DIError: No provider registered

# Решение
from PyPoE.poe.providers import register_core_providers
register_core_providers(container)
ggpk = container.resolve(GGPKFile)  # OK
```

### Ошибка: "Specification database not found"

```python
# Проблема
container = create_configured_container()  # FileNotFoundError

# Решение
# Запустите миграцию спецификаций:
python scripts/migrate_specs_to_db.py
```

### Singleton не работает как ожидалось

```python
# Проблема
factory1 = container.resolve(FileParserFactory)
factory2 = container.resolve(FileParserFactory)
assert factory1 is not factory2  # Fail!

# Причина: используется разный контейнер
# Решение: используйте один контейнер
from PyPoE.shared.di import get_container
container = get_container()  # Глобальный singleton
```

---

## 📖 Дополнительные ресурсы

- **DI Container:** `PyPoE/shared/di.py`
- **Providers:** `PyPoE/poe/providers.py`
- **Тесты DI:** `tests/unit/shared/test_di.py`
- **Тесты Providers:** `tests/unit/poe/test_providers.py`
- **Архитектурный анализ:** `ARCHITECTURE_ANALYSIS.md`

---

## 🎯 Roadmap

### ✅ Completed
- DI Container
- Core providers
- Integration guide

### 🔄 In Progress
- UI integration with DI
- GGPKFile refactoring

### 📅 Planned
- CLI integration with DI
- Plugin system with DI
- Auto-wiring support

---

**Happy Injecting! 💉**

