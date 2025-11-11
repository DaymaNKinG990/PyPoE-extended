"""
Translation file cache.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/cache.py                            |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Translation file cache implementation for efficient file management.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================


from PyPoE.poe.constants import MOD_GENERATION_TYPE
from PyPoE.poe.file.shared.cache import AbstractFileCache
from PyPoE.poe.file.translations.constants import (  # type: ignore[attr-defined]
    CUSTOM_TRANSLATION_FILE,
    _custom_translation_file,
)
from PyPoE.poe.file.translations.file import TranslationFile
from PyPoE.poe.file.translations.models import (
    TQReminderString,
    TranslationQuantifier,
    TranslationQuantifierHandler,
)
from PyPoE.shared.decorators import doc

# =============================================================================
# Globals
# =============================================================================

__all__ = ["TranslationFileCache"]

# =============================================================================
# Classes
# =============================================================================


class TranslationFileCache(AbstractFileCache):
    """
    Creates a memory cache of :class:`TranslationFile` objects.

    It will store any loaded file in the cache and return it as needed.
    The advantage is that there is only one object that will handle all
    translation files and only load them if they're not in the cache already.

    In particular this is useful as many translation files include other
    files which will only be read once and then passed to the other file
    accordingly - separately loading those files would read any included
    file multiple times, as such there is a fairly significant performance
    improvement over using single files.
    """

    FILE_TYPE = TranslationFile  # type: ignore[assignment]

    @doc(prepend=AbstractFileCache.__init__)
    def __init__(
        self, *args, merge_with_custom_file: None | bool | TranslationFile = None, **kwargs
    ):
        """
        Parameters
        ----------
        merge_with_custom_file : None, bool or TranslationFile
            If this option is specified, each file will be merged with a custom
            translation file. If set to True, it will load the default
            translation file located in PyPoE's data directory. Alternatively a
            TranslationFile instance can be passed which then will be used.
        """
        if merge_with_custom_file is None or merge_with_custom_file is False:
            self._custom_file = None
        elif merge_with_custom_file is True:
            self._custom_file = get_custom_translation_file()
        elif isinstance(merge_with_custom_file, TranslationFile):
            self._custom_file = merge_with_custom_file
        else:
            raise TypeError(
                "Argument merge_with_custom_file is of wrong type. %(type)s"
                % {"type": type(merge_with_custom_file)}
            )

        # Call order matters here
        super().__init__(*args, **kwargs)

    def __getitem__(self, item: str) -> TranslationFile:
        """
        Shortcut for :meth:`TranslationFileCache.get_file` that will also
        added Metadata automatically.

        That means the following is equivalent:
        obj['stat_descriptions.txt']
        obj.get_file('Metadata/StatDescriptions/stat_descriptions.txt')

        Parameters
        ----------
        item :  str
            file name/path relative to the Metadata/StatDescriptions/ directory


        Returns
        -------
        TranslationFile
            the specified TranslationFile
        """
        if not item.startswith("Metadata/StatDescriptions/"):
            item = "Metadata/StatDescriptions/" + item
        return self.get_file(item)

    @doc(doc=AbstractFileCache._get_file_instance_args)
    def _get_file_instance_args(self, file_name, *args, **kwargs):
        return {
            "parent": self,
        }

    def get_file(self, file_name: str) -> TranslationFile:
        """
        Returns the specified file from the cache (and loads it if not in the
        cache already).

        Note that the file name must be relative to the root path of exile
        folder (or a virtual) folder or it won't work properly.
        That means 'Metadata/stat_descriptions.txt' needs to be referenced
        as such.
        For a shortcut consider using obj[name] instead.


        Parameters
        ----------
        file_name :  str
            file name/path relative to the root path of exile directory


        Returns
        -------
        TranslationFile
            the specified TranslationFile
        """
        if file_name not in self.files:
            tf = self._create_instance(file_name=file_name)

            if self._custom_file:
                tf.merge(self._custom_file)

            self.files[file_name] = tf

            return tf  # type: ignore[no-any-return]

        return self.files[file_name]  # type: ignore[return-value, no-any-return]


# =============================================================================
# Functions
# =============================================================================


def _diff_list(self, other, diff=True):
    len_self = len(self)
    len_other = len(other)
    if len_self != len_other:
        print("Different length, %s vs %s" % (len_self, len_other))

        set_self = set(self)
        set_other = set(other)
        print("Extra items in self: %s" % set_self.difference(set_other))
        print("Extra item in other: %s" % set_other.difference(set_self))
        return

    if diff:
        for i in range(0, len_self):
            self[i].diff(other[i])


def _diff_dict(self, other):
    key_self = set(tuple(self.keys()))
    key_other = set(tuple(other.keys()))

    kdiff_self = key_self.difference(key_other)
    kdiff_other = key_other.difference(key_self)

    if kdiff_self:
        print("Extra keys in self:")
        for key in kdiff_self:
            print('Key "%s": Value "%s"' % (key, self[key]))

    if kdiff_other:
        print("Extra keys in other:")
        for key in kdiff_other:
            print('Key "%s": Value "%s"' % (key, other[key]))


def get_custom_translation_file() -> TranslationFile:
    """
    Returns the currently loaded custom translation file.

    Loads the default file if none is loaded.

    Returns
    -------
    TranslationFile
        the currently loaded custom translation file
    """
    global _custom_translation_file
    if _custom_translation_file is None:
        set_custom_translation_file()
    return _custom_translation_file  # type: ignore[no-any-return]


def set_custom_translation_file(file: str | None = None):
    """
    Sets the custom translation file.

    Parameters
    ----------
    file : str
        Path where the custom translation file is located. If None,
        the default file will be loaded
    """
    global _custom_translation_file
    _custom_translation_file = TranslationFile(file_path=file or CUSTOM_TRANSLATION_FILE)


custom_translation_file = property(  # type: ignore[arg-type]
    fget=get_custom_translation_file,  # type: ignore[arg-type]
    fset=set_custom_translation_file,  # type: ignore[arg-type]
)


def install_data_dependant_quantifiers(relational_reader):
    """
    Install data dependant quantifiers into this class.

    Parameters
    ----------
    relational_reader : RelationalReader
        :class:`RelationalReader` instance to read the required game data
        files from.
    """

    def _get_reverse_lookup_from_reader(relational_reader, key):
        def _get_from_value(value):
            for row in relational_reader:
                if row[key] == value:
                    return row.rowid

        return _get_from_value

    TranslationQuantifier(
        id="mod_value_to_item_class",
        handler=lambda v: relational_reader["ItemClasses.dat"][v]["Name"],
        reverse_handler=_get_reverse_lookup_from_reader(
            relational_reader["ItemClasses.dat"], "Name"
        ),
    )

    def _tempest_mod_text_reverse(value):
        results = []
        for row in relational_reader["Mods.dat"]:
            if row["GenerationType"] != MOD_GENERATION_TYPE.TEMPEST:
                continue
            if row["Name"] == value:
                results.append(row.rowid)

        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            return None
        else:
            return results

    TranslationQuantifier(
        id="tempest_mod_text",
        handler=lambda v: relational_reader["Mods.dat"][v]["Name"],
        reverse_handler=_tempest_mod_text_reverse,
    )

    def _get_reverse_lookup_from_reader(relational_reader, key):  # type: ignore[no-redef]
        def _get_from_value(value):
            for row in relational_reader:
                if row[key] == value:
                    return row.rowid

        return _get_from_value

    TranslationQuantifier(
        id="display_indexable_support",
        handler=lambda v: relational_reader["IndexableSupportGems.dat"][v]["Name"],
        reverse_handler=_get_reverse_lookup_from_reader(
            relational_reader["IndexableSupportGems.dat"], "Name"
        ),
    )

    TranslationQuantifier(
        id="tree_expansion_jewel_passive",
        handler=lambda v: relational_reader["Data/PassiveTreeExpansionJewelSizes.dat"][v]["Name"],
        reverse_handler=_get_reverse_lookup_from_reader(
            relational_reader["Data/PassiveTreeExpansionJewelSizes.dat"], "Name"
        ),
    )

    TranslationQuantifier(
        id="affliction_reward_type",
        handler=lambda v: relational_reader["Data/AfflictionRewardTypeVisuals.dat"][v]["Name"],
        reverse_handler=_get_reverse_lookup_from_reader(
            relational_reader["Data/AfflictionRewardTypeVisuals.dat"], "Name"
        ),
    )

    # I believe this is currently not right, as the handler actually uses a value located in additionalProperties of the item, and
    # not in the mod itself. THe mod itself has min = max = 0.
    TranslationQuantifier(
        id="passive_hash",
        handler=lambda v: relational_reader["Data/PassiveSkills.dat"][v]["PassiveSkillGraphId"],
        reverse_handler=_get_reverse_lookup_from_reader(
            relational_reader["Data/PassiveSkills.dat"], "PassiveSkillGraphId"
        ),
    )

    TQReminderString(relational_reader=relational_reader)

    TranslationQuantifierHandler.init()


# =============================================================================
# Init
# =============================================================================

#
# Translation Quantifiers
#

# Notes:
# * It's hardly possible to reverse rounding accurately

"""
TranslationQuantifier(
    id='',
    handler=lambda v: ,
    reverse_handler=lambda v: ,
)
"""

TranslationQuantifier(
    id="30%_of_value",
    handler=lambda v: v * 0.3,
    reverse_handler=lambda v: v / 0.3,
)

TranslationQuantifier(
    id="60%_of_value",
    handler=lambda v: v * 0.6,
    reverse_handler=lambda v: v / 0.6,
)

TranslationQuantifier(
    id="deciseconds_to_seconds",
    handler=lambda v: v / 10,
    reverse_handler=lambda v: float(v) * 10,
)

TranslationQuantifier(
    id="divide_by_three",
    handler=lambda v: v / 3,
    reverse_handler=lambda v: float(v) * 3,
)

TranslationQuantifier(
    id="divide_by_five",
    handler=lambda v: v / 5,
    reverse_handler=lambda v: float(v) * 5,
)

TranslationQuantifier(
    id="divide_by_one_hundred",
    handler=lambda v: v / 100,
    reverse_handler=lambda v: float(v) * 100,
)

TranslationQuantifier(
    id="divide_by_one_hundred_and_negate",
    handler=lambda v: -v / 100,
    reverse_handler=lambda v: -float(v) * 100,
)

TranslationQuantifier(
    id="divide_by_one_hundred_0dp",
    handler=lambda v: round(v / 100, 0),
    reverse_handler=lambda v: float(v) * 100,
)

TranslationQuantifier(
    id="divide_by_one_hundred_1dp",
    handler=lambda v: round(v / 100, 1),
    reverse_handler=lambda v: float(v) * 100,
)
TranslationQuantifier(
    id="divide_by_one_hundred_2dp",
    handler=lambda v: round(v / 100, 2),
    reverse_handler=lambda v: float(v) * 100,
)

TranslationQuantifier(
    id="divide_by_one_hundred_2dp_if_required",
    handler=lambda v: round(v / 100, 2),
    reverse_handler=lambda v: float(v) * 100,
)


TranslationQuantifier(
    id="divide_by_two_0dp",
    handler=lambda v: v // 2,
    reverse_handler=lambda v: int(v) * 2,
)

TranslationQuantifier(
    id="divide_by_six",
    handler=lambda v: v / 6,
    reverse_handler=lambda v: int(v) * 6,
)

TranslationQuantifier(
    id="divide_by_ten_0dp",
    handler=lambda v: v // 10,
    reverse_handler=lambda v: int(v) * 10,
)

TranslationQuantifier(
    id="divide_by_ten_1dp",
    handler=lambda v: round(v / 10, 1),
    reverse_handler=lambda v: int(v) * 10,
)

TranslationQuantifier(
    id="divide_by_ten_1dp_if_required",
    handler=lambda v: round(v / 10, 1),
    reverse_handler=lambda v: int(v) * 10,
)

TranslationQuantifier(
    id="divide_by_twelve",
    handler=lambda v: v / 12,
    reverse_handler=lambda v: int(v) * 12,
)

TranslationQuantifier(
    id="divide_by_fifteen_0dp",
    handler=lambda v: v // 15,
    reverse_handler=lambda v: int(v) * 15,
)

TranslationQuantifier(
    id="divide_by_fifty",
    handler=lambda v: v / 50,
    reverse_handler=lambda v: int(v) * 50,
)

TranslationQuantifier(
    id="divide_by_twenty_then_double_0dp",
    handler=lambda v: v // 20 * 2,
    reverse_handler=lambda v: int(v) * 20 // 2,
)

TranslationQuantifier(
    id="divide_by_one_thousand",
    handler=lambda v: v / 1000,
    reverse_handler=lambda v: int(v) * 1000,
)

TranslationQuantifier(
    id="milliseconds_to_seconds",
    handler=lambda v: v / 1000,
    reverse_handler=lambda v: float(v) * 1000,
)

TranslationQuantifier(
    id="milliseconds_to_seconds_halved",
    handler=lambda v: v / 500,
    reverse_handler=lambda v: float(v) * 500,
)

TranslationQuantifier(
    id="milliseconds_to_seconds_0dp",
    handler=lambda v: int(round(v / 1000, 0)),
    reverse_handler=lambda v: float(v) * 1000,
)
TranslationQuantifier(
    id="milliseconds_to_seconds_1dp",
    handler=lambda v: round(v / 1000, 1),
    reverse_handler=lambda v: float(v) * 1000,
)

TranslationQuantifier(
    id="milliseconds_to_seconds_2dp",
    handler=lambda v: round(v / 1000, 2),
    reverse_handler=lambda v: float(v) * 1000,
)

# TODO: Not exactly sure yet how this one works
TranslationQuantifier(
    id="milliseconds_to_seconds_2dp_if_required",
    handler=lambda v: round(v / 1000, 2),
    reverse_handler=lambda v: float(v) * 1000,
)

TranslationQuantifier(
    id="multiplicative_damage_modifier",
    handler=lambda v: v + 100,
    reverse_handler=lambda v: float(v) - 100,
)

TranslationQuantifier(
    id="multiplicative_permyriad_damage_modifier",
    handler=lambda v: v / 100 + 100,
    reverse_handler=lambda v: (float(v) - 100) * 100,
)

TranslationQuantifier(
    id="multiply_by_four",
    handler=lambda v: v * 4,
    reverse_handler=lambda v: int(v) // 4,
)

TranslationQuantifier(
    id="multiply_by_four_and_",
    handler=lambda v: v * 4,
    reverse_handler=lambda v: int(v) // 4,
)

TranslationQuantifier(
    id="multiply_by_ten",
    handler=lambda v: v * 10,
    reverse_handler=lambda v: int(v) // 10,
)

TranslationQuantifier(
    id="negate",
    handler=lambda v: -v,
    reverse_handler=lambda v: -float(v),
)

TranslationQuantifier(
    id="old_leech_percent",
    handler=lambda v: v / 5,
    reverse_handler=lambda v: float(v) * 5,
)

TranslationQuantifier(
    id="old_leech_permyriad",
    handler=lambda v: v / 500,
    reverse_handler=lambda v: float(v) * 500,
)

TranslationQuantifier(
    id="per_minute_to_per_second",
    handler=lambda v: round(v / 60, 1),
    reverse_handler=lambda v: float(v) * 60,
)

TranslationQuantifier(
    id="per_minute_to_per_second_0dp",
    handler=lambda v: int(round(v / 60, 0)),
    reverse_handler=lambda v: float(v) * 60,
)

TranslationQuantifier(
    id="per_minute_to_per_second_1dp",
    handler=lambda v: round(v / 60, 1),
    reverse_handler=lambda v: float(v) * 60,
)

TranslationQuantifier(
    id="per_minute_to_per_second_2dp",
    handler=lambda v: round(v / 60, 2),
    reverse_handler=lambda v: float(v) * 60,
)

TranslationQuantifier(
    id="per_minute_to_per_second_2dp_if_required",
    handler=lambda v: round(v / 60, 2) if v % 60 != 0 else v // 60,
    reverse_handler=lambda v: float(v) * 60,
)

TranslationQuantifier(
    id="times_twenty",
    handler=lambda v: v * 20,
    reverse_handler=lambda v: int(v) // 20,
)

TranslationQuantifier(
    id="times_one_point_five",
    handler=lambda v: v * 1.5,
    reverse_handler=lambda v: int(v / 1.5),
)

TranslationQuantifier(
    id="double",
    handler=lambda v: v * 2,
    reverse_handler=lambda v: int(v) // 2,
)

TranslationQuantifier(
    id="negate_and_double",
    handler=lambda v: -v * 2,
    reverse_handler=lambda v: int(-v) // 2,
)

TranslationQuantifier(
    id="divide_by_four",
    handler=lambda v: v / 4,
    reverse_handler=lambda v: v * 4,
)

TranslationQuantifier(
    id="canonical_line",
    type=TranslationQuantifier.QuantifierTypes.STRING,
    arg_size=0,
)

TranslationQuantifier(
    id="canonical_stat",
)

# These will be replaced by install_data_dependant_quantifiers
TranslationQuantifier(
    id="mod_value_to_item_class",
)

TranslationQuantifier(
    id="tempest_mod_text",
)

TranslationQuantifier(
    id="display_indexable_support",
)

TranslationQuantifier(
    id="tree_expansion_jewel_passive",
)

TranslationQuantifier(
    id="affliction_reward_type",
)

TranslationQuantifier(
    id="passive_hash",
)


TranslationQuantifier(
    id="metamorphosis_reward_description",
)

TranslationQuantifier(
    id="reminderstring",
    type=TranslationQuantifier.QuantifierTypes.STRING,
)

TranslationQuantifierHandler.init()
