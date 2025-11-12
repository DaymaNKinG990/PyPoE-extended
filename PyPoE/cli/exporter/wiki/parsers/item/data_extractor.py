"""
Item Data Extractor.

Handles extraction and processing of item data.
Extracted from UtilsMixin for better separation of concerns.

This class uses composition instead of inheritance, making it easier to test
and maintain.
"""

import os
import re
import warnings
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from PyPoE.cli.core import Msg, console
from PyPoE.cli.exporter.wiki.handler import ExporterResult
from PyPoE.cli.exporter.wiki.parsers.item.base import ItemWikiCondition


class ItemDataExtractor:
    """
    Extracts and processes item data.

    This class handles filtering, processing, and exporting items to wiki format.

    Attributes:
        rr: RelationalReader instance for data access
        rr2: RelationalReader instance for English language (optional)
        tc: TranslationFileCache instance
        file_system: FileSystem instance
        language: Language code for translations
        lang_map: Language mapping dictionary
        skip_items_by_id: Set of item IDs to skip
        drop_disabled_items_by_id: Set of item IDs with disabled drops
        ignore_drop_level_classes: Tuple of class IDs to ignore drop level
        ignore_drop_level_items_by_id: Set of item IDs to ignore drop level
        name_override_by_id: Dictionary of name overrides by ID
        conflict_resolver_map: Dictionary of conflict resolvers by class ID
        cls_map: Dictionary of class handlers
    """

    def __init__(
        self,
        relational_reader: Any,
        translation_cache: Any,
        file_system: Any,
        language: str,
        lang_map: dict[str, dict[str, str]],
        skip_items_by_id: set[str],
        drop_disabled_items_by_id: set[str],
        ignore_drop_level_classes: tuple[str, ...],
        ignore_drop_level_items_by_id: set[str],
        name_override_by_id: dict[str, dict[str, str]],
        conflict_resolver_map: dict[str, Callable[[Any, dict[str, Any], Any, Any, str], str | None]],
        cls_map: dict[str, tuple[Callable[..., bool], ...]],
        *,
        relational_reader_english: Any | None = None,
        process_base_item_type: Callable[[Any, dict[str, Any], bool], None] | None = None,
        process_purchase_costs: Callable[[Any, dict[str, Any]], None] | None = None,
        image_init: Callable[[Any], None] | None = None,
        write_dds: Callable[[Any, str, Any], None] | None = None,
        img_path: str | None = None,
    ):
        """
        Initialize data extractor.

        Args:
            relational_reader: RelationalReader instance
            translation_cache: TranslationFileCache instance
            file_system: FileSystem instance
            language: Language code
            lang_map: Language mapping dictionary
            skip_items_by_id: Set of item IDs to skip
            drop_disabled_items_by_id: Set of item IDs with disabled drops
            ignore_drop_level_classes: Tuple of class IDs to ignore drop level
            ignore_drop_level_items_by_id: Set of item IDs to ignore drop level
            name_override_by_id: Dictionary of name overrides by ID
            conflict_resolver_map: Dictionary of conflict resolvers by class ID
            cls_map: Dictionary of class handlers
            relational_reader_english: Optional RelationalReader for English language
            process_base_item_type: Optional function to process base item type
            process_purchase_costs: Optional function to process purchase costs
            image_init: Optional function to initialize image storage
            write_dds: Optional function to write DDS files
            img_path: Optional path for image storage
        """
        self.rr = relational_reader
        self.rr2 = relational_reader_english
        self.tc = translation_cache
        self.file_system = file_system
        self.language = language
        self.lang_map = lang_map
        self.skip_items_by_id = skip_items_by_id
        self.drop_disabled_items_by_id = drop_disabled_items_by_id
        self.ignore_drop_level_classes = ignore_drop_level_classes
        self.ignore_drop_level_items_by_id = ignore_drop_level_items_by_id
        self.name_override_by_id = name_override_by_id
        self.conflict_resolver_map = conflict_resolver_map
        self.cls_map = cls_map
        self._img_path = img_path

        # Optional callbacks
        self._process_base_item_type = (
            process_base_item_type or (lambda bit, ib, not_new_map=True: None)  # type: ignore[misc]
        )
        self._process_purchase_costs = process_purchase_costs or (lambda bit, ib: None)
        self._image_init = image_init or (lambda args: None)
        self._write_dds = write_dds or (lambda data, out_path, parsed_args: None)

    def parse_class_filter(self, parsed_args: Any) -> list[str]:
        """
        Parse class filter from parsed arguments.

        Args:
            parsed_args: Parsed command-line arguments

        Returns:
            List of class names to filter
        """
        if parsed_args.item_class_id:
            return [
                self.rr["ItemClasses.dat"].index["Id"][cls]["Name"]  # type: ignore[index]
                for cls in parsed_args.item_class_id
            ]
        elif parsed_args.item_class:
            self.rr["ItemClasses.dat"].build_index("Name")
            return [
                self.rr["ItemClasses.dat"].index["Name"][cls][0]["Name"]  # type: ignore[index]
                for cls in parsed_args.item_class
            ]
        else:
            return []

    def item_column_index_filter(
        self,
        column_id: str,
        arg_list: list[str],
    ) -> list[Any]:
        """
        Filter items by column index.

        Args:
            column_id: Column ID to filter by
            arg_list: List of values to filter

        Returns:
            List of filtered items
        """
        self.rr["BaseItemTypes.dat"].build_index(column_id)
        items = []
        for arg in arg_list:
            try:
                items.extend(self.rr["BaseItemTypes.dat"].index[column_id][arg])
            except KeyError:
                console(f'Item with {column_id} "{arg}" not found', msg=Msg.error)
        return items

    def process_name_conflicts(
        self,
        infobox: dict[str, Any],
        base_item_type: Any,
        language: str,
    ) -> str | None:
        """
        Process name conflicts for items.

        Args:
            infobox: Infobox dictionary to update
            base_item_type: Base item type data
            language: Language code

        Returns:
            Resolved name string or None if conflict cannot be resolved
        """
        rr = self.rr2 if language != self.language else self.rr
        # Get the base item of other language
        base_item_type_lang = rr["BaseItemTypes.dat"][base_item_type.rowid]  # type: ignore[index]

        name = base_item_type_lang["Name"]  # type: ignore[index]
        cls_id = base_item_type_lang["ItemClassesKey"]["Id"]  # type: ignore[index]
        m_id = base_item_type_lang["Id"]  # type: ignore[index]
        appendix = self.name_override_by_id.get(language, {}).get(m_id)

        if appendix is not None:
            name += appendix
            infobox["inventory_icon"] = name
        elif (
            cls_id == "Map"
            or len(
                rr["BaseItemTypes.dat"].index["Name"][name]  # type: ignore[index]
                + rr["Prophecies.dat"].index["Name"][name]  # type: ignore[index]
            )
            > 1
        ):
            resolver = self.conflict_resolver_map.get(cls_id)

            if resolver:
                name = resolver(self, infobox, base_item_type_lang, rr, language)  # type: ignore[call-arg]
                if name is None:
                    console(
                        'Unresolved ambiguous item "{}" with name "{}". Skipping'.format(
                            m_id, infobox.get("name", "unknown")
                        ),
                        msg=Msg.error,
                    )
                    return None
            else:
                console(
                    'Unresolved ambiguous item "{}" with name "{}". Skipping'.format(
                        m_id, infobox.get("name", "unknown")
                    ),
                    msg=Msg.error,
                )
                console(
                    f'No name conflict handler defined for item class id "{cls_id}"',
                    msg=Msg.error,
                )
                return None

        return str(name)  # type: ignore[arg-type]

    def format_map_name(
        self,
        base_item_type: Any,
        map_series: Any,
        language: str | None = None,
    ) -> str:
        """
        Format map name.

        Args:
            base_item_type: Base item type data
            map_series: Map series data
            language: Optional language code (defaults to instance language)

        Returns:
            Formatted map name
        """
        if language is None:
            language = self.language
        if "Harbinger" in base_item_type["Id"]:  # type: ignore[index]
            return "{} ({}) ({})".format(
                base_item_type["Name"],  # type: ignore[index]
                self.lang_map[language][re.sub(r"^.*Harbinger", "", base_item_type["Id"])],  # type: ignore[index]
                map_series["Name"],  # type: ignore[index]
            )
        else:
            return "{} ({})".format(
                base_item_type["Name"],  # type: ignore[index]
                map_series["Name"],  # type: ignore[index]
            )

    def get_map_series(self, parsed_args: Any) -> Any | bool:
        """
        Get map series from parsed arguments.

        Args:
            parsed_args: Parsed command-line arguments

        Returns:
            Map series data or False if invalid
        """
        self.rr["MapSeries.dat"].build_index("Id")
        self.rr["MapSeries.dat"].build_index("Name")
        if parsed_args.map_series_id is not None:
            try:
                map_series = self.rr["MapSeries.dat"].index["Id"][parsed_args.map_series_id]  # type: ignore[index]
            except (IndexError, KeyError):
                console("Invalid map series id", msg=Msg.error)
                return False
        elif parsed_args.map_series is not None:
            try:
                map_series = self.rr["MapSeries.dat"].index["Name"][parsed_args.map_series][0]  # type: ignore[index]
            except (IndexError, KeyError):
                console("Invalid map series name", msg=Msg.error)
                return False
        else:
            map_series = self.rr["MapSeries.dat"][-1]
            console(
                f'No map series specified, using latest: "{map_series["Name"]}"',  # type: ignore[index]
                msg=Msg.warning,
            )

        return map_series

    def export_items(
        self,
        parsed_args: Any,
        items: list[Any],
    ) -> ExporterResult:
        """
        Export items to wiki format.

        Args:
            parsed_args: Parsed command-line arguments
            items: List of items to export

        Returns:
            ExporterResult instance
        """
        classes = self.parse_class_filter(parsed_args)
        if classes:
            items = [
                item
                for item in items
                if item["ItemClassesKey"]["Name"] in classes  # type: ignore[index]
            ]

        console(f"Found {len(items)} items. Removing disabled items...")
        items = [
            base_item_type
            for base_item_type in items
            if base_item_type["Id"] not in self.skip_items_by_id  # type: ignore[index]
        ]
        console(f"{len(items)} items left for processing.")

        console("Loading additional files - this may take a while...")
        self._image_init(parsed_args)

        r = ExporterResult()
        self.rr["BaseItemTypes.dat"].build_index("Name")
        self.rr["Prophecies.dat"].build_index("Name")
        self.rr["MapPurchaseCosts.dat"].build_index("Tier")

        if self.language != "English" and parsed_args.english_file_link:
            if self.rr2 is None:
                console("English RelationalReader not available", msg=Msg.error)
                return r
            self.rr2["BaseItemTypes.dat"].build_index("Name")
            self.rr2["Prophecies.dat"].build_index("Name")

        console("Processing item information...")

        for base_item_type in items:
            name = base_item_type["Name"]  # type: ignore[index]
            cls_id = base_item_type["ItemClassesKey"]["Id"]  # type: ignore[index]
            m_id = base_item_type["Id"]  # type: ignore[index]

            infobox: OrderedDict[str, Any] = OrderedDict()
            self._process_base_item_type(base_item_type, infobox, not_new_map=True)  # type: ignore[call-arg]
            self._process_purchase_costs(base_item_type, infobox)  # type: ignore[call-arg]

            funcs = self.cls_map.get(cls_id)
            if funcs:
                fail = False
                for f in funcs:
                    if not f(self, infobox, base_item_type):  # type: ignore[call-arg]
                        fail = True
                        console(
                            f'Required extra info for item "{name}" with class id '
                            f'"{cls_id}" not found. Skipping.',
                            msg=Msg.error,
                        )
                        break
                if fail:
                    continue

            # Handle items with duplicate name entries
            # Maps must be handled in any case due to unique naming style of pages
            page = self.process_name_conflicts(infobox, base_item_type, self.language)
            if page is None:
                continue
            if self.language != "English" and parsed_args.english_file_link:
                icon = self.process_name_conflicts(infobox, base_item_type, "English")
                key = "card_art" if cls_id == "DivinationCard" else "inventory_icon"

                if icon:
                    infobox[key] = icon
                else:
                    if self.rr2 is None:
                        continue
                    infobox[key] = self.rr2["BaseItemTypes.dat"][base_item_type.rowid]["Name"]  # type: ignore[index]

            # Putting this last since it's usually manually added
            if m_id in self.drop_disabled_items_by_id:
                infobox["drop_enabled"] = False

            inventory_icon = infobox.get("inventory_icon") or page
            if ":" in inventory_icon:
                infobox["inventory_icon"] = inventory_icon.replace(":", "")

            cond = ItemWikiCondition(
                data=infobox,
                cmdargs=parsed_args,
            )

            r.add_result(
                text=cond,
                out_file=f"item_{page}.txt",
                wiki_page=[
                    {
                        "page": page,
                        "condition": cond,
                    }
                ],
                wiki_message="Item exporter",
            )

            if parsed_args.store_images:
                if not base_item_type["ItemVisualIdentityKey"]["DDSFile"]:  # type: ignore[index]
                    warnings.warn(
                        f'Missing 2d art inventory icon for item "{name}"',
                        stacklevel=2,
                    )
                    continue

                if self._img_path is None:
                    continue

                self._write_dds(  # type: ignore[call-arg]
                    self.file_system.get_file(
                        base_item_type["ItemVisualIdentityKey"]["DDSFile"]  # type: ignore[index]
                    ),
                    os.path.join(
                        self._img_path,
                        (infobox.get("inventory_icon") or page) + " inventory icon.dds",
                    ),
                    parsed_args,
                )

        return r

