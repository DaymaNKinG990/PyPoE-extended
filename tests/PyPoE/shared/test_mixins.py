"""


Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | tests/PyPoE/shared/test_mixins.py                                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================



Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from collections import OrderedDict

# 3rd-party
import pytest

# self
from PyPoE.shared import mixins

# =============================================================================
# Setup
# =============================================================================


class Repr(mixins.ReprMixin):
    def __init__(self, a, b=42):
        self.a = a
        self._b = b
        self.extra = 1337


# =============================================================================
# Tests
# =============================================================================


class TestReprMixin:
    @pytest.fixture
    def r(self):
        return Repr(5)

    def test_defaults(self, r):
        assert repr(r) == f"Repr<{hex(id(r))}>(a=5)"

    def test_private(self, r):
        r._REPR_PRIVATE_ATTRIBUTES = True
        assert repr(r) == f"Repr<{hex(id(r))}>(a=5, b=42)"

    def test_override(self, r):
        r._REPR_ARGUMENTS_TO_ATTRIBUTES = {"b": "extra"}
        assert repr(r) == f"Repr<{hex(id(r))}>(a=5, b=1337)"

    def test_override_missing(self, r):
        r._REPR_ARGUMENTS_TO_ATTRIBUTES = {"b": "extra"}
        r._REPR_ARGUMENTS_IGNORE_MISSING = True
        assert repr(r) == f"Repr<{hex(id(r))}>(b=1337)"

    def test_ingore(self, r):
        r._REPR_ARGUMENTS_IGNORE = {"a"}
        assert repr(r) == f"Repr<{hex(id(r))}>()"

    def test_extra_attributes(self, r):
        r._REPR_EXTRA_ATTRIBUTES = OrderedDict(
            (
                (
                    "b",
                    "_b",
                ),
                ("extra", None),
            )
        )
        assert repr(r) == f"Repr<{hex(id(r))}>(a=5, b=42, extra=1337)"
