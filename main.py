#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from pathlib import Path
from typing import List

try:
    from libs.helper import ColorHelpFormatter, COLOR_BOLD, COLOR_RESET, COLOR_DEBUG, COLOR_CYAN, COLOR_YELLOW
    from libs.manager import CopyrightManager
    COLOR_DARK_WHITE    = "\x1b[0;37;2;3m"
    COLOR_PURPLE_ITALIC = "\x1b[0;35;3m"
    COLOR_GREEN_ITALIC  = "\x1b[0;32m"
    COLOR_YELLOW_ITALIC = "\x1b[0;33;1m"
except ImportError as e:
    print( f"Error: Failed to import from 'libs' package. Make sure it's accessible and contains helper.py and manager.py." )
    print( f"Details: {e}" )
    sys.exit( 1 )

# default name for the copyright template file
DEFAULT_COPYRIGHT_FILE = "COPYRIGHT"

def main():
    """Main function to handle command-line arguments and process files."""
    parser = argparse.ArgumentParser(
        prog='cr-manager',
        description=COLOR_BOLD + 'A tool to automatically add, update, or delete multi-format copyright headers.' + COLOR_RESET,
        formatter_class=ColorHelpFormatter,
        add_help=False             # manually add help for better group control
    )

    # argument groups for better help output organization
    pos_group = parser.add_argument_group( COLOR_BOLD + 'POSITIONAL ARGUMENTS' + COLOR_RESET )
    action_group = parser.add_argument_group( COLOR_BOLD + 'ACTION MODES (choose one, default is add)' + COLOR_RESET )
    option_group = parser.add_argument_group( COLOR_BOLD + 'OPTIONS' + COLOR_RESET )

    # positional arguments
    pos_group.add_argument(
        'files',
        nargs='*',                 # allows zero or more files
        metavar='FILES',
        help='List of target files or directories to process.'
    )

    # action modes (mutually exclusive)
    action = action_group.add_mutually_exclusive_group()
    action.add_argument( '--check', action='store_true', help='Check mode: Verifies file copyright status (match, mismatch, or not found).' )
    action.add_argument( '--delete', action='store_true', help='Delete mode: Removes detected copyright headers from files.' )
    action.add_argument( '--update', action='store_true', help='Update mode: Forces replacement of copyright or adds it if missing.' )

    # optional arguments
    option_group.add_argument( '--copyright-file', metavar='FILE', type=Path, default=Path(DEFAULT_COPYRIGHT_FILE), help=f'Specify the copyright template file path (default: {DEFAULT_COPYRIGHT_FILE}).' )
    option_group.add_argument( '--filetype', metavar='TYPE', help="Force a filetype to override auto-detection (e.g., 'python', 'java').\nIf provided alone, displays a formatted preview for that type." )
    option_group.add_argument( '--recursive', '-r', action='store_true', help='If FILES includes directories, process their contents recursively.' )
    option_group.add_argument( '--debug', action='store_true', help='Debug mode: Preview the result of an action without modifying files.' )
    option_group.add_argument( '-v', '--verbose', action='store_true', help='Show a detailed processing summary.' )
    option_group.add_argument( '-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit.' )
    option_group.add_argument( '--version', action='version', version='%(prog)s 2.0', help="Show program's version number and exit." )

    args = parser.parse_args()

    # initialize copyrightmanager
    try:
        manager = CopyrightManager( args.copyright_file )
    except SystemExit as e:
        sys.exit( e.code )

    # handle the special case where only --filetype is provided for a format preview
    is_action_mode = args.check or args.delete or args.update
    if args.filetype and not args.files and not is_action_mode:
        formatted = manager.format_for_file( forced_filetype=args.filetype )
        if formatted:
            if args.verbose: print( f"--- Copyright Format Preview ({args.filetype}) ---" )
            print( f"{COLOR_DEBUG}{formatted}{COLOR_RESET}" )
            if args.verbose: print( "--- End of Preview ---" )
            sys.exit(0)
        else:
            sys.exit(1)

    # validate that files are provided for standard operation modes
    if not args.files:
        parser.error( "At least one target file or directory is required for this operation. Use --filetype <type> for format preview, or -h for help." )

    # collect all files to be processed
    files_to_process: List[Path] = []
    for item_str in args.files:
        item_path = Path( item_str )
        if item_path.is_dir():
            if args.recursive:
                if args.verbose: print( f"Info: Recursively scanning directory {item_path} ..." )
                files_to_process.extend( p for p in item_path.rglob('*') if p.is_file() )
            else:
                print( f"Warning: '{item_path}' is a directory but --recursive was not specified. Skipped.", file=sys.stderr )
        elif item_path.is_file():
            files_to_process.append( item_path )
        else:
            print( f"Warning: '{item_path}' does not exist or is not a valid file/directory. Skipped.", file=sys.stderr )

    if not files_to_process:
        print( "Error: No valid files found to process.", file=sys.stderr )
        sys.exit(1)

    if args.verbose:
        print( f"Info: Will process {len(files_to_process)} file(s)..." )

    # initialize counters and state
    exit_code = 0
    stats = { "processed": 0, "skipped": 0, "updated": 0, "added": 0, "deleted": 0, "errors": 0, "debug": 0 }
    forced_type = args.filetype.lower() if args.filetype else None

    for path in files_to_process:
        stats["processed"] += 1
        # print( f"[{stats['processed']}/{len(files_to_process)}] Processing: {path} ... ", end="" )
        print( f"\n{COLOR_DARK_WHITE}>> "
               f"{COLOR_GREEN_ITALIC}{stats['processed']}{COLOR_DARK_WHITE}/"
               f"{COLOR_YELLOW_ITALIC}{len(files_to_process)}"
               f"{COLOR_PURPLE_ITALIC} {path} "
               f"{COLOR_DARK_WHITE}... {COLOR_RESET}",
              end=""
             )

        try:
            success, msg = False, "unknown_operation"
            if args.check:
                success, msg = manager.check_copyright_status( path, forced_type )
                if msg == "match": print( f"Status: OK (exists and matches)" ); stats["skipped"] += 1
                elif msg == "mismatch": print( f"Status: {COLOR_YELLOW}Needs Update{COLOR_RESET}" ); exit_code = 1
                elif msg == "not_found": print( f"Status: {COLOR_YELLOW}Not Found{COLOR_RESET}" ); exit_code = 1
                else: raise ValueError( msg )

            elif args.delete:
                success, msg = manager.delete_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if msg.startswith( "debug" ):
                    if args.verbose: print( f"Status: Dry-run delete preview shown" )
                    stats["debug"] += 1
                elif success: print( f"Action: {COLOR_YELLOW}Deleted{COLOR_RESET}" ); stats["deleted"] += 1
                elif msg == "not_found": print( f"Action: Not found, nothing to delete" ); stats["skipped"] += 1
                else: raise ValueError( msg )

            elif args.update:
                success, msg = manager.update_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if msg.startswith( "debug" ):
                    if args.verbose: print( f"Status: Dry-run update preview shown" )
                    stats["debug"] += 1
                elif success:
                    if msg == "updated": print( f"Action: {COLOR_CYAN}Updated{COLOR_RESET}" ); stats["updated"] += 1
                    elif msg == "inserted": print( f"Action: {COLOR_CYAN}Added (was not found){COLOR_RESET}" ); stats["added"] += 1
                else: raise ValueError( msg )

            else:                  # Default action: add
                success, msg = manager.add_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if msg.startswith( "debug" ):
                    if args.verbose: print( f"Status: Dry-run add preview shown" )
                    stats["debug"] += 1
                elif success:
                    if msg == "skipped": print( f"Action: Skipped (already exists and matches)" ); stats["skipped"] += 1
                    elif msg == "updated": print( f"Action: {COLOR_CYAN}Updated (due to mismatch){COLOR_RESET}" ); stats["updated"] += 1
                    elif msg == "inserted": print( f"Action: {COLOR_CYAN}Added{COLOR_RESET}" ); stats["added"] += 1
                else: raise ValueError( msg )

        except ( ValueError, FileNotFoundError ) as e:
            if "unsupported_format" in str(e):
                print( f"Status: Unsupported file format" )
            elif "generate_failed" in str(e):
                print( f"Status: {COLOR_BOLD}Error: Failed to generate copyright for target format{COLOR_RESET}" )
            else:
                print( f"Status: {COLOR_BOLD}Error: {e}{COLOR_RESET}" )
            stats["errors"] += 1
            exit_code = 1
        except Exception as e:
            print( f"{COLOR_BOLD}Unexpected error: {e}{COLOR_RESET}" )
            stats["errors"] += 1
            exit_code = 1

    if args.verbose:
        print( "\n--- Processing Summary ---" )
        print( f"Total files processed: {len(files_to_process)}" )
        if args.debug: print( f"Debug previews shown: {stats['debug']}" )
        elif args.check: print( f"Matched/OK: {stats['skipped']}" ); print(f"Needs action/Not found: (see logs above)" )
        else: print( f"Added: {stats['added']}" ); print(f"Updated: {stats['updated']}"); print(f"Deleted: {stats['deleted']}"); print(f"Skipped: {stats['skipped']}" )
        print( f"Errors/Unsupported: {stats['errors']}" )
        print( "--------------------------" )
        if exit_code != 0:
            if args.check: print( "Check finished; some files require action or are unsupported." )
            else: print( "Processing finished with one or more errors or unsupported files." )
        elif not args.debug: print( "Processing completed successfully." )

    sys.exit( exit_code )

if __name__ == "__main__":
    main()

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
