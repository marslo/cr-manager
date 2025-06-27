#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from pathlib import Path
from typing import List

try:
    from libs.helper import ColorHelpFormatter
    from libs.helper import COLOR_BOLD, COLOR_RESET, COLOR_DEBUG, COLOR_CYAN, COLOR_YELLOW, COLOR_GREEN, COLOR_BLUE, COLOR_DEBUG_I, COLOR_PURPLE_I, COLOR_CYAN_I, COLOR_GREEN_I, COLOR_RED_I, COLOR_YELLOW_I, COLOR_BLUE_I
    from libs.manager import CopyrightManager
except ImportError as e:
    print( f"Error: Failed to import from 'libs' package. Make sure it's accessible and contains helper.py and manager.py." )
    print( f"Details: {e}" )
    sys.exit( 1 )

# default name for the copyright template file
DEFAULT_COPYRIGHT_FILE = "COPYRIGHT"
VERSION = "v2.0"

def main():
    """Main function to handle command-line arguments and process files."""
    parser = argparse.ArgumentParser(
        prog='crm.py',
        description=COLOR_BOLD + 'A tool to automatically add, update, or delete multi-format copyright headers.' + COLOR_RESET,
        formatter_class=ColorHelpFormatter,
        add_help=False
    )

    # argument groups for better help output organization
    pos_group    = parser.add_argument_group( COLOR_BOLD + 'POSITIONAL ARGUMENTS' + COLOR_RESET )
    action_group = parser.add_argument_group( COLOR_BOLD + 'ACTION MODES (default is add)' + COLOR_RESET )
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
    action.add_argument( '--check'  , action='store_true', help='Check mode: Verifies file copyright status (match, mismatch, or not found).' )
    action.add_argument( '--delete' , action='store_true', help='Delete mode: Removes detected copyright headers from files.' )
    action.add_argument( '--update' , action='store_true', help='Update mode: Forces replacement of copyright or adds it if missing.' )

    # optional arguments
    option_group.add_argument( '--copyright'       , metavar='FILE'      , type=Path, default=Path(DEFAULT_COPYRIGHT_FILE), help=f'Specify the copyright template file path (default: {DEFAULT_COPYRIGHT_FILE}).' )
    option_group.add_argument( '--filetype',  '-t' , metavar='TYPE'      , help="Force a filetype to override auto-detection (e.g., 'python', 'java').\nIf provided alone, displays a formatted preview for that type." )
    option_group.add_argument( '--recursive', '-r' , action='store_true' , help='If FILES includes directories, process their contents recursively.' )
    option_group.add_argument( '--debug',     '-d' , action='store_true' , help='Debug mode: Preview the result of an action without modifying files.' )
    option_group.add_argument( '--verbose',   '-v' , action='store_true' , help='Show a detailed processing summary.' )
    option_group.add_argument( '--help',      '-h' , action='help'       , default=argparse.SUPPRESS, help='Show this help message and exit.' )
    option_group.add_argument( '--version'         , action='version'    , version=f"%(prog)s - cr-manager {VERSION}", help="Show program's version number and exit." )

    args = parser.parse_args()

    # initialize copyright manager
    try:
        manager = CopyrightManager( args.copyright )
    except SystemExit as e:
        sys.exit( e.code )

    # handle the special case where only --filetype is provided for a format preview
    is_action_mode = args.check or args.delete or args.update
    if args.filetype and not args.files and not is_action_mode:
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
    supported_types_str = ', '.join(manager.supported_types)

    for path in files_to_process:
        stats["processed"] += 1
        # print( f"[{stats['processed']}/{len(files_to_process)}] Processing: {path} ... ", end="" )
        print( f"{COLOR_DEBUG_I}>> "
               f"{COLOR_GREEN}{stats['processed']}{COLOR_DEBUG_I}/"
               f"{COLOR_YELLOW}{len(files_to_process)}"
               f"{COLOR_PURPLE_I} {path} "
               f"{COLOR_DEBUG_I}... {COLOR_RESET}",
              end=""
             )

        try:
            success, msg = False, "unknown_operation"
            if args.check:
                success, msg = manager.check_copyright_status( path, forced_type )
                if msg == "match": print( f"Status: OK (exists and matches)" ); stats["skipped"] += 1
                elif msg == "mismatch": print( f"{COLOR_DEBUG_I}Status: {COLOR_YELLOW}NEEDS UPDATE{COLOR_RESET}" ); exit_code = 1
                elif msg == "not_found": print( f"{COLOR_DEBUG_I}Status: {COLOR_YELLOW}NOT FOUND{COLOR_RESET}" ); exit_code = 1
                else: raise ValueError( msg )

            elif args.delete:
                success, msg = manager.delete_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if msg.startswith( "debug" ):
                    if args.verbose: print( f"Status: Dry-run delete preview shown" )
                    stats["debug"] += 1
                elif success: print( f"{COLOR_YELLOW}DELETED{COLOR_RESET}" ); stats["deleted"] += 1
                elif msg == "not_found": print( f"{COLOR_DEBUG_I}action: Not found, nothing to delete{COLOR_RESET}" ); stats["skipped"] += 1
                else: raise ValueError( msg )

            elif args.update:
                success, msg = manager.update_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if msg.startswith( "debug" ):
                    if args.verbose: print( f"{COLOR_DEBUG_I}Status: {COLOR_DEBUG}DRYRUN {COLOR_DEBUG_I}preview shown{COLOR_RESET}" )
                    stats["debug"] += 1
                elif success:
                    if msg == "updated": print( f"{COLOR_CYAN}UPDATED{COLOR_RESET}" ); stats["updated"] += 1
                    elif msg == "inserted": print( f"{COLOR_GREEN}ADDED{COLOR_RESET}" ); stats["added"] += 1
                else: raise ValueError( msg )

            else:                  # default action: add
                success, msg = manager.add_copyright( path, forced_type, debug=args.debug, verbose=args.verbose )
                if msg.startswith( "debug" ):
                    if args.verbose: print( f"Status: Dry-run add preview shown" )
                    stats["debug"] += 1
                elif success:
                    if msg == "skipped": print( f"{COLOR_DEBUG}SKIPPED {COLOR_DEBUG_I}(already exists and matches){COLOR_RESET}" ); stats["skipped"] += 1
                    elif msg == "updated": print( f"{COLOR_CYAN}UPDATED {COLOR_DEBUG_I}(due to mismatch){COLOR_RESET}" ); stats["updated"] += 1
                    elif msg == "inserted": print( f"{COLOR_CYAN}ADDED{COLOR_RESET}" ); stats["added"] += 1
                else: raise ValueError( msg )

        except ( ValueError, FileNotFoundError ) as e:
            if "unsupported_format" in str(e):
                print( f"{COLOR_YELLOW}UNSUPPORTED{COLOR_RESET}" )
                print( f"{COLOR_BLUE}HINT: {COLOR_DEBUG_I}supported filetypes include: {COLOR_BLUE_I}{supported_types_str}{COLOR_RESET}" )
            elif "generate_failed" in str(e):
                print( f"{COLOR_BOLD}ERROR: {COLOR_DEBUG_I}Failed to generate copyright for target format{COLOR_RESET}" )
            else:
                print( f"{COLOR_BOLD}ERROR: {COLOR_DEBUG_I}{e}{COLOR_RESET}" )
            stats["errors"] += 1
            exit_code = 1
        except Exception as e:
            print( f"{COLOR_BOLD}UNEXPECTED ERROR: {e}{COLOR_RESET}" )
            stats["errors"] += 1
            exit_code = 1

    if args.verbose:
        print( "\n{COLOR_DEBUG_I}--- Processing Summary ---{COLOR_RESET}" )
        print( f"{COLOR_DEBUG_I}total files processed: {COLOR_DEBUG}{len(files_to_process)}{COLOR_RESET}" )
        if args.debug:
            print( f"{COLOR_DEBUG_I}debug previews shown: {COLOR_CYAN}{stats['debug']}{COLOR_RESET}" )
        elif args.check:
            print( f"Matched/OK: {stats['skipped']}" );
            print( f"{COLOR_DEBUG_I}needs action/not found: (see logs above){COLOR_RESET}"  )
        else:
            print( f"{COLOR_DEBUG}ADDED   : {COLOR_GREEN_I}{stats['added']}{COLOR_RESET}" );
            print( f"{COLOR_DEBUG}UPDATED : {COLOR_CYAN_I}{stats['updated']}{COLOR_RESET}" );
            print( f"{COLOR_DEBUG}DELETED : {COLOR_RED_I}{stats['deleted']}{COLOR_RESET}" );
            print( f"{COLOR_DEBUG}SKIPPED : {COLOR_YELLOW_I}{stats['skipped']}{COLOR_RESET}" )
        print( f"{COLOR_DEBUG}ERRORS/UNSUPPORTED: {COLOR_PURPLE_I}{stats['errors']}{COLOR_RESET}" )
        print( "--------------------------" )
        if exit_code != 0:
            if args.check: print( "{COLOR_DEBUG}check finished; some files require action or are unsupported{COLOR_RESET}" )
            else: print( "{COLOR_DEBUG}processing finished with one or more errors or unsupported files{COLOR_RESET}" )
        elif not args.debug: print( "{COLOR_GREEN_I}processing completed successfully{COLOR_RESET}" )

    sys.exit( exit_code )

if __name__ == "__main__":
    main()

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
