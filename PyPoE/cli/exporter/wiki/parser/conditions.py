"""
Wiki condition class.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parser/conditions.py                    |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Wiki condition class for conditional output in wiki templates.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================


from PyPoE.cli.exporter.wiki.parser.utils import find_template, format_result_rows

# =============================================================================
# Globals
# =============================================================================

__all__ = ["WikiCondition"]

# =============================================================================
# Classes
# =============================================================================


class WikiCondition:
    COPY_KEYS = ()
    COPY_MATCH = None

    NAME = NotImplemented
    MATCH = None
    INDENT = 33
    ADD_INCLUDE = False

    def __init__(self, data, cmdargs, handler=None):
        self.data = data
        self.cmdargs = cmdargs
        if handler is None:
            self.handler = self._handler
        self.template_arguments = None

    def __call__(self, *args, **kwargs):
        page = kwargs.get("page")

        if page is not None:
            # Abuse this so it can be called as "text" and "condition"
            if self.template_arguments is None:
                self.template_arguments = find_template(page.text(), self.MATCH or self.NAME)
                if len(self.template_arguments["texts"]) == 1:
                    self.template_arguments = None
                    return False

                return True

            k: str
            for k in self.COPY_KEYS:
                try:
                    self.data[k] = self.template_arguments["kwargs"][k]
                except KeyError:
                    pass

            if self.COPY_MATCH:
                for k, v in self.template_arguments["kwargs"].items():
                    if self.COPY_MATCH.match(k):
                        self.data[k] = v

            prefix = ""
            if self.ADD_INCLUDE and "<onlyinclude></onlyinclude>" not in page.text():
                prefix = "<onlyinclude></onlyinclude>"

            return self.handler(
                prefix
                + self.template_arguments["texts"][0]
                + self._get_text()
                + "".join(self.template_arguments["texts"][1:])
            )
        else:
            return self.handler(self._get_text())

    def _handler(self, text):
        return text

    def _get_text(self):
        return format_result_rows(
            parsed_args=self.cmdargs,
            template_name=self.NAME,
            indent=self.INDENT,
            ordered_dict=self.data,
        )


# =============================================================================
# Functions
# =============================================================================
