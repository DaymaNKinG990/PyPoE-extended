"""
Example: Using Dependency Injection in PyPoE

This example demonstrates how to use the DI container to manage
dependencies and create loosely coupled code.
"""

from pathlib import Path

from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.poe.file.ggpk import GGPKFile
from PyPoE.poe.providers import create_configured_container
from PyPoE.shared.di import DIContainer, get_container
from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)


def example_1_basic_usage():
    """Example 1: Basic DI container usage."""
    print("\n" + "=" * 60)
    print("Example 1: Basic DI Container Usage")
    print("=" * 60)

    # Create configured container with all providers
    container = create_configured_container()

    # Resolve GGPKFile (transient - new instance each time)
    ggpk1 = container.resolve(GGPKFile)
    ggpk2 = container.resolve(GGPKFile)

    print(f"GGPKFile instance 1: {id(ggpk1)}")
    print(f"GGPKFile instance 2: {id(ggpk2)}")
    print(f"Are they the same? {ggpk1 is ggpk2}")  # False - transient

    # Resolve FileParserFactory (singleton - same instance)
    factory1 = container.resolve(FileParserFactory)
    factory2 = container.resolve(FileParserFactory)

    print(f"\nFileParserFactory instance 1: {id(factory1)}")
    print(f"FileParserFactory instance 2: {id(factory2)}")
    print(f"Are they the same? {factory1 is factory2}")  # True - singleton


def example_2_with_game_path():
    """Example 2: Using DI with game path."""
    print("\n" + "=" * 60)
    print("Example 2: DI with Game Path")
    print("=" * 60)

    # This will fail if game is not installed at this path
    # Replace with your actual Path of Exile installation path
    game_path = "C:/Program Files/Grinding Gear Games/Path of Exile"

    if Path(game_path).exists():
        from PyPoE.poe.file.file_system import FileSystem

        container = create_configured_container(
            game_path=game_path, version=VERSION.STABLE
        )

        # Now FileSystem is available
        fs = container.resolve(FileSystem)
        print(f"FileSystem root path: {fs.root_path}")
        print(f"FileSystem has GGPK: {fs.ggpk is not None}")
    else:
        print(f"Game path not found: {game_path}")
        print("Skipping FileSystem example")


def example_3_custom_service():
    """Example 3: Creating custom service with DI."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Service with DI")
    print("=" * 60)

    # Define a custom service that depends on FileParserFactory
    class DataService:
        """Service that uses FileParserFactory."""

        def __init__(self, factory: FileParserFactory):
            self.factory = factory
            logger.info("DataService initialized")

        def get_spec_count(self) -> int:
            """Get number of specifications."""
            spec = self.factory.get_specification()
            return len(spec)

        def list_specs(self) -> list[str]:
            """List all specification names."""
            spec = self.factory.get_specification()
            return list(spec.keys())[:10]  # First 10

    # Create container and register custom service
    container = create_configured_container()

    container.register_factory(
        DataService, lambda c: DataService(c.resolve(FileParserFactory))
    )

    # Resolve and use custom service
    service = container.resolve(DataService)
    count = service.get_spec_count()
    specs = service.list_specs()

    print(f"Total specifications: {count}")
    print(f"First 10 specs: {specs}")


def example_4_manual_registration():
    """Example 4: Manual provider registration."""
    print("\n" + "=" * 60)
    print("Example 4: Manual Provider Registration")
    print("=" * 60)

    # Create empty container
    container = DIContainer()

    # Manually register providers
    container.register_transient(GGPKFile, lambda: GGPKFile())

    print("Registered providers:")
    for provider in container.list_providers():
        print(f"  - {provider}")

    # Check if registered
    print(f"\nIs GGPKFile registered? {container.is_registered(GGPKFile)}")
    print(
        f"Is FileParserFactory registered? {container.is_registered(FileParserFactory)}"
    )

    # Resolve
    ggpk = container.resolve(GGPKFile)
    print(f"\nResolved GGPKFile: {type(ggpk).__name__}")


def example_5_global_container():
    """Example 5: Using global container singleton."""
    print("\n" + "=" * 60)
    print("Example 5: Global Container Singleton")
    print("=" * 60)

    from PyPoE.poe.providers import register_core_providers
    from PyPoE.shared.di import reset_container

    # Reset to ensure clean state
    reset_container()

    # Get global container
    container1 = get_container()
    container2 = get_container()

    print(f"Container 1 ID: {id(container1)}")
    print(f"Container 2 ID: {id(container2)}")
    print(f"Are they the same? {container1 is container2}")  # True

    # Register providers in global container
    register_core_providers(container1)

    # Can now resolve from any reference to global container
    ggpk = container2.resolve(GGPKFile)
    print(f"\nResolved GGPKFile from container2: {type(ggpk).__name__}")


def example_6_testing_pattern():
    """Example 6: Testing pattern with DI."""
    print("\n" + "=" * 60)
    print("Example 6: Testing Pattern with DI")
    print("=" * 60)

    # Create a mock GGPK file for testing
    class MockGGPKFile:
        """Mock GGPK file for testing."""

        def __init__(self):
            self.data = b"mock data"
            logger.info("MockGGPKFile created")

        def read(self, path: str):
            logger.info(f"Mock reading: {path}")
            return self.data

    # Create test container with mock
    test_container = DIContainer()
    test_container.register_instance(GGPKFile, MockGGPKFile())  # type: ignore[arg-type]

    # Use mock in test
    ggpk = test_container.resolve(GGPKFile)
    data = ggpk.read("test.ggpk")  # type: ignore[attr-defined]

    print(f"Mock GGPK type: {type(ggpk).__name__}")
    print(f"Mock data: {data}")


def example_7_lifecycle_comparison():
    """Example 7: Comparing singleton vs transient lifecycles."""
    print("\n" + "=" * 60)
    print("Example 7: Singleton vs Transient Lifecycles")
    print("=" * 60)

    container = create_configured_container()

    # Transient: new instance each time
    print("Transient (GGPKFile):")
    instances = [container.resolve(GGPKFile) for _ in range(3)]
    ids = [id(inst) for inst in instances]
    print(f"  Instance IDs: {ids}")
    print(f"  All unique: {len(set(ids)) == 3}")

    # Singleton: same instance each time
    print("\nSingleton (FileParserFactory):")
    factory_instances = [container.resolve(FileParserFactory) for _ in range(3)]
    factory_ids = [id(inst) for inst in factory_instances]
    print(f"  Instance IDs: {factory_ids}")
    print(f"  All same: {len(set(factory_ids)) == 1}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PyPoE Dependency Injection Examples")
    print("=" * 60)

    try:
        example_1_basic_usage()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_2_with_game_path()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        example_3_custom_service()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        example_4_manual_registration()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    try:
        example_5_global_container()
    except Exception as e:
        print(f"Example 5 failed: {e}")

    try:
        example_6_testing_pattern()
    except Exception as e:
        print(f"Example 6 failed: {e}")

    try:
        example_7_lifecycle_comparison()
    except Exception as e:
        print(f"Example 7 failed: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

