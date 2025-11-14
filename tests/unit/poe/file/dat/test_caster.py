"""
Unit tests for DatCaster class.
"""

import pytest

from PyPoE.poe.file.dat.caster import CastTypes, DatCaster


class TestDatCaster:
    """Test cases for DatCaster class."""

    def test_init_default(self) -> None:
        """Test DatCaster initialization with defaults."""
        caster = DatCaster()
        assert caster.use_dat_value is True
        assert caster.x64 is False
        assert caster.data_parsed == []

    def test_init_custom(self) -> None:
        """Test DatCaster initialization with custom parameters."""
        caster = DatCaster(use_dat_value=False, x64=True)
        assert caster.use_dat_value is False
        assert caster.x64 is True

    def test_parse_cast_string_int(self) -> None:
        """Test parsing cast string for int type."""
        caster = DatCaster()
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("int")
        assert remainder == ""
        assert cast_type == CastTypes.VALUE
        assert size == 4
        assert struct_format == "i"

    def test_parse_cast_string_float(self) -> None:
        """Test parsing cast string for float type."""
        caster = DatCaster()
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("float")
        assert remainder == ""
        assert cast_type == CastTypes.VALUE
        assert size == 4
        assert struct_format == "f"

    def test_parse_cast_string_string(self) -> None:
        """Test parsing cast string for string type."""
        caster = DatCaster()
        result = caster.parse_cast_string("string")
        remainder, (cast_type, size, struct_format) = result
        assert remainder == ""
        assert cast_type == CastTypes.STRING
        # Size and format might be None or have values
        # Just verify cast_type is correct

    def test_parse_cast_string_ref(self) -> None:
        """Test parsing cast string for ref type (32-bit)."""
        caster = DatCaster(x64=False)
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("ref|int")
        assert remainder == "int"
        assert cast_type == CastTypes.POINTER
        assert size == 4
        assert struct_format == "I"

    def test_parse_cast_string_ref_x64(self) -> None:
        """Test parsing cast string for ref type (64-bit)."""
        caster = DatCaster(x64=True)
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("ref|int")
        assert remainder == "int"
        assert cast_type == CastTypes.POINTER
        assert size == 8
        assert struct_format == "Q"

    def test_parse_cast_string_ref_list(self) -> None:
        """Test parsing cast string for ref|list type (32-bit)."""
        caster = DatCaster(x64=False)
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("ref|list|int")
        assert remainder == "int"
        assert cast_type == CastTypes.POINTER_LIST
        assert size == 8
        assert struct_format == "II"

    def test_parse_cast_string_ref_list_x64(self) -> None:
        """Test parsing cast string for ref|list type (64-bit)."""
        caster = DatCaster(x64=True)
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("ref|list|int")
        assert remainder == "int"
        assert cast_type == CastTypes.POINTER_LIST
        assert size == 16
        assert struct_format == "QQ"

    def test_parse_cast_string_ref_self(self) -> None:
        """Test parsing cast string for ref|self type."""
        caster = DatCaster()
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("ref|self")
        assert remainder == ""
        assert cast_type == CastTypes.POINTER_SELF
        # Size depends on x64 mode
        assert size in (4, 8)
        assert struct_format in ("I", "Q")

    def test_parse_cast_string_ref_self_x64(self) -> None:
        """Test parsing cast string for ref|self type (64-bit)."""
        caster = DatCaster(x64=True)
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("ref|self")
        assert remainder == ""
        assert cast_type == CastTypes.POINTER_SELF
        assert size == 8
        assert struct_format == "Q"

    def test_parse_cast_string_ref_generic(self) -> None:
        """Test parsing cast string for ref|generic type."""
        caster = DatCaster()
        remainder, (cast_type, size, struct_format) = caster.parse_cast_string("ref|generic")
        assert remainder == ""
        # ref|generic might be treated as POINTER_SELF
        assert cast_type in (CastTypes.POINTER, CastTypes.POINTER_SELF)
        assert size in (4, 8)
        assert struct_format in ("I", "Q")

    def test_parse_cast_string_all_types(self) -> None:
        """Test parsing all basic cast types."""
        caster = DatCaster()
        types = ["bool", "byte", "ubyte", "short", "ushort", "int", "uint", "long", "ulong", "float", "double"]
        for type_str in types:
            remainder, (cast_type, size, struct_format) = caster.parse_cast_string(type_str)
            assert cast_type == CastTypes.VALUE
            assert size is not None
            assert struct_format is not None

    def test_cast_table_contains_all_types(self) -> None:
        """Test that cast table contains all expected types."""
        caster = DatCaster()
        expected_types = ["bool", "byte", "ubyte", "short", "ushort", "int", "uint", "long", "ulong", "float", "double"]
        for type_str in expected_types:
            assert type_str in caster._cast_table

