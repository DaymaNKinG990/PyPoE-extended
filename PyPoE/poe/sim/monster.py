"""
Utilities for dealing with monsters and related calculations.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/sim/monster.py.                                        |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utilities for dealing with monsters and related calculations.

Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

Public API
-------------------------------------------------------------------------------

Internal API
-------------------------------------------------------------------------------
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from collections.abc import Iterable

# 3rd-party
# self
from PyPoE.poe.constants import RARITY
from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.ot import OTFileCache

# =============================================================================
# Globals
# =============================================================================

__all__ = []

# =============================================================================
# Classes
# =============================================================================


class Monster:
    """
    Represents a monster for simulation purposes.

    Provides access to monster data and calculations including damage,
    resistances, and granted effects.

    Attributes:
        parent: MonsterFactory instance
        mv: MonsterVarieties.dat row
        mt: MonsterTypes.dat row
        _res: MonsterResistances.dat row
        _ge: GrantedEffects list
        _gepl: GrantedEffectsPerLevel list
        _mods: Mods list
        _level: Monster level (1-100)
    """

    def __init__(self, parent: Any, mv: Any) -> None:
        """
        Initialize monster instance.

        Args:
            parent: MonsterFactory instance
            mv: MonsterVarieties.dat row
        """
        self.parent = parent
        self._mv = mv
        self._mt = self.mv["MonsterTypesKey"]
        self._res = self.mt["MonsterResistancesKey"]
        self._ge = self.mv["GrantedEffectsKeys"]
        self._gepl = [
            gepl
            for gepl in parent.rr["GrantedEffectsPerLevel.dat"]
            if gepl["GrantedEffectsKey"] == self._ge
        ]
        self._mods = self.mv["ModsKeys"]

        self._level = None

    @property
    def mv(self) -> Any:  # type: ignore[attr-defined]
        """
        Get MonsterVarieties.dat row.

        Returns:
            MonsterVarieties.dat row
        """
        return self._mv

    @property
    def mt(self) -> Any:  # type: ignore[attr-defined]
        """
        Get MonsterTypes.dat row.

        Returns:
            MonsterTypes.dat row
        """
        return self._mt

    @property
    def level(self) -> int:
        """
        Get monster level.

        Returns:
            Monster level (1-100)

        Raises:
            ValueError: If level has not been set
        """
        if self._level is None:
            raise ValueError(
                "Set monster level first before performing actions that require monster level"
            )
        return self._level

    @level.setter
    def level(self, value: int) -> None:
        """
        Set monster level.

        Args:
            value: Level value (1-100)

        Raises:
            ValueError: If level is not in valid range
        """
        if value < 1 or value > 100:
            raise ValueError("Monster level must be 1-100")
        self._level = value

    def damage(self, map_tier: int | None = None) -> Any:
        """
        Calculate monster damage.

        Args:
            map_tier: Optional map tier for damage calculation

        Returns:
            Damage value or calculation result
        """
        self.parent.rr["DefaultMonsterStats.dat"][self.level]


class MonsterFactory:
    """
    Factory for creating and managing Monster instances.

    Handles loading of monster data and provides methods to create
    Monster instances from various search criteria.

    Attributes:
        rr: RelationalReader instance
        ot: OTFileCache instance
        rarity_mods: Dictionary mapping rarities to mods
    """

    _files = [
        "DefaultMonsterStats.dat",
        # Loads mods, stats, granted effects, etc
        "MonsterVarieties.dat",
        "GrantedEffectsPerLevel.dat",
    ]

    rarity_mods: dict[Any, Any] | None = None

    def __init__(self, *args: Any, relational_reader: Any, otfile_cache: Any, **kwargs: Any) -> None:
        """
        Initialize monster factory.

        Args:
            *args: Additional positional arguments (unused)
            relational_reader: RelationalReader instance for data access
            otfile_cache: OTFileCache instance for OT file access
            **kwargs: Additional keyword arguments (unused)

        Raises:
            ValueError: If relational_reader is not a RelationalReader instance
            ValueError: If otfile_cache is not an OTFileCache instance
        """
        if isinstance(relational_reader, RelationalReader):
            self.rr = relational_reader
        else:
            raise ValueError("relational_reader must be a RelationalReader instance")
        if isinstance(otfile_cache, OTFileCache):
            self.ot = otfile_cache
        else:
            raise ValueError("otfile_cache must be a OTFileCache instance.")

        # Load files
        for fn in self._files:
            self.rr[fn]

        self.rarity_mods = {
            RARITY.NORMAL: [],
        }
        for mod in self.rr["Mods.dat"]:
            if mod["Id"].startswith("MonsterMagic"):
                self.rarity_mods[RARITY.MAGIC] = mod  # type: ignore[index]
            elif mod["Id"].startswith("MonsterRare"):
                self.rarity_mods[RARITY.RARE] = mod  # type: ignore[index]
            elif mod["Id"].startswith("MonsterUnique"):
                self.rarity_mods[RARITY.UNIQUE] = mod  # type: ignore[index]

    def monster(self, rowid: int | Iterable[int] | None = None, metaid: str | Iterable[str] | None = None, name: str | Iterable[str] | None = None, *args: Any, **kwargs: Any) -> list[Monster]:
        """
        Create Monster instances based on search parameters.

        Args:
            rowid: Row ID or list of row IDs to search for
            metaid: Metadata ID or list of metadata IDs to search for
            name: Name or list of names to search for
            *args: Additional positional arguments (unused)
            **kwargs: Additional keyword arguments (unused)

        Returns:
            List of Monster instances matching the search criteria
        """
        if isinstance(rowid, int):
            mv = [
                self.rr["MonsterVarieties.dat"][rowid],
            ]
        elif isinstance(rowid, Iterable):
            mv = [self.rr["MonsterVarieties.dat"][rid] for rid in rowid]
        elif isinstance(metaid, str):
            mv = [
                self.rr["MonsterVarieties.dat"].index["Id"][metaid],
            ]
        elif isinstance(metaid, Iterable):
            mv = [self.rr["MonsterVarieties.dat"].index["Id"][mid] for mid in metaid]
        elif isinstance(name, str):
            mv = [m for m in self.rr["MonsterVarieties.dat"] if m["Name"] == name]
        elif isinstance(name, Iterable):
            mv = [m for m in self.rr["MonsterVarieties.dat"] if m["Name"] in name]
        else:
            raise ValueError(
                "One of rowid, metaid or name must be specified and be of the correct type"
            )

        return [
            Monster(  # type: ignore[misc]
                *args, parent=self, mv=m, **kwargs
            )
            for m in mv
        ]


# =============================================================================
# Functions
# =============================================================================
