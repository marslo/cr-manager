#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from pathlib import Path
from typing import List

try:
    from libs.helper import ColorHelpFormatter, COLOR_BOLD, COLOR_RESET, COLOR_DEBUG, COLOR_CYAN, COLOR_YELLOW
    from libs.manager import CopyrightManager, detect_file_format
except ImportError as e:
    print(f"Error: Failed to import from 'libs' package. Make sure it's accessible and contains helper.py and manager.py.")
    print(f"Details: {e}")
    sys.exit(1)

# default name for the copyright template file
DEFAULT_COPYRIGHT_FILE = "COPYRIGHT"

def main():
    """Main function to handle command-line arguments and process files."""
    parser = argparse.ArgumentParser(
        prog='cr-manager',
        description=COLOR_BOLD + 'A tool to automatically add, update, or delete multi-format copyright headers.' + COLOR_RESET,
        formatter_class=ColorHelpFormatter,
        add_help=False # manually add help for better group control
    )

    # argument groups for better help output organization
    pos_group = parser.add_argument_group(
        COLOR_BOLD + 'POSITIONAL ARGUMENTS' + COLOR_RESET
    )
    action_group = parser.add_argument_group(
        COLOR_BOLD + 'ACTION MODES (choose one, default is add)' + COLOR_RESET
    )
    option_group = parser.add_argument_group(
        COLOR_BOLD + 'OPTIONS' + COLOR_RESET
    )

    # positional arguments
    pos_group.add_argument(
        'files',
        nargs='*', # allows zero or more files
        metavar='FILES',
        help='List of target files or directories to process.'
    )

    # action modes (mutually exclusive)
    action = action_group.add_mutually_exclusive_group()
    action.add_argument('--check', action='store_true', help='Check mode: Verifies file copyright status (match, mismatch, or not found).')
    action.add_argument('--delete', action='store_true', help='Delete mode: Removes detected copyright headers from files.')
    action.add_argument('--update', action='store_true', help='Update mode: Forces replacement of copyright or adds it if missing.')

    # optional arguments
    option_group.add_argument('--copyright-file', metavar='FILE', type=Path, default=Path(DEFAULT_COPYRIGHT_FILE), help=f'Specify the copyright template file path (default: {DEFAULT_COPYRIGHT_FILE}).')
    option_group.add_argument('--filetype', metavar='TYPE', help="Force a filetype to override auto-detection (e.g., 'python', 'java').\nIf provided alone, displays a formatted preview for that type.")
    option_group.add_argument('--recursive', '-r', action='store_true', help='If FILES includes directories, process their contents recursively.')
    option_group.add_argument('--debug', action='store_true', help='Debug mode: Display the formatted copyright without modifying files.')
    option_group.add_argument('-v', '--verbose', action='store_true', help='Show a detailed processing summary.')
    option_group.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit.')
    option_group.add_argument('--version', action='version', version='%(prog)s 1.2', help="Show program's version number and exit.")

    args = parser.parse_args()

    # handle the special case where only --filetype is provided for a format preview
    is_action_mode = args.check or args.delete or args.update or args.debug
    if args.filetype and not args.files and not is_action_mode:
        if args.verbose:
            print(f"Info: Entering format preview mode (only --filetype was provided)...")
        try:
            manager = CopyrightManager(args.copyright_file)
        except SystemExit as e:
            print(f"Error: Could not load copyright file '{args.copyright_file}' for preview.", file=sys.stderr)
            sys.exit(e.code)

        fmt_key = manager.filetype_map.get(args.filetype.lower())
        if not fmt_key:
            # attempt detection using a dummy path to find a matching format
            dummy_path = Path(f"preview.{args.filetype.lower()}")
            fmt_key = detect_file_format(dummy_path, args.filetype.lower())
            if not fmt_key:
                print(f"Error: Invalid or unsupported filetype '{args.filetype}' for format preview.", file=sys.stderr)
                print(f"Hint: Supported filetypes include: {', '.join(manager.supported_types)}")
                print(f"Hint: You can also try known suffixes (e.g., 'py', 'java') as the type.", file=sys.stderr)
                sys.exit(1)
            elif args.verbose:
                print(f"Info: Filetype '{args.filetype}' mapped to format '{fmt_key}' via heuristics.", file=sys.stderr)

        formatted = manager._format_copyright(fmt_key)
        if formatted:
            if args.verbose: print(f"--- Copyright Format Preview ({args.filetype} / Format Key: {fmt_key}) ---")
            print(f"{COLOR_DEBUG}{formatted}{COLOR_RESET}")
            if args.verbose: print("--- End of Preview ---")
            sys.exit(0)
        else:
            print(f"Error: Could not generate formatted preview for format key '{fmt_key}'.", file=sys.stderr)
            sys.exit(1)

    # validate that files are provided for standard operation modes
    if not args.files:
        parser.error("At least one target file or directory is required for this operation. Use --filetype <type> for format preview, or -h for help.")

    # initialize copyrightmanager for file processing
    try:
        manager = CopyrightManager(args.copyright_file)
    except SystemExit as e:
        sys.exit(e.code)

    # collect all files to be processed, handling directories recursively if specified
    files_to_process: List[Path] = []
    for item_str in args.files:
        item_path = Path(item_str)
        if item_path.is_dir():
            if args.recursive:
                if args.verbose:
                    print(f"Info: Recursively scanning directory {item_path} ...")
                files_to_process.extend(p for p in item_path.rglob('*') if p.is_file())
            else:
                print(f"Warning: '{item_path}' is a directory but --recursive was not specified. Skipped.", file=sys.stderr)
        elif item_path.is_file():
            files_to_process.append(item_path)
        else:
            print(f"Warning: '{item_path}' does not exist or is not a valid file/directory. Skipped.", file=sys.stderr)

    if not files_to_process:
        print("Error: No valid files found to process.", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Info: Will process {len(files_to_process)} file(s)...")

    # initialize counters and state for the processing loop
    exit_code = 0
    processed_count, skipped_count, updated_count, added_count, deleted_count, error_count, debug_shown_count = 0, 0, 0, 0, 0, 0, 0
    forced_type = args.filetype.lower() if args.filetype else None
    supported_types_str = ', '.join(manager.supported_types)

    for path in files_to_process:
        processed_count += 1
        print(f"[{processed_count}/{len(files_to_process)}] Processing: {path} ... ", end="")

        # handle debug mode separately
        if args.debug:
            formatted = manager.format_for_file(path, forced_type)
            if formatted:
                print(f"Debug Output (Formatted Content):")
                print(f"{COLOR_DEBUG}{formatted}{COLOR_RESET}")
                debug_shown_count += 1
            else:
                print(f"{COLOR_YELLOW}Debug: Could not generate formatted copyright for this file (type might be unsupported or file is unreadable).{COLOR_RESET}")
                error_count += 1
                exit_code = 1
            continue # move to the next file in debug mode

        # standard action modes (check, delete, update, add)
        success = False
        msg = "unknown_operation"
        try:
            if args.check:
                success, msg = manager.check_copyright_status(path, forced_type)
                if msg == "match": print(f"Status: OK (exists and matches)"); skipped_count += 1
                elif msg == "mismatch": print(f"Status: {COLOR_YELLOW}Needs Update{COLOR_RESET}"); exit_code = 1
                elif msg == "not_found": print(f"Status: {COLOR_YELLOW}Not Found{COLOR_RESET}"); exit_code = 1
                elif msg == "unsupported_format":
                    print(f"Status: Unsupported file format")
                    print(f"Hint: Supported filetypes include: {supported_types_str}")
                    error_count += 1
                elif msg.startswith("error:"):
                    print(f"Status: {COLOR_BOLD}Check Error: {msg}{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                else:
                    print(f"Status: Unknown check result '{msg}'")
                    error_count += 1; exit_code = 1

            elif args.delete:
                success, msg = manager.delete_copyright(path, forced_type)
                if success: print(f"Action: {COLOR_YELLOW}Deleted{COLOR_RESET}"); deleted_count += 1
                elif msg == "not_found": print(f"Action: Not found, nothing to delete"); skipped_count += 1
                elif msg == "unsupported_format":
                    print(f"Action: Unsupported format, cannot delete")
                    print(f"Hint: Supported filetypes include: {supported_types_str}")
                    error_count += 1
                elif msg.startswith("error:"):
                    print(f"Action: {COLOR_BOLD}Delete Error: {msg}{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                else:
                    print(f"Action: Unknown delete result '{msg}'")
                    error_count += 1; exit_code = 1

            elif args.update:
                success, msg = manager.update_copyright(path, forced_type)
                if success:
                    if msg == "updated": print(f"Action: {COLOR_CYAN}Updated{COLOR_RESET}"); updated_count += 1
                    elif msg == "inserted": print(f"Action: {COLOR_CYAN}Added (was not found){COLOR_RESET}"); added_count += 1
                    else: print(f"Action: Done ({msg})")
                elif msg == "unsupported_format":
                    print(f"Action: Unsupported format, cannot update")
                    print(f"Hint: Supported filetypes include: {supported_types_str}")
                    error_count += 1
                elif msg == "generate_failed":
                    print(f"Action: {COLOR_BOLD}Update Error: Failed to generate copyright for target format{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                elif msg.startswith("error:"):
                    print(f"Action: {COLOR_BOLD}Update Error: {msg}{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                else:
                    print(f"Action: Unknown update result '{msg}'")
                    error_count += 1; exit_code = 1

            else: # default action is to 'add'
                success, msg = manager.add_copyright(path, forced_type)
                if success:
                    if msg == "skipped": print(f"Action: Skipped (already exists and matches)"); skipped_count += 1
                    elif msg == "updated": print(f"Action: {COLOR_CYAN}Updated (due to mismatch){COLOR_RESET}"); updated_count += 1
                    elif msg == "inserted" or msg == "added": print(f"Action: {COLOR_CYAN}Added{COLOR_RESET}"); added_count += 1
                    else: print(f"Action: Done ({msg})")
                elif msg == "unsupported_format":
                    print(f"Action: Unsupported format, cannot add")
                    print(f"Hint: Supported filetypes include: {supported_types_str}")
                    error_count += 1
                elif msg == "generate_failed":
                    print(f"Action: {COLOR_BOLD}Add Error: Failed to generate copyright for target format{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                elif msg.startswith("error:"):
                    print(f"Action: {COLOR_BOLD}Add Error: {msg}{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                else:
                    print(f"Action: Unknown add result '{msg}'")
                    error_count += 1; exit_code = 1

        except Exception as e:
            # catch any unexpected errors during a single file's processing
            print(f"{COLOR_BOLD}Unexpected error while processing {path}: {e}{COLOR_RESET}")
            error_count += 1
            exit_code = 1

    # print a final summary if verbose mode is enabled
    if args.verbose:
        print("\n--- Processing Summary ---")
        print(f"Total files processed: {len(files_to_process)}")
        if args.debug: print(f"Debug previews shown: {debug_shown_count}")
        elif args.check: print(f"Matched/OK: {skipped_count}"); print(f"Needs action/Not found: (see logs above)")
        else: print(f"Added: {added_count}"); print(f"Updated: {updated_count}"); print(f"Deleted: {deleted_count}"); print(f"Skipped: {skipped_count}")
        print(f"Errors/Unsupported: {error_count}")
        print("--------------------------")
        if exit_code != 0:
            if args.debug: print("Debug run finished; some files could not be formatted.")
            elif args.check: print("Check finished; some files require action or are unsupported.")
            else: print("Processing finished with one or more errors or unsupported files.")
        elif not args.debug:
            print("Processing completed successfully.")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
