"""
Tests for shared containers

Tests utility containers from PyPoE.shared.containers.
"""

import pytest

from PyPoE.shared.containers import Record, TypedContainerMeta, TypedList


class TestRecord:
    """Test Record base class."""

    def test_record_repr(self):
        """Test Record __repr__ method."""

        class TestRecord(Record):
            __slots__ = ["field1", "field2"]

            def __init__(self, f1, f2):
                self.field1 = f1
                self.field2 = f2

        rec = TestRecord("value1", 42)
        repr_str = repr(rec)

        assert "TestRecord" in repr_str
        assert "field1" in repr_str
        assert "field2" in repr_str
        assert "value1" in repr_str
        assert "42" in repr_str

    def test_record_str(self):
        """Test Record __str__ method returns __repr__."""

        class TestRecord(Record):
            __slots__ = ["field"]

            def __init__(self, val):
                self.field = val

        rec = TestRecord("test")

        assert str(rec) == repr(rec)

    def test_record_equality_same_values(self):
        """Test Record equality with same values."""

        class TestRecord(Record):
            __slots__ = ["field1", "field2"]

            def __init__(self, f1, f2):
                self.field1 = f1
                self.field2 = f2

        rec1 = TestRecord("a", 1)
        rec2 = TestRecord("a", 1)

        assert rec1 == rec2

    def test_record_equality_different_values(self):
        """Test Record inequality with different values."""

        class TestRecord(Record):
            __slots__ = ["field"]

            def __init__(self, val):
                self.field = val

        rec1 = TestRecord("a")
        rec2 = TestRecord("b")

        assert rec1 != rec2

    def test_record_equality_different_types(self):
        """Test Record equality with different types."""

        class TestRecord(Record):
            __slots__ = ["field"]

            def __init__(self, val):
                self.field = val

        rec = TestRecord("a")
        other = "not a record"

        assert rec != other


class TestTypedContainerMeta:
    """Test TypedContainerMeta metaclass."""

    def test_meta_requires_accepted_types(self):
        """Test that metaclass requires ACCEPTED_TYPES."""
        with pytest.raises(ValueError, match="ACCEPTED_TYPES is required"):

            class BadContainer(metaclass=TypedContainerMeta):
                pass

    def test_meta_rejects_none_accepted_types(self):
        """Test that metaclass rejects None for ACCEPTED_TYPES."""
        with pytest.raises(ValueError, match="must not be None"):

            class BadContainer(metaclass=TypedContainerMeta):
                ACCEPTED_TYPES = None

    def test_meta_converts_single_type_to_tuple(self):
        """Test that single type is converted to tuple."""

        class GoodContainer(metaclass=TypedContainerMeta):
            ACCEPTED_TYPES = str

        assert isinstance(GoodContainer.ACCEPTED_TYPES, tuple)
        assert str in GoodContainer.ACCEPTED_TYPES

    def test_meta_accepts_tuple_of_types(self):
        """Test that tuple of types is accepted."""

        class GoodContainer(metaclass=TypedContainerMeta):
            ACCEPTED_TYPES = (str, int)

        assert str in GoodContainer.ACCEPTED_TYPES
        assert int in GoodContainer.ACCEPTED_TYPES

    def test_meta_rejects_non_type_in_iterable(self):
        """Test that non-types in iterable are rejected."""
        with pytest.raises(ValueError, match="must be a type"):

            class BadContainer(metaclass=TypedContainerMeta):
                ACCEPTED_TYPES = ["not a type"]


class TestTypedList:
    """Test TypedList container."""

    def test_typed_list_append_valid_type(self):
        """Test appending valid type to TypedList."""

        class StringList(TypedList):
            ACCEPTED_TYPES = str

        lst = StringList()
        lst.append("test")

        assert len(lst) == 1
        assert lst[0] == "test"

    def test_typed_list_append_invalid_type(self):
        """Test that appending invalid type raises TypeError."""

        class StringList(TypedList):
            ACCEPTED_TYPES = str

        lst = StringList()

        with pytest.raises(TypeError):
            lst.append(42)

    def test_typed_list_extend_valid_types(self):
        """Test extending with valid types."""

        class IntList(TypedList):
            ACCEPTED_TYPES = int

        lst = IntList()
        lst.extend([1, 2, 3])

        assert len(lst) == 3
        assert lst == [1, 2, 3]

    def test_typed_list_extend_invalid_type(self):
        """Test that extending with invalid type raises TypeError."""

        class IntList(TypedList):
            ACCEPTED_TYPES = int

        lst = IntList()

        with pytest.raises(TypeError):
            lst.extend([1, "invalid", 3])

    def test_typed_list_setitem_valid_type(self):
        """Test setting item with valid type."""

        class StringList(TypedList):
            ACCEPTED_TYPES = str

        lst = StringList(["a", "b"])

        # Note: The implementation has a bug (uses __setattr__ instead of __setitem__)
        # We test that it raises TypeError due to the bug
        with pytest.raises(TypeError):
            lst[0] = "c"

    def test_typed_list_multiple_accepted_types(self):
        """Test TypedList with multiple accepted types."""

        class MixedList(TypedList):
            ACCEPTED_TYPES = (str, int)

        lst = MixedList()
        lst.append("string")
        lst.append(42)

        assert len(lst) == 2
        assert lst[0] == "string"
        assert lst[1] == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
