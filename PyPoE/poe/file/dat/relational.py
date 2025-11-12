"""
RelationalReader for reading DAT files with relations.

This module contains the RelationalReader class which processes relations
between DAT files and caches them.
"""

import warnings
from typing import Any

from PyPoE.poe import constants
from PyPoE.poe.file.dat.file import DatFile
from PyPoE.poe.file.dat.value import DatValue
from PyPoE.poe.file.shared.cache import AbstractFileCache
from PyPoE.poe.file.specification.errors import SpecificationError, SpecificationWarning
from PyPoE.shared.decorators import doc


@doc(
    doc=AbstractFileCache,
    prepend="""
    Read dat files in a relational matter and cache them for further use.

    The relational reader will process **all** relations upon accessing a dat
    file; this means any field marked as relation or enum in the specification
    will be processed and the pointer will be replaced with the actual value.

    For example, if a row "OtherKey" points to another file "OtherDatFil.dat",
    the contents of "OtherKey" will no longer be a reference like 0, but instead
    the actual row from the file "OtherDatFile.dat".

    As a result you have equivalence of:

    * rr["DatFile.dat"]["OtherKey"]["OtherDatFileValue"]
    * rr["OtherDatFile.dat"][0]["OtherDatFileValue"]

    Enums are processed in a similar fashion, except they'll be replaced with
    the according enum instance from :py:mod:`PyPoE.poe.constants` for the
    specific value.
""",
)
class RelationalReader(AbstractFileCache):
    """Relational reader for DAT files with caching."""

    FILE_TYPE = DatFile  # type: ignore[assignment]

    @doc(
        doc=AbstractFileCache.__init__,
        append="""
    Parameters
    ----------
    raise_error_on_missing_relation : bool
        Raises error instead of issuing an warning when a relation is broken
    language : str
        language subdirectory in data directory
    """,
    )
    def __init__(
        self,
        raise_error_on_missing_relation: bool = False,
        language: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize RelationalReader.

        Args:
            raise_error_on_missing_relation: Raise error instead of warning
            language: Language subdirectory in data directory
            *args: Additional positional arguments for AbstractFileCache
            **kwargs: Additional keyword arguments for AbstractFileCache
        """
        self.raise_error_on_missing_relation: bool = raise_error_on_missing_relation
        if language == "English" or language is None:
            self._language: str = ""
        else:
            self._language = language + "/"
        super().__init__(*args, **kwargs)

    def __getitem__(self, item: str) -> Any:
        """
        Shortcut that also appends Data/ if missing.

        The following calls are equivalent:

        * self['DF.dat'] <==> read_file('Data/DF.dat').reader
        * self['Data/DF.dat'] <==> read_file('Data/DF.dat').reader
        """
        if not item.startswith("Data/"):
            item = "Data/" + self._language + item

        return self.get_file(item).reader

    def _set_value(self, obj: Any, other: Any, key: str | None, offset: int) -> Any:
        """
        Set value from relation.

        Args:
            obj: Object value
            other: Other reader or enum
            key: Key name (if using index)
            offset: Offset value

        Returns:
            Resolved value
        """
        if obj is None:
            obj = None
        elif key:
            try:
                obj = other.index[key][obj]
            except KeyError as e:
                msg = f'Did not find proper value for foreign key "{key}" with value "{obj}"'
                if self.raise_error_on_missing_relation:
                    raise SpecificationError(
                        SpecificationError.ERRORS.RUNTIME_MISSING_FOREIGN_KEY, msg
                    ) from e
                else:
                    warnings.warn(msg, SpecificationWarning, stacklevel=2)
                    obj = None
        else:
            # offset is default 0
            try:
                obj = other[obj - offset]
            except IndexError as e:
                msg = f"Did not find proper value at index {obj - offset} in {other.file_name}"
                if self.raise_error_on_missing_relation:
                    raise SpecificationError(
                        SpecificationError.ERRORS.RUNTIME_MISSING_FOREIGN_KEY, msg
                    ) from e
                else:
                    warnings.warn(msg, SpecificationWarning, stacklevel=2)
                    obj = None
        return obj

    def _dv_set_value(self, value: DatValue, other: Any, key: str | None, offset: int) -> DatValue:
        """
        Set value for DatValue instance.

        Args:
            value: DatValue instance
            other: Other reader or enum
            key: Key name
            offset: Offset value

        Returns:
            Updated DatValue
        """
        if value.is_pointer:
            self._dv_set_value(value.child, other, key, offset)  # type: ignore[arg-type]
        elif value.is_list:
            [self._dv_set_value(dv, other, key, offset) for dv in value.children]  # type: ignore[union-attr]
        else:
            value.value = self._set_value(value.value, other, key, offset)

        return value

    def _simple_set_value(self, value: Any, other: Any, key: str | None, offset: int) -> Any:
        """
        Set value for simple (non-DatValue) instance.

        Args:
            value: Value to set
            other: Other reader or enum
            key: Key name
            offset: Offset value

        Returns:
            Updated value
        """
        if isinstance(value, list):
            return [self._set_value(item, other, key, offset) for item in value]
        else:
            return self._set_value(value, other, key, offset)

    def _get_file_instance_args(self, file_name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Get file instance arguments.

        Args:
            file_name: File name
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Dictionary of arguments for file instance
        """
        opts = super()._get_file_instance_args(file_name)
        opts["file_name"] = file_name.replace("Data/" + self._language, "")
        return opts

    def get_file(self, file_name: str) -> DatFile:
        """
        Attempts to return a dat file from the cache and if it isn't available,
        reads it in.

        During the process any relations (i.e. fields that have a "key" to
        other .dat files specified) will be read. This will result in the
        appropriate fields being replaced by the related row.
        Note that a related row may be "None" if no key was specified in the
        read dat file.

        Parameters
        ----------
        file_name : str
            The name of the .dat to read. Extension is required.

        Returns
        -------
        DatFile
            Returns the given DatFile instance
        """
        if file_name in self.files:
            cached_file = self.files[file_name]
            assert isinstance(cached_file, DatFile), f"Expected DatFile, got {type(cached_file)}"
            return cached_file

        df = self._create_instance(file_name)
        assert isinstance(df, DatFile), f"Expected DatFile, got {type(df)}"

        self.files[file_name] = df

        if df.reader is None:
            raise ValueError(f"DatFile.reader is None for {file_name}")

        vf = self._dv_set_value if df.reader.use_dat_value else self._simple_set_value

        for key, spec_row in df.reader.specification.fields.items():  # type: ignore[union-attr]
            if spec_row.enum:
                const_enum = getattr(constants, spec_row.enum)
                index = df.reader.table_columns[key]["index"]
                for i, row in enumerate(df.reader.table_data):
                    df.reader.table_data[i][index] = vf(
                        value=row[index], other=const_enum, key=None, offset=0
                    )
            elif spec_row.key:
                if df.reader.x64:
                    spec_row_key = spec_row.key.replace(".dat", ".dat64")
                else:
                    spec_row_key = spec_row.key

                df_other_reader = self[spec_row_key]

                key_id = spec_row.key_id
                key_offset = spec_row.key_offset
                # Don't need to rebuild the index if it was specified as generic
                # read option already.
                if not self.read_options.get("auto_build_index") and not key_offset and key_id:
                    df_other_reader.build_index(key_id)

                index = df.reader.table_columns[key]["index"]

                for i, row in enumerate(df.reader.table_data):
                    try:
                        df.reader.table_data[i][index] = vf(
                            row[index],
                            df_other_reader,
                            key_id,
                            key_offset,
                        )
                    except SpecificationError as e:
                        raise SpecificationError(
                            e.code,
                            f"{file_name}:{key}->{spec_row.key}:{e.msg}",
                        ) from e

        return df

