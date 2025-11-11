"""Extract class attributes from mixins and move to main ItemsParser class"""

import os

# Read all mixins and extract class attributes
mixins_dir = "PyPoE/cli/exporter/wiki/parsers/item/mixins/"
all_attrs = {}

for filename in os.listdir(mixins_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        filepath = os.path.join(mixins_dir, filename)
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        # Find class attributes (between 'class' and first 'def')
        in_attrs = False
        attr_lines = []
        for _i, line in enumerate(lines):
            if "class " in line and "Mixin" in line:
                in_attrs = True
                continue
            if in_attrs and line.strip().startswith("def "):
                break  # First method found
            if in_attrs and line.strip():
                attr_lines.append(line)

        if attr_lines:
            all_attrs[filename] = attr_lines

            # Remove attributes from mixin, keep only methods
            # Find where class definition ends (first def)
            class_start = None
            first_def = None
            for i, line in enumerate(lines):
                if "class " in line and "Mixin" in line:
                    class_start = i
                if class_start is not None and line.strip().startswith("def "):
                    first_def = i
                    break

            # Remove attr lines
            if class_start is not None and first_def is not None:
                new_lines = lines[: class_start + 1] + [lines[class_start + 1]] + lines[first_def:]
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                print(f"Cleaned {filename}: removed {len(attr_lines)} attribute lines")

# Now add all attributes to parser.py
with open("PyPoE/cli/exporter/wiki/parsers/item/parser.py", encoding="utf-8") as f:
    parser_lines = f.readlines()

# Find where to insert attributes (after class definition line and docstring/slots)
insert_pos = None
for i, line in enumerate(parser_lines):
    if line.strip().startswith("def __init__"):
        insert_pos = i
        break

if insert_pos:
    # Insert all attributes before __init__
    attr_block = ["    # Class attributes from mixins\n"]
    for filename, attr_lines in all_attrs.items():
        attr_block.append(f"    # From {filename}\n")
        attr_block.extend(attr_lines)
        attr_block.append("\n")

    new_parser_lines = parser_lines[:insert_pos] + attr_block + parser_lines[insert_pos:]
    with open("PyPoE/cli/exporter/wiki/parsers/item/parser.py", "w", encoding="utf-8") as f:
        f.writelines(new_parser_lines)
    print(f"\nAdded {len(attr_block)} lines of attributes to parser.py before __init__")

print("\nDone! All class attributes moved to parser.py")
