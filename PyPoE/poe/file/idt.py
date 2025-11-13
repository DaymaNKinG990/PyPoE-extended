"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/idt.py                                            |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

File Format handler for Grinding Gear Games' .idt format.

.idt files are generally used to link the inventory texture to an object.

Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

Public API
-------------------------------------------------------------------------------

.. autoclass:: IDTFile

.. autoclass:: TextureRecord

.. autoclass:: CoordinateRecord


Internal API
-------------------------------------------------------------------------------

.. autoclass:: TextureList

.. autoclass:: CoordinateList
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import codecs
import re
from typing import Any

from PyPoE.poe.file.shared import AbstractFile, ParserError

# self
from PyPoE.shared.containers import Record, TypedContainerMeta, TypedList

# =============================================================================
# Globals
# =============================================================================

__all__ = ["IDTFile", "TextureRecord", "CoordinateRecord"]

# =============================================================================
# Classes
# =============================================================================


class CoordinateRecord(Record):
    """
    Object that represents a single coordinate with the relevant attributes.

    Attributes:
        x: X-coordinate
        y: Y-coordinate
    """

    __slots__ = ["x", "y"]

    def __init__(self, x: int, y: int) -> None:
        """
        Initialize coordinate record.

        Args:
            x: X-coordinate
            y: Y-coordinate
        """
        self.x = int(x)
        self.y = int(y)


class CoordinateList(TypedList, metaclass=TypedContainerMeta):
    """
    A list that only accepts CoordinateRecord instances.
    """

    ACCEPTED_TYPES = CoordinateRecord  # type: ignore[assignment]


class TextureRecord(Record):
    """
    Object that represents a single texture with the relevant attributes.

    Attributes:
        name: Name (internal path) of the texture
        records: CoordinateList of CoordinateRecord instances for this texture
    """

    __slots__ = ["name", "records"]

    def __init__(self, name: str, records: CoordinateList | list | None = None) -> None:
        """
        Initialize texture record.

        Args:
            name: Name (internal path) of the texture
            records: CoordinateList of CoordinateRecord instances for this texture.
                If None, an empty CoordinateList will be created.

        Raises:
            TypeError: If records is of invalid type or contains invalid types
        """
        self.name = name
        if records is None:
            self.records = CoordinateList()
        elif isinstance(records, CoordinateList):
            self.records = records
        elif isinstance(records, list):
            self.records = CoordinateList(records)
        else:
            raise TypeError("records must a valid CoordinateList.")


class TextureList(TypedList, metaclass=TypedContainerMeta):
    """
    A list that only accepts TextureRecord instances.
    """

    ACCEPTED_TYPES = TextureRecord  # type: ignore[assignment]


class IDTFile(AbstractFile):
    """
    Encapsulated in-memory representation of .idt files.

    .idt files are generally used to link the inventory texture to an object.

    Attributes:
        version: File version number
        image: Image file path
        records: TextureList of TextureRecord instances
    """

    # complete match
    _regex_parse = re.compile(
        r"^"
        r"version (?P<version>[0-9]+)[\r\n]*"
        r'image "(?P<image>[\w\./\\_\'\-]+)"[\r\n]*'
        r"(?P<texture_count>[0-9]+)[\r\n]*"
        r"(?P<textures>.*)"  # Match the rest
        r"$",
        re.UNICODE | re.MULTILINE | re.DOTALL,
    )

    # for findall
    _regex_texture = re.compile(
        r"^"
        r"(?P<name>[a-zA-Z]+)[ ]+"
        r"(?P<count>[0-9]+)[ ]+"
        r"(?P<coordinates>(?:[0-9]+[ ]*)*)"
        r"[\r\n]*$",
        re.UNICODE | re.MULTILINE | re.DOTALL,
    )

    # for findall
    _regex_coordinates = re.compile(
        r"(?P<x>[0-9]+)[ ]+"
        r"(?P<y>[0-9]+)[ ]*"
        r"",
        re.UNICODE | re.MULTILINE | re.DOTALL,
    )

    EXTENSION = ".idt"

    def __init__(self, data: dict | None = None) -> None:
        """
        Create a new IDTFile instance.

        Optionally data can be specified to initialize the object in memory
        with the given data. The same can be achieved by simply setting the
        relevant attributes. Note that read() will override any initial data.

        Args:
            data: Dictionary containing the data to create this object with.
                The dict should match the structure of the class attributes
                and the respective sub attributes.

        Raises:
            TypeError: If dict contains data of invalid types
        """
        if data is None:
            self.version = 0
            self._image = None
            self._records = TextureList()
        else:
            tex = TextureList()
            for tex_record in data["records"]:
                x = CoordinateList()
                for coord_record in tex_record["records"]:
                    x.append(CoordinateRecord(**coord_record))

                kwargs = tex_record.copy()
                del kwargs["records"]

                tex.append(TextureRecord(records=x, **kwargs))

            self.version = data["version"]
            self.image = data["image"]
            self._records = tex

    # Properties

    def _get_records(self):
        """
        Get records

        Returns
        -------
        TextureList[TextureRecord]
            List of stored :class:`TextureRecord` instances
        """
        return self._records

    def _set_records(self, value):
        """
        Set records

        Parameters
        ----------
        value : TextureList[TextureRecord]
            value to set the records to

        Raises
        ------
        TypeError
            if the record is an invalid texture list

        """
        if isinstance(value, TextureList):
            self._records = value
        elif isinstance(value, list):
            self._records = TextureList(value)
        else:
            raise TypeError("records must be a valid TextureList.")

    records = property(fget=_get_records, fset=_set_records)

    def _get_image(self) -> str | None:
        """
        Get image path.

        Returns:
            Image path relative to content.ggpk root
        """
        return self._image

    def _set_image(self, value: str) -> None:
        """
        Set image path.

        Args:
            value: Image path relative to content.ggpk root
        """
        self._image = value.replace("\\", "/")

    image = property(fget=_get_image, fset=_set_image)

    # Private

    def _write(self, buffer: Any) -> None:
        """
        Write IDT file to buffer.

        Args:
            buffer: Binary file buffer to write to
        """
        out = []

        out.append(f"version {self.version}\n")
        out.append(f'image "{self._image}"\n')
        out.append(f"{len(self._records)}\n")
        for tex_record in self._records:
            out.append(f"{tex_record.name} {len(tex_record.records)}")
            for coord_record in tex_record.records:
                out.append(f" {coord_record.x} {coord_record.y}")
            out.append("\n")

        "".join(out).encode("utf-16_le")

        buffer.write(codecs.BOM_UTF16_LE + "".join(out).encode("utf-16_le"))

    def _read(self, buffer: Any, *args: Any, **kwargs: Any) -> None:
        """
        Read IDT file from buffer.

        Args:
            buffer: Binary file buffer to read from
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Raises:
            ParserError: If file format is invalid or malformed
        """
        # Should detect little endian byte order accordingly and remove the BOM
        data = buffer.read().decode("utf-16")
        match = self._regex_parse.match(data)

        if not match:
            raise ParserError(
                "Failed to find the base information. File may not be a .idt file or malformed."
            )

        textures = TextureList()
        for tex_match in self._regex_texture.finditer(match.group("textures")):
            coordinates = CoordinateList()
            for coord_match in self._regex_coordinates.finditer(tex_match.group("coordinates")):
                coordinates.append(CoordinateRecord(**coord_match.groupdict()))

            if len(coordinates) != int(tex_match.group("count")):
                raise ParserError(
                    "Amount of found coordinates ({}) does not match the amount of specified coordinates ({})".format(
                        len(coordinates), tex_match.group("count")
                    )
                )

            textures.append(TextureRecord(tex_match.group("name"), coordinates))

        if len(textures) != int(match.group("texture_count")):
            raise ParserError(
                "Amount of found textures ({}) does not match the amount of specified textures ({})".format(
                    len(textures), match.group("texture_count")
                )
            )

        self._records = textures
        self.version = int(match.group("version"))
        self.image = match.group("image")
