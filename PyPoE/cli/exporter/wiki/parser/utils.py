"""
Wiki parser utility functions.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parser/utils.py                         |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utility functions for wiki parsing including inter-wiki link generation,
template finding, and description tag parsing.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

import re
from collections import OrderedDict
from functools import partial
from typing import Any

from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.wiki.parser.constants import DEFAULT_INDENT, _inter_wiki_map
from PyPoE.cli.exporter.wiki.parser.tags import TagHandler
from PyPoE.poe.text import parse_description_tags

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    "_make_inter_wiki_re",
    "format_result_rows",
    "make_inter_wiki_links",
    "find_template",
    "parse_and_handle_description_tags",
]

# =============================================================================
# Functions
# =============================================================================


"""_inter_wiki_re = re.compile(
    r'(?: |^)(?P<text>%s))' % '|'.join([item[0] for item in _inter_wiki_map]),
    re.UNICODE | re.IGNORECASE
)"""

_MAX_RE = 97


def _make_inter_wiki_re():
    out: dict[str, list[Any]] = {}
    for language, _inter_wiki_mapping in _inter_wiki_map.items():
        out[language] = []
        for i in range(0, (len(_inter_wiki_mapping) // _MAX_RE) + 1):
            id = i * _MAX_RE
            out[language].append(
                re.compile(
                    r"(?![^\[]*\]\])"
                    r"(?: |^)"
                    r"(?P<text>{})"
                    r"(?= |$)".format("|".join(
                        [f"({item[0]})" for item in _inter_wiki_mapping[id : id + _MAX_RE]]
                    )),
                    re.UNICODE | re.IGNORECASE,
                )
            )
    return out


_inter_wiki_re = _make_inter_wiki_re()

# =============================================================================
# Classes
# =============================================================================


def format_result_rows(parsed_args, ordered_dict, template_name, indent=DEFAULT_INDENT):
    """
    Formats the given result rows as mediawiki template or module.

    Parameters
    ----------
    parsed_args
        argument parser argument containing the format argument
    ordered_dict : OrderedDict
        OrderedDict instance of the rows to format
    template_name : str
        name of the template
    indent : int
        number of spaces to use for indentation/padding up to the given size

    Returns
    -------
    out : str
        formatted string
    """
    if parsed_args.format == "template":
        out = [f"{{{{{template_name}\n"]
        for k, v in ordered_dict.items():
            if v is not None:
                out.append((f"|{{0: <{indent}}}= {{1}}\n").format(k, v))
        out.append("}}")
    elif parsed_args.format == "module":
        ordered_dict["debug_id"] = 1
        out = ["{"]
        for k, v in ordered_dict.items():
            if v is not None:
                out.append(f'{k} = "{v}", ')
        out[-1] = out[-1].strip(", ")
        out.append("}")
    return "".join(out)


def make_inter_wiki_links(string):
    """
    Formats the given string according to the predefined inter wiki formatting
    rules and returns it.

    Parameters
    ----------
    string : str
        String to format

    Returns
    -------
    str
        String formatted with inter wiki links
    """

    _inter_wiki = _inter_wiki_re.get(config.get_option("language"))

    if _inter_wiki is None:
        return string

    mapping = _inter_wiki_map.get(config.get_option("language"))

    for i, regex in enumerate(_inter_wiki):
        out = []
        last_index = 0
        for match in regex.finditer(string):
            text = match.group("text")
            # Offset by 1 to account for text group
            index = match.groups().index(text, 1) - 1
            data = mapping[i * _MAX_RE + index][1]  # type: ignore[index]

            out.append(string[last_index : match.start("text")])
            if text == data["link"]:
                out.append("[[{}]]".format(data["link"]))
            else:
                out.append("[[{}|{}]]".format(data["link"], text))

            last_index = match.end("text")

        out.append(string[last_index:])
        string = "".join(out)

    return string


def find_template(wikitext, template_name):
    """
    Finds a template within wikitext and parses the arguments.

    Parameters
    ----------
    wikitext: string
        wiktext
    template_name: string
        Name of the template to find

    Returns
    -------
    dict[str, object]
        returns a dictionary containing 3 keys:

        texts: list[str]
            text not included in the template itself; each template call
            inbetween
        args: list[str]
            positional arguments passed to the template
        kwargs: OrderedDict[str, str]
            keyword arguments passed to the template in the order they
            appeared in the wikitext

    """

    def f(scanner, result, tid):
        return tid, scanner.match, result

    scanner = re.Scanner(
        [  # type: ignore[attr-defined]
            # Need to have this look ahead to avoid matching templates that start
            # with the same name.
            (rf"{{{{{template_name}(?=[^\w}}\|]*\||}}}})", partial(f, tid="template")),
            (r"{{", partial(f, tid="l_brace")),
            (r"}}", partial(f, tid="r_brace")),
            (r"\[\[", partial(f, tid="l_brackets")),
            (r"\]\]", partial(f, tid="r_brackets")),
            (r"\|", partial(f, tid="pipe")),
            (r"=", partial(f, tid="equals")),
            (r"[{}]{1}", partial(f, tid="single_brace")),
            (r"[\[\]]{1}", partial(f, tid="single_bracket")),
            (r"[^{}\|=\[\]]+", partial(f, tid="text")),
        ],
        re.UNICODE | re.MULTILINE,
    )

    # Returns
    texts: list[list[Any]] = [
        [],
    ]
    kw_arguments = OrderedDict()
    arguments = []

    # Loop parameters
    in_template = False
    pre_equal = True
    brace_count = 0
    bracket_count = 0
    template_argument = ["", ""]

    for tid, _match, text in scanner.scan(wikitext)[0]:
        if tid == "template":
            in_template = True
        elif in_template:
            # r_brace is needed to capture the last argument, as it's not
            # delimited by a pipe
            # It also prevents reaching the second condition in that case
            if tid in ("pipe", "r_brace") and brace_count == 0 and bracket_count == 0:
                pre_equal = True
                for i in range(0, 2):
                    template_argument[i] = template_argument[i].strip(" \n")

                if template_argument[1]:
                    kw_arguments[template_argument[0]] = template_argument[1]
                elif template_argument[0]:
                    arguments.append([template_argument[0]])
                template_argument = ["", ""]
            elif tid in (
                "text",
                "l_brace",
                "r_brace",
                "single_brace",
                "pipe",
                "l_brackets",
                "r_brackets",
                "single_bracket",
            ) or (tid == "equals" and brace_count >= 1):
                index = 0 if pre_equal else 1
                template_argument[index] += text
            elif tid == "equals" and brace_count == 0:
                pre_equal = False

            # Brace counting must be done after the text parsing because
            # the previous brace count is needed up there
            if tid == "l_brace":
                brace_count += 1
            elif tid == "r_brace":
                if brace_count == 0:
                    in_template = False
                    texts.append([])
                else:
                    brace_count -= 1
            elif tid == "l_brackets":
                bracket_count += 1
            elif tid == "r_brackets":
                bracket_count -= 1
        else:
            texts[-1].append(text)

    # Don't really need the list anymore
    texts = ["".join(t) for t in texts]  # type: ignore[misc]

    return {"texts": texts, "args": arguments, "kwargs": kw_arguments}


def parse_and_handle_description_tags(rr, text):
    """
    Parses and handles description texts

    Parameters
    ----------
    rr : RelationalReader
        RelationalReader instance to pass to TagHandler when parsing
    text : str
        Text which to parse

    Returns
    -------
    str
        Parsed texts with wiki templates/links
    """
    return (
        parse_description_tags(text)
        .handle_tags(TagHandler(rr).tag_handlers)
        .replace("\n", "<br>")
        .replace("\r", "")
    )  # type: ignore[arg-type]
