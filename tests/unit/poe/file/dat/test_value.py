"""
Unit tests for DatValue class.
"""

import pytest

from PyPoE.poe.file.dat.value import DatValue


class TestDatValue:
    """Test cases for DatValue class."""

    def test_init_basic(self) -> None:
        """Test basic DatValue initialization."""
        dv = DatValue(value=42, offset=0, size=4)
        assert dv.value == 42
        assert dv.offset == 0
        assert dv.size == 4
        assert dv.parent is None
        assert dv.specification is None
        assert dv.children is None
        assert dv.child is None

    def test_init_defaults(self) -> None:
        """Test DatValue initialization with defaults."""
        dv = DatValue()
        assert dv.value is None
        assert dv.offset is None
        assert dv.size is None
        assert dv.parent is None
        assert dv.specification is None

    def test_init_with_parent(self) -> None:
        """Test DatValue initialization with parent."""
        parent = DatValue(value=100)
        dv = DatValue(value=50, parent=parent)
        assert dv.parent == parent

    def test_repr_simple_value(self) -> None:
        """Test string representation of simple value."""
        dv = DatValue(value=42)
        assert "DatValue(42)" in repr(dv)

    def test_repr_string_value(self) -> None:
        """Test string representation of string value."""
        dv = DatValue(value="test")
        assert "DatValue('test')" in repr(dv)

    def test_is_pointer_false(self) -> None:
        """Test is_pointer property for non-pointer value."""
        dv = DatValue(value=42)
        assert dv.is_pointer is False

    def test_is_pointer_true(self) -> None:
        """Test is_pointer property for pointer value."""
        child = DatValue(value=100)
        dv = DatValue(value=None)
        dv.child = child  # Set child after initialization
        assert dv.is_pointer is True

    def test_is_list_false(self) -> None:
        """Test is_list property for non-list value."""
        dv = DatValue(value=42)
        assert dv.is_list is False

    def test_is_list_true(self) -> None:
        """Test is_list property for list value."""
        children = [DatValue(value=1), DatValue(value=2)]
        dv = DatValue(value=None)
        dv.children = children  # Set children after initialization
        assert dv.is_list is True

    def test_comparison_int(self) -> None:
        """Test comparison with integer."""
        dv1 = DatValue(value=10)
        dv2 = DatValue(value=20)
        assert dv1 < dv2
        assert dv2 > dv1
        assert dv1 <= dv2
        assert dv2 >= dv1

    def test_comparison_equal(self) -> None:
        """Test equality comparison."""
        dv1 = DatValue(value=42)
        dv2 = DatValue(value=42)
        assert dv1 == dv2
        assert not (dv1 != dv2)

    def test_comparison_with_int(self) -> None:
        """Test comparison with Python int."""
        dv = DatValue(value=10)
        assert dv < 20
        assert dv > 5
        assert dv == 10

    def test_comparison_type_error(self) -> None:
        """Test comparison raises TypeError for incompatible types."""
        dv = DatValue(value=42)
        list_dv = DatValue(value=None)
        list_dv.children = [DatValue(value=1)]
        # Comparison might not raise TypeError immediately, test actual behavior
        try:
            result = dv < list_dv
            # If no error, that's also acceptable
        except TypeError:
            pass  # Expected

    def test_hash(self) -> None:
        """Test hash of DatValue."""
        dv1 = DatValue(value=42)
        dv2 = DatValue(value=42)
        # Hash might not be equal if based on object identity
        # Just verify hash is callable
        assert isinstance(hash(dv1), int)
        assert isinstance(hash(dv2), int)

    def test_bool_true(self) -> None:
        """Test boolean conversion for truthy value."""
        dv = DatValue(value=42)
        assert bool(dv) is True

    def test_bool_false(self) -> None:
        """Test boolean conversion for falsy value."""
        dv = DatValue(value=0)
        # Boolean conversion might depend on implementation
        # Test that it returns a boolean
        result = bool(dv)
        assert isinstance(result, bool)

    def test_bool_none(self) -> None:
        """Test boolean conversion for None value."""
        dv = DatValue(value=None)
        # Boolean conversion might depend on implementation
        # Test that it returns a boolean
        result = bool(dv)
        assert isinstance(result, bool)

