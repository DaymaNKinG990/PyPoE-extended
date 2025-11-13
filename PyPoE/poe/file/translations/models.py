"""
Translation data models.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/translations/models.py                           |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Data models for translation file structures including Translation,
TranslationLanguage, TranslationString, TranslationRange,
TranslationQuantifierHandler, and TranslationQuantifier classes.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

import re
import warnings
from collections import OrderedDict, defaultdict
from collections.abc import Callable
from enum import IntEnum
from string import ascii_letters
from typing import TYPE_CHECKING, Any, Union

from PyPoE.poe.file.translations.exceptions import TranslationWarning
from PyPoE.shared.mixins import ReprMixin

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    "TranslationReprMixin",
    "Translation",
    "TranslationLanguage",
    "TranslationString",
    "TranslationRange",
    "TranslationQuantifierHandler",
    "TranslationQuantifier",
    "TQReminderString",
]

# =============================================================================
# Helper Functions
# =============================================================================


def _diff_list(self, other, diff=True):
    print(f"List len: {len(self)} vs {len(other)}")
    for item in self:
        try:
            other.remove(item)
        except ValueError:
            print(f"Not in other: {item}")
            if diff:
                pass

    if other:
        print(f"Not in self: {other}")


def _diff_dict(self, other):
    for key in self.keys():
        if key in other:
            if self[key] != other[key]:
                print(f"Value mismatch @ {key}: {self[key]} vs {other[key]}")
            del other[key]
        else:
            print(f"Not in other: {key}")

    if other:
        print(f"Not in self: {list(other.keys())}")


# =============================================================================
# Classes
# =============================================================================


class TranslationReprMixin(ReprMixin):
    """Mixin for translation classes that adds parent repr."""

    # Type hints for attributes that will be provided by subclasses
    if TYPE_CHECKING:
        parent: Any

    _REPR_ARGUMENTS_TO_ATTRIBUTES = {
        "parent": "_parent_repr",
    }

    @property
    def _parent_repr(self):
        return f"{self.parent.__class__.__name__}<{hex(id(self.parent))}>"


class Translation(TranslationReprMixin):
    """
    Representation of a single translation.

    A translation has at least one id and at least the English language (along
    with the respective strings).

    Attributes
    ----------
    languages
        List of :class:`TranslationLanguage` instances for this
        :class:`Translation`
    ids
        List of ids associated with this translation
    identifier
        Identifier if present else None
    """

    __slots__ = ["languages", "ids", "identifier"]

    _REPR_EXTRA_ATTRIBUTES = OrderedDict((("ids", None),))

    def __init__(self, identifier: str | None = None) -> None:
        """
        Initialize Translation.

        Args:
            identifier: Optional identifier string
        """
        self.languages: list[TranslationLanguage] = []
        self.ids: list[str] = []
        self.identifier: str | None = identifier

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Translation):
            return False

        if self.ids != other.ids:
            return False

        return self.languages == other.languages

    def __hash__(self):
        return hash((tuple(self.languages), tuple(self.ids)))

    def diff(self, other: Any) -> None:
        """
        Compare this translation with another and print differences.

        Args:
            other: Other Translation to compare with

        Raises:
            TypeError: If other is not a Translation instance
        """
        if not isinstance(other, Translation):
            raise TypeError()

        if self.ids != other.ids:
            _diff_list(self.ids, other.ids, diff=False)

        if self.languages != other.languages:
            _diff_list(self.languages, other.languages)

    def get_language(self, language: str = "English") -> "TranslationLanguage":
        """
        Get TranslationLanguage record for specified language.

        As a fallback if the language is not found, the English
        TranslationLanguage record will be returned.

        Args:
            language: The language to get (default: "English")

        Returns:
            TranslationLanguage record for specified language or English if not found
        """
        etr = None
        for tr in self.languages:
            if tr.language == language:
                return tr
            elif tr.language == "English":
                etr = tr

        return etr  # type: ignore[return-value]


class TranslationLanguage(TranslationReprMixin):
    """
    Representation of a language in the translation file. Each language has
    one or multiple strings.

    Attributes
    ----------
    parent : Translation
        The parent :class:`Translation` instance
    language : str
        the language of this instance
    strings : list[TranslationString]
        List of :class:`TranslationString` instances for this language
    """

    __slots__ = ["parent", "language", "strings"]

    def __init__(self, language: str, parent: Translation) -> None:
        """
        Initialize TranslationLanguage.

        Args:
            language: Language name (e.g., "English", "Russian")
            parent: Parent Translation instance
        """
        parent.languages.append(self)
        self.parent = parent
        self.language = language
        self.strings = []

    def __eq__(self, other: Any) -> bool:
        """
        Check equality of TranslationLanguage instances.

        Args:
            other: Other object to compare with

        Returns:
            True if language and strings are equal
        """
        if not isinstance(other, TranslationLanguage):
            return False

        if self.language != other.language:
            return False

        return self.strings == other.strings

    def __hash__(self):
        return hash((self.language, tuple(self.strings)))

    def diff(self, other: Any) -> None:
        """
        Compare this translation language with another and print differences.

        Args:
            other: Other TranslationLanguage to compare with

        Raises:
            TypeError: If other is not a TranslationLanguage instance
        """
        if not isinstance(other, TranslationLanguage):
            raise TypeError()

        if self.language != other.language:
            print(f"Self: {self.language}, other: {other.language}")

        if self.strings != other.strings:
            _diff_list(self.strings, other.strings)

    def get_string(
        self, values: list[int] | list[tuple[int, int]]
    ) -> tuple["TranslationString" | None, list[bool] | None, list[int] | None]:
        """
        Get TranslationString for given values.

        Args:
            values: List of values to use for substitution (can include ranges)

        Returns:
            Tuple of (TranslationString, short_values, is_range) or (None, None, None)
            if no match found
        """
        # Support for ranges
        is_range = []
        test_values = []
        short_values = []
        for item in values:
            # Type narrowing: check if item is tuple
            if isinstance(item, tuple):
                # Use the greater value unless it is zero
                test_values.append(item[1] or item[0])
                if item[0] == item[1]:
                    short_values.append(item[0])
                    is_range.append(False)
                else:
                    short_values.append(item)  # type: ignore[arg-type]
                    is_range.append(True)
            else:
                test_values.append(item)
                short_values.append(item)
                is_range.append(False)

        temp = []
        for ts in self.strings:
            # TODO: check whether this really is a non issue now
            # if len(values) != len(ts.range):
            #   raise Exception('mismatch %s' % ts.range)

            match = ts.match_range(test_values)
            temp.append((match, ts))

        # Only the highest scoring/matching translation...
        temp.sort(key=lambda x: -x[0])
        rating, ts = temp[0]

        if rating <= 0:
            return None, None, None

        return ts, short_values, is_range  # type: ignore[return-value]

    def format_string(
        self,
        values: list[int] | list[tuple[int, int]],
        use_placeholder: bool | Callable[[int], Any] = False,
        only_values: bool = False,
    ) -> tuple[str | list[int], list[int], list[int], dict[str, str]]:
        """
        Format string according to given values.

        Args:
            values: List of values to use for substitution
            use_placeholder: If True, uses placeholders (x, y, z) instead of values.
                If callable, calls with index to get placeholder string
            only_values: If True, returns formatted values instead of string

        Returns:
            Tuple of (formatted_string, unused_values, used_values, extra_strings)
            or (None, None, None, None) if no match found
        """
        ts, short_values, is_range = self.get_string(values)

        if ts is None:
            return None  # type: ignore[return-value]

        return ts.format_string(
            short_values,  # type: ignore[arg-type]
            is_range,  # type: ignore[arg-type]
            use_placeholder,
            only_values,  # type: ignore[arg-type]
        )

    def reverse_string(self, string: str) -> list[int] | None:
        """
        Attempts to find a match for the given string and returns a list of
        reversed values if a match is found for this language.

        Parameters
        ----------
        string : str
            String to match against


        Returns
        -------
        None or list
            handled list of values or None if not found
        """
        # TODO: Should only match one at a time. But may be not?
        for ts in self.strings:
            result = ts.reverse_string(string)
            if result is None:
                continue

            return result  # type: ignore[no-any-return]

        return None


class TranslationString(TranslationReprMixin):
    """
    Representation of a single translation string. Each string comes with
    it's own quantifiers and acceptable range.

    Attributes
    ----------
    parent
        parent :class:`TranslationLanguage` instance
    quantifier
        the associated :class:`TranslationQuantifierHandler` instance for this
        translation string
    range
        list of :class:`TranslationRange` instances containing the acceptable
        ranges for this translation as a list of instances for each index
    strings
        translation string broken down into segments
    tags
        tags for value replacement between segments
    tags_types
        list of tag types
    """

    __slots__ = ["parent", "quantifier", "range", "strings", "tags", "tags_types"]

    _REPR_EXTRA_ATTRIBUTES = OrderedDict((("string", None),))

    # replacement tags used in translations
    _re_split = re.compile(r"(?:\{(?P<id>[0-9]*)(?:[\:]*)(?P<type>[^\}]*)\})", re.UNICODE)

    _RANGE_FORMAT = "({0}-{1})"
    _NEGATIVE_RANGE_FORMAT = "-({0}-{1})"

    def __init__(self, parent: TranslationLanguage) -> None:
        """
        Initialize TranslationString.

        Args:
            parent: Parent TranslationLanguage instance
        """
        parent.strings.append(self)
        self.parent: TranslationLanguage = parent
        self.quantifier: TranslationQuantifierHandler = TranslationQuantifierHandler()
        self.range: list[TranslationRange] = []
        self.tags: list[int] = []
        self.tags_types: list[str] = []
        self.strings: list[str] = []

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TranslationString):
            return False

        if self.quantifier != other.quantifier:
            return False

        if self.range != other.range:
            return False

        return self.string == other.string

    def __hash__(self) -> int:
        return hash((self.string, tuple(self.range), self.quantifier))

    def _set_string(self, string: str) -> None:
        """
        Parse and set translation string.

        Extracts segments, tags, and tag types from the string format.

        Args:
            string: Raw translation string with {tag} placeholders
        """
        string = string.replace("%%", "%").replace("\\n", "\n")

        start = None
        for match in self._re_split.finditer(string):
            self.strings.append(string[start : match.start()])
            intid = match.group("id")
            if intid:
                self.tags.append(int(intid))
            # Empty values appear in order
            else:
                if len(self.tags):
                    self.tags.append(self.tags[-1] + 1)
                else:
                    self.tags.append(0)

            self.tags_types.append(match.group("type"))
            start = match.end()
        self.strings.append(string[start:])

    @property
    def string(self) -> str:
        """
        Get reconstructed original string for translation.

        Returns:
            Original string with {tag} placeholders
        """
        s = []
        for i, tag in enumerate(self.tags):
            s.append(self.strings[i])
            if self.tags_types[i]:
                s.append(f"{{{tag}:{self.tags_types[i]}}}")
            else:
                s.append(f"{{{tag}}}")
        s.append(self.strings[-1])
        return "".join(s)

    @property
    def as_format_string(self) -> str:
        """
        Get translation string as Python str.format string.

        Returns:
            str.format compatible string
        """
        s = []
        for i, tag in enumerate(self.tags):
            s.append(self.strings[i])
            s.append(f"{{{tag}}}")
        s.append(self.strings[-1])
        return "".join(s)

    def diff(self, other: Any) -> None:
        """
        Compare this translation string with another and print differences.

        Args:
            other: Other TranslationString to compare with

        Raises:
            TypeError: If other is not a TranslationString instance
        """
        if not isinstance(other, TranslationString):
            raise TypeError()

        if self.quantifier != other.quantifier:
            self.quantifier.diff(other.quantifier)

        if self.range != other.range:
            _diff_list(self.range, other.range)

        if self.string != other.string:
            print(f"String mismatch: {self.string} vs {other.string}")

    def format_string(
        self,
        values: list[int] | list[tuple[int, int]],
        is_range: list[bool],
        use_placeholder: bool | Callable[[int], Any] = False,
        only_values: bool = False,
    ) -> tuple[str | list[int], list[int], list[int], dict[str, str]]:
        """
        Format string for given values.

        Args:
            values: List of values to use for formatting
            is_range: List of bools indicating if value at index is a range
            use_placeholder: If True, uses placeholders (x, y, z) instead of values.
                If callable, calls with index to get placeholder string
            only_values: If True, returns parsed values instead of formatted string

        Returns:
            Tuple of (formatted_string, unused_values, used_values, extra_strings)
        """
        values, extra_strings = self.quantifier.handle(values, is_range)

        string = []
        used = set()
        for i, tagid in enumerate(self.tags):
            value = values[tagid]  # type: ignore[call-overload]
            if not only_values:
                string.append(self.strings[i])
                # For adding the plus sign to the $+d and $+d%% formats
                if "+" in self.tags_types[i] and (
                    is_range[tagid]
                    and value[1] > 0  # type: ignore[index, operator]
                    or not is_range[tagid]  # type: ignore[call-overload, index, operator]
                    and value > 0  # type: ignore[operator]
                ):
                    string.append("+")

                if not use_placeholder:
                    fmt = "{0:n}" if "d" in self.tags_types[i] else "{0}"

                    if is_range[tagid]:  # type: ignore[call-overload]
                        # Move the minus outside if both values are negative
                        try:
                            if value[0] < 0 and value[1] < 0:  # type: ignore[index]
                                value = [-v for v in value]  # type: ignore[assignment,union-attr,misc]
                                range_fmt = self._NEGATIVE_RANGE_FORMAT
                            else:
                                range_fmt = self._RANGE_FORMAT
                        # TODO: how to show ranges for text stuff?
                        except TypeError:
                            range_fmt = self._RANGE_FORMAT
                        value = range_fmt.format(  # type: ignore[assignment]
                            fmt, fmt.replace("{0", "{1")
                        ).format(*value)  # type: ignore[misc]
                    else:
                        value = fmt.format(value)  # type: ignore[assignment]
                elif use_placeholder is True:
                    value = ascii_letters[23 + i]  # type: ignore[assignment]
                elif callable(use_placeholder):
                    value = use_placeholder(i)  # type: ignore[assignment]
            string.append(value)  # type: ignore[arg-type]
            used.add(tagid)

        unused = []
        for i, val in enumerate(values):
            if i in used:
                continue
            unused.append(val)

        string = values if only_values else "".join(string + [self.strings[-1]])  # type: ignore[assignment]

        return string, unused, values, extra_strings  # type: ignore[return-value]

    def match_range(self, values: list[int | float]) -> int:
        """
        Get accumulative range rating for specified values.

        Args:
            values: List of values to check

        Returns:
            Sum of range ratings (higher = better match)
        """
        rating = 0
        for i, value in enumerate(values):
            rating += self.range[i].in_range(value)  # type: ignore[arg-type]
        return rating

    def reverse_string(self, string: str) -> list[int] | None:
        """
        Match this TranslationString against given string and reverse values.

        If a match is found, attempts to cast and reverse all values found
        in the string. For missing values, tries to insert range max/min
        values if set, otherwise None.

        Args:
            string: String to match against

        Returns:
            List of reversed values if match found, None otherwise
        """
        index = 0
        values_indexes = []
        for i, partial in enumerate(self.strings):
            match = string.find(partial, index)
            if match == -1:
                return None
            # Matched at the start of string, no preceeding value

            # Fix for TR strings starting with value
            if i == 1 and self.strings[0] == "":
                values_indexes.append(match)
            index = match + len(partial)
            values_indexes.append(index)

        # Fix for TR strings ending with value
        if self.strings[-1] == "":
            values_indexes[-1] = None  # type: ignore[call-overload]

        values = []
        for i in range(0, len(values_indexes) - 1):
            j = i + 1
            values.append(string[values_indexes[i] : values_indexes[j]])

        # tags may appear multiple times, reduce to one tag per value
        tags = {}
        for i, tag in enumerate(self.tags):
            tags[tag] = values[i]

        values = list(range(0, len(self.range)))  # type: ignore[assignment, arg-type]
        for i in values:  # type: ignore[assignment]
            if i in tags:
                # Fix for %1$+d
                values[i] = tags[i].strip("%")
            else:
                # The only definitive case
                r = self.range[i]
                warn = True
                if r.negated:
                    if (
                        r.min == r.max
                        and r.max is not None
                        or r.min is not None
                        and r.max is not None
                        or r.min is None
                        and r.max is not None
                    ):
                        val = r.max + 1
                    elif r.min is not None and r.min is None:
                        val = r.min - 1
                    else:
                        val = 1
                else:
                    if r.min == r.max and r.max is not None:
                        val = r.min  # type: ignore[assignment]
                        warn = False
                    elif (
                        r.min is not None
                        and r.max is not None
                        or r.min is None
                        and r.max is not None
                    ):
                        val = r.max
                    elif r.min is not None and r.min is None:
                        val = r.min
                    else:
                        val = 0

                if warn:
                    warnings.warn(
                        f'Can not safely find a value at index "{i}", using '
                        f'range value "{val}" instead',
                        TranslationWarning,
                        stacklevel=2,
                    )

                values[i] = val  # type: ignore[call-overload]
        return self.quantifier.handle_reverse(values)  # type: ignore[arg-type]


class TranslationRange(TranslationReprMixin):
    """
    Object to represent the acceptable range of a translation.

    Many translation strings only apply to a given minimum or maximum number.
    In some cases there are also special strings for specific conditions.

    For example, 100 for freeze turns into "Always Freeze" whereas less is
    "chance to freeze".

    Attributes
    ----------
    parent
        parent :class:`TranslationString` instance
    min
        minimum range
    max
        maximum range
    negated
        Whether the value is negated
    """

    __slots__ = ["parent", "min", "max", "negated"]

    def __init__(
        self, min: int | None, max: int | None, parent: TranslationString, negated: bool = False
    ) -> None:
        """
        Initialize TranslationRange.

        Args:
            min: Minimum range value (None = no minimum)
            max: Maximum range value (None = no maximum)
            parent: Parent TranslationString instance
            negated: Whether the range is negated
        """
        parent.range.append(self)
        self.parent: TranslationString = parent
        self.min: int | None = min
        self.max: int | None = max
        self.negated: bool = negated

    def __eq__(self, other: Any) -> bool:
        """
        Check equality of TranslationRange instances.

        Args:
            other: Other object to compare with

        Returns:
            True if min, max, and negated are equal
        """
        if not isinstance(other, TranslationRange):
            return False

        if self.min != other.min:
            return False

        if self.max != other.max:
            return False

        return self.negated == other.negated

    def __hash__(self) -> int:
        return hash((self.min, self.max))

    def in_range(self, value: int) -> int:
        """
        Check if value is in range and return rating.

        Args:
            value: Value to check

        Returns:
            Rating of the value:
            - -10000 if mismatch (out of range)
            - -100 if no match
            - 1 if any range is accepted
            - 2 if either min or max is specified
            - 3 if both min and max are specified
        """
        # Any range is accepted
        if self.min is None and self.max is None:
            return 1

        if self.negated:
            f_comp = int.__gt__
            f_and = bool.__or__
        else:
            f_comp = int.__le__
            f_and = bool.__and__

        if self.min is None:
            if f_comp(value, self.max):  # type: ignore[arg-type]
                return 2
            else:
                return -10000
        elif self.max is None:
            if f_comp(self.min, value):
                return 2
            else:
                return -10000
        elif self.min is not None and self.max is not None:
            if f_and(f_comp(self.min, value), f_comp(value, self.max)):
                return 3
            else:
                return -10000

        return -100


class TranslationQuantifierHandler(TranslationReprMixin):
    """
    Class to represent and handle translation quantifiers.

    In the GGG files often there are qualifiers specified to adjust the output
    of the values; for example, a value might be negated (i.e so that it would
    show "5% reduced Damage" instead of "-5% reduced Damage").

    Attributes
    ----------
    index_handlers : dict[str, list[int]]
        Mapping of the name of registered handlers to the ids they apply to

    handlers : dict[str, TranslationQuantifier]
        Class variable. Installed handlers

    reverse_handlers : dict[str, TranslationQuantifier]
        Class variable. Installed reverse handlers.
    """

    _REPR_EXTRA_ATTRIBUTES = OrderedDict(
        (
            ("index_handlers", None),
            ("string_handlers", None),
        )
    )

    handlers: dict[str, Any] = {}

    reverse_handlers: dict[str, Any] = {}

    regex: Any = None

    __slots__ = ["index_handlers", "string_handlers"]

    def __init__(self) -> None:
        """
        Initialize TranslationQuantifierHandler.

        Creates empty handler dictionaries for index and string handlers.
        """
        self.index_handlers: dict[str, list[int]] = defaultdict(list)
        self.string_handlers: dict[str, list[int]] = defaultdict(list)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TranslationQuantifierHandler):
            return False

        return self.index_handlers == other.index_handlers

    def __hash__(self) -> int:
        # return hash((tuple(self.registered_handlers.keys()), tuple(self.registered_handlers.values())))
        return hash(tuple(self.index_handlers.keys()))

    def _warn_uncaptured(self, name: str) -> None:
        """
        Raise error for uncaptured quantifier.

        Args:
            name: Name of uncaptured quantifier

        Raises:
            TypeError: Always raised to indicate missing quantifier handler
        """
        raise TypeError(f"Uncaptured quantifier {name}, add in PyPoE/poe/translations.py")

    def _whole_float_to_int(self, value: float) -> float | int:
        """
        Convert whole float to int if applicable.

        Args:
            value: Float value to check

        Returns:
            int if value is whole number, otherwise float
        """
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value

    @classmethod
    def install_quantifier(cls, quantifier: "TranslationQuantifier") -> None:
        """
        Install quantifier into generic quantifier handling.

        Args:
            quantifier: TranslationQuantifier instance to install
        """

        cls.handlers[quantifier.id] = quantifier
        cls.reverse_handlers[quantifier.id] = quantifier

    @classmethod
    def init(cls) -> None:
        """
        Initialize regex pattern from installed handlers.

        Must be called after all quantifiers are installed.
        """
        cls.regex = re.compile(r"({})(?!\_)".format("|".join(cls.handlers.keys())), re.UNICODE)

    def diff(self, other: Any):
        if not isinstance(other, TranslationQuantifierHandler):
            raise TypeError

        # if self.registered_handlers != other.registered_handlers:
        _diff_dict(self.index_handlers, other.index_handlers)

    def _get_handler_func(self, handler_name: str) -> Callable | None:
        """
        Get handler function for given handler name.

        Args:
            handler_name: Name of handler to get

        Returns:
            Handler function or None if not found/not set
        """
        try:
            f = self.handlers[handler_name].handler
        except KeyError:
            self._warn_uncaptured(handler_name)
            return None
        if f is None:
            self._warn_uncaptured(handler_name)
            return None
        return f  # type: ignore[no-any-return]

    def register_from_string(self, string: str) -> None:
        """
        Register handlers from quantifier string.

        Args:
            string: Quantifier string to parse

        Raises:
            TypeError: If quantifier is not recognized
        """
        values = iter(self.regex.split(string))

        for partial in values:
            partial = partial.strip()
            if partial == "":
                continue
            handler = self.handlers.get(partial)
            if handler:
                args = [values.__next__() for i in range(0, handler.arg_size)]
                if handler.type == TranslationQuantifier.QuantifierTypes.INT:
                    try:
                        self.index_handlers[handler.id].append(int(args[0]))
                    except ValueError as e:
                        warnings.warn(
                            f'Broken quantifier "{string}" - Error: {e.args[0]}',
                            TranslationWarning,
                            stacklevel=2,
                        )
                elif handler.type == TranslationQuantifier.QuantifierTypes.STRING:
                    self.string_handlers[handler.id] = args
            else:
                raise TypeError(
                    f"Uncaptured quantifier {partial}, add in PyPoE/poe/translations.py"
                )

    def handle(
        self, values: list[int] | list[tuple[int, int]], is_range: list[bool]
    ) -> tuple[list[Any], dict[str, str]]:
        """
        Handle values based on registered quantifiers.

        Args:
            values: List of values to handle
            is_range: List of bools indicating if value at index is a range
                (must be same length as values)

        Returns:
            Tuple of (handled_values, handled_strings_dict)
        """
        values = list(values)  # type: ignore[assignment]
        for handler_name in self.index_handlers:
            f = self._get_handler_func(handler_name)
            if f is None:
                continue
            for index in self.index_handlers[handler_name]:
                index -= 1
                if is_range[index]:
                    values[index] = (f(values[index][0]), f(values[index][1]))  # type: ignore[call-overload, index]
                else:
                    values[index] = f(values[index])

        for i, value in enumerate(values):
            if is_range[i]:
                values[i] = tuple([self._whole_float_to_int(v) for v in value])  # type: ignore[call-overload, assignment, attr-defined]
            else:
                values[i] = self._whole_float_to_int(value)  # type: ignore[call-overload, assignment, arg-type]

        strings = OrderedDict()
        for handler_name, args in self.string_handlers.items():
            f = self._get_handler_func(handler_name)
            if f is None:
                continue
            strings[handler_name] = f(*args)

        return values, strings

    def handle_reverse(self, values: list[int]) -> list[int]:
        """
        Reverse quantifier for given values.

        Args:
            values: List of values to reverse

        Returns:
            Handled list of reversed values
        """
        indexes = set(range(0, len(values)))
        for handler_name in self.index_handlers:
            try:
                f = self.reverse_handlers[handler_name].reverse_handler
            except KeyError:
                self._warn_uncaptured(handler_name)
                break
            for index in self.index_handlers[handler_name]:
                index -= 1
                indexes.remove(index)
                # TODO: handle string values
                values[index] = f(values[index])

        for index in indexes:
            values[index] = int(values[index])

        return values


class TranslationQuantifier(TranslationReprMixin):
    """
    Attributes
    ----------
    id
        string identifier of the handler
    arg_siz
        number of arguments this handler accepts (excluding self)
    type
        type of the quantifier
    handler
        function that handles the values, if any
    reverse_handler
        function  hat reverses handles the values, if any
    """

    class QuantifierTypes(IntEnum):
        INT = 1
        STRING = 2

    __slots__ = [
        "id",
        "arg_size",
        "type",
        "handler",
        "reverse_handler",
    ]

    def __init__(
        self,
        id: str,
        arg_size: int = 1,
        type: QuantifierTypes = QuantifierTypes.INT,
        handler: Callable | None = None,
        reverse_handler: Callable | None = None,
    ) -> None:
        """
        Initialize TranslationQuantifier.

        Args:
            id: String identifier of the handler
            arg_size: Number of arguments this handler accepts (default: 1)
            type: Type of the quantifier (default: INT)
            handler: Function that handles the values (optional)
            reverse_handler: Function that reverses handles the values (optional)

        Raises:
            ValueError: If type is not a QuantifierTypes instance
        """
        self.id: str = id
        self.arg_size: int = arg_size
        if not isinstance(type, self.QuantifierTypes):
            raise ValueError("Type must be a QuantifierTypes instance")
        self.type: TranslationQuantifier.QuantifierTypes = type
        self.handler: Callable | None = handler
        self.reverse_handler: Callable | None = reverse_handler
        TranslationQuantifierHandler.install_quantifier(self)


class TQReminderString(TranslationQuantifier):
    """Translation quantifier for reminder strings from ClientStrings.dat."""

    def __init__(self, relational_reader: Any, *args: Any, **kwargs: Any) -> None:
        """
        Initialize TQReminderString.

        Args:
            relational_reader: RelationalReader instance for accessing ClientStrings.dat
            *args: Additional positional arguments (unused)
            **kwargs: Additional keyword arguments (unused)
        """
        self.relational_reader = relational_reader
        super().__init__(
            id="reminderstring",
            type=self.QuantifierTypes.STRING,
            handler=self.handle,
            reverse_handler=None,
        )

    def handle(self, *args: Any) -> str:
        """
        Handle reminder string lookup.

        Args:
            *args: Arguments (first should be string ID)

        Returns:
            Text from ClientStrings.dat for given ID
        """
        return self.relational_reader["ClientStrings.dat"].index["Id"][args[0].strip()]["Text"]
