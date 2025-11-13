"""
DatValue class for representing values in DAT files.

This module contains the DatValue class which represents individual values
found in DAT files, including support for pointers and lists.
"""

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from PyPoE.poe.file.dat.reader import DatReader
    from PyPoE.poe.file.dat.value import DatValue as DatValueType


class DatValue:
    """
    Representation of a value found in a dat file.

    DatValue instances are created by reading or writing a DatValue and should
    not be directly be created. The purpose of DatValues is to keep information
    regarding the placement of the value in the respective DatFile intact.

    Support for built-ins:

    DatValue do support comparison, however is it performed on the dereferenced
    value it holds, not the equality of the dat value itself.

    This means generally DatValues can be compared to anything, the actual
    comparison is however performed depending on the data type.

    Example 1: dat_value < 0

    * works if the dat_value holds an integer
    * raises TypeError if it holds a list

    Example 2: dat_value1 < dat_value2

    * works if both dat values have the same or comparable types
    * raises TypeError if one holds a list, and the other an integer

    Dev notes:
    Must keep the init
    """

    # Very important to cut down the cost of class creation
    # In some dat files we may be creating millions of instances, simply using
    # slots can make a significant difference (~35% speedup)
    __slots__ = [
        "value",
        "size",
        "offset",
        "parent",
        "specification",
        "children",
        "child",
    ]

    def __init__(
        self,
        value: Any = None,
        offset: int | None = None,
        size: int | None = None,
        parent: Union["DatReader", "DatValueType"] | None = None,
        specification: Any = None,
    ) -> None:
        self.value: Any = value
        self.size: int | None = size
        self.offset: int | None = offset
        self.parent: DatReader | DatValueType | None = parent
        self.specification: Any = specification
        self.children: list[DatValue] | None = None
        self.child: DatValue | None = None

    def __repr__(self):
        # TODO: iterative vs recursive?
        if self.is_pointer:
            return repr(self.child)
        elif self.is_list:
            return repr([repr(dv) for dv in self.children])  # type: ignore[union-attr]
        else:
            return "DatValue(" + repr(self.value) + ")"

    def __lt__(self, other):
        if not isinstance(other, DatValue):
            return self.get_value() < other

        return self.get_value() < other.get_value()

    def __le__(self, other):
        if not isinstance(other, DatValue):
            return self.get_value() <= other

        return self.get_value() <= other.get_value()

    def __eq__(self, other):
        if not isinstance(other, DatValue):
            return self.get_value() == other

        return self.get_value() == other.get_value()

    def __ne__(self, other):
        if not isinstance(other, DatValue):
            return self.get_value() != other

        return self.get_value() != other.get_value()

    def __gt__(self, other):
        if not isinstance(other, DatValue):
            return self.get_value() > other

        return self.get_value() > other.get_value()

    def __ge__(self, other):
        if not isinstance(other, DatValue):
            return self.get_value() >= other

        return self.get_value() >= other.get_value()

    # Properties

    def _get_data_size(self) -> int:
        """
        Retrieve size of the data held by the current instance in the data section.

        Returns:
            Size of data in bytes

        Raises:
            TypeError: If performed on DatValue instances without data
        """
        if self.is_list:
            size = self.children[0].size * self.value[0] if self.children else 0  # type: ignore[union-attr]
        elif self.is_pointer:
            size = self.child.size  # type: ignore[union-attr]
        else:
            raise TypeError("Only supported on DatValue instances with data (lists, pointers)")
        return size

    def _get_data_start_offset(self) -> int:
        """
        Retrieve the start offset of the data held by the current instance in the data section.

        Returns:
            Start offset of data in bytes

        Raises:
            TypeError: If performed on DatValue instances without data
        """
        if self.is_list:
            return self.value[1]
        elif self.is_pointer:
            return self.value
        else:
            raise TypeError("Only supported on DatValue instances with data (lists, pointers)")

    def _get_data_end_offset(self) -> int:
        """
        Retrieve the end offset of the data held by the current instance in the data section.

        Returns:
            End offset of data in bytes

        Raises:
            TypeError: If performed on DatValue instances without data
        """
        return self._get_data_start_offset() + self._get_data_size()

    def _is_data(self) -> bool:
        """
        Check whether this DatValue instance is data or not.

        Returns:
            True if this instance is data, False otherwise
        """
        return self.parent is not None

    def _has_data(self) -> bool:
        """
        Check whether this DatValue instance has data or not.

        This applies to types that hold a pointer.

        Returns:
            True if this instance has data, False otherwise
        """
        return self.is_list or self.is_pointer

    def _is_list(self) -> bool:
        """
        Check whether this DatValue instance is a list.

        Returns:
            True if this instance is a list, False otherwise
        """
        return self.children is not None

    def _is_pointer(self) -> bool:
        """
        Check whether this DatValue instance is a pointer.

        Returns:
            True if this instance is a pointer, False otherwise
        """
        return self.child is not None

    def _is_parsed(self) -> bool:
        """
        Check whether this DatValue instance is parsed (i.e. non bytes).

        Returns:
            True if this instance is parsed, False otherwise
        """
        return not isinstance(self.value, bytes)

    data_size = property(fget=_get_data_size)
    data_start_offset = property(fget=_get_data_start_offset)
    data_end_offset = property(fget=_get_data_end_offset)
    is_data = property(fget=_is_data)
    has_data = property(fget=_has_data)
    is_list = property(fget=_is_list)
    is_pointer = property(fget=_is_pointer)
    is_parsed = property(fget=_is_parsed)

    # Public

    def get_value(self) -> Any:
        """
        Return the value that is held by the DatValue instance.

        This is done recursively, i.e. pointers will be dereferenced accordingly.

        This means if you want the actual value of the DatValue, you should
        probably access the value attribute instead.

        If this DatValue instance is a list, a Python list of items will be returned.
        If this DatValue instance is a pointer, whatever value the child of this
        instance holds will be returned.
        Otherwise the value of the DatValue instance itself will be returned.

        Note:
            Values may be nested, i.e. if a list contains a list, a nested list
            will be returned accordingly.

        Returns:
            The dereferenced value
        """
        if self.is_pointer:
            return self.child.get_value()  # type: ignore[union-attr]
        elif self.is_list:
            return [dv.get_value() for dv in self.children]  # type: ignore[union-attr]
        else:
            return self.value

