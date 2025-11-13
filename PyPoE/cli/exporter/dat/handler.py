"""
.dat export base handler

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/dat/handler.py                                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

.dat export base handler

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from typing import Any

# self
from PyPoE.cli.core import Msg, console
from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.util import get_content_path
from PyPoE.poe.constants import VERSION
from PyPoE.poe.file import dat
from PyPoE.poe.file.file_system import FileSystem

# =============================================================================
# Globals
# =============================================================================

__all__ = []

# =============================================================================
# Classes
# =============================================================================


class DatExportHandler:
    def add_default_arguments(self, parser):
        """

        :param parser:
        :type parser: argparse.ArgumentParser

        :return:
        """
        parser.set_defaults(func=self.handle)
        parser.add_argument(
            "--files",
            "--file",
            help=".dat files to export",
            nargs="*",
        )

        parser.add_argument(
            "-lang",
            "--language",
            help="Language subdirectory to use",
            dest="language",
            default=None,
        )

    def handle(self, args: Any) -> None:
        """
        Handle DAT export command.

        Validates and processes file list, loads specifications,
        and prepares arguments for export operations.

        Args:
            args: Parsed command-line arguments
        """
        ver = config.get_option("version")

        if ver != VERSION.DEFAULT:
            console(f"Loading specification for {ver}")
            dat.set_default_spec(version=ver)  # type: ignore[attr-defined]

        spec = dat._default_spec  # type: ignore[attr-defined]
        if args.files is None:
            args.files = list(spec)
        else:
            files_set = set()

            for file_name in args.files:
                if file_name in spec:
                    files_set.add(file_name)
                elif not file_name.endswith(".dat"):
                    file_name += ".dat"
                    if file_name not in spec:
                        console(
                            f'.dat file "{file_name}" is not in specification. Removing.',
                            msg=Msg.error,
                        )
                    else:
                        files_set.add(file_name)

            files = list(files_set)
            files.sort()
            args.files = files

        args.spec = spec

    def _read_dat_files(self, args: Any, prefix: str = "") -> dict[str, Any]:
        """
        Read DAT files from file system.

        Loads DAT files from the game's file system, handling language
        subdirectories and missing files gracefully.

        Args:
            args: Parsed command-line arguments
            prefix: Prefix for console messages

        Returns:
            Dictionary mapping file names to DatFile instances
        """
        path = get_content_path()

        console(prefix + "Loading file system...")

        file_system = FileSystem(root_path=path)

        console(prefix + "Reading .dat files")

        dat_files = {}
        lang = args.language or config.get_option("language")
        dir_path = "Data/"
        if lang != "English":
            # ggpk_data = index.get_dir_record("Data/%s" % lang)
            dir_path = f"Data/{lang}/"
        remove = []
        for name in args.files:
            file_path = dir_path + name
            try:
                data = file_system.get_file(file_path)
            except FileNotFoundError:
                console(f'Skipping "{file_path}" (missing)', msg=Msg.warning)
                remove.append(name)
                continue

            df = dat.DatFile(name)

            df.read(file_path_or_raw=data, use_dat_value=False)

            dat_files[name] = df

        for file_name in remove:
            args.files.remove(file_name)

        return dat_files


# =============================================================================
# Functions
# =============================================================================
