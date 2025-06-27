# -*- coding: utf-8 -*-

# libs/manager.py
import sys
import textwrap
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

# ====================== CONFIGURATION ======================
LINE_LENGTH = 80

COLOR_GRAY  = "\x1b[0;37;3m"
COLOR_RESET = "\x1b[0m"

FILE_TYPE_MAP = {
    "hash_comment": {
        "filetypes": {"python", "shell", "bash", "sh", "dockerfile"},
        "suffixes": {".sh", ".py", ".dockerfile"},
        "config": {
            "start_line": "",
            "end_line": "",
            "comment_string": "#",
            "box_char": "=",
            "simple_format": False
        }
    },
    "groovy_style_comment": {
        "filetypes": {"jenkinsfile", "groovy", "gradle", "java"},
        "suffixes": {".groovy", ".java"},
        "config": {
            "start_line": "/**",
            "end_line": "**/",
            "comment_string": "* ",
            "box_char": "*",
            "simple_format": False
        }
    },
    "c_style_comment": {
        "filetypes": {"c", "cpp", "c++", "cxx", "h", "hpp", "hxx"},
        "suffixes": {".c", ".cpp", ".cxx", ".h", ".hpp", ".hxx"},
        "config": {
            "start_line": "/**",
            "end_line": " */",
            "comment_string": " * ",
            "box_char": "*",
            "simple_format": True
        }
    }
}

COPYRIGHT_KEYWORD_PAT = re.compile( r'copyright|©|license|licensed', re.I )
AUTHOR_KEYWORD_PAT = re.compile( r'@author|@date|@brief|@file|@description', re.I )

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
        for line in reversed( [line.strip() for line in lines_to_check if line.strip()] ):
            if line.startswith( ("#", "//", "/*", "*") ) and ( match := modeline_pattern.search(line) ):
                return match.group(1).lower()
    except Exception:
        pass
    return None

def get_supported_filetypes() -> List[str]:
    """Get all supported filetypes."""
    all_ft: Set[str] = set()
    for data in FILE_TYPE_MAP.values():
        all_ft.update( data.get("filetypes", set()) )
    return sorted( list(all_ft) )

def detect_file_format(path: Path, filetype: Optional[str] = None) -> Optional[str]:
    """
    Detects the file format.
    Priority order: 1. Forced filetype, 2. Vim modeline, 3. File suffix, 4. Content heuristics.
    """
    # 1. forced filetype
    if filetype:
        normalized_ft = filetype.lower()
        for fmt, data in FILE_TYPE_MAP.items():
            if normalized_ft in data.get( "filetypes", set() ):
                return fmt

    def _safe_read(p: Path) -> Optional[str]:
        try:
            return p.read_text( encoding='utf-8', errors='ignore' )
        except Exception as e:
            print( f"Warning: Could not read file content from {p} for detection: {e}", file=sys.stderr )
            return None

    # 2. vim modeline (only if content was readable)
    content = _safe_read(path)
    if content:
        if modeline_type := _parse_modeline(content):
            for fmt, data in FILE_TYPE_MAP.items():
                if modeline_type in data.get( "filetypes", set() ):
                    return fmt

    # 3. file suffix
    suffix = path.suffix.lower()
    if suffix:
        for fmt, data in FILE_TYPE_MAP.items():
            if suffix in data.get( "suffixes", set() ):
                return fmt

    # 4. content/path heuristics (shebang, jenkinsfile)
    if content:
        if any( part.lower() == "jenkinsfile" for part in path.parts ):
            return "groovy_style_comment"

        first_line = content.split('\n', 1)[0].strip().lower()
        if first_line.startswith("#!"):
            if "python" in first_line: return "hash_comment"
            if "bash" in first_line or "sh" in first_line: return "hash_comment"
            if "groovy" in first_line: return "groovy_style_comment"

    # 5. re-check forced filetype as a potential suffix alias
    if filetype:
        normalized_ft = filetype.lower()
        for fmt, data in FILE_TYPE_MAP.items():
            if normalized_ft in data.get( "filetypes", set() ):
                return fmt
        print( f"Warning: Forced filetype '{filetype}' is not in the known configurations.", file=sys.stderr )


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

        processed.append(stripped)
        prev_blank = is_blank

    while processed and not processed[0]:
        processed.pop(0)
    while processed and not processed[-1]:
        processed.pop()

    return processed

# ====================== CORE CLASS ======================
class CopyrightManager:
    def __init__( self, copyright_path: Path ):
        """Initializes the manager with the path to the copyright template file."""
        self.copyright_text = self._load_copyright(copyright_path)
        self.supported_types = get_supported_filetypes()
        self.filetype_map: Dict[str, str] = {}
        self.suffix_map: Dict[str, str] = {}
        for fmt, data in FILE_TYPE_MAP.items():
            for ft in data.get( "filetypes", set() ): self.filetype_map[ft] = fmt
            for sfx in data.get( "suffixes", set() ): self.suffix_map[sfx] = fmt

    @staticmethod
    def _load_copyright(path: Path) -> str:
        """Loads the copyright template text from the specified file."""
        try:
            return path.read_text( encoding='utf-8' )
        except FileNotFoundError:
            print( f"Error: Copyright file not found - {path}", file=sys.stderr )
            sys.exit(2)
        except Exception as e:
            print( f"Error: Failed to read copyright file {path} - {e}", file=sys.stderr )
            sys.exit(3)

    def _get_format_from_filetype(self, filetype: str) -> Optional[str]:
        """Utility to get format key from a filetype string."""
        normalized_ft = filetype.lower()
        for fmt, data in FILE_TYPE_MAP.items():
            if normalized_ft in data.get( "filetypes", set() ):
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
                 print( f"Error: A file path or a filetype must be provided.", file=sys.stderr )
            else:
                 print( f"Error: Target is not a valid file - {path}", file=sys.stderr )
            return None

        if fmt:
            return self._format_copyright( fmt )
        else:
            target = f"type '{forced_filetype}'" if forced_filetype else f"file '{path}'"
            print( f"Info: Could not determine a supported format for {target}", file=sys.stderr )
            return None

    def _format_copyright_content_lines( self, fmt: str, bordered: bool ) -> List[str]:
        """Generates just the content lines of a copyright block."""
        config = FILE_TYPE_MAP[fmt]["config"]
        comment_string = config.get( "comment_string", "#" )
        processed_text_lines = _preprocess_copyright_text( self.copyright_text )
        content_lines = []

        if not bordered:              # simple format content
            line_prefix = comment_string.rstrip() + " "
            wrap_width = max( 10, LINE_LENGTH - len(line_prefix) )
            for line in processed_text_lines:
                if not line:
                    content_lines.append( comment_string.rstrip() )
                else:
                    wrapped = textwrap.wrap( line, width=wrap_width, replace_whitespace=False, drop_whitespace=False )
                    for part in wrapped:
                        content_lines.append( f"{line_prefix}{part}" )
        else:                         # bordered format content
            left_content = " " + comment_string.strip() + " "
            right_content = " " + comment_string.strip()
            text_width = max(0, LINE_LENGTH - len(left_content) - len(right_content))
            for line in processed_text_lines:
                wrapped = textwrap.wrap( line, width=text_width, replace_whitespace=False, drop_whitespace=False ) if line else [""]
                for part in wrapped:
                    content_lines.append( f"{left_content}{part.ljust(text_width)}{right_content}" )
        return content_lines

    def _format_copyright_as_list( self, fmt: str ) -> List[str]:
        """Generates the full formatted copyright block as a list of lines."""
        if fmt not in FILE_TYPE_MAP: return []

        config = FILE_TYPE_MAP[fmt]["config"]
        simple_format = config.get( "simple_format", False )
        start_line = config.get( "start_line", "" )
        end_line = config.get( "end_line", "" )
        full_block = []

        if start_line: full_block.append( start_line )

        if simple_format:
            full_block.extend( self._format_copyright_content_lines(fmt, bordered=False) )
        else:                         # bordered format
            box_char = config.get( "box_char", "=" )
            comment_string = config.get( "comment_string", "#" )
            left_border_prefix = " " if start_line else comment_string
            right_border_suffix = comment_string.strip() if start_line else ""

            border_width = max(0, LINE_LENGTH - len(left_border_prefix) - len(right_border_suffix) - len(box_char) * 2)
            border_line = f"{left_border_prefix}{box_char}{box_char * border_width}{box_char}{right_border_suffix}"

            lines = []
            lines.append( border_line )
            lines.extend( self._format_copyright_content_lines(fmt, bordered=True) )
            lines.append( border_line )
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

    def _isolate_copyright_in_simple_block( self, lines: List[str], block_start: int, block_end: int ) -> Tuple[int, int]:
        """Finds the precise start and end of the copyright section within a simple block."""
        cr_start = -1
        for i in range( block_start, block_end ):
            if COPYRIGHT_KEYWORD_PAT.search( lines[i] ):
                cr_start = i
                break

        if cr_start == -1:
            return -1, -1

        cr_end = cr_start
        for i in range( cr_start + 1, block_end ):
            line = lines[i]
            if AUTHOR_KEYWORD_PAT.search( line ):
                break

            line_content = line.strip().lstrip( FILE_TYPE_MAP["c_style_comment"]["config"]["comment_string"].strip() ).strip()
            if not line_content:
                break

            cr_end = i

        return cr_start, cr_end

    def _find_bordered_section( self, lines: List[str], block_start: int, block_end: int, fmt: str ) -> Tuple[int, int]:
        """Finds the start and end of a bordered section within a larger block."""
        config = FILE_TYPE_MAP[fmt]["config"]
        comment, box_char = config.get( "comment_string", "#" ), config.get( "box_char", "=" )
        esc_comment_rstrip = re.escape( comment.rstrip() )
        esc_box = re.escape( box_char )
        border_pat = re.compile( r"^\s*" + esc_comment_rstrip + r".*" + esc_box + r"+.*" + re.escape(comment.strip()) + r"\s*$" )

        borders_in_block = [ i for i in range(block_start, block_end + 1) if border_pat.match(lines[i]) ]

        if len(borders_in_block) >= 2:
            return borders_in_block[0], borders_in_block[-1]

        return -1, -1

    def _find_first_comment_block( self, lines: List[str], search_start_idx: int, fmt: str ) -> Tuple[int, int]:
        """Finds the first continuous block of comments."""
        config = FILE_TYPE_MAP[fmt]["config"]
        start_marker = config.get( "start_line", "" )
        comment_string = config.get( "comment_string", "#" )

        block_start, in_block = -1, False

        if start_marker:
            end_marker = config.get( "end_line", "" )
            start_pat = re.compile( r"^\s*" + re.escape(start_marker.strip()) )
            end_pat = re.compile( re.escape(end_marker.strip()) + r"\s*$" )

            for i in range( search_start_idx, len(lines) ):
                stripped_line = lines[i].strip()
                if not in_block and start_pat.match( stripped_line ):
                    in_block = True
                    block_start = i
                if in_block and end_pat.search( stripped_line ):
                    return block_start, i
        else:                         # line comment
            comment_pat = re.compile( r"^\s*" + re.escape(comment_string.strip()) )
            for i in range( search_start_idx, len(lines) ):
                line = lines[i]
                if comment_pat.match( line ):
                    if not in_block:
                        block_start = i
                        in_block = True
                elif in_block:
                    return block_start, i - 1
            if in_block:
                return block_start, len( lines ) - 1

        return -1, -1

    def _get_current_copyright( self, content: str, fmt: str ) -> Optional[str]:
        """Gets the existing copyright block from the file content."""
        lines = content.splitlines()
        block_start, block_end = self._detect_copyright_block( lines, fmt )
        if block_start == -1:
            return None

        config = FILE_TYPE_MAP[fmt]["config"]
        if config.get( "simple_format", False ):
            cr_start, cr_end = self._isolate_copyright_in_simple_block(lines, block_start, block_end)
            if cr_start != -1:
                return '\n'.join( lines[cr_start : cr_end + 1] )
            return None
        else:
            return '\n'.join( lines[block_start : block_end + 1] )

    @staticmethod
    def _is_blank_comment_line( line: str, config: Dict ) -> bool:
        """Checks if a line is a blank comment line."""
        stripped = line.strip()
        comment_marker = config['comment_string'].strip()
        if not comment_marker:
            return not stripped
        return stripped == comment_marker

    def delete_copyright( self, path: Path, forced_type: Optional[str] = None, debug: bool = False, verbose: bool = False ) -> Tuple[bool, str]:
        """Deletes the copyright block from a file."""
        try:
            content = path.read_text( encoding='utf-8' )
            fmt = detect_file_format( path, forced_type )
            if not fmt: raise ValueError( "unsupported_format" )

            lines = content.splitlines()
            block_start, block_end = self._detect_copyright_block( lines, fmt )

            if block_start == -1:
                return False, "not_found"

            config = FILE_TYPE_MAP[fmt]["config"]

            has_other_info = any(AUTHOR_KEYWORD_PAT.search(line) for line in lines[block_start:block_end+1])

            if config.get( "simple_format", False ):
                del_start, del_end = self._isolate_copyright_in_simple_block( lines, block_start, block_end )
            else:
                del_start, del_end = self._find_bordered_section( lines, block_start, block_end, fmt )

            if del_start == -1: return False, "not_found"

            if has_other_info:
                if del_end + 1 <= block_end and self._is_blank_comment_line( lines[del_end + 1], config ):
                    del_end += 1
                if del_start - 1 >= block_start and self._is_blank_comment_line( lines[del_start - 1], config ):
                    del_start -= 1
                new_lines = lines[:del_start] + lines[del_end + 1:]
            else:
                new_lines = lines[:block_start] + lines[block_end + 1:]

            final_content = '\n'.join( new_lines )
            if content.endswith('\n') and final_content:
                if not final_content.endswith('\n'):
                    final_content += '\n'

            if debug:
                header = f"\n--- DEBUG PREVIEW: DELETE from {path} ---\n" if verbose else "\n"
                footer = "\n--- END PREVIEW ---" if verbose else ""
                print( f"{header}{COLOR_GRAY}{final_content}{COLOR_RESET}{footer}", end="" )
                return True, "debug_deleted"

            path.write_text( final_content, encoding='utf-8' )
            return True, "deleted"

        except FileNotFoundError: return False, f"error: {path} not found"
        except Exception as e: return False, f"error: {e}"

    def check_copyright_status( self, path: Path, forced_type: Optional[str] = None ) -> Tuple[bool, str]:
        """Checks copyright status. Returns: 'match', 'mismatch', 'not_found', etc."""
        try:
            fmt = detect_file_format( path, forced_type )
            if not fmt: raise ValueError( "unsupported_format" )

            content = path.read_text( encoding='utf-8' )
            current = self._get_current_copyright( content, fmt )
            if not current: return False, "not_found"

            config = FILE_TYPE_MAP[fmt]["config"]
            if config.get( "simple_format", False ):
                norm_expected = "\n".join( line.strip() for line in self._format_copyright_content_lines(fmt, bordered=False) )
            else:
                norm_expected = "\n".join( line.strip() for line in self._format_copyright_as_list(fmt) )

            norm_current = "\n".join( line.strip() for line in current.strip().splitlines() )

            if norm_current == norm_expected: return True, "match"
            else: return False, "mismatch"
        except FileNotFoundError: return False, "error: file_not_found"
        except Exception as e: return False, f"error: {e}"

    def _insert_copyright( self, path: Path, content: str, formatted_lines: List[str], fmt: str, debug: bool = False, verbose: bool = False ) -> Tuple[bool, str]:
        """Inserts the formatted copyright block into the file content."""
        lines = content.splitlines()
        insert_pos = 0

        if lines and lines[0].startswith("#!"):
            insert_pos = 1
        if len( lines ) > insert_pos and re.match( r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)", lines[insert_pos] ):
            insert_pos += 1

        first_comment_start, _ = self._find_first_comment_block( lines, insert_pos, fmt )
        if first_comment_start != -1:
            insert_pos = first_comment_start

        new_lines = lines[:insert_pos]
        if insert_pos > 0 and lines[insert_pos-1].strip():
            new_lines.append("")

        new_lines.extend( formatted_lines )

        if len( lines ) > insert_pos and lines[insert_pos].strip():
            new_lines.append("")

        new_lines.extend( lines[insert_pos:] )

        final_content = '\n'.join( new_lines )
        if content.endswith('\n') or ( not content and final_content ):
            if not final_content.endswith('\n'):
                final_content += '\n'

        if debug:
            header = f"\n--- DEBUG PREVIEW: ADD to {path} ---\n" if verbose else "\n"
            footer = "\n--- END PREVIEW ---" if verbose else ""
            print( f"{header}{COLOR_GRAY}{final_content}{COLOR_RESET}{footer}", end="" )
            return True, "debug_added"

        path.write_text( final_content, encoding='utf-8' )
        return True, "inserted"

    def update_copyright( self, path: Path, forced_type: Optional[str] = None, debug: bool = False, verbose: bool = False ) -> Tuple[bool, str]:
        """Updates or adds a copyright header."""
        try:
            fmt = detect_file_format( path, forced_type )
            if not fmt: raise ValueError( "unsupported_format" )

            content = path.read_text( encoding='utf-8' )
            lines = content.splitlines()
            block_start, block_end = self._detect_copyright_block( lines, fmt )

            if block_start == -1:
                new_formatted_lines = self._format_copyright_as_list( fmt )
                return self._insert_copyright( path, content, new_formatted_lines, fmt, debug=debug, verbose=verbose )

            config = FILE_TYPE_MAP[fmt]["config"]

            if config.get( "simple_format", False ):
                cr_start, cr_end = self._isolate_copyright_in_simple_block( lines, block_start, block_end )
                new_content_lines = self._format_copyright_content_lines( fmt, bordered=False )

                if cr_start != -1:
                    new_lines_before = lines[:cr_start]
                    new_lines_after = lines[cr_end + 1:]

                    separator = []
                    if any( line.strip().lstrip(config['comment_string'].strip()) for line in new_lines_after ):
                        if not self._is_blank_comment_line(new_lines_after[0], config):
                            separator = [config["comment_string"].rstrip()]

                    new_lines = new_lines_before + new_content_lines + separator + new_lines_after
                else:
                    insert_pos = block_start + 1
                    separator = [ config["comment_string"].rstrip() ]
                    new_lines = lines[:insert_pos] + new_content_lines + separator + lines[insert_pos:]
            else:                     # bordered format logic
                border_start, border_end = self._find_bordered_section( lines, block_start, block_end, fmt )

                if border_start != -1 and border_end != -1:
                    new_content = self._format_copyright_content_lines( fmt, bordered=True )
                    new_lines = lines[:border_start + 1] + new_content + lines[border_end:]
                else:                 # fallback
                    new_formatted_lines = self._format_copyright_as_list( fmt )
                    new_lines = lines[:block_start] + new_formatted_lines + lines[block_end + 1:]

            final_content = '\n'.join( new_lines )
            if content.endswith('\n'):
                if not final_content.endswith('\n'):
                    final_content += '\n'

            if debug:
                header = f"\n--- DEBUG PREVIEW: UPDATE for {path} ---\n" if verbose else "\n"
                footer = "\n--- END PREVIEW ---" if verbose else ""
                print( f"{header}{COLOR_GRAY}{final_content}{COLOR_RESET}{footer}", end="" )
                return True, "debug_updated"

            path.write_text( final_content, encoding='utf-8' )
            return True, "updated"

        except FileNotFoundError: return False, f"error: {path} not found"
        except Exception as e: return False, f"error: {e}"

    def add_copyright( self, path: Path, forced_type: Optional[str] = None, debug: bool = False, verbose: bool = False ) -> Tuple[bool, str]:
        """Adds copyright: Skips if match, updates if mismatch, inserts if not found."""
        try:
            _, status = self.check_copyright_status( path, forced_type )

            if status == "match":
                return True, "skipped"
            elif status == "mismatch":
                return self.update_copyright( path, forced_type, debug=debug, verbose=verbose )
            elif status == "not_found":
                fmt = detect_file_format( path, forced_type )
                if not fmt: raise ValueError( "unsupported_format" )

                formatted_lines = self._format_copyright_as_list( fmt )
                content = path.read_text( encoding='utf-8' )
                return self._insert_copyright( path, content, formatted_lines, fmt, debug=debug, verbose=verbose )
            else:
                raise ValueError( status )
        except FileNotFoundError: return False, "file_not_found"
        except Exception as e: return False, f"error: {e}"

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
