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

    def __init__(self, identifier: str | None = None):
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

    def diff(self, other):
        if not isinstance(other, Translation):
            raise TypeError()

        if self.ids != other.ids:
            _diff_list(self.ids, other.ids, diff=False)

        if self.languages != other.languages:
            _diff_list(self.languages, other.languages)

    def get_language(self, language: str = "English") -> "TranslationLanguage":
        """
        Returns the :class:`TranslationLanguage` record for the specified
        language.

        As a fallback if the language is not found, the English
        :class:`TranslationLanguage` record will be returned.

        Parameters
        ----------
        language : str
            The language to get.


        Returns
        -------
            Returns the :class:`TranslationLanguage` record for the specified
            language or the English one if not found
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

    def __init__(self, language, parent):
        parent.languages.append(self)
        self.parent = parent
        self.language = language
        self.strings = []

    def __eq__(self, other):
        if not isinstance(other, TranslationLanguage):
            return False

        if self.language != other.language:
            return False

        return self.strings == other.strings

    def __hash__(self):
        return hash((self.language, tuple(self.strings)))

    def diff(self, other):
        if not isinstance(other, TranslationLanguage):
            raise TypeError()

        if self.language != other.language:
            print(f"Self: {self.language}, other: {other.language}")

        if self.strings != other.strings:
            _diff_list(self.strings, other.strings)

    def get_string(
        self, values: list[int] | list[tuple[int, int]]
    ) -> tuple[Union["TranslationString", None], list[bool] | None, list[int] | None]:
        """
        Formats the string according with the given values and returns the
        TranslationString instance as well as any left over (unused) values.


        Parameters
        ----------
        values
            A list of values to be used for substitution

        Returns
        -------
        str or list[int], list[int], list[int], dict[str, str]
            Returns the formatted string. See
            :meth:`TranslationString:format_string` for details.
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
        Formats the string according with the given values and
        returns the string and any left over (unused) values.

        If use_placeholder is specified, the values will be replaced with
        a placeholder instead of the actual value.

        If only_values is specified, the instead of the string the formatted
        values will be returned.


        Parameters
        ----------
        values
            A list of values to be used for substitution
        use_placeholder
            If true, Instead of values in the translations a placeholder (i.e.
            x, y, z) will be used. Values are still required however to find
            the "correct" wording of the translation.
            If a callable is specified, it will call the function with
            the index as first parameter. The callable should return a
            string to use as placeholder.
        only_values
            Whether to return formatted values instead of the formatted string.


        Returns
        -------
            Returns the formatted string. See
            :meth:`TranslationString:format_string` for details.
        """
        ts, short_values, is_range = self.get_string(values)

        if ts is None:
            return None  # type: ignore[return-value]

        return ts.format_string(
            short_values,
            is_range,
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

    def __init__(self, parent: TranslationLanguage):
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

    def _set_string(self, string: str):
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
        Reconstructed original string that would be used for translation

        Returns
        -------
            the original string
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
        The translation string as python str.format string

        Returns
        -------
        str
            str.format string
        """
        s = []
        for i, tag in enumerate(self.tags):
            s.append(self.strings[i])
            s.append(f"{{{tag}}}")
        s.append(self.strings[-1])
        return "".join(s)

    def diff(self, other):
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
        Formats the string for the given values.

        Optionally use_placeholder can be specified to return a string formatted
        with a placeholder in place of the real value. It will use lowercase
        ASCII starting at x. For indexes > 3, it will use uppercase ASCII.

        If only_values is specified, no string formatting will performed
        and instead just parsed values will be returned.

        Parameters
        ----------
        values
            List of values to use for the formatting
        is_range
            List of bools representing whether the values at the list index is
            a range or not
        use_placeholder
            If true, Instead of values in the translations a placeholder (i.e.
            x, y, z) will be used. Values are still required however to find
            the "correct" wording of the translation.
            If a callable is specified, it will call the function with
            the index as first parameter. The callable should return a
            string to use as placeholder.
        only_values
            Only return the values and not


        Returns
        -------
            Returns 4 values.

            The first return value is the formatted string. If only placeholder
            is specified, instead of the string a list of parsed values is
            returned.

            The second return value is a list of unused values.

            The third return value is a list of used values.

            The forth return value is a dictionary of extra strings
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
                    and value[1] > 0
                    or not is_range[tagid]  # type: ignore[call-overload, index, operator]
                    and value > 0
                ):  # type: ignore[operator]
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
        Returns the accumulative range rating of the specified values.

        Parameters
        ----------
        values
            List of values

        Returns
        -------
            Sum of the ratings
        """
        rating = 0
        for i, value in enumerate(values):
            rating += self.range[i].in_range(value)  # type: ignore[arg-type]
        return rating

    def reverse_string(self, string: str) -> list[int] | None:
        """
        Attempts to match this :class:`TranslationString` against the given
        string.

        If a match is found, it will attempt to cast and reverse all values
        found in the string itself.

        For missing values, it will try to insert the range maximum/minimum
        values if set, otherwise None.

        Parameters
        ----------
        string
            string to match against


        Returns
        -------
            handled list of values or None if no match
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
    ):
        parent.range.append(self)
        self.parent: TranslationString = parent
        self.min: int | None = min
        self.max: int | None = max
        self.negated: bool = negated

    def __eq__(self, other: Any) -> bool:
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
        Checks whether the value is in range and returns the rating/accuracy
        of the check performed.

        Parameters
        ----------
        value
            Value to check


        Returns
        -------
            Returns the rating of the value
            -10000 if mismatch (out of range)
            -100 if no match
            1 if any range is accepted
            2 if either minimum or maximum is specified
            3 if both minimum and maximum is specified
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

    def __init__(self):
        self.index_handlers: dict[str, list[int]] = defaultdict(list)
        self.string_handlers: dict[str, list[int]] = defaultdict(list)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TranslationQuantifierHandler):
            return False

        return self.index_handlers == other.index_handlers

    def __hash__(self) -> int:
        # return hash((tuple(self.registered_handlers.keys()), tuple(self.registered_handlers.values())))
        return hash(tuple(self.index_handlers.keys()))

    def _warn_uncaptured(self, name: str):
        raise TypeError(f"Uncaptured quantifier {name}, add in PyPoE/poe/translations.py")

    def _whole_float_to_int(self, value: float) -> float | int:
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value

    @classmethod
    def install_quantifier(cls, quantifier: "TranslationQuantifier"):
        """
        Install the specified quantifier into the generic quantifier handling

        Parameters
        ----------
        quantifier - TranslationQuantifier
            :class:`TranslationQuantifier` instance

        Returns
        -------
        """

        cls.handlers[quantifier.id] = quantifier
        cls.reverse_handlers[quantifier.id] = quantifier

    @classmethod
    def init(cls):
        cls.regex = re.compile(r"({})(?!\_)".format("|".join(cls.handlers.keys())), re.UNICODE)

    def diff(self, other: Any):
        if not isinstance(other, TranslationQuantifierHandler):
            raise TypeError

        # if self.registered_handlers != other.registered_handlers:
        _diff_dict(self.index_handlers, other.index_handlers)

    def _get_handler_func(self, handler_name: str) -> Callable:
        try:
            f = self.handlers[handler_name].handler
        except KeyError:
            self._warn_uncaptured(handler_name)
            return None  # type: ignore[return-value]
        if f is None:
            self._warn_uncaptured(handler_name)
            return None  # type: ignore[return-value]
        return f  # type: ignore[no-any-return]

    def register_from_string(self, string: str):
        """
        Registers handlers from the quantifier string.

        Parameters
        ----------
        string
            quantifier string
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
        Handle the given values based on the registered quantifiers.

        Parameters
        ----------
        values
            list of values
        is_range
            specifies whether the value at the index is a range or not. Must be
            the same length as values.

        Returns
        -------
            Returns a handled list of values and a dictionary of handled
            strings

            The keys of the dictionary refer to the translation quantifier
            string used
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
        Reverses the quantifier for the given values.

        Parameters
        ----------
        values
            list of values

        Returns
        -------
            handled list of values
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
    ):
        """
        Parameters
        ----------
        id
            string identifier of the handler
        arg_size
            number of arguments this handler accepts (excluding self)
        type
            type of the quantifier
        handler
            function that handles the values, if any
        reverse_handler
            function  hat reverses handles the values, if any
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
    def __init__(self, relational_reader, *args, **kwargs):
        self.relational_reader = relational_reader
        super().__init__(
            id="reminderstring",
            type=self.QuantifierTypes.STRING,
            handler=self.handle,
            reverse_handler=None,
        )

    def handle(self, *args):
        return self.relational_reader["ClientStrings.dat"].index["Id"][args[0].strip()]["Text"]
