"""
ExportsMixin for ItemsParser.

Contains exports-related methods only.
Class attributes are defined in the main ItemsParser class.
"""

# =============================================================================
# Imports
# =============================================================================

import os
import warnings
from collections import OrderedDict, defaultdict
from typing import TYPE_CHECKING, Any

from PyPoE.cli.core import Msg, console
from PyPoE.cli.exporter.wiki.handler import ExporterResult
from PyPoE.cli.exporter.wiki.parsers.item.base import MapItemWikiCondition

# =============================================================================
# Classes
# =============================================================================


class ExportsMixin:
    """Mixin providing exports methods for ItemsParser."""

    # Type hints for attributes from parent ItemsParser class
    if TYPE_CHECKING:
        rr: Any
        rr2: Any
        tc: Any
        file_system: Any
        _parsed_args: Any
        _language: str
        _LANG: dict[str, dict[str, str]]
        _MAP_COLORS: dict[str, str]
        _MAP_RELEASE_VERSION: dict[str, str]
        _img_path: Any
        _type_map: Any

        def _image_init(self, *args: Any, **kwargs: Any) -> None: ...
        def _write_dds(self, *args: Any, **kwargs: Any) -> None: ...
        def _format_map_name(self, *args: Any, **kwargs: Any) -> str: ...
        def _get_map_series(self, *args: Any, **kwargs: Any) -> Any: ...
        def _process_base_item_type(self, *args: Any, **kwargs: Any) -> None: ...
        def _process_purchase_costs(self, *args: Any, **kwargs: Any) -> None: ...

    def export_map_icons(self, parsed_args):
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
        base_ico = os.path.join(self._img_path, "Base.dds")

        self._write_dds(
            data=self.file_system.get_file(map_series["BaseIcon_DDSFile"]),
            out_path=base_ico,
            parsed_args=parsed_args,
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

            self._write_dds(
                data=self.file_system.get_file(atlas_node["ItemVisualIdentityKey"]["DDSFile"]),
                out_path=ico,
                parsed_args=parsed_args,
            )

            if "Unique" not in atlas_node["WorldAreasKey"]["Id"]:
                ico = ico.replace(".dds", ".png")
                for name, color in self._MAP_COLORS.items():
                    # -tint
                    os.system(
                        '''magick convert "{}" -fill rgb({}) -tint 100 "{}"'''.format(
                            ico, color, ico.replace(".png", f" {name}.png")
                        )
                    )

        return r

    def export_map(self, parsed_args):
        r = ExporterResult()

        map_series = self._get_map_series(parsed_args)
        if map_series is False:
            return r

        if map_series.rowid <= 3:
            console(
                "Only Betrayal and newer map series are supported by this function", msg=Msg.error
            )
            return r

        # Store whether this is the latest map series to determine later whether
        # atlas info should be stored
        latest = map_series == self.rr["MapSeries.dat"][-1]

        self.rr["AtlasNode.dat"].build_index("MapsKey")
        names = set(parsed_args.name)
        map_series_tiers = {}
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
            base_ico = os.path.join(self._img_path, "Map base icon.dds")

            self._write_dds(
                data=self.file_system.get_file(map_series["BaseIcon_DDSFile"]),
                out_path=base_ico,
                parsed_args=parsed_args,
            )

            base_ico = base_ico.replace(".dds", ".png")

        #
        self.rr["MapSeriesTiers.dat"].build_index("MapsKey")
        self.rr["MapPurchaseCosts.dat"].build_index("Tier")
        self.rr["UniqueMaps.dat"].build_index("ItemVisualIdentityKey")

        for row, atlas_node in map_series_tiers.items():
            maps = row["MapsKey"]
            base_item_type = maps["BaseItemTypesKey"]
            name = self._format_map_name(base_item_type, map_series)
            tier = row["{}Tier".format(map_series["Id"])]

            # Base info
            infobox: OrderedDict[str, Any] = OrderedDict()
            self._process_base_item_type(base_item_type, infobox, not_new_map=False)
            self._type_map(infobox, base_item_type)

            # Overrides
            infobox["map_tier"] = tier
            infobox["map_area_level"] = 67 + tier
            # Map start dropping at one tier lower, with the exception of
            # tier 1 maps which can drop rather early
            infobox["drop_level"] = 66 + tier if tier > 1 else 58
            infobox["unique_map_area_level"] = 67 + tier
            infobox["map_series"] = map_series["Name"]
            infobox["inventory_icon"] = name

            if self._language != "English" and parsed_args.english_file_link:
                infobox["inventory_icon"] = self._format_map_name(
                    self.rr2["BaseItemTypes.dat"][base_item_type.rowid],
                    self.rr2["MapSeries.dat"][map_series.rowid],
                    "English",
                )
            else:
                infobox["inventory_icon"] = name

            if atlas_node:
                if latest:
                    infobox["atlas_x"] = atlas_node["X"]
                    infobox["atlas_y"] = atlas_node["Y"]
                    infobox["atlas_region_id"] = atlas_node["AtlasRegionsKey"]["Id"]

                    minimum = 0
                    connections: defaultdict = defaultdict(lambda: ["False" for i in range(0, 5)])
                    for i in range(0, 5):
                        tier = atlas_node[f"Tier{i}"]
                        infobox[f"atlas_x{i}"] = atlas_node[f"X{i}"]
                        infobox[f"atlas_y{i}"] = atlas_node[f"Y{i}"]
                        infobox[f"atlas_map_tier{i}"] = tier
                        if tier and minimum == 0:
                            minimum = i

                        for atlas_node2 in atlas_node[f"AtlasNodeKeys{i}"]:
                            ivi = atlas_node2["ItemVisualIdentityKey"]
                            if ivi["IsAtlasOfWorldsMapIcon"]:
                                key = self._format_map_name(
                                    atlas_node2["MapsKey"]["BaseItemTypesKey"],
                                    map_series,
                                )
                            else:
                                key = "{} ({})".format(
                                    self.rr["UniqueMaps.dat"].index["ItemVisualIdentityKey"][ivi][
                                        "WordsKey"
                                    ]["Text"],
                                    map_series["Name"],
                                )
                            connections[key][i] = "True"

                    infobox["atlas_region_minimum"] = minimum
                    for i, (k, v) in enumerate(connections.items(), start=1):
                        infobox[f"atlas_connection{i}_target"] = k
                        infobox[f"atlas_connection{i}_tier"] = ", ".join(v)

                infobox["flavour_text"] = (
                    atlas_node["FlavourTextKey"]["Text"].replace("\n", "<br>").replace("\r", "")
                )

            if 0 < tier < 17:
                self._process_purchase_costs(
                    self.rr["MapPurchaseCosts.dat"].index["Tier"][tier], infobox
                )

            """if maps['UpgradedFrom_MapsKey']:
                infobox['upgeaded_from_set1_group1_page'] = '%s (%s)' % (
                    maps['UpgradedFrom_MapsKey']['BaseItemTypesKey']['Name'],
                    map_series['Name']
                )
                infobox['upgraded_from_set1_group1_amount'] = 3"""

            infobox["release_version"] = self._MAP_RELEASE_VERSION[map_series["Id"]]

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

                ico = os.path.join(self._img_path, name + " inventory icon.dds")

                self._write_dds(
                    data=self.file_system.get_file(atlas_node["ItemVisualIdentityKey"]["DDSFile"]),
                    out_path=ico,
                    parsed_args=parsed_args,
                )

                ico = ico.replace(".dds", ".png")

                color = None
                if 5 < tier <= 10:
                    color = self._MAP_COLORS["mid tier"]
                elif 10 < tier <= 15:
                    color = self._MAP_COLORS["high tier"]
                if color:
                    os.system(
                        f'''magick convert "{ico}" -fill rgb({color}) -colorize 100 "{ico}"'''
                    )

                os.system(f'magick composite -gravity center "{ico}" "{base_ico}" "{ico}"')

        return r

    def export_unique_map(self):
        pass
