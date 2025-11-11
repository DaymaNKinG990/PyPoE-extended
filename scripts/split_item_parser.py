"""Split item/parser.py into mixin-based structure"""

import re

with open("PyPoE/cli/exporter/wiki/parsers/item/parser.py", encoding="utf-8") as f:
    lines = f.readlines()

# Find where class starts (line 42) and all method boundaries
class_start = 41  # 0-indexed
methods = []
for i in range(class_start, len(lines)):
    if re.match(r"    def \w+", lines[i]):
        match = re.match(r"    def (\w+)", lines[i])
        if match:
            methods.append((match.group(1), i))

# Add end marker
methods.append(("__END__", len(lines)))

# Categorize methods with their line ranges
categories = {
    "skills": [],
    "types": [],
    "extras": [],
    "conflicts": [],
    "exports": [],
    "utils": [],
}

for i, (name, start_line) in enumerate(methods[:-1]):
    end_line = methods[i + 1][1]
    method_lines = lines[start_line:end_line]

    if name == "__init__":
        # Skip __init__ for now, will handle separately
        continue
    elif "_skill" in name:
        categories["skills"].append((name, start_line, end_line, method_lines))
    elif "_extra" in name:
        categories["extras"].append((name, start_line, end_line, method_lines))
    elif name.startswith("_conflict_"):
        categories["conflicts"].append((name, start_line, end_line, method_lines))
    elif name.startswith("export"):
        categories["exports"].append((name, start_line, end_line, method_lines))
    elif name.startswith("_type_"):
        categories["types"].append((name, start_line, end_line, method_lines))
    else:
        categories["utils"].append((name, start_line, end_line, method_lines))

# Extract imports and class fields (lines before __init__)
imports_and_fields = lines[:1123]  # Everything before __init__

# Extract __init__ method
init_start = 1122  # 0-indexed, line 1123
init_end = 1140
init_lines = lines[init_start:init_end]

print("Categorization summary:")
for cat, items in categories.items():
    total_lines = sum(end - start for _, start, end, _ in items)
    print(f"  {cat}: {len(items)} methods, ~{total_lines} lines")

# ===== Create mixin files =====


def create_mixin_file(filename, class_name, methods_data, extra_imports=""):
    header = f'''"""
{class_name} mixin for ItemsParser.

Contains {class_name.replace("Mixin", "").lower()}-related methods.
"""

# =============================================================================
# Imports
# =============================================================================

{extra_imports}

# =============================================================================
# Classes
# =============================================================================


class {class_name}:
    """Mixin providing {class_name.replace("Mixin", "").lower()} functionality for ItemsParser."""
'''

    with open(
        f"PyPoE/cli/exporter/wiki/parsers/item/mixins/{filename}", "w", encoding="utf-8"
    ) as f:
        f.write(header)
        for _name, _start, _end, method_lines in methods_data:
            f.writelines(method_lines)

    return len(methods_data), sum(end - start for _, start, end, _ in methods_data)


# Create each mixin
stats = {}

stats["skills"] = create_mixin_file(
    "skills.py",
    "SkillsMixin",
    categories["skills"],
    extra_imports="from PyPoE.poe.sim.formula import gem_stat_requirement, GemTypes",
)

stats["types"] = create_mixin_file("types.py", "TypesMixin", categories["types"], extra_imports="")

stats["extras"] = create_mixin_file(
    "extras.py",
    "ExtrasMixin",
    categories["extras"],
    extra_imports="""from collections import OrderedDict, defaultdict
from PyPoE.poe.constants import RARITY""",
)

stats["conflicts"] = create_mixin_file(
    "conflicts.py", "ConflictsMixin", categories["conflicts"], extra_imports=""
)

stats["exports"] = create_mixin_file(
    "exports.py",
    "ExportsMixin",
    categories["exports"],
    extra_imports="""import os
from collections import OrderedDict
from PyPoE.cli.core import console, Msg
from PyPoE.cli.exporter.wiki.handler import ExporterResult""",
)

stats["utils"] = create_mixin_file(
    "utils.py",
    "UtilsMixin",
    categories["utils"],
    extra_imports="""import re
from collections import OrderedDict
from PyPoE.cli.exporter.wiki import parser""",
)

print("\nCreated mixin files:")
for name, (count, line_count) in stats.items():
    print(f"  {name}.py: {count} methods, {line_count} lines")

# ===== Create mixins/__init__.py =====
mixins_init = '''"""
Mixins for ItemsParser.

Exports all mixin classes for easy importing.
"""

from PyPoE.cli.exporter.wiki.parsers.item.mixins.skills import SkillsMixin
from PyPoE.cli.exporter.wiki.parsers.item.mixins.types import TypesMixin
from PyPoE.cli.exporter.wiki.parsers.item.mixins.extras import ExtrasMixin
from PyPoE.cli.exporter.wiki.parsers.item.mixins.conflicts import ConflictsMixin
from PyPoE.cli.exporter.wiki.parsers.item.mixins.exports import ExportsMixin
from PyPoE.cli.exporter.wiki.parsers.item.mixins.utils import UtilsMixin

__all__ = [
    'SkillsMixin',
    'TypesMixin',
    'ExtrasMixin',
    'ConflictsMixin',
    'ExportsMixin',
    'UtilsMixin',
]
'''

with open("PyPoE/cli/exporter/wiki/parsers/item/mixins/__init__.py", "w", encoding="utf-8") as f:
    f.write(mixins_init)

print("\nCreated mixins/__init__.py")

# ===== Create new parser.py =====
# Extract class definition and fields (lines 42-1122)
class_header_and_fields = lines[class_start:init_start]

new_parser = '''"""
Items wiki parser

Contains ItemsParser class for exporting items to wiki format.
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import re
import warnings
import os
from collections import OrderedDict, defaultdict
from functools import partialmethod

# Self
from PyPoE.poe.constants import RARITY
from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.ot import OTFile
from PyPoE.poe.sim.formula import gem_stat_requirement, GemTypes
from PyPoE.cli.core import console, Msg
from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.wiki.handler import ExporterResult
from PyPoE.cli.exporter.wiki import parser
from PyPoE.cli.exporter.wiki.parsers.skill import SkillParserShared
from PyPoE.cli.exporter.wiki.parsers.item.base import (
    _apply_column_map,
    _type_factory,
    _simple_conflict_factory,
    ItemWikiCondition,
    MapItemWikiCondition,
    UniqueMapItemWikiCondition,
)

# Mixins
from PyPoE.cli.exporter.wiki.parsers.item.mixins import (
    SkillsMixin,
    TypesMixin,
    ExtrasMixin,
    ConflictsMixin,
    ExportsMixin,
    UtilsMixin,
)

# =============================================================================
# Classes
# =============================================================================


class ItemsParser(
    SkillsMixin,
    TypesMixin,
    ExtrasMixin,
    ConflictsMixin,
    ExportsMixin,
    UtilsMixin,
    SkillParserShared,
):
'''

with open("PyPoE/cli/exporter/wiki/parsers/item/parser_new.py", "w", encoding="utf-8") as f:
    f.write(new_parser)
    # Write class fields (before __init__)
    f.writelines(class_header_and_fields[1:])  # Skip 'class ItemsParser...' line
    # Write __init__
    f.writelines(init_lines)

print("\nCreated new parser_new.py")
print("\nAll files created successfully!")
