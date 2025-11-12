"""
Item Wiki Exporter.

Handles exporting items to wiki format.
Extracted from ExportsMixin for better separation of concerns.

This class uses composition instead of inheritance, making it easier to test
and maintain.
"""

import os
import warnings
from collections import OrderedDict, defaultdict
from collections.abc import Callable
from typing import Any

from PyPoE.cli.core import Msg, console
from PyPoE.cli.exporter.wiki.handler import ExporterResult
from PyPoE.cli.exporter.wiki.parsers.item.base import MapItemWikiCondition


class ItemWikiExporter:
    """
    Exports items to wiki format.

    This class handles exporting items (especially maps) to wiki format,
    including image processing and formatting.

    Attributes:
        rr: RelationalReader instance for data access
        rr2: RelationalReader instance for English language (optional)
        tc: TranslationFileCache instance
        file_system: FileSystem instance
        language: Language code
        lang_map: Language mapping dictionary
        map_colors: Map color configuration
        map_release_version: Map release version mapping
    """

    def __init__(
        self,
        relational_reader: Any,
        translation_cache: Any,
        file_system: Any,
        language: str,
        lang_map: dict[str, dict[str, str]],
        map_colors: dict[str, str],
        map_release_version: dict[str, str],
        *,
        relational_reader_english: Any | None = None,
        image_init: Callable[[Any], None] | None = None,
        write_dds: Callable[[Any, str, Any], None] | None = None,
        format_map_name: Callable[[Any, Any | None, str | None], str] | None = None,
        get_map_series: Callable[[Any], Any] | None = None,
        process_base_item_type: Callable[[Any, dict[str, Any], bool], None] | None = None,
        process_purchase_costs: Callable[[Any, dict[str, Any]], None] | None = None,
        type_map: Callable[[dict[str, Any], Any], None] | None = None,
        img_path: str | None = None,
    ):
        """
        Initialize wiki exporter.

        Args:
            relational_reader: RelationalReader instance
            translation_cache: TranslationFileCache instance
            file_system: FileSystem instance
            language: Language code
            lang_map: Language mapping dictionary
            map_colors: Map color configuration
            map_release_version: Map release version mapping
            relational_reader_english: Optional RelationalReader for English language
            image_init: Optional function to initialize image storage
            write_dds: Optional function to write DDS files
            format_map_name: Optional function to format map names
            get_map_series: Optional function to get map series
            process_base_item_type: Optional function to process base item type
            process_purchase_costs: Optional function to process purchase costs
            type_map: Optional function to process map type data
            img_path: Optional path for image storage
        """
        self.rr = relational_reader
        self.rr2 = relational_reader_english
        self.tc = translation_cache
        self.file_system = file_system
        self.language = language
        self.lang_map = lang_map
        self.map_colors = map_colors
        self.map_release_version = map_release_version
        self._img_path = img_path

        # Optional callbacks (injected dependencies)
        self._image_init = image_init or (lambda args: None)
        self._write_dds = write_dds or (lambda data, out_path, parsed_args: None)
        self._format_map_name = format_map_name or self._default_format_map_name
        self._get_map_series = get_map_series or (lambda args: None)
        self._process_base_item_type = (
            process_base_item_type or (lambda bit, ib, not_new_map=True: None)  # type: ignore[misc]
        )
        self._process_purchase_costs = process_purchase_costs or (lambda source, ib: None)
        self._type_map = type_map or (lambda ib, bit: None)

    def _default_format_map_name(
        self,
        base_item_type: Any,
        map_series: Any | None,
        language: str | None = None,
    ) -> str:
        """Default implementation of format_map_name."""
        return str(base_item_type["Name"])  # type: ignore[no-any-return]

    def export_map_icons(self, parsed_args: Any) -> ExporterResult:
        """
        Export map icons to files.

        Args:
            parsed_args: Parsed command-line arguments

        Returns:
            ExporterResult instance
        """
        r = ExporterResult()

        if not parsed_args.store_images or not parsed_args.convert_images:
            console(
                "Image storage options must be specified for this function",
                msg=Msg.error,
            )
            return r

        map_series = self._get_map_series(parsed_args)
        if map_series is False:
            return r

        # base images
        self._image_init(parsed_args)
        if self._img_path is None:
            console("Image path not set", msg=Msg.error)
            return r

        base_ico = os.path.join(self._img_path, "Base.dds")

        self._write_dds(  # type: ignore[call-arg]
            self.file_system.get_file(map_series["BaseIcon_DDSFile"]),  # type: ignore[index]
            base_ico,
            parsed_args,
        )

        for atlas_node in self.rr["AtlasNode.dat"]:
            if not atlas_node["ItemVisualIdentityKey"]["DDSFile"]:
                warnings.warn(
                    f"Missing 2d art inventory icon at index {atlas_node.index}",
                    stacklevel=2,
                )
                continue

            name = atlas_node["WorldAreasKey"]["Name"]

            ico = os.path.join(self._img_path, name + ".dds")

            self._write_dds(  # type: ignore[call-arg]
                self.file_system.get_file(atlas_node["ItemVisualIdentityKey"]["DDSFile"]),  # type: ignore[index]
                ico,
                parsed_args,
            )

            if "Unique" not in atlas_node["WorldAreasKey"]["Id"]:
                ico = ico.replace(".dds", ".png")
                for name_color, color in self.map_colors.items():
                    # -tint
                    os.system(
                        '''magick convert "{}" -fill rgb({}) -tint 100 "{}"'''.format(
                            ico, color, ico.replace(".png", f" {name_color}.png")
                        )
                    )

        return r

    def export_map(self, parsed_args: Any) -> ExporterResult:
        """
        Export maps to wiki format.

        Args:
            parsed_args: Parsed command-line arguments

        Returns:
            ExporterResult instance
        """
        r = ExporterResult()

        map_series = self._get_map_series(parsed_args)
        if map_series is False or map_series is None:
            return r

        if map_series.rowid <= 3:  # type: ignore[union-attr]
            console(
                "Only Betrayal and newer map series are supported by this function",
                msg=Msg.error,
            )
            return r

        # Store whether this is the latest map series to determine later whether
        # atlas info should be stored
        latest = map_series == self.rr["MapSeries.dat"][-1]

        self.rr["AtlasNode.dat"].build_index("MapsKey")
        names = set(parsed_args.name)
        map_series_tiers: dict[Any, Any] = {}
        for row in self.rr["MapSeriesTiers.dat"]:
            maps = row["MapsKey"]
            for atlas_node in self.rr["AtlasNode.dat"].index["MapsKey"][maps]:
                # This excludes the unique maps
                if atlas_node["ItemVisualIdentityKey"]["IsAtlasOfWorldsMapIcon"]:
                    break
            else:
                # Maps that are no longer on the atlas such as guardian maps
                # or harbinger
                atlas_node = None
            if names and maps["BaseItemTypesKey"]["Name"] in names or not names:
                map_series_tiers[row] = atlas_node

        if parsed_args.store_images:
            if not parsed_args.convert_images:
                console(
                    "Map images need to be processed and require conversion option to be enabled.",
                    msg=Msg.error,
                )
                return r

            self._image_init(parsed_args)
            if self._img_path is None:
                console("Image path not set", msg=Msg.error)
                return r

            base_ico = os.path.join(self._img_path, "Map base icon.dds")

            self._write_dds(  # type: ignore[call-arg]
                self.file_system.get_file(map_series["BaseIcon_DDSFile"]),  # type: ignore[index]
                base_ico,
                parsed_args,
            )

            base_ico = base_ico.replace(".dds", ".png")

        #
        self.rr["MapSeriesTiers.dat"].build_index("MapsKey")
        self.rr["MapPurchaseCosts.dat"].build_index("Tier")
        self.rr["UniqueMaps.dat"].build_index("ItemVisualIdentityKey")

        for row, atlas_node in map_series_tiers.items():
            maps = row["MapsKey"]
            base_item_type = maps["BaseItemTypesKey"]
            if map_series is None:
                console("Map series is None", msg=Msg.error)
                continue
            name = self._format_map_name(base_item_type, map_series)  # type: ignore[call-arg]
            tier = row["{}Tier".format(map_series["Id"])]  # type: ignore[index]

            # Base info
            infobox: OrderedDict[str, Any] = OrderedDict()
            self._process_base_item_type(base_item_type, infobox, not_new_map=False)  # type: ignore[call-arg]
            self._type_map(infobox, base_item_type)  # type: ignore[call-arg]

            # Overrides
            infobox["map_tier"] = tier
            infobox["map_area_level"] = 67 + tier
            # Map start dropping at one tier lower, with the exception of
            # tier 1 maps which can drop rather early
            infobox["drop_level"] = 66 + tier if tier > 1 else 58
            infobox["unique_map_area_level"] = 67 + tier
            infobox["map_series"] = map_series["Name"]
            infobox["inventory_icon"] = name

            if self.language != "English" and parsed_args.english_file_link:
                if self.rr2 is None:
                    console("English RelationalReader not available", msg=Msg.error)
                    return r
                infobox["inventory_icon"] = self._format_map_name(  # type: ignore[call-arg]
                    self.rr2["BaseItemTypes.dat"][base_item_type.rowid],  # type: ignore[index]
                    self.rr2["MapSeries.dat"][map_series.rowid],  # type: ignore[index,union-attr]
                    "English",
                )
            else:
                infobox["inventory_icon"] = name

            if atlas_node is not None:
                if latest:
                    infobox["atlas_x"] = atlas_node["X"]  # type: ignore[index]
                    infobox["atlas_y"] = atlas_node["Y"]  # type: ignore[index]
                    infobox["atlas_region_id"] = atlas_node["AtlasRegionsKey"]["Id"]  # type: ignore[index]

                    minimum = 0
                    connections: defaultdict[str, list[str]] = defaultdict(
                        lambda: ["False" for _i in range(0, 5)]
                    )
                    for i in range(0, 5):
                        tier_val = atlas_node[f"Tier{i}"]  # type: ignore[index]
                        infobox[f"atlas_x{i}"] = atlas_node[f"X{i}"]  # type: ignore[index]
                        infobox[f"atlas_y{i}"] = atlas_node[f"Y{i}"]  # type: ignore[index]
                        infobox[f"atlas_map_tier{i}"] = tier_val
                        if tier_val and minimum == 0:
                            minimum = i

                        for atlas_node2 in atlas_node[f"AtlasNodeKeys{i}"]:  # type: ignore[index]
                            ivi = atlas_node2["ItemVisualIdentityKey"]  # type: ignore[index]
                            if ivi["IsAtlasOfWorldsMapIcon"]:  # type: ignore[index]
                                key = self._format_map_name(  # type: ignore[call-arg]
                                    atlas_node2["MapsKey"]["BaseItemTypesKey"],  # type: ignore[index]
                                    map_series,
                                )
                            else:
                                key = "{} ({})".format(
                                    self.rr["UniqueMaps.dat"].index["ItemVisualIdentityKey"][ivi][  # type: ignore[index]
                                        "WordsKey"
                                    ]["Text"],  # type: ignore[index]
                                    map_series["Name"],
                                )
                            connections[key][i] = "True"

                    infobox["atlas_region_minimum"] = minimum
                    for i, (k, v) in enumerate(connections.items(), start=1):
                        infobox[f"atlas_connection{i}_target"] = k
                        infobox[f"atlas_connection{i}_tier"] = ", ".join(v)

                infobox["flavour_text"] = (
                    atlas_node["FlavourTextKey"]["Text"].replace("\n", "<br>").replace("\r", "")  # type: ignore[index]
                )

            if 0 < tier < 17:
                self._process_purchase_costs(  # type: ignore[call-arg]
                    self.rr["MapPurchaseCosts.dat"].index["Tier"][tier], infobox
                )

            if map_series is not None:
                infobox["release_version"] = self.map_release_version[map_series["Id"]]  # type: ignore[index]

            if not latest:
                infobox["drop_enabled"] = "False"

            cond = MapItemWikiCondition(
                data=infobox,
                cmdargs=parsed_args,
            )

            r.add_result(
                text=cond,
                out_file=f"map_{name}.txt",
                wiki_page=[
                    {
                        "page": name,
                        "condition": cond,
                    }
                ],
                wiki_message="Map exporter",
            )

            if parsed_args.store_images:
                if atlas_node is None or not atlas_node["ItemVisualIdentityKey"]["DDSFile"]:
                    warnings.warn(
                        'Missing 2d art inventory icon for item "{}"'.format(
                            base_item_type["Name"]
                        ),
                        stacklevel=2,
                    )
                    continue

                if self._img_path is None:
                    continue

                ico = os.path.join(self._img_path, name + " inventory icon.dds")

                self._write_dds(  # type: ignore[call-arg]
                    self.file_system.get_file(atlas_node["ItemVisualIdentityKey"]["DDSFile"]),  # type: ignore[index]
                    ico,
                    parsed_args,
                )

                ico = ico.replace(".dds", ".png")

                color = None
                if 5 < tier <= 10:
                    color = self.map_colors["mid tier"]
                elif 10 < tier <= 15:
                    color = self.map_colors["high tier"]
                if color:
                    os.system(
                        f'''magick convert "{ico}" -fill rgb({color}) -colorize 100 "{ico}"'''
                    )

                os.system(f'magick composite -gravity center "{ico}" "{base_ico}" "{ico}"')

        return r

    def export_unique_map(self, parsed_args: Any) -> ExporterResult:
        """
        Export unique maps to wiki format.

        Args:
            parsed_args: Parsed command-line arguments

        Returns:
            ExporterResult instance

        Note:
            This method is currently not implemented.
        """
        # Implementation from ExportsMixin (currently empty)
        return ExporterResult()

