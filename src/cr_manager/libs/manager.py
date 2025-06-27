# -*- coding: utf-8 -*-

# libs/manager.py
import sys
import textwrap
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

# ====================== CONFIGURATION ======================
LINE_LENGTH = 80

FILE_TYPE_MAP = {
    "hash_comment": {
        "filetypes": {"python", "shell", "bash", "sh"},
        "suffixes": {".sh", ".py"},
        "config": {
            "start_line": "",
            "end_line": "",
            "comment_string": "#",
            "box_char": "="
        }
    },
    "slash_star_comment": {
        "filetypes": {"jenkinsfile", "groovy", "gradle", "java"},
        "suffixes": {".groovy", ".java"},
        "config": {
            "start_line": "/**",
            "end_line": "**/",
            "comment_string": "* ",
            "box_char": "*"
        }
    }
}

# ====================== UTILITY FUNCTIONS (INTERNAL) ======================
def _parse_modeline(content: str) -> Optional[str]:
    """Parse Vim modeline to get the filetype."""
    modeline_pattern = re.compile(r"""
        (?:^|\s)              # start of line or whitespace
        (?:vim?|ex):          # starts with vim: or ex:
        .*?                   # any characters (non-greedy)
        (?:filetype|ft)       # match 'filetype' or 'ft'
        [=\s]+                # separator (= or whitespace)
        ([a-zA-Z0-9_-]+)      # capture the filetype
        (?=\s|:|$)            # followed by whitespace, colon, or end of line
    """, re.VERBOSE | re.IGNORECASE)

    try:
        # process only the last few lines for efficiency
        lines_to_check = content.splitlines()[-5:]
        for line in reversed([line.strip() for line in lines_to_check if line.strip()]):
            # check if it looks like a comment line before applying the more expensive regex
            if line.startswith(("#", "//", "/*", "*")) and (match := modeline_pattern.search(line)):
                return match.group(1).lower()
    except Exception: # broad exception for robustness against file content issues
        pass
    return None

def get_supported_filetypes() -> List[str]:
    """Get all supported filetypes."""
    all_ft: Set[str] = set()
    for data in FILE_TYPE_MAP.values():
        all_ft.update(data.get("filetypes", set()))
    return sorted(list(all_ft))

def detect_file_format(path: Path, filetype: Optional[str] = None) -> Optional[str]:
    """
    Detects the file format.
    Priority order: 1. Forced filetype, 2. Vim modeline, 3. File suffix, 4. Content heuristics.
    """
    # 1. forced filetype
    if filetype:
        normalized_ft = filetype.lower()
        for fmt, data in FILE_TYPE_MAP.items():
            if normalized_ft in data.get("filetypes", set()):
                return fmt
        print(f"Warning: Forced filetype '{filetype}' is not in the known configurations.", file=sys.stderr)
        # fall through to other detection methods.

    def _safe_read(p: Path) -> Optional[str]:
        try:
            return p.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"Warning: Could not read file content from {p} for detection: {e}", file=sys.stderr)
            return None

    content = _safe_read(path)

    # 2. vim modeline (only if content was readable)
    if content:
        if modeline_type := _parse_modeline(content):
            for fmt, data in FILE_TYPE_MAP.items():
                if modeline_type in data.get("filetypes", set()):
                    return fmt

    # 3. file suffix
    suffix = path.suffix.lower()
    if suffix:
        for fmt, data in FILE_TYPE_MAP.items():
            if suffix in data.get("suffixes", set()):
                return fmt

    # 4. content/path heuristics (shebang, jenkinsfile)
    if content:
        if any(part.lower() == "jenkinsfile" for part in path.parts):
            for fmt, data in FILE_TYPE_MAP.items():
                if "jenkinsfile" in data.get("filetypes", set()):
                    return fmt

        first_line = content.split('\n', 1)[0].strip().lower()
        if first_line.startswith("#!"):
            if "python" in first_line: return "hash_comment"
            if "bash" in first_line or "sh" in first_line: return "hash_comment"
            if "groovy" in first_line: return "slash_star_comment"

    # 5. re-check forced filetype as a potential suffix alias
    if filetype:
        normalized_ft = filetype.lower()
        possible_suffix = f".{normalized_ft}"
        for fmt, data in FILE_TYPE_MAP.items():
            if possible_suffix in data.get("suffixes", set()):
                print(f"Debug: Forced type '{filetype}' not in filetypes, but matched suffix '{possible_suffix}' for format {fmt}", file=sys.stderr)
                return fmt

    return None

def _preprocess_copyright_text(raw_text: str) -> List[str]:
    """Preprocesses copyright text: collapses consecutive blank lines and trims."""
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
    def __init__(self, copyright_path: Path):
        """Initializes the manager with the path to the copyright template file."""
        self.copyright_text = self._load_copyright(copyright_path)
        self.supported_types = get_supported_filetypes()
        self.filetype_map: Dict[str, str] = {} # filetype -> format_key
        self.suffix_map: Dict[str, str] = {}   # suffix -> format_key
        for fmt, data in FILE_TYPE_MAP.items():
            for ft in data.get("filetypes", set()): self.filetype_map[ft] = fmt
            for sfx in data.get("suffixes", set()): self.suffix_map[sfx] = fmt

    @staticmethod
    def _load_copyright(path: Path) -> str:
        """Loads the copyright template text from the specified file."""
        try:
            return path.read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"Error: Copyright file not found - {path}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error: Failed to read copyright file {path} - {e}", file=sys.stderr)
            sys.exit(3)

    def _format_copyright(self, fmt: str) -> Optional[str]:
        """Generates the full formatted copyright string based on the format key."""
        if fmt not in FILE_TYPE_MAP:
            print(f"Error: Unknown internal format key '{fmt}'", file=sys.stderr)
            return None

        config = FILE_TYPE_MAP[fmt]["config"]
        start_line = config.get("start_line", "")
        end_line = config.get("end_line", "")
        comment_string = config.get("comment_string", "#")
        box_char = config.get("box_char", "=")
        is_block = bool(start_line and end_line)

        lines = []
        processed_text_lines = _preprocess_copyright_text(self.copyright_text)

        if is_block:
            trimmed_comment = comment_string.strip()
            lines.append(start_line)
            left_border_marker = " " + trimmed_comment
            right_border_marker = trimmed_comment
            border_content_width = max(0, LINE_LENGTH - len(left_border_marker) - len(right_border_marker))
            border_line = f"{left_border_marker}{box_char * border_content_width}{right_border_marker}"
            lines.append(border_line)

            left_content_marker = " " + trimmed_comment + " "
            right_content_marker = " " + trimmed_comment
            text_content_width = max(0, LINE_LENGTH - len(left_content_marker) - len(right_content_marker))

            for line in processed_text_lines:
                if not line:
                    lines.append(f"{left_content_marker}{' ' * text_content_width}{right_content_marker}")
                else:
                    wrapped = textwrap.wrap(line, width=text_content_width, replace_whitespace=False, drop_whitespace=False)
                    for part in wrapped:
                        lines.append(f"{left_content_marker}{part.ljust(text_content_width)}{right_content_marker}")

            lines.append(border_line)
            lines.append(end_line)
        else: # line comment format
            left_marker = comment_string + " "
            right_marker = " " + comment_string
            content_width = max(0, LINE_LENGTH - len(left_marker) - len(right_marker))
            border_line = f"{left_marker}{box_char * content_width}{right_marker}"
            lines.append(border_line)

            for line in processed_text_lines:
                if not line:
                    lines.append(f"{left_marker}{' ' * content_width}{right_marker}")
                else:
                    wrapped = textwrap.wrap(line, width=content_width, replace_whitespace=False, drop_whitespace=False)
                    for part in wrapped:
                        lines.append(f"{left_marker}{part.ljust(content_width)}{right_marker}")

            lines.append(border_line)

        return '\n'.join(lines)

    def _generate_formatted_middle(self, fmt: str) -> Optional[List[str]]:
        """Generates the middle part (borders and text) of a formatted copyright block."""
        if fmt not in FILE_TYPE_MAP:
            print(f"Error: (Internal) Unknown format key '{fmt}' for generating middle section", file=sys.stderr)
            return None

        config = FILE_TYPE_MAP[fmt]["config"]
        comment_string = config.get("comment_string", "* ")
        box_char = config.get("box_char", "*")

        trimmed_comment = comment_string.strip()
        middle_lines = []

        left_border_marker = " " + trimmed_comment
        right_border_marker = trimmed_comment
        border_content_width = max(0, LINE_LENGTH - len(left_border_marker) - len(right_border_marker))
        border_line = f"{left_border_marker}{box_char * border_content_width}{right_border_marker}"
        middle_lines.append(border_line) # top border

        left_content_marker = " " + trimmed_comment + " "
        right_content_marker = " " + trimmed_comment
        text_content_width = max(0, LINE_LENGTH - len(left_content_marker) - len(right_content_marker))

        processed_text_lines = _preprocess_copyright_text(self.copyright_text)
        for line in processed_text_lines:
            if not line:
                middle_lines.append(f"{left_content_marker}{' ' * text_content_width}{right_content_marker}")
            else:
                wrapped_lines = textwrap.wrap(line, width=text_content_width, replace_whitespace=False, drop_whitespace=False)
                for text_part in wrapped_lines:
                    formatted_line = f"{left_content_marker}{text_part.ljust(text_content_width)}{right_content_marker}"
                    middle_lines.append(formatted_line)

        middle_lines.append(border_line) # bottom border
        return middle_lines

    def format_for_file(self, path: Path, forced_filetype: Optional[str] = None) -> Optional[str]:
        """Generates the formatted copyright for a specific file by detecting its format."""
        if not path.is_file():
            print(f"Error: Target is not a valid file - {path}", file=sys.stderr)
            return None

        fmt = detect_file_format(path, forced_filetype)
        if fmt:
            return self._format_copyright(fmt)
        else:
            if not forced_filetype:
                print(f"Info: Auto-detection could not determine a supported filetype for: {path}", file=sys.stderr)
            else:
                print(f"Info: Neither forced type '{forced_filetype}' nor auto-detection matched a supported format for: {path}", file=sys.stderr)
            return None

    def detect_copyright_structure(self, content: str, fmt: str) -> Tuple[int, int, int, int]:
        """
        Detects the start, top border, bottom border, and end line indices.
        Returns (start_idx, top_border_idx, bottom_border_idx, end_idx).
        For line comments, top/bottom border indices will be -1.
        Returns (-1, -1, -1, -1) if not found.
        """
        if fmt not in FILE_TYPE_MAP: return (-1, -1, -1, -1)

        config = FILE_TYPE_MAP[fmt]["config"]
        lines = content.splitlines()
        start_idx, end_idx = -1, -1
        top_border_idx, bottom_border_idx = -1, -1

        comment, box_char = config.get("comment_string", "#"), config.get("box_char", "=")
        start_marker, end_marker = config.get("start_line", ""), config.get("end_line", "")
        is_block = bool(start_marker and end_marker)

        esc_comment_rstrip = re.escape(comment.rstrip())
        esc_comment_base = re.escape(comment.strip())
        esc_box = re.escape(box_char)
        block_border_pat = re.compile(r"^\s*" + esc_comment_rstrip + r".*" + esc_box + r".*" + esc_comment_base + r"\s*$")
        line_border_pat = re.compile(r"^\s*" + esc_comment_rstrip + r"\s+" + esc_box + r"+\s+" + esc_comment_base + r"\s*$")

        if is_block:
            start_pat = re.compile(r"^\s*" + re.escape(start_marker) + r"\s*$")
            end_pat = re.compile(r"^\s*" + re.escape(end_marker) + r"\s*$")
            found_start, found_top, found_bottom, found_end = -1, -1, -1, -1

            for i, line in enumerate(lines):
                if start_pat.match(line.strip()):
                    if i + 1 < len(lines) and block_border_pat.match(lines[i+1].strip()):
                        found_start, found_top = i, i + 1
                        break
            if found_start == -1: return (-1, -1, -1, -1)

            for i in range(len(lines) - 1, found_top, -1):
                if end_pat.match(lines[i].strip()):
                    found_end = i
                    break
            if found_end == -1: return (-1, -1, -1, -1)

            for i in range(found_end - 1, found_top, -1):
                if block_border_pat.match(lines[i].strip()):
                    found_bottom = i
                    break
            if found_bottom == -1: return (-1, -1, -1, -1)

            if found_start < found_top < found_bottom < found_end:
                start_idx, top_border_idx, bottom_border_idx, end_idx = found_start, found_top, found_bottom, found_end
            else:
                return (-1,-1,-1,-1)
        else: # line comment detection
            simple_content_pat = re.compile(r"^\s*" + esc_comment_rstrip)
            p_start, p_end = -1, -1
            for i, line in enumerate(lines):
                if line_border_pat.match(line.strip()):
                    p_start = i
                    break
            if p_start != -1:
                top_border = lines[p_start].strip()
                for i in range(p_start + 1, len(lines)):
                    s_line = lines[i].strip()
                    if s_line == top_border:
                        p_end = i
                        break
                    elif not simple_content_pat.match(lines[i]) and s_line:
                        break
            if p_start != -1 and p_end != -1:
                valid = all(simple_content_pat.match(lines[j]) or not lines[j].strip() for j in range(p_start + 1, p_end))
                if valid:
                    start_idx, end_idx = p_start, p_end

        return (start_idx, top_border_idx, bottom_border_idx, end_idx)

    def _get_current_copyright(self, content: str, fmt: str) -> Optional[str]:
        """Gets the existing copyright block from the file content."""
        start, _, _, end = self.detect_copyright_structure(content, fmt)
        if start == -1:
            return None
        return '\n'.join(content.splitlines()[start : end + 1])

    def delete_copyright(self, path: Path, forced_type: Optional[str] = None) -> Tuple[bool, str]:
        """Deletes the copyright block from a file."""
        try:
            content = path.read_text(encoding='utf-8')
            fmt = detect_file_format(path, forced_type)
            if not fmt: return False, "unsupported_format"

            start, top_border, bottom_border, end = self.detect_copyright_structure(content, fmt)
            if start == -1:
                return False, "not_found"

            lines = content.splitlines()
            config = FILE_TYPE_MAP.get(fmt, {}).get("config", {})
            is_block = bool(config.get("start_line") and config.get("end_line"))

            del_start_idx, del_end_idx = start, end

            if is_block and bottom_border != -1 and end > bottom_border + 1:
                # non-standard block: only delete from top to bottom border
                del_start_idx, del_end_idx = top_border, bottom_border

            lines_before = lines[:del_start_idx]
            lines_after = lines[del_end_idx + 1:]

            new_lines = lines_before
            needs_blank_line = False
            if lines_before and lines_after and lines_after[0].strip():
                last_line_kept = lines_before[-1].strip()
                if last_line_kept.startswith(("#!", "package ", "import ")):
                     needs_blank_line = True

            if needs_blank_line and not (new_lines and not new_lines[-1].strip()):
                new_lines.append("")

            new_lines.extend(lines_after)
            final_content = '\n'.join(new_lines) + ('\n' if not new_lines or new_lines[-1] else '')
            path.write_text(final_content, encoding='utf-8')
            return True, "deleted"

        except FileNotFoundError: return False, "file_not_found"
        except Exception as e:
            print(f"Error: An error occurred while deleting copyright from {path} - {e}", file=sys.stderr)
            return False, f"error: {str(e)}"

    def check_copyright_status(self, path: Path, forced_type: Optional[str] = None) -> Tuple[bool, str]:
        """Checks copyright status. Returns: 'match', 'mismatch', 'not_found', 'unsupported_format', or 'error:*'."""
        try:
            fmt = detect_file_format(path, forced_type)
            if not fmt: return False, "unsupported_format"

            expected = self._format_copyright(fmt)
            if not expected: return False, "error: could not generate expected format"

            content = path.read_text(encoding='utf-8')
            current = self._get_current_copyright(content, fmt)
            if not current: return False, "not_found"

            if current == expected: return True, "match"
            else: return False, "mismatch"
        except FileNotFoundError: return False, "error: file_not_found"
        except Exception as e:
            print(f"Error: An error occurred while checking copyright status for {path} - {e}", file=sys.stderr)
            return False, f"error: {str(e)}"

    def _insert_copyright(self, path: Path, content: str, formatted: str) -> Tuple[bool, str]:
        """Inserts the formatted copyright block into the file content."""
        try:
            lines = content.splitlines()
            insert_pos = 0
            prefix_lines = []

            if lines and lines[0].startswith("#!"):
                prefix_lines.append(lines[0])
                insert_pos = 1
            if len(lines) > insert_pos and re.match(r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)", lines[insert_pos]):
                prefix_lines.append(lines[insert_pos])
                insert_pos += 1
            elif len(lines) > insert_pos and lines[insert_pos].strip().startswith("package "):
                prefix_lines.append(lines[insert_pos])
                insert_pos += 1

            if prefix_lines and len(lines) > insert_pos and lines[insert_pos].strip():
                prefix_lines.append("")

            suffix_lines = lines[insert_pos:]
            new_lines = prefix_lines + [formatted]
            if suffix_lines and suffix_lines[0].strip():
                new_lines.append("")

            new_lines.extend(suffix_lines)
            final_content = '\n'.join(new_lines) + ('\n' if not new_lines or new_lines[-1] else '')
            path.write_text(final_content, encoding='utf-8')
            return True, "inserted"
        except Exception as e:
            print(f"Error: An error occurred while inserting copyright into {path} - {e}", file=sys.stderr)
            return False, f"error: {str(e)}"

    def update_copyright(self, path: Path, forced_type: Optional[str] = None) -> Tuple[bool, str]:
        """Updates the copyright. Replaces content between borders for block, replaces whole block for line comments."""
        try:
            fmt = detect_file_format(path, forced_type)
            if not fmt: return False, "unsupported_format"

            config = FILE_TYPE_MAP.get(fmt, {}).get("config", {})
            is_block = bool(config.get("start_line") and config.get("end_line"))
            content = path.read_text(encoding='utf-8')
            start, top_border, bottom_border, end = self.detect_copyright_structure(content, fmt)

            if start == -1: # not found, so insert
                print(f"Info: Existing copyright not found during update, attempting to insert new one: {path}", file=sys.stderr)
                new_formatted_full = self._format_copyright(fmt)
                if not new_formatted_full: return False, "generate_failed"
                return self._insert_copyright(path, content, new_formatted_full)

            lines = content.splitlines()
            updated_lines = []

            if is_block and top_border != -1 and bottom_border != -1:
                # block comment update: replace middle part
                new_middle_lines = self._generate_formatted_middle(fmt)
                if new_middle_lines is None: return False, "generate_failed"

                updated_lines.extend(lines[:top_border])
                updated_lines.extend(new_middle_lines)
                updated_lines.extend(lines[bottom_border + 1:])
            else:
                # line comment or fallback block update: replace entire block
                if is_block:
                     print(f"Warning: Block structure detected in {path}, but borders could not be determined. Replacing the entire block.", file=sys.stderr)
                new_formatted_full = self._format_copyright(fmt)
                if not new_formatted_full: return False, "generate_failed"

                lines_before = lines[:start]
                lines_after = lines[end + 1:]
                new_block_lines = new_formatted_full.splitlines()

                updated_lines.extend(lines_before)
                updated_lines.extend(new_block_lines)

                if lines_after and lines_after[0].strip():
                     if not (lines_before and not lines_before[-1].strip()):
                         if new_block_lines and new_block_lines[-1].strip():
                             updated_lines.append("")
                updated_lines.extend(lines_after)

            final_content = '\n'.join(updated_lines) + ('\n' if not updated_lines or updated_lines[-1] else '')
            path.write_text(final_content, encoding='utf-8')
            return True, "updated"

        except FileNotFoundError: return False, "file_not_found"
        except Exception as e:
            print(f"Error: An error occurred while updating copyright for {path} - {e}", file=sys.stderr)
            return False, f"error: {str(e)}"

    def add_copyright(self, path: Path, forced_type: Optional[str] = None) -> Tuple[bool, str]:
        """Adds copyright: Skips if matched, updates if mismatched, inserts if not found."""
        try:
            _, status = self.check_copyright_status(path, forced_type)

            if status == "match":
                return True, "skipped"
            elif status == "mismatch":
                print(f"Info: Copyright mismatch detected, attempting to update: {path}", file=sys.stderr)
                return self.update_copyright(path, forced_type)
            elif status == "not_found":
                print(f"Info: Copyright not found, attempting to add: {path}", file=sys.stderr)
                fmt = detect_file_format(path, forced_type)
                if not fmt: return False, "unsupported_format"

                formatted = self._format_copyright(fmt)
                if not formatted: return False, "generate_failed"

                content = path.read_text(encoding='utf-8')
                return self._insert_copyright(path, content, formatted)
            else: # catches "unsupported_format" and "error:*"
                return False, status
        except FileNotFoundError:
            return False, "file_not_found"
        except Exception as e:
            print(f"Error: An error occurred while adding copyright to {path} - {e}", file=sys.stderr)
            return False, f"error: {str(e)}"

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
