"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/psg.py                                            |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Support for .psg (Passive Skill Graph) file format.

Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

Public API
-------------------------------------------------------------------------------

API for common and every day use.

.. autoclass:: PSGFile
    :inherited-members:

Internal API
-------------------------------------------------------------------------------

API for internal use, but still may be useful to work with more directly.

.. autoclass:: GraphGroup

.. autoclass:: GraphGroupNode
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import struct
from collections import OrderedDict
from typing import Any

from PyPoE.poe.file.dat import DatFile, RelationalReader
from PyPoE.poe.file.shared import AbstractFileReadOnly

# 3rd-party
# self
from PyPoE.shared.mixins import ReprMixin

# =============================================================================
# Globals
# =============================================================================

__all__ = ["PSGFile"]

PSG_COL = "PassiveSkillGraphId"

# =============================================================================
# Classes
# =============================================================================


class GraphGroup(ReprMixin):
    """
    Representation of a group in the passive skill tree graph.

    Groups are a "circle" in the passive at a given position containing all the
    relevant nodes. It is possible that a group only contains one node - this is
    common for the highway/pathway nodes.

    Attributes:
        x: X coordinate in the passive skill tree
        y: Y coordinate in the passive skill tree
        id: ID (index in list) of this group
        nodes: List of child GraphGroupNode instances
        flag: Unknown flag value
    """

    __slots__ = ["x", "y", "id", "nodes", "flag"]

    _REPR_EXTRA_ATTRIBUTES = OrderedDict((("nodes", None),))

    def __init__(self, x: float, y: float, id: int, flag: bool) -> None:
        """
        Initialize graph group.

        Args:
            x: X coordinate in the passive skill tree
            y: Y coordinate in the passive skill tree
            id: ID (index in list) of this group
            flag: Unknown flag value
        """
        self.x = x
        self.y = y
        self.id = id
        self.nodes = []
        self.flag = flag

    @property
    def point(self) -> tuple[float, float]:
        """
        Get point coordinates as tuple.

        Returns:
            Tuple containing the x and y coordinate
        """
        return self.x, self.y

    def _update_connections(self, dat_reader: Any) -> None:
        """
        Update stored connections using the given dat_reader instance.

        Args:
            dat_reader: DatReader instance to use for updating connections
        """
        for node in self.nodes:
            node._update_connections(dat_reader)


class GraphGroupNode(ReprMixin):
    """
    Representation of a single node in a GraphGroup.

    A node contains the actual information about the passive skill value it
    holds and the connection as well the as the position within the group.

    Warning:
        If the parent PSGFile was instantiated with a valid 'PassiveSkills.dat'
        DatFile instance, the passive_skill and connections variables contain
        references to the respective row (i.e. a DatRecord instance) instead
        of the integer id.

    Attributes:
        parent: Parent GraphGroup this node belongs to
        passive_skill: Passive skill node (int or DatRecord)
        radius: Radius from the parent's x,y-position
        position: Position within the group (0-11, clockwise rotation)
        connections: List of connected node IDs or DatRecords
    """

    __slots__ = ["parent", "passive_skill", "radius", "position", "connections"]

    def __init__(
        self,
        parent: GraphGroup,
        passive_skill: int | Any,
        radius: int,
        position: int,
        connections: list[int] | list[Any],
    ) -> None:
        """
        Initialize graph group node.

        Args:
            parent: Parent GraphGroup this node belongs to
            passive_skill: Passive skill node (int or DatRecord)
            radius: Radius from the parent's x,y-position
            position: Position within the group (0-11, clockwise rotation)
            connections: List of connected node IDs or DatRecords
        """
        self.parent = parent
        self.passive_skill = passive_skill
        self.radius = radius
        self.position = position
        self.connections = connections

    def _update_connections(self, dat_reader: Any) -> None:
        """
        Update stored connections using the given dat_reader instance.

        Args:
            dat_reader: DatReader instance to use for updating connections
        """
        self.passive_skill = dat_reader.index[PSG_COL][self.passive_skill]
        for i, connection in enumerate(self.connections):
            self.connections[i] = dat_reader.index[PSG_COL][connection]


class PSGFile(AbstractFileReadOnly):
    """
    Representation of a .psg (Passive Skill Tree Graph) file.

    This class implements the following Protocol interfaces:
    - IReadable: Provides read() method (inherited from AbstractFileReadOnly)
    - IBufferable: Provides get_read_buffer() method (inherited)

    Attributes:
        root_passives: List of root (starting class) passive nodes
        groups: List of GraphGroup instances
        _passive_skills: Reference to DatReader if specified (None otherwise)
    """

    EXTENSION = ".psg"

    def __init__(
        self, passive_skills_dat_file: DatFile | RelationalReader | None = None, *args: Any, **kwargs: Any
    ) -> None:
        """
        Initialize PSG file.

        Args:
            passive_skills_dat_file: DatFile or RelationalReader instance
                (optional, for resolving passive skill references)
            *args: Additional positional arguments for AbstractFileReadOnly
            **kwargs: Additional keyword arguments for AbstractFileReadOnly

        Raises:
            ValueError: If passive_skills_dat_file is not a valid type
        """
        super().__init__(*args, **kwargs)

        self.root_passives = []
        self.groups = []

        if isinstance(passive_skills_dat_file, DatFile):
            # TODO check whether is read and raise exception
            self._passive_skills = passive_skills_dat_file.reader
        elif isinstance(passive_skills_dat_file, RelationalReader):
            self._passive_skills = passive_skills_dat_file.get_file("Data/PassiveSkills.dat").reader
        elif passive_skills_dat_file is None:
            self._passive_skills = passive_skills_dat_file
        else:
            raise ValueError(
                "passive_skills_dat_file must be a DatFile instance, a "
                "RelationalReader instance or None"
            )

        if self._passive_skills:
            self._passive_skills.build_index("PassiveSkillGraphId")

    def _read(self, buffer: Any, *args: Any, **kwargs: Any) -> None:
        """
        Read PSG file from buffer.

        Args:
            buffer: Binary file buffer
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        data = buffer.read()
        offset = 0

        # version?
        struct.unpack_from("<B", data, offset=offset)[0]
        offset += 1

        unknown_length = struct.unpack_from("<B", data, offset=offset)[0]
        offset += 1

        struct.unpack_from("<" + "B" * unknown_length, data, offset=offset)
        offset += 1 * unknown_length

        root_length = struct.unpack_from("<I", data, offset=offset)[0]
        offset += 4

        self.root_passives = list(struct.unpack_from("<" + "I" * root_length, data, offset=offset))
        offset += 4 * root_length

        group_length = struct.unpack_from("<I", data, offset=offset)[0]
        offset += 4

        self.groups = []
        for _i in range(0, group_length):
            x, y, flag, passive_length = struct.unpack_from("<ffbI", data, offset=offset)
            offset += 4 * 2 + 4 + 1

            group = GraphGroup(x=x, y=y, id=len(self.groups), flag=flag)

            for _j in range(0, passive_length):
                rowid, radius, position, connections_length = struct.unpack_from(
                    "<IIII", data, offset=offset
                )
                offset += 4 * 4

                connections = struct.unpack_from(
                    "<" + "I" * connections_length, data, offset=offset
                )
                offset += 4 * connections_length

                group.nodes.append(
                    GraphGroupNode(
                        parent=group,
                        passive_skill=rowid,
                        radius=radius,
                        position=position,
                        connections=list(connections),
                    )
                )

            self.groups.append(group)

        # Done parsing, finalize the connections if the dat file is specified
        if self._passive_skills is not None:
            for i, psg_id in enumerate(self.root_passives):
                self.root_passives[i] = self._passive_skills.index[PSG_COL][psg_id]

            for group in self.groups:
                group._update_connections(self._passive_skills)

    @property
    def is_read(self) -> bool:
        """
        Check if PSG file has been read.

        Returns:
            True if file has been read (groups list is not empty)
        """
        return bool(self.groups)

    @property
    def passive_skills_dat_file(self) -> Any:
        """
        Get passive skills dat file reader.

        Returns:
            DatReader instance or None if not specified
        """
        return self._passive_skills


# =============================================================================
# Functions
# =============================================================================

if __name__ == "__main__":
    psg = PSGFile()
    psg.read("C:/Temp/Metadata/PassiveSkillGraph.psg")
