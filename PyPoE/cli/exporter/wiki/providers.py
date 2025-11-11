"""
Dependency Injection providers for Wiki Export CLI components.

This module provides factory functions and registration helpers for CLI
export components, enabling dependency injection for BaseParser and ItemsParser.
"""


from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.util import get_content_path
from PyPoE.poe.constants import VERSION
from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.factory import FileParserFactory
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.ot import OTFileCache
from PyPoE.poe.file.specification.fields import Specification
from PyPoE.poe.file.translations import (
    TranslationFile,
    TranslationFileCache,
    get_custom_translation_file,
    install_data_dependant_quantifiers,
)
from PyPoE.shared.di import DIContainer
from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)


def register_wiki_providers(
    container: DIContainer,
    game_path: str | None = None,
    version: VERSION = VERSION.STABLE,
    language: str | None = None,
) -> None:
    """
    Register Wiki Export CLI providers in the DI container.

    This function registers dependencies used by BaseParser and ItemsParser:
    - FileSystem (if game_path provided)
    - Specification (from FileParserFactory)
    - RelationalReader (with proper configuration)
    - TranslationFileCache
    - OTFileCache
    - Custom TranslationFile

    Args:
        container: DI container instance
        game_path: Path to game installation (optional, uses config if None)
        version: Game version for specifications
        language: Language code (optional, uses config if None)

    Example:
        >>> from PyPoE.shared.di import DIContainer
        >>> from PyPoE.cli.exporter.wiki.providers import register_wiki_providers
        >>> from PyPoE.cli.exporter.wiki.parser.base import BaseParser
        >>>
        >>> container = DIContainer()
        >>> register_wiki_providers(container, game_path="C:/PoE")
        >>>
        >>> # Create BaseParser with DI
        >>> parser = BaseParser.with_factory(
        ...     base_path="output",
        ...     parsed_args=args,
        ...     container=container,
        ... )
    """
    logger.info("Registering wiki export providers", version=version.name)

    # Ensure core providers are registered first
    from PyPoE.poe.providers import register_core_providers

    register_core_providers(container, game_path=game_path, version=version)

    # Get language from config if not provided
    lang = language if language is not None else config.get_option("language")

    # Get game path from config if not provided
    content_path = game_path if game_path is not None else get_content_path()

    # FileSystem (singleton, if not already registered)
    if not container.is_registered(FileSystem):
        container.register_singleton(
            FileSystem,
            lambda: FileSystem(root_path=content_path),
        )
        logger.info("FileSystem registered for wiki export", game_path=content_path)

    # Specification (from FileParserFactory)
    if not container.is_registered(Specification):
        container.register_factory(
            Specification,
            lambda c: c.resolve(FileParserFactory).get_specification(version),
        )

    # RelationalReader (transient - each parser needs its own)
    # Note: BaseParser creates its own RelationalReader with specific files,
    # so we register a factory that can be customized per parser
    container.register_factory(
        RelationalReader,
        lambda c: _create_relational_reader(
            c.resolve(FileSystem),
            c.resolve(Specification),
            lang,
        ),
    )

    # TranslationFileCache (singleton - can be shared)
    if not container.is_registered(TranslationFileCache):
        container.register_factory(
            TranslationFileCache,
            lambda c: TranslationFileCache(path_or_file_system=c.resolve(FileSystem)),
        )

    # OTFileCache (singleton - can be shared)
    if not container.is_registered(OTFileCache):
        container.register_factory(
            OTFileCache,
            lambda c: OTFileCache(path_or_file_system=c.resolve(FileSystem)),
        )

    # Custom TranslationFile (singleton - can be shared)
    if not container.is_registered(TranslationFile):
        container.register_factory(
            TranslationFile,
            lambda c: get_custom_translation_file(),
        )

    logger.info("Wiki export providers registered successfully", language=lang)


def _create_relational_reader(
    file_system: FileSystem,
    specification: Specification,
    language: str,
) -> RelationalReader:
    """
    Create RelationalReader with default configuration.

    Args:
        file_system: FileSystem instance
        specification: Specification instance
        language: Language code

    Returns:
        RelationalReader instance

    Note:
        This creates a basic RelationalReader. BaseParser will create
        its own with specific files list. This is mainly for ItemsParser
        which may need additional readers.
    """
    opt = {
        "use_dat_value": False,
        "auto_build_index": True,
        "specification": specification,
    }
    rr = RelationalReader(
        path_or_file_system=file_system,
        files=[],  # Empty - BaseParser will specify its own files
        read_options=opt,
        raise_error_on_missing_relation=False,
        language=language,
    )
    install_data_dependant_quantifiers(rr)
    return rr  # type: ignore[no-any-return]

