"""
Wiki Export Base Parser

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/handler.py                               |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Base classes and related functions for Wiki Export Parsers.

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import os
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from requests.exceptions import HTTPError  # type: ignore[import-untyped]

# 3rd Party
try:
    import mwclient  # type: ignore[import-untyped]
except Exception:
    mwclient = None

# self
from PyPoE import __version__
from PyPoE.cli.core import Msg, console
from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.util import fix_path
from PyPoE.cli.handler import BaseHandler

# =============================================================================
# Globals
# =============================================================================

__all__ = ["ExporterHandler", "ExporterResult", "WikiHandler"]

WIKIS = {
    "English": "pathofexile.gamepedia.com",
    "Russian": "pathofexile-ru.gamepedia.com",
    "German": "pathofexile-de.gamepedia.com",
    "French": "pathofexile-fr.gamepedia.com",
    "Spanish": "pathofexile-es.gamepedia.com",
}

# =============================================================================
# Classes
# =============================================================================


class WikiHandler:
    """
    Handler for wiki export operations.

    Manages wiki page editing, including authentication, page creation/editing,
    and error handling with retry logic.
    """

    def add_arguments(self, parser: Any) -> None:
        """
        Add command-line arguments for wiki export.

        Args:
            parser: ArgumentParser instance to add arguments to
        """
        add_parser_arguments(parser)
        parser.add_argument(
            "-w-mt",
            "--wiki-max-threads",
            dest="wiki_threads",
            help="Maximum number of threads to spawn when editing wiki",
            action="store",
            type=int,
            default=1,
        )

        parser.add_argument(
            "-w-oe",
            "--wiki-only-existing",
            dest="only_existing",
            help="Only write to existing pages and do not create new ones",
            action="store_true",
        )

        parser.add_argument(
            "-w-slp",
            "--wiki-sleep",
            dest="wiki_sleep",
            help="Time to sleep in seconds between requests",
            type=int,
            default=0,
        )

    def _error_catcher(self, *args: Any, **kwargs: Any) -> None:
        """
        Catch and retry errors when handling wiki pages.

        Handles APIError and HTTPError exceptions with retry logic.
        For HTTP 429 (rate limit), waits 30 seconds before retrying.

        Args:
            *args: Positional arguments passed to handle_page
            **kwargs: Keyword arguments passed to handle_page
        """
        fail = 1
        while fail > 0:
            try:
                self.handle_page(*args, **kwargs)
                fail = 0
            except mwclient.APIError:
                console(f"APIError occurred. Retrying - total attempts: {fail}", msg=Msg.error)
                fail += 1
            except HTTPError as e:
                if "429" in e.args[0]:
                    console(e.args[0], Msg.error)
                    console(f"Retrying in 30s- total attempts: {fail}")
                    time.sleep(30)
                    fail += 1
                else:
                    console(f"HTTPError occurred. Retrying - total attempts: {fail}", msg=Msg.error)
                    fail += 1

    def handle_page(self, *a: Any, row: dict[str, Any]) -> None:
        """
        Handle editing a single wiki page.

        Finds the appropriate wiki page, checks conditions, and edits it.
        Supports multiple page candidates and conditional editing.

        Args:
            *a: Additional positional arguments (unused)
            row: Dictionary containing wiki_page, text, wiki_message, and other data
        """
        if isinstance(row["wiki_page"], str):
            pages = [
                {"page": row["wiki_page"], "condition": None},
            ]
        else:
            pages = row["wiki_page"]
        console(
            'Scanning for wiki page candidates "{}"'.format(
                ", ".join([p["page"] for p in pages if p["page"]])  # type: ignore[misc]
            )
        )
        page_found = False
        new = False
        for pdata in pages:
            page = self.site.pages[pdata["page"]]
            if page.exists:
                condition = pdata.get("condition")
                success = True
                if condition is None:
                    console(
                        'No conditions given - page content on "{}" will be overriden'.format(
                            pdata["page"]
                        ),
                        msg=Msg.warning,
                    )
                    success = True
                elif callable(condition):
                    success = condition(page=page)
                elif isinstance(condition, Iterable):
                    for cond in condition:
                        success = cond(page=page)  # type: ignore[operator]
                        if not success:
                            break
                else:
                    raise ValueError(f'Invalid condition type "{type(condition)}"')
                if success:
                    console('All conditions met on page "{}". Editing.'.format(pdata["page"]))
                    page_found = True
                    break
                else:
                    console(
                        'One or more conditions failed on page "{}". Skipping.'.format(
                            pdata["page"]
                        ),
                        msg=Msg.warning,
                    )
            elif self.cmdargs.only_existing:
                console(
                    'Page "{}" does not exist. Bot is set to only write to '
                    "existing pages, skipping.".format(pdata["page"]),
                    msg=Msg.warning,
                )
                return
            else:
                console('Page "{}" does not exist. It will be created.'.format(pdata["page"]))
                page_found = True
                new = True
                break

        if page_found:
            text = row["text"]
            if callable(text):
                kwargs = {}
                if not new:
                    kwargs["page"] = page
                text = text(**kwargs)

            if text == page.text():
                console("No update required. Skipping.")
                return

            if self.cmdargs.dry_run:
                console(text)
            else:
                response = page.save(
                    text=text,
                    summary="PyPoE/ExporterBot/{}: {}".format(
                        __version__, self.cmdargs.wiki_message or row["wiki_message"]
                    ),
                )
                if response["result"] == "Success":
                    console(
                        "Page was edited successfully (time: {})".format(
                            response.get("newtimestamp")
                        )
                    )
                else:
                    # TODO: what happens if it fails?
                    console("Something went wrong, status code:", msg=Msg.error)
                    console(response, msg=Msg.error)
        else:
            console(
                "No wiki page candidates found, skipping this row.",
                msg=Msg.error,
            )

    def handle(self, *a: Any, mwclient: Any, result: Any, cmdargs: Any, parser: Any) -> None:
        """
        Handle wiki export command.

        Authenticates with wiki, processes results, and edits pages.
        Supports multi-threaded editing if wiki_threads > 1.

        Args:
            *a: Additional positional arguments (unused)
            mwclient: mwclient module
            result: Iterable of result rows to process
            cmdargs: Parsed command-line arguments
            parser: Parser instance
        """
        # First row is handled separately to prompt the user for his password
        url = WIKIS.get(config.get_option("language"))
        if url is None:
            console(f'There is no wiki defined for language "{cmdargs.language}"', msg=Msg.error)
            return
        self.site = mwclient.Site(url, path="/", scheme="https")

        self.site.login(
            username=cmdargs.user or input("Enter your gamepedia user name:\n"),
            password=cmdargs.password
            or input(
                "Please enter your password for the specified user\n"
                "WARNING: Password will be visible in console\n"
            ),
        )
        self.mwclient = mwclient
        self.cmdargs = cmdargs
        self.parser = parser

        if cmdargs.wiki_threads > 1:
            console("Starting thread pool...")
            tp = ThreadPoolExecutor(max_workers=cmdargs.wiki_threads)

            for row in result:
                tp.submit(
                    self._error_catcher,
                    row=row,
                )

            tp.shutdown(wait=True)
        else:
            console("Editing pages...")
            for row in result:
                self._error_catcher(row=row)
                time.sleep(cmdargs.wiki_sleep)


class ExporterHandler(BaseHandler):
    """
    Handler for exporter operations.

    Manages parsing, file writing, and wiki export operations.
    Provides wrapper functions for common export workflows.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize exporter handler.

        Args:
            *args: Additional positional arguments for BaseHandler
            **kwargs: Additional keyword arguments for BaseHandler
        """
        super().__init__(*args, **kwargs)

    def get_wrap(
        self, cls: type, func: Any, handler: Any, wiki_handler: WikiHandler | None
    ) -> Any:
        """
        Get wrapper function for export operations.

        Creates a wrapper that handles:
        - Directory validation
        - Parser initialization
        - Result processing (print/write)
        - Wiki export (if enabled)

        Args:
            cls: Parser class to instantiate
            func: Function to call for parsing
            handler: Optional handler function
            wiki_handler: Optional WikiHandler instance

        Returns:
            Wrapper function that processes export operations
        """
        def wrapper(pargs: Any, *args: Any, **kwargs: Any) -> int:
            # Check outdir, if specified:
            if hasattr(pargs, "outdir") and pargs.outdir:
                out_dir = pargs.outdir
            else:
                out_dir = config.get_option("out_dir")
            temp_dir = config.get_option("temp_dir")

            for item in (out_dir, temp_dir):
                if not os.path.exists(item):
                    console(f'Path "{item}" does not exist', msg=Msg.error)
                    return -1

            console("Reading .dat files...")
            parser = cls(base_path=temp_dir, parsed_args=pargs)

            console("Parsing...")
            if handler:
                return handler(parser, pargs, out_dir=out_dir)
            else:
                result = func(parser, pargs, *args, **kwargs)

                for item in result:
                    text = item["text"]() if callable(item["text"]) else item["text"]
                    if pargs.print:
                        console(text)

                    if pargs.write:
                        out_path = os.path.join(out_dir, fix_path(item["out_file"]))
                        console(f'Writing data to "{out_path}"...')
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(text)

                if pargs.wiki:
                    if mwclient is None:
                        try:
                            # Will raise the exception appropriately
                            __import__("")
                        except ImportError:
                            console("Run pip install -e cli", msg=Msg.error)
                        except Exception:
                            raise

                    if wiki_handler is None:
                        console("No wiki-handler defined for this function", msg=Msg.error)
                        return 0

                    console("Running wikibot...")
                    console("-" * 80)
                    wiki_handler.handle(
                        mwclient=mwclient, result=result, cmdargs=pargs, parser=parser
                    )
                    console("-" * 80)
                    console("Completed wikibot execution.")

                console("Done.")

                return 0

        return wrapper

    def add_default_subparser_filters(self, sub_parser: Any, cls: type, *args: Any, **kwargs: Any) -> None:
        """
        Add default sub parsers for id, name and rowid.

        Creates subparsers for common filtering operations:
        - id: Extract via internal IDs
        - name: Extract via visible names
        - rowid: Extract via row IDs in primary dat file

        Args:
            sub_parser: Argument parser subparser
            cls: Parser class expected to have methods:
                - by_id: Handling for ID-based searching
                - by_name: Handling for name-based searching
                - by_rowid: Handling for rowid-based searching
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        # By id
        a_id = sub_parser.add_parser("id", help="Extract via a list of internal ids.")
        self.add_default_parsers(  # type: ignore[misc]
            parser=a_id, cls=cls, func=cls.by_id, *args, **kwargs
        )
        a_id.add_argument(
            "id",
            help="Internal id. Can be specified multiple times.",
            nargs="+",
        )

        # by name
        a_name = sub_parser.add_parser("name", help="Extract via a list of names.")
        self.add_default_parsers(  # type: ignore[misc]
            parser=a_name, cls=cls, func=cls.by_name, *args, **kwargs
        )
        a_name.add_argument(
            "name",
            help="Visible name (i.e. the name you see in game). Can be specified multiple times.",
            nargs="+",
        )

        # by row ID
        a_rid = sub_parser.add_parser("rowid", help="Extract via rowid in the primary dat file.")
        self.add_default_parsers(  # type: ignore[misc]
            parser=a_rid, cls=cls, func=cls.by_rowid, *args, **kwargs
        )
        a_rid.add_argument(
            "start",
            help="Starting index",
            nargs="?",
            type=int,
            default=0,
        )
        a_rid.add_argument(
            "end",
            nargs="?",
            help="Ending index",
            type=int,
        )

    def add_default_parsers(
        self,
        parser: Any,
        cls: type,
        func: Any = None,
        handler: Any = None,
        wiki: bool = True,
        wiki_handler: WikiHandler | None = None,
    ) -> None:
        """
        Add default parsers for export operations.

        Sets up common arguments for export commands including output directory,
        print/write options, and wiki export options.

        Args:
            parser: Argument parser to add arguments to
            cls: Parser class
            func: Function to call for parsing (if handler is None)
            handler: Optional handler function (if func is None)
            wiki: Whether to enable wiki export options (default: True)
            wiki_handler: Optional WikiHandler instance (creates new if None and wiki=True)

        Raises:
            ValueError: If both func and handler are None
            TypeError: If wiki_handler is not a WikiHandler instance
        """
        if handler is None:
            for item in (func,):
                if item is None:
                    raise ValueError("Must set either handler or func")

        if wiki:
            if wiki_handler is not None:
                if not isinstance(wiki_handler, WikiHandler):
                    raise TypeError("wiki_handler must be a WikiHandler instance.")
            else:
                wiki_handler = WikiHandler()
            wiki_handler.add_arguments(parser)

        parser.set_defaults(func=self.get_wrap(cls, func, handler, wiki_handler))
        parser.add_argument(
            "-d", "--outdir", help="Destination directory. If empty, uses current directory."
        )
        parser.add_argument(
            "-p",
            "--print",
            help="Print the contents of the file",
            action="store_true",
        )
        parser.add_argument(
            "-wr",
            "--write",
            help="Write to file",
            action="store_true",
        )

    def add_image_arguments(self, parser: Any) -> None:
        """
        Add image-related arguments to parser.

        Adds arguments for storing and converting item 2D art images.

        Args:
            parser: Argument parser to add arguments to
        """
        parser.add_argument(
            "-im",
            "--store-images",
            help="If specified item 2d art images will be extracted. "
            "Requires brotli to be installed.",
            action="store_true",
            dest="store_images",
        )

        parser.add_argument(
            "-im-c",
            "--convert-images",
            help="Convert extracted images to png using ImageMagick "
            '(requires "magick" command to be executeable)',
            action="store_true",
            dest="convert_images",
        )

    def add_format_argument(self, parser: Any) -> None:
        """
        Add format argument to parser.

        Adds argument for selecting output format (template or module).

        Args:
            parser: Argument parser to add arguments to
        """
        parser.add_argument(
            "--format",
            help="Output format",
            choices=["template", "module"],
            default="template",
        )


class ExporterResult(list):
    """
    Result container for export operations.

    Stores export results including text, output file, wiki page, and metadata.
    """

    def add_result(
        self,
        text: str | None = None,
        out_file: str | None = None,
        wiki_page: str | None = None,
        wiki_message: str = "",
        **extra: Any,
    ) -> None:
        """
        Add a result entry to the export results.

        Args:
            text: Text content to export (can be callable)
            out_file: Output file path
            wiki_page: Wiki page name (can be string or list of page dicts)
            wiki_message: Wiki edit message
            **extra: Additional metadata to include in result
        """
        data = {
            "text": text,
            "out_file": out_file,
            "wiki_page": wiki_page,
            "wiki_message": wiki_message,
        }
        data.update(extra)

        self.append(data)


# =============================================================================
# Functions
# =============================================================================


def add_parser_arguments(parser: Any) -> None:
    """
    Add wiki-related parser arguments.

    Adds command-line arguments for wiki export operations including
    authentication, dry-run mode, and edit messages.

    Args:
        parser: Argument parser to add arguments to
    """
    parser.add_argument(
        "-w",
        "--wiki",
        help="Write to the gamepedia page (requires pywikibot)",
        action="store_true",
    )

    parser.add_argument(
        "-w-u",
        "--wiki-user",
        dest="user",
        help="Gamepedia user name to use to login into the wiki",
        action="store",
        type=str,
        default="",
    )

    parser.add_argument(
        "-w-p",
        "-w-pw",
        "--wiki-password",
        dest="password",
        help="Gamepedia password to use to login into the wiki",
        action="store",
        type=str,
        default="",
    )

    parser.add_argument(
        "-w-dr",
        "--wiki-dry-run",
        dest="dry_run",
        help="Don't actually save the wiki page and print it instead",
        action="store_true",
    )

    parser.add_argument(
        "-w-msg",
        "--wiki-message",
        "--wiki-edit-message",
        dest="wiki_message",
        help="Override the default edit message",
        action="store",
        type=str,
        default="",
    )
