"""
Items exporter handler

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parsers/item/handler.py                 |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Contains ItemsHandler for command-line interface.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Self
from PyPoE.cli.exporter.wiki.handler import ExporterHandler
from PyPoE.cli.exporter.wiki import parser

# Importing parser and prophecy to avoid circular imports
# They will be available after module initialization
ItemsParser = None
ProphecyParser = None

# =============================================================================
# Classes
# =============================================================================


class ItemsHandler(ExporterHandler):
    def __init__(self, sub_parser, *args, **kwargs):
        # Late import to avoid circular dependency
        from PyPoE.cli.exporter.wiki.parsers.item.parser import ItemsParser as IP
        from PyPoE.cli.exporter.wiki.parsers.item.prophecy import ProphecyParser as PP
        global ItemsParser, ProphecyParser
        ItemsParser = IP
        ProphecyParser = PP

        super().__init__(self, sub_parser, *args, **kwargs)
        self.parser = sub_parser.add_parser('items', help='Items Exporter')
        self.parser.set_defaults(func=lambda args: self.parser.print_help())
        core_sub = self.parser.add_subparsers()

        #
        # Generic base item export
        #
        item_parser = core_sub.add_parser('item', help='Regular item export')
        item_parser.set_defaults(func=lambda args: parser.print_help())  # type: ignore[attr-defined]
        sub = item_parser.add_subparsers()

        self.add_default_subparser_filters(sub, cls=ItemsParser, type='item')

        item_filter_parser = sub.add_parser(
            'by_filter',
            help='Extracts all items matching various filters',
        )

        self.add_default_parsers(
            parser=item_filter_parser,
            cls=ItemsParser,
            func=ItemsParser.by_filter,
            type='item',
        )
        item_filter_parser.add_argument(
            '-ft-n', '--filter-name',
            help='Filter by item name using regular expression.',
            dest='re_name',
        )

        item_filter_parser.add_argument(
            '-ft-id', '--filter-id', '--filter-metadata-id',
            help='Filter by item metadata id using regular expression',
            dest='re_id',
        )

        #
        # Prophecies
        #
        parser = core_sub.add_parser('prophecy', help='Prophecy export')
        parser.set_defaults(func=lambda args: parser.print_help())
        sub = parser.add_subparsers()
        self.add_default_subparser_filters(sub, cls=ProphecyParser,
                                           type='prophecy')

        #
        # Betrayal and later map series
        #
        parser = core_sub.add_parser(
            'maps', help='Map export (Betrayal and later)')
        parser.set_defaults(func=lambda args: parser.print_help())

        self.add_default_parsers(
            parser=parser,
            cls=ItemsParser,
            func=ItemsParser.export_map,
        )
        self.add_image_arguments(parser)
        self.add_map_series_parsers(parser)

        parser.add_argument(
            'name',
            help='Visible name (i.e. the name you see in game). Can be '
                 'specified multiple times.',
            nargs='*',
        )

        #
        # Atlas nodes
        #

        parser = core_sub.add_parser(
            'atlas_icons', help='Atlas icons export')
        parser.set_defaults(func=lambda args: parser.print_help())

        self.add_default_parsers(
            parser=parser,
            cls=ItemsParser,
            func=ItemsParser.export_map_icons,
        )
        self.add_image_arguments(parser)
        self.add_map_series_parsers(parser)

    def add_map_series_parsers(self, parser):
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '-ms', '--map-series', '--filter-map-series',
            help='Filter by map series name (localized)',
            dest='map_series',
        )

        group.add_argument(
            '-msid', '--map-series-id', '--filter-map-series-id',
            help='Filter by internal map series id',
            dest='map_series_id',
        )

    def add_default_parsers(self, *args, type=None, **kwargs):
        super().add_default_parsers(*args, **kwargs)
        parser = kwargs['parser']
        self.add_format_argument(parser)
        parser.add_argument(
            '--disable-english-file-links',
            help='Disables putting english file links in inventory icon for non'
                 ' English languages',
            action='store_false',
            dest='english_file_link',
            default=True,
        )

        if type == 'item':
            parser.add_argument(
                '-ft-c', '--filter-class',
                help='Filter by item class(es). Case sensitive.',
                nargs='*',
                dest='item_class',
            )

            parser.add_argument(
                '-ft-cid', '--filter-class-id',
                help='Filter by item class id(s). Case sensitive.',
                nargs='*',
                dest='item_class_id',
            )

            self.add_image_arguments(parser)
        elif type == 'prophecy':
            parser.add_argument(
                '--allow-disabled',
                help='Allows disabled prophecies to be exported',
                action='store_true',
                dest='allow_disabled',
                default=False,
            )


__all__ = ['ItemsHandler']

