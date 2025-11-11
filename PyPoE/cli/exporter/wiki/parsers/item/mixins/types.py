"""
TypesMixin for ItemsParser.

Contains types-related methods only.
Class attributes are defined in the main ItemsParser class.
"""

# =============================================================================
# Imports
# =============================================================================

import re
from typing import TYPE_CHECKING, Any, Dict

# =============================================================================
# Classes
# =============================================================================


class TypesMixin:
    """Mixin providing types methods for ItemsParser."""
    
    # Type hints for attributes from parent ItemsParser class
    if TYPE_CHECKING:
        _LANG: Dict[str, Dict[str, str]]

    def _type_level(self, infobox, base_item_type):
        infobox["required_level"] = base_item_type["DropLevel"]

        return True

    def _type_amulet(self, infobox, base_item_type):
        match = re.search("Talisman([0-9])", base_item_type["Id"])
        if match:
            infobox["is_talisman"] = True
            infobox["talisman_tier"] = match.group(1)

        return True
