"""
Protocol interfaces for ItemsParser and its mixins.

Defines the contract that ItemsParser must implement for type checking.
"""

from typing import Protocol, Any, Dict, Set, OrderedDict as OrderedDictType
from collections import OrderedDict

# =============================================================================
# Protocols
# =============================================================================


class ItemsParserProtocol(Protocol):
    """
    Protocol defining the interface that ItemsParser provides to mixins.
    
    This allows mixins to reference parent class attributes without
    causing circular imports or MyPy errors.
    """

    # Language and localization
    _LANG: Dict[str, Dict[str, str]]
    _language: str
    
    # Item filtering and configuration
    _DROP_DISABLED_ITEMS_BY_ID: Set[str]
    _IGNORE_DROP_LEVEL_CLASSES: tuple
    _IGNORE_DROP_LEVEL_ITEMS_BY_ID: Set[str]
    _SKIP_ITEMS_BY_ID: Set[str]
    _NAME_OVERRIDE_BY_ID: Dict[str, Dict[str, str]]
    
    # Map configuration
    _MAP_COLORS: Dict[str, str]
    _MAP_RELEASE_VERSION: Dict[str, str]
    
    # Attribute mappings
    _attribute_map: OrderedDictType
    _master_hideout_doodad_map: tuple
    
    # Properties
    _cls_map: Any  # Returns dict, but defined as @property
    
    # Data access
    rr: Any  # RelationalReader
    rr2: Any  # RelationalReader (alternative)
    tc: Any  # TranslationFileCache
    ot: Any  # OTFile
    file_system: Any
    
    # Image handling
    _img_path: Any
    
    # Parsed arguments
    _parsed_args: Any
    
    # Methods that mixins call
    def _format_map_name(self, *args: Any, **kwargs: Any) -> str: ...
    def _get_map_series(self, *args: Any, **kwargs: Any) -> Any: ...
    def _get_stats(self, *args: Any, **kwargs: Any) -> Any: ...
    def _image_init(self, *args: Any, **kwargs: Any) -> None: ...
    def _write_dds(self, *args: Any, **kwargs: Any) -> None: ...
    def _item_column_index_filter(self, *args: Any, **kwargs: Any) -> Any: ...
    def _parse_class_filter(self, *args: Any, **kwargs: Any) -> bool: ...
    def _process_base_item_type(self, *args: Any, **kwargs: Any) -> None: ...
    def _process_name_conflicts(self, *args: Any, **kwargs: Any) -> None: ...
    def _process_purchase_costs(self, *args: Any, **kwargs: Any) -> None: ...
    def _skill(self, *args: Any, **kwargs: Any) -> bool: ...
    def _export(self, *args: Any, **kwargs: Any) -> Any: ...


__all__ = ['ItemsParserProtocol']

