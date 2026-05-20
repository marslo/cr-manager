#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught

""" Manage copyright headers in source code files of various formats. """

import re
import argparse
import sys
from pathlib import Path
from typing import List
import importlib.metadata

try:
    from .libs.helper import (
        ColorHelpFormatter,
        COLOR_BOLD, COLOR_RESET, COLOR_DEBUG, COLOR_DEBUG_I,
        COLOR_CYAN, COLOR_MAGENTA, COLOR_YELLOW, COLOR_GREEN, COLOR_BLUE, COLOR_RED, COLOR_GRAY,
        COLOR_CYAN_I, COLOR_MAGENTA_I, COLOR_YELLOW_I, COLOR_GREEN_I, COLOR_BLUE_I, COLOR_RED_I
    )
    from .libs.manager import CopyrightManager, get_supported_filetypes
    from .install_completion import get_completion_text, install_completion
except ImportError as e:
    print( "ERROR: Failed to import from 'libs' package. Make sure it's accessible and contains helper.py and manager.py." )
    print( f"Details: {e}" )
    sys.exit( 1 )

# default name for the copyright template file
DEFAULT_COPYRIGHT_FILE = "COPYRIGHT"

_ANSI_ESC_RE = re.compile( r'\x1b\[[0-9;]*m' )

def _format_progress_line( counter_c: str, path: Path, status_c: str, total_width: int = 79, min_dots: int = 3 ) -> str:
    """Format a fixed-width progress line (pre-commit style): counter path ... status."""
    counter_p = _ANSI_ESC_RE.sub( '', counter_c )
    status_p  = _ANSI_ESC_RE.sub( '', status_c )

    # max chars the path may occupy so dots stay >= min_dots; clamp to 0 to avoid negative-index bugs
    max_path = max( 0, total_width - len(counter_p) - 3 - min_dots - len(status_p) )
    path_str = str(path)
    if max_path == 0:
        path_str = ''
    elif len( path_str ) > max_path:
        path_str = ( '...' + path_str[-(max_path - 3):] ) if max_path > 3 else path_str[-max_path:]

    dots_n = max( min_dots, total_width - len(counter_p) - 1 - len(path_str) - 1 - len(status_p) - 1 )
    return f"{counter_c} {COLOR_MAGENTA_I}{path_str}{COLOR_RESET} {'.' * dots_n} {status_c}"

# pylint: disable=too-many-branches,too-many-locals,too-many-statements
def main():
    """Main function to handle command-line arguments and process files."""

    try:
        supported_types_str = ', '.join( get_supported_filetypes() )
    except Exception:
        supported_types_str = "[Could not load supported types]"

    try:
        app_version = importlib.metadata.version( 'cr-manager' )
    except importlib.metadata.PackageNotFoundError:
        app_version = "UNKNOWN (not installed)"

    prog = ( Path(sys.argv[0]).name if (Path(sys.argv[0]).name not in {Path(__file__).name, "__main__.py"} and Path(sys.argv[0]).suffix != ".py") else f"{Path(sys.executable).name} -m {__package__}.{Path(__file__).stem}" )
    parser = argparse.ArgumentParser(
        prog=prog,
        description=COLOR_BOLD + 'A tool to automatically add, update, or delete multi-format copyright headers.' + COLOR_RESET,
        formatter_class=ColorHelpFormatter,
        add_help=False
    )

    # argument groups for better help output organization
    pos_group    = parser.add_argument_group( COLOR_BOLD + 'POSITIONAL ARGUMENTS' + COLOR_RESET )
    action_group = parser.add_argument_group( COLOR_BOLD + 'ACTION MODES' + COLOR_RESET )
    option_group = parser.add_argument_group( COLOR_BOLD + 'OPTIONS' + COLOR_RESET )

    # positional arguments
    pos_group.add_argument(
        'files',
        nargs='*',                # allows zero or more files
        metavar='FILES',
        help='List of target files or directories to process.'
    )

    # action modes (mutually exclusive)
    action = action_group.add_mutually_exclusive_group()
    action.add_argument( '--add'    , '-a', action='store_true', help='Add mode: Adds copyright header to files that are missing it (default).' )
    action.add_argument( '--check'  , '-c', action='store_true', help='Check mode: Verifies file copyright status (match, mismatch, or not found).' )
    action.add_argument( '--delete' , '-d', action='store_true', help='Delete mode: Removes detected copyright headers from files.' )
    action.add_argument( '--update' , '-u', action='store_true', help='Update mode: Forces replacement of copyright or adds it if missing.' )

    # optional arguments
    option_group.add_argument( '--copyright'       , metavar='FILE'      , type=Path, default=Path(DEFAULT_COPYRIGHT_FILE), help=f'Specify the copyright template file path (default: {COLOR_MAGENTA_I}{DEFAULT_COPYRIGHT_FILE}{COLOR_RESET}).' )
    option_group.add_argument( '--filetype',  '-t' , metavar='TYPE'      , help=f"Force override a filetype instead of auto-detection.\nIf provided, displays a formatted preview for that type. "
                                                                                f"Supported: {COLOR_MAGENTA_I}{supported_types_str}{COLOR_RESET}" )
    option_group.add_argument( '--recursive', '-r' , action='store_true' , help=f"If {COLOR_GREEN_I}FILES{COLOR_RESET} includes directories, process their contents recursively." )
    option_group.add_argument( '--debug'           , action='store_true' , help='Debug mode: Preview the result of an action without modifying files.' )
    option_group.add_argument( '--verbose'         , action='store_true' , help='Show a detailed processing summary.' )
    option_group.add_argument( '--completion'      , action='store_true' , help='Print the bash completion script to stdout.' )
    option_group.add_argument( '--install-completion'                    , action='store_true',  help='Install bash completion to the OS-appropriate directory (auto-detected, no root needed by default).' )
    option_group.add_argument( '--help',      '-h' , action='help'       , default=argparse.SUPPRESS, help='Show this help message and exit.' )
    option_group.add_argument( '--version',   '-v' , action='version'    , version=f"cr-manager v{app_version}", help="Show program's version number and exit." )

    args = parser.parse_args()

    # ── completion flags: handled before any file processing ────────────────
    if args.completion:
        sys.stdout.write( get_completion_text() )
        sys.exit( 0 )

    if args.install_completion:
        install_completion()
        sys.exit( 0 )

    # initialize copyright manager
    try:
        manager = CopyrightManager( args.copyright )
    except SystemExit as e:
        sys.exit( e.code )

    # handle the special case where only --filetype is provided for a format preview
    is_action_mode = args.add or args.check or args.delete or args.update or args.debug
    if args.filetype and not args.files and not is_action_mode:
        if args.verbose:
            print( f"{COLOR_DEBUG_I}INFO: Entering format preview mode (since only --filetype was provided)...{COLOR_RESET}", file=sys.stderr )

        formatted = manager.format_for_file( forced_filetype=args.filetype )
        if formatted:
            if args.verbose: print( f"{COLOR_DEBUG_I}--- Copyright Format Preview ({COLOR_DEBUG}{args.filetype}{COLOR_DEBUG_I}) ---{COLOR_RESET}" )
            print( f"{COLOR_DEBUG}{formatted}{COLOR_RESET}" )
            if args.verbose: print( f"{COLOR_DEBUG_I}--- End of Preview ---{COLOR_RESET}" )
            sys.exit(0)
        else:
            sys.exit(1)

    # validate that files are provided for standard operation modes
    if not args.files:
        parser.error( f"\n{COLOR_RED}ERROR:{COLOR_RESET} At least one target file or directory is required for this operation. Use {COLOR_YELLOW}--filetype {COLOR_CYAN}<type>{COLOR_RESET} for format preview, or {COLOR_YELLOW}-h{COLOR_RESET} for help" )

    # collect all files to be processed
    files_to_process: List[Path] = []
    ignores = {
        "dirs": {".git", "__pycache__"},
        "files": {"COPYRIGHT", "LICENSE", "README.md"},
    }
    for item_str in args.files:
        item_path = Path( item_str )
        if item_path.is_dir():
            if args.recursive:
                if args.verbose: print( f"Info: Recursively scanning directory {item_path} ..." )
                files_to_process.extend(
                    p for p in item_path.rglob("*")
                    if p.is_file()
                    and not any( part in ignores["dirs"] for part in p.parts )
                    and p.name not in ignores["files"]
                )
            else:
                print( f"Warning: '{item_path}' is a directory but --recursive was not specified. Skipped.", file=sys.stderr )
        elif item_path.is_file():
            files_to_process.append( item_path )
        else:
            print( f"Warning: '{item_path}' does not exist or is not a valid file/directory. Skipped.", file=sys.stderr )

    if not files_to_process:
        print( f"{COLOR_RED}ERROR: {COLOR_DEBUG_I}No valid files found to process.{COLOR_RESET}", file=sys.stderr )
        sys.exit(1)

    if args.verbose:
        print( f"{COLOR_DEBUG_I}INFO: Will process {COLOR_MAGENTA}{len(files_to_process)} {COLOR_DEBUG_I}file(s)...{COLOR_RESET}" )

    # initialize counters and state
    exit_code = 0
    stats = { "processed": 0, "matched": 0, "skipped": 0, "updated": 0, "added": 0, "deleted": 0, "errors": 0, "debug": 0 }
    forced_type = args.filetype.lower() if args.filetype else None

    for path in files_to_process:
        stats["processed"] += 1
        counter_c = (
            f"{COLOR_GREEN}{stats['processed']}{COLOR_DEBUG_I}/"
            f"{COLOR_YELLOW}{len(files_to_process)}{COLOR_RESET}"
        )
        path_indent = " " * ( len(str(stats['processed'])) + 1 + len(str(len(files_to_process))) + 1 )
        status_c, hint = "", ""

        try:
            success, msg = False, 'unknown_operation'
            if args.check:
                success, msg = manager.check_copyright_status( path, forced_type )
                if   msg == 'match'    : status_c = f"{COLOR_GREEN}OK{COLOR_RESET}";                 stats['matched'] += 1
                elif msg == 'mismatch' : status_c = f"{COLOR_YELLOW}NEEDS UPDATE{COLOR_RESET}";       exit_code = 1
                elif msg == 'not_found': status_c = f"{COLOR_YELLOW}NOT FOUND{COLOR_RESET}";          exit_code = 1
                else: raise ValueError( msg )

            elif args.delete:
                success, msg = manager.delete_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if   msg.startswith('debug'): status_c = f"{COLOR_DEBUG_I}(preview){COLOR_RESET}";   stats['debug'] += 1
                elif success              : status_c = f"{COLOR_YELLOW}DELETED{COLOR_RESET}";         stats['deleted'] += 1
                elif msg == 'not_found'   : status_c = f"{COLOR_DEBUG_I}NOT FOUND{COLOR_RESET}";      stats['skipped'] += 1
                else: raise ValueError( msg )

            elif args.update:
                success, msg = manager.update_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if   msg.startswith('debug'): status_c = f"{COLOR_DEBUG_I}(preview){COLOR_RESET}";   stats['debug'] += 1
                elif success:
                    if   msg == 'skipped' : status_c = f"{COLOR_DEBUG}SKIPPED{COLOR_RESET}";           stats['skipped'] += 1
                    elif msg == 'updated' : status_c = f"{COLOR_CYAN}UPDATED{COLOR_RESET}";            stats['updated'] += 1
                    elif msg == 'inserted': status_c = f"{COLOR_GREEN}ADDED{COLOR_RESET}";              stats['added'] += 1
                    else: raise ValueError( msg )
                else: raise ValueError( msg )

            else:                       # --add / default
                success, msg = manager.add_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if   msg.startswith('debug'): status_c = f"{COLOR_DEBUG_I}(preview){COLOR_RESET}";                     stats['debug'] += 1
                elif success:
                    if   msg == 'skipped' : status_c = f"{COLOR_DEBUG}SKIPPED{COLOR_RESET}";                            stats['skipped'] += 1
                    elif msg == 'updated' : status_c = f"{COLOR_DEBUG_I}(mismatch) {COLOR_CYAN}UPDATED{COLOR_RESET}";   stats['updated'] += 1
                    elif msg == 'inserted': status_c = f"{COLOR_CYAN}ADDED{COLOR_RESET}";                               stats['added'] += 1
                    else: raise ValueError( msg )
                else: raise ValueError( msg )

        except ( ValueError, FileNotFoundError ) as e:
            if 'unsupported_format' in str(e):
                status_c = f"{COLOR_YELLOW}UNSUPPORTED{COLOR_RESET}"
                hint = f"{path_indent}{COLOR_BLUE}HINT: {COLOR_DEBUG_I}supported filetypes: {COLOR_BLUE_I}{supported_types_str}{COLOR_RESET}"
            else:
                status_c = f"{COLOR_BOLD}ERROR: {COLOR_DEBUG_I}{e}{COLOR_RESET}"
            stats['errors'] += 1
            exit_code = 1
        except Exception as e:
            status_c = f"{COLOR_BOLD}UNEXPECTED ERROR: {e}{COLOR_RESET}"
            stats['errors'] += 1
            exit_code = 1

        print( _format_progress_line( counter_c, path, status_c ) )
        if hint: print( hint )

    if args.verbose:
        print( f"\n{COLOR_DEBUG}--------- SUMMARY ---------{COLOR_RESET}" )
        print( f"{COLOR_DEBUG_I}total files processed: {COLOR_DEBUG}{len(files_to_process)}{COLOR_RESET}" )
        if args.debug:
            print( f"{COLOR_DEBUG_I}debug previews shown: {COLOR_CYAN}{stats['debug']}{COLOR_RESET}" )
        elif args.check:
            print( f"{COLOR_DEBUG_I}MATCHED/OK: {COLOR_GREEN_I}{stats['matched']}{COLOR_RESET}" )
            print( f"{COLOR_DEBUG_I}needs action/not found: (see logs above){COLOR_RESET}"  )
        else:
            print( f"{COLOR_GRAY}ADDED   : {COLOR_GREEN_I}{stats['added']}{COLOR_RESET}" )
            print( f"{COLOR_GRAY}UPDATED : {COLOR_CYAN_I}{stats['updated']}{COLOR_RESET}" )
            print( f"{COLOR_GRAY}DELETED : {COLOR_RED_I}{stats['deleted']}{COLOR_RESET}" )
            print( f"{COLOR_GRAY}SKIPPED : {COLOR_YELLOW_I}{stats['skipped']}{COLOR_RESET}" )
        print( f"{COLOR_DEBUG_I}errors or unsupported: {COLOR_MAGENTA_I}{stats['errors']}{COLOR_RESET}" )
        print( f"{COLOR_DEBUG_I}--------------------------{COLOR_RESET}" )
        if exit_code != 0:
            if args.check: print( f"{COLOR_DEBUG}check finished; some files require action or are unsupported{COLOR_RESET}" )
            else: print( f"{COLOR_DEBUG}processing finished with one or more errors or unsupported files{COLOR_RESET}" )
        elif not args.debug: print( f"{COLOR_GREEN}processing completed successfully{COLOR_RESET}" )

    sys.exit( exit_code )

if __name__ == "__main__":
    main()

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
