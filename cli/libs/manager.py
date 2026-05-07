# -*- coding: utf-8 -*-
# pylint: disable=broad-exception-caught

"""
to provides the core logic for detecting, inserting, updating, and
removing copyright headers across multiple programming languages and file
formats. It is designed to work with configurable comment styles and supports
both “simple” and “bordered” formats, making it suitable for heterogeneous
codebases.
"""

# libs/manager.py
import sys
import textwrap
import re
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple, Set

try:
    import tomllib                    # stdlib: Python >= 3.11
except ImportError:
    import tomli as tomllib           # type: ignore[no-redef]  # pip: Python < 3.11

from .helper import (
    COLOR_RESET, COLOR_DEBUG, COLOR_YELLOW, COLOR_MAGENTA, COLOR_CYAN, COLOR_RED,
    COLOR_DEBUG_I, COLOR_YELLOW_I, COLOR_MAGENTA_I, COLOR_GRAY_I, COLOR_RED_I, COLOR_CYAN_I, COLOR_GREEN_I,
)

# ====================== CONFIGURATION ======================
LINE_LENGTH = 80

def _load_file_type_map() -> Dict[str, Any]:
    """Load format configs from formats.toml (lives alongside this module)."""
    toml_path = Path(__file__).parent / 'formats.toml'
    try:
        with open( toml_path, 'rb' ) as fh:
            raw = tomllib.load( fh )
    except FileNotFoundError:
        print( f"{COLOR_RED}ERROR: {COLOR_DEBUG_I}Format config not found: {COLOR_MAGENTA_I}{toml_path}{COLOR_RESET}", file=sys.stderr )
        sys.exit(4)
    except tomllib.TOMLDecodeError as e:
        print( f"{COLOR_RED}ERROR: {COLOR_DEBUG_I}Failed to parse {COLOR_MAGENTA_I}{toml_path}{COLOR_RESET} — {e}", file=sys.stderr )
        sys.exit(5)
    return {
        fmt: {
            'filetypes' : set( data.get('filetypes', []) ),
            'suffixes'  : set( data.get('suffixes',  []) ),
            'config'    : data.get('config', {}),
        }
        for fmt, data in raw.items()
    }

# Format definitions are in cli/libs/formats.toml (loaded at import time).
FILE_TYPE_MAP: Dict[str, Any] = _load_file_type_map()

COPYRIGHT_KEYWORD_PAT = re.compile( r'copyright|©|license|licensed', re.I )
AUTHOR_KEYWORD_PAT = re.compile(
    r'@author|@date|@brief|@file|@description'    # javadoc / doxygen style
    r'|@since|@update|@version|@usage|@note'      # common shell / project metadata
    r'|#\s*shellcheck\s',                         # shellcheck directives
    re.I
)

# ====================== UTILITY FUNCTIONS (INTERNAL) ======================
def _parse_modeline(content: str) -> Optional[str]:
    """Parse Vim modeline to get the filetype."""
    modeline_pattern = re.compile( r"""
        (?:^|\s)              # start of line or whitespace
        (?:vim?|ex):          # starts with vim: or ex:
        .*?                   # any characters (non-greedy)
        (?:filetype|ft)       # match 'filetype' or 'ft'
        [=\s]+                # separator (= or whitespace)
        ([a-zA-Z0-9_-]+)      # capture the filetype
        (?=\s|:|$)            # followed by whitespace, colon, or end of line
    """, re.VERBOSE | re.IGNORECASE )

    try:
        lines_to_check = content.splitlines()[-5:]
        for line in reversed([ line.strip() for line in lines_to_check if line.strip() ]):
            if line.startswith(( "#", "//", "/*", "*" )) and ( match := modeline_pattern.search(line) ):
                return match.group(1).lower()
    except Exception:
        pass
    return None

def get_supported_filetypes() -> List[str]:
    """Get all supported filetypes."""
    all_ft: Set[str] = set()
    for data in FILE_TYPE_MAP.values():
        all_ft.update( data.get('filetypes', set()) )
    return sorted( list(all_ft) )

def detect_file_format( path: Path, filetype: Optional[str] = None ) -> Optional[str]:
    # pylint: disable=too-many-branches,too-many-return-statements
    """
    Detects the file format.
    Priority order: 1. Forced filetype, 2. Vim modeline, 3. File suffix, 4. Content heuristics.
    """
    # 1. forced filetype
    if filetype:
        normalized_ft = filetype.lower()
        for fmt, data in FILE_TYPE_MAP.items():
            if normalized_ft in data.get( 'filetypes', set() ):
                return fmt

    def _safe_read( p: Path ) -> Optional[str]:
        try:
            return p.read_text( encoding='utf-8', errors='ignore' )
        except Exception as e:
            print( f"{COLOR_YELLOW}WARNING: {COLOR_DEBUG}Could not read file content from {COLOR_YELLOW_I}{p} {COLOR_DEBUG}for detection: {COLOR_MAGENTA_I}{e}{COLOR_RESET}", file=sys.stderr )
            return None

    # 2. vim modeline (only if content was readable)
    content = _safe_read(path)
    if content:
        if modeline_type := _parse_modeline( content ):
            for fmt, data in FILE_TYPE_MAP.items():
                if modeline_type in data.get( 'filetypes', set() ):
                    return fmt

    # 3. file suffix
    suffix = path.suffix.lower()
    if suffix:
        for fmt, data in FILE_TYPE_MAP.items():
            if suffix in data.get( 'suffixes', set() ):
                return fmt

    # 4. content/path heuristics (shebang, jenkinsfile)
    if content:
        if any( part.lower() == 'jenkinsfile' for part in path.parts ):
            return 'groovy_style_comment'

        first_line = content.split('\n', 1)[0].strip().lower()
        if first_line.startswith("#!"):
            if 'python' in first_line: return 'hash_comment'
            if 'bash' in first_line or 'sh' in first_line: return 'hash_comment'
            if 'groovy' in first_line: return 'groovy_style_comment'

    # 5. forced filetype given but matched nothing above — warn and fall through to None
    if filetype:
        print( f"{COLOR_YELLOW}WARNING: {COLOR_DEBUG}Forced filetype {COLOR_YELLOW_I}'{filetype}' {COLOR_DEBUG}is not in the known configurations.{COLOR_RESET}", file=sys.stderr )


    return None

def _preprocess_copyright_text( raw_text: str ) -> List[str]:
    """Pre-processes copyright text: collapses consecutive blank lines and trims."""
    processed: List[str] = []
    prev_blank = False
    for line in raw_text.splitlines():
        stripped = line.rstrip()
        is_blank = not stripped

        if is_blank and prev_blank:
            continue

        processed.append( stripped )
        prev_blank = is_blank

    while processed and not processed[0]:
        processed.pop(0)
    while processed and not processed[-1]:
        processed.pop()

    return processed

# ====================== CORE CLASS ======================
class CopyrightManager:
    """Core engine for detecting, generating, inserting, updating, and removing copyright headers across multiple file formats."""

    def __init__( self, copyright_path: Path ):
        """Initializes the manager with the path to the copyright template file."""
        self.copyright_text = self._load_copyright( copyright_path )
        self.supported_types = get_supported_filetypes()

    @staticmethod
    def _load_copyright( path: Path ) -> str:
        """Loads the copyright template text from the specified file."""
        try:
            return path.read_text( encoding='utf-8' )
        except FileNotFoundError:
            print( f"{COLOR_RED}ERROR: {COLOR_DEBUG_I}Copyright file not found - {COLOR_MAGENTA_I}{path}{COLOR_RESET}", file=sys.stderr )
            sys.exit(2)
        except Exception as e:
            print( f"{COLOR_RED}ERROR: {COLOR_DEBUG_I}Failed to read copyright file {COLOR_MAGENTA_I}{path}{COLOR_RESET} - {e}", file=sys.stderr )
            sys.exit(3)

    @staticmethod
    def _restore_trailing_newline( original: str, new_content: str ) -> str:
        """Re-add trailing newline if original had one, or if original was empty (new file)."""
        if new_content and not new_content.endswith('\n'):
            if original.endswith('\n') or not original:
                return new_content + '\n'
        return new_content

    @staticmethod
    def _debug_preview( action: str, color: str, prep: str, path: Path, lines: List[str], verbose: bool ) -> None:
        # pylint: disable=too-many-arguments too-many-positional-arguments
        """Print a standardised debug preview block."""
        header = (
            f"\n{COLOR_DEBUG}--- DEBUG PREVIEW: {color}{action}{COLOR_RESET} "
            f"{COLOR_DEBUG}{prep}{COLOR_RESET} {COLOR_MAGENTA}{path} "
            f"{COLOR_DEBUG}---{COLOR_RESET}\n" if verbose else "\n"
        )
        footer = f"\n{COLOR_DEBUG}--- END PREVIEW ---{COLOR_RESET}" if verbose else ""
        print( f"{header}{COLOR_GRAY_I}{chr(10).join(lines)}{COLOR_RESET}{footer}", end="\n" )

    def _get_format_from_filetype( self, filetype: str ) -> Optional[str]:
        """Utility to get format key from a filetype string."""
        normalized_ft = filetype.lower()
        for fmt, data in FILE_TYPE_MAP.items():
            if normalized_ft in data.get( 'filetypes', set() ):
                return fmt
        return None

    def format_for_file( self, path: Optional[Path] = None, forced_filetype: Optional[str] = None ) -> Optional[str]:
        """Generates the formatted copyright string for a specific file or filetype."""
        fmt = None
        if forced_filetype and not path:
            fmt = self._get_format_from_filetype( forced_filetype )
        elif path and path.is_file():
            fmt = detect_file_format( path, forced_filetype )
        else:
            if not path:
                print( f"{COLOR_MAGENTA}ERROR: {COLOR_DEBUG_I}a file path or a filetype must be provided{COLOR_RESET}", file=sys.stderr )
            else:
                print( f"{COLOR_MAGENTA}ERROR: {COLOR_DEBUG_I}target is not a valid file - {COLOR_RED_I}{path}{COLOR_RESET}", file=sys.stderr )
            return None

        if fmt: return self._format_copyright( fmt )

        target = f"type {COLOR_MAGENTA_I}'{forced_filetype}'" if forced_filetype else f"file {COLOR_MAGENTA_I}'{path}'"
        print( f"{COLOR_CYAN}INFO: {COLOR_DEBUG_I}could not determine a supported format for {target}{COLOR_RESET}", file=sys.stderr )
        if self.supported_types:
            hint = f"{COLOR_CYAN}HINT: {COLOR_DEBUG}Supported filetypes are: {COLOR_MAGENTA_I}{', '.join(self.supported_types)}{COLOR_RESET}"
            print( hint, file=sys.stderr )
        return None

    def _format_copyright_content_lines( self, fmt: str, bordered: bool ) -> List[str]:
        """Generates just the content lines of a copyright block."""
        config = FILE_TYPE_MAP[fmt]["config"]
        content_left  = config.get( 'content_left',  '# ' )
        content_right = config.get( 'content_right', ' #' )
        processed_text_lines = _preprocess_copyright_text( self.copyright_text )
        content_lines = []

        if not bordered:      # simple format: no box, just a left prefix per line
            wrap_width = max( 10, LINE_LENGTH - len(content_left) )
            for line in processed_text_lines:
                if not line:
                    content_lines.append( content_left.rstrip() )
                else:
                    wrapped = textwrap.wrap( line, width=wrap_width, replace_whitespace=False, drop_whitespace=False )
                    for part in wrapped:
                        content_lines.append( f"{content_left}{part}" )
        else:                 # bordered format: pad text between left and right delimiters
            text_width = max( 0, LINE_LENGTH - len(content_left) - len(content_right) )
            for line in processed_text_lines:
                wrapped = textwrap.wrap( line, width=text_width, replace_whitespace=False, drop_whitespace=False ) if line else [""]
                for part in wrapped:
                    content_lines.append( f"{content_left}{part.ljust(text_width)}{content_right}" )
        return content_lines

    def _format_copyright_as_list( self, fmt: str ) -> List[str]:
        """Generates the full formatted copyright block as a list of lines."""
        if fmt not in FILE_TYPE_MAP: return []

        config = FILE_TYPE_MAP[fmt]['config']
        simple_format = config.get( 'simple_format', False )
        start_line = config.get( 'start_line', '' )
        end_line = config.get( 'end_line', '' )
        full_block = []

        if start_line: full_block.append( start_line )

        if simple_format:
            full_block.extend( self._format_copyright_content_lines(fmt, bordered=False) )
        else:                 # bordered format
            missing = [ k for k in ('box_char', 'box_left', 'box_right') if k not in config ]
            if missing:
                raise ValueError( f"Format '{fmt}' has simple_format=False but is missing required box keys: {missing}" )

            box_char  = config['box_char']
            box_left  = config['box_left']
            box_right = config['box_right']

            box_width = max( 0, LINE_LENGTH - len(box_left) - len(box_right) - len(box_char) * 2 )
            box_line  = f"{box_left}{box_char}{box_char * box_width}{box_char}{box_right}"

            lines = []
            lines.append( box_line )
            lines.extend( self._format_copyright_content_lines(fmt, bordered=True) )
            lines.append( box_line )
            full_block.extend( lines )

        if end_line: full_block.append( end_line )
        return full_block

    def _format_copyright( self, fmt: str ) -> str:
        return '\n'.join( self._format_copyright_as_list(fmt) )

    def _detect_copyright_block( self, lines: List[str], fmt: str ) -> Tuple[int, int]:
        """Detects the start and end indices of a full comment block containing a copyright."""
        first_block_start, first_block_end = self._find_first_comment_block( lines, 0, fmt )
        if first_block_start == -1:
            return -1, -1

        has_copyright = any( COPYRIGHT_KEYWORD_PAT.search(lines[i]) for i in range(first_block_start, first_block_end + 1) )

        if has_copyright:
            return first_block_start, first_block_end

        return -1, -1

    def _isolate_copyright_in_simple_block( self, lines: List[str], block_start: int, block_end: int, fmt: str ) -> Tuple[int, int]:
        """Finds the precise start and end of the copyright section within a simple block."""
        comment = FILE_TYPE_MAP[fmt]['config']['comment']
        cr_start = -1
        for i in range( block_start, block_end ):
            if COPYRIGHT_KEYWORD_PAT.search( lines[i] ): cr_start = i; break

        if cr_start == -1: return -1, -1

        cr_end = cr_start
        for i in range( cr_start + 1, block_end ):
            line = lines[i]
            if AUTHOR_KEYWORD_PAT.search( line ): break

            line_content = line.strip().lstrip( comment ).strip()
            if not line_content: break

            cr_end = i

        return cr_start, cr_end

    def _find_bordered_section( self, lines: List[str], block_start: int, block_end: int, fmt: str ) -> Tuple[int, int]:
        """Find the start and end line indexes of the bordered copyright section."""
        config = FILE_TYPE_MAP[fmt]['config']
        bl  = re.escape( config.get( 'box_left',  '' ).strip() )
        br  = re.escape( config.get( 'box_right', '' ).strip() )
        box = re.escape( config.get( 'box_char',  '=' ) )

        border_re = re.compile( rf"^\s*{bl}\s*{box}{{3,}}\s*{br}\s*$" )

        borders = [ i for i in range(block_start, block_end + 1) if border_re.match(lines[i]) ]
        if len(borders) >= 2: return borders[0], borders[-1]
        return -1, -1

    def _find_first_comment_block( self, lines: List[str], search_start_idx: int, fmt: str ) -> Tuple[int, int]:
        # pylint: disable=too-many-locals,too-many-branches
        """Finds the first continuous block of comments."""
        config = FILE_TYPE_MAP[fmt]['config']
        start_marker   = config.get( 'start_line', '' )
        comment_marker = config.get( 'comment', '#' )

        block_start, in_block = -1, False

        if start_marker:
            end_marker = config.get( 'end_line', '' )
            start_pat = re.compile( r"^\s*" + re.escape(start_marker.strip()) )
            end_pat = re.compile( re.escape(end_marker.strip()) + r"\s*$" )

            for i in range( search_start_idx, len(lines) ):
                stripped_line = lines[i].strip()
                if not in_block and start_pat.match( stripped_line ):
                    in_block = True
                    block_start = i
                if in_block and end_pat.search( stripped_line ):
                    return block_start, i
        else:                 # line comment
            # exclude shebang lines (#!) so they don't absorb the first comment block
            if comment_marker == '#':
                comment_pat = re.compile( r"^\s*#(?!!)" )
            else:
                comment_pat = re.compile( r"^\s*" + re.escape(comment_marker) )
            for i in range( search_start_idx, len(lines) ):
                line = lines[i]
                if comment_pat.match( line ):
                    if not in_block:
                        block_start = i
                        in_block = True
                elif in_block:
                    if line.strip(): return block_start, i - 1
            if in_block:
                return block_start, len( lines ) - 1

        return -1, -1

    def _get_current_copyright( self, content: str, fmt: str ) -> Optional[str]:
        """Gets the existing copyright block from the file content."""
        lines = content.splitlines()
        block_start, block_end = self._detect_copyright_block( lines, fmt )
        if block_start == -1:
            return None

        config = FILE_TYPE_MAP[fmt]['config']
        if config.get( 'simple_format', False ):
            cr_start, cr_end = self._isolate_copyright_in_simple_block( lines, block_start, block_end + 1, fmt )
            if cr_start != -1:
                return '\n'.join( lines[cr_start : cr_end + 1] )
            return None

        # for bordered formats that combine copyright + author info,
        # narrow to just the bordered copyright section for accurate comparison
        bs, be = self._find_bordered_section( lines, block_start, block_end, fmt )
        if bs != -1:
            return '\n'.join( lines[bs : be + 1] )
        return '\n'.join( lines[block_start : block_end + 1] )

    @staticmethod
    def _is_blank_comment_line( line: str, config: Dict ) -> bool:
        """Checks if a line is a blank comment line."""
        stripped = line.strip()
        comment_marker = config.get( 'comment', '' )
        if not comment_marker:
            return not stripped
        return stripped == comment_marker

    def delete_copyright( self, path: Path, forced_type: Optional[str] = None, debug: bool = False, verbose: bool = False ) -> Tuple[bool, str]:
        # pylint: disable=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements
        """Delete the copyright header. Prefer removing only the bordered section when present."""
        try:
            content = path.read_text( encoding='utf-8' )
            fmt = detect_file_format( path, forced_type )
            if not fmt: raise ValueError( 'unsupported_format' )

            lines = content.splitlines()
            block_start, block_end = self._detect_copyright_block( lines, fmt )
            if block_start == -1: return False, 'not_found'

            config = FILE_TYPE_MAP[fmt]['config']
            is_simple_format = config.get( 'simple_format', False )
            start_marker = config.get( 'start_line', '' ).strip()
            end_marker = config.get( 'end_line', '' ).strip()

            has_other_info = any( AUTHOR_KEYWORD_PAT.search(line) for line in lines[block_start:block_end + 1] )

            del_start, del_end = -1, -1
            if not is_simple_format:
                del_start, del_end = self._find_bordered_section( lines, block_start, block_end, fmt )
            else:
                del_start, del_end = self._isolate_copyright_in_simple_block( lines, block_start, block_end + 1, fmt )

            # ======================== find the copyright block ========================
            if del_start != -1:
                # try to merge inwards
                if del_end + 1 <= block_end and self._is_blank_comment_line( lines[del_end + 1], config ):
                    del_end += 1
                if del_start - 1 >= block_start and self._is_blank_comment_line( lines[del_start - 1], config ):
                    del_start -= 1

                # groovy/java wrapper clean
                if start_marker and end_marker:
                    prefix_is_clean = True
                    for i in range(block_start, del_start):
                        if lines[i].strip() != start_marker: prefix_is_clean = False; break

                    suffix_is_clean = True
                    for i in range(del_end + 1, block_end + 1):
                        if lines[i].strip() != end_marker: suffix_is_clean = False; break

                    if prefix_is_clean and suffix_is_clean:
                        del_start = block_start
                        del_end = block_end

                if del_end + 1 < len(lines) and not lines[del_end + 1].strip():
                    del_end += 1

                new_lines = lines[:del_start] + lines[del_end + 1:]
                final_content = self._restore_trailing_newline( content, '\n'.join(new_lines) )

                if debug:
                    self._debug_preview( 'DELETE', COLOR_RED_I, 'from', path, lines[del_start : del_end + 1], verbose )
                    return True, 'debug_deleted'

                path.write_text( final_content, encoding='utf-8' )
                return True, 'deleted'

            if has_other_info:
                return False, 'not_found_in_combined'

            remove_end = block_end
            if remove_end + 1 < len(lines) and not lines[remove_end + 1].strip():
                remove_end += 1

            new_lines = lines[ :block_start ] + lines[ remove_end + 1: ]
            final_content = self._restore_trailing_newline( content, '\n'.join(new_lines) )

            if debug:
                self._debug_preview( 'DELETE', COLOR_RED_I, 'from', path, lines[block_start : remove_end + 1], verbose )
                return True, 'debug_deleted'

            path.write_text( final_content, encoding='utf-8' )
            return True, 'deleted'

        except FileNotFoundError:
            return False, f"{COLOR_RED}ERROR: {COLOR_MAGENTA_I}{path} {COLOR_DEBUG_I}not found{COLOR_RESET}"
        except Exception as e:
            return False, f"ERROR: {e}"

    def check_copyright_status( self, path: Path, forced_type: Optional[str] = None ) -> Tuple[bool, str]:
        """Checks copyright status. Returns: 'match', 'mismatch', 'not_found', etc."""
        try:
            fmt = detect_file_format( path, forced_type )
            if not fmt: raise ValueError( 'unsupported_format' )

            content = path.read_text( encoding='utf-8' )
            current = self._get_current_copyright( content, fmt )
            if not current: return False, 'not_found'

            config = FILE_TYPE_MAP[fmt]['config']
            if config.get( 'simple_format', False ):
                norm_expected = "\n".join( line.strip() for line in self._format_copyright_content_lines(fmt, bordered=False) )
            else:
                norm_expected = "\n".join( line.strip() for line in self._format_copyright_as_list(fmt) )

            norm_current = "\n".join( line.strip() for line in current.strip().splitlines() )

            if norm_current == norm_expected: return True, 'match'
            return False, 'mismatch'
        except FileNotFoundError: return False, 'error: file_not_found'
        except Exception as e: return False, f"error: {e}"

    def _insert_copyright( self, path: Path, content: str, formatted_lines: List[str], fmt: str, debug: bool = False, verbose: bool = False ) -> Tuple[bool, str]:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """Inserts the formatted copyright block into the file content."""
        _ = fmt             # avoid pylint unused-argument, kept for API compatibility
        lines = content.splitlines()
        insert_pos = 0

        if lines and lines[0].startswith('#!'):
            insert_pos = 1
        if len( lines ) > insert_pos and re.match( r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)", lines[insert_pos] ):
            insert_pos += 1

        new_lines: List[str] = []

        if insert_pos > 0:
            new_lines.extend( lines[:insert_pos] )
            if new_lines and new_lines[-1].strip(): new_lines.append('')

        new_lines.extend( formatted_lines )

        if len( lines ) > insert_pos and lines[insert_pos].strip():
            new_lines.append('')

        new_lines.extend( lines[insert_pos:] )
        final_content = self._restore_trailing_newline( content, '\n'.join(new_lines) )

        if debug:
            self._debug_preview( 'ADD', COLOR_GREEN_I, 'to', path, formatted_lines, verbose )
            return True, 'debug_added'

        path.write_text( final_content, encoding='utf-8' )
        return True, 'inserted'

    # pylint: disable=too-many-branches,too-many-locals
    def update_copyright( self, path: Path, forced_type: Optional[str] = None, debug: bool = False, verbose: bool = False ) -> Tuple[bool, str]:
        """Update (or add) a copyright header, replacing only the bordered section for bordered formats."""
        try:
            fmt = detect_file_format( path, forced_type )
            if not fmt: raise ValueError( 'unsupported_format' )

            new_formatted_lines = self._format_copyright_as_list( fmt )
            content = path.read_text( encoding='utf-8' )
            lines = content.splitlines()

            block_start, block_end = self._detect_copyright_block( lines, fmt )
            if block_start == -1:
                return self._insert_copyright( path, content, new_formatted_lines, fmt, debug=debug, verbose=verbose )

            config = FILE_TYPE_MAP[fmt]['config']
            is_simple_format = config.get( 'simple_format', False )
            has_other_info = any( AUTHOR_KEYWORD_PAT.search(line) for line in lines[block_start:block_end + 1] )

            replace_start, replace_end = block_start, block_end
            lines_to_insert = new_formatted_lines

            # Bordered formats: try to replace only the bordered section first
            if not is_simple_format:
                bs, be = self._find_bordered_section(lines, block_start, block_end, fmt)
                if bs != -1:
                    replace_start, replace_end = bs, be
                    tmp = list( new_formatted_lines )
                    start_line = config.get( 'start_line', '' )
                    end_line = config.get( 'end_line', '' )
                    if start_line and tmp and tmp[0] == start_line: tmp.pop(0)
                    if end_line and tmp and tmp[-1] == end_line: tmp.pop()
                    lines_to_insert = tmp

            # Simple formats that contain other info: narrow to the actual subrange
            if is_simple_format and has_other_info:
                cr_start, cr_end = self._isolate_copyright_in_simple_block( lines, block_start, block_end + 1, fmt )
                if cr_start != -1:
                    replace_start, replace_end = cr_start, cr_end
                    lines_to_insert = self._format_copyright_content_lines( fmt, bordered=False )

            if debug:
                preview = (
                    lines[block_start:replace_start] + lines_to_insert + lines[replace_end + 1:block_end + 1]
                    if replace_start != block_start or replace_end != block_end
                    else new_formatted_lines
                )
                self._debug_preview( 'UPDATE', COLOR_CYAN_I, 'for', path, preview, verbose )
                return True, 'debug_updated'

            new_lines = lines[:replace_start] + lines_to_insert + lines[replace_end + 1:]
            final_content = self._restore_trailing_newline( content, '\n'.join(new_lines) )

            path.write_text( final_content, encoding='utf-8' )
            return True, 'updated'

        except FileNotFoundError: return False, f"error: {path} not found"
        except Exception as e: return False, f"error: {e}"

    def add_copyright( self, path: Path, forced_type: Optional[str] = None, debug: bool = False, verbose: bool = False ) -> Tuple[bool, str]:
        """Adds copyright: Skips if match, updates if mismatch, inserts if not found."""
        try:
            fmt = detect_file_format( path, forced_type )
            if not fmt: raise ValueError( 'unsupported_format' )

            _, status = self.check_copyright_status( path, forced_type )

            if status == 'match':
                return True, 'skipped'
            if status == 'mismatch':
                return self.update_copyright( path, forced_type, debug=debug, verbose=verbose )
            if status == 'not_found':
                formatted_lines = self._format_copyright_as_list( fmt )
                content = path.read_text( encoding='utf-8' )
                return self._insert_copyright( path, content, formatted_lines, fmt, debug=debug, verbose=verbose )
            raise ValueError( status )
        except FileNotFoundError: return False, 'file_not_found'
        except Exception as e: return False, f"error: {e}"

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
