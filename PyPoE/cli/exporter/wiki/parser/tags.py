"""
Wiki tag handler class.

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parser/tags.py                          |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Tag handler for processing wiki description tags.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

from collections import OrderedDict
from functools import partial

from PyPoE.poe.constants import WORDLISTS
from PyPoE.cli.exporter.wiki.parser.utils import format_result_rows

# =============================================================================
# Globals
# =============================================================================

__all__ = ['TagHandler']

# =============================================================================
# Classes
# =============================================================================

class TagHandler:
    """
    Provides tag handlers for use with :func:`parse_description_tags`

    Parameters
    ----------
    tag_handlers : dict[str, callable]
        dictionary containing tags and a callable function for passing to
        :func:`parse_description_tags`
    """

    _IL_FORMAT = '{{il|%s|html=}}'
    _C_FORMAT = '{{c|%s|%s}}'

    def __init__(self, rr):
        """
        Parameters
        ----------
        rr : RelationalReader
            RelationalReader instance to use when looking up whether items are
            'real' for linking purposes
        """
        self.rr = rr
        self.rr['BaseItemTypes.dat'].build_index('Name')
        self.rr['Words.dat'].build_index('Text')

        self.tag_handlers = {}
        for key, func in self.__class__.tag_handlers.items():
            self.tag_handlers[key] = partial(func, self)

    def _check_link(self, string):
        items = self.rr['BaseItemTypes.dat'].index['Name'][string]
        if items:
            if items[0]['ItemClassesKey']['Name'] == 'Maps':
                string = self._IL_FORMAT % string
            elif len(items) > 1:
                return '[[%s]]' % string
            else:
                string = self._IL_FORMAT % string
        return string

    def _basic_handler(self, hstr, parameter, tid):
        return self._C_FORMAT % (tid, hstr)

    def _default_handler(self, hstr, parameter, tid):
        return self._C_FORMAT % (tid, self._check_link(hstr))

    def _link_handler(self, hstr, parameter, tid):
        return self._C_FORMAT % (tid, '[[%s]]' % hstr)

    def _unique_handler(self, hstr, parameter):
        words = self.rr['Words.dat'].index['Text'][hstr]
        if words and words[0]['WordlistsKey'] == WORDLISTS.UNIQUE_ITEM:
            # Check whether unique item name clashes with base item name
            items = self.rr['BaseItemTypes.dat'].index['Name'][hstr]
            if len(items) > 0:
                hstr = '[[%s]]' % hstr
            else:
                hstr = self._IL_FORMAT % hstr
        else:
            hstr = self._check_link(hstr)
        return self._C_FORMAT % ('unique', hstr)

    def _currency_handler(self, hstr, parameter):
        if 'x ' in hstr:
            s = hstr.split('x ', maxsplit=1)
            return self._C_FORMAT % (
                'currency', '%sx %s' % (s[0], self._check_link(s[1]))
            )
        else:
            return self._default_handler(hstr, parameter, 'currency')

    def _pass_through_handler(self, hstr, parameter):
        return hstr

    tag_handlers = {
        'normal': partial(_default_handler, tid='normal'),
        'default': partial(_default_handler, tid='default'),
        'augmented': partial(_default_handler, tid='augmented'),
        'enchanted': partial(_default_handler, tid='enchanted'),

        'size': _pass_through_handler,
        'smaller': _pass_through_handler,

        'gemitem': partial(_default_handler, tid='gem'),
        'currencyitem': _currency_handler,

        'whiteitem': partial(_default_handler, tid='white'),
        'magicitem': partial(_default_handler, tid='magic'),
        'rareitem': partial(_default_handler, tid='rare'),
        'uniqueitem': _unique_handler,

        'divination': partial(_default_handler, tid='divination'),
        'prophecy': partial(_default_handler, tid='prophecy'),

        'corrupted': partial(_link_handler, tid='corrupted'),
    }


