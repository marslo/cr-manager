# -*- coding: utf-8 -*-

import sys
import textwrap
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

# ====================== 配置区 ======================
LINE_LENGTH = 80

FILE_TYPE_MAP = {
    "format_1": {
        "filetypes": {"python", "shell", "bash", "sh"},
        "suffixes": {".sh", ".py"},
        "config": {
            "start_line": "",
            "end_line": "",
            "comment_string": "#",
            "box_char": "="
        }
    },
    "format_2": {
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

# ====================== 工具函数 (内部使用) ======================
def _parse_modeline(content: str) -> Optional[str]:
    """解析Vim modeline获取文件类型"""
    modeline_pattern = re.compile(r"""
        (?:^|\s)                        # 开头或空格
        (?:vim?|ex):                    # 以vim:或ex:开头
        .*?                             # 任意内容
        (?:filetype|ft)                 # 匹配filetype或ft
        [= ]+                           # 分隔符（=或空格）
        ([a-zA-Z0-9_-]+)                # 捕获文件类型
        (?=\s|:|$)                      # 确保后面是空格、冒号或结束
    """, re.VERBOSE | re.IGNORECASE)

    try:
        # Process only the last few lines for efficiency
        lines_to_check = content.splitlines()[-5:]
        for line in reversed([line.strip() for line in lines_to_check if line.strip()]):
            # Check if it looks like a comment line before applying regex
            if line.startswith(("#", "//", "/*", "*")) and (match := modeline_pattern.search(line)):
                return match.group(1).lower()
    except Exception: # Broad exception for robustness against file content issues
        pass
    return None

def get_supported_filetypes() -> List[str]:
    """获取所有支持的文件类型"""
    all_ft: Set[str] = set()
    for data in FILE_TYPE_MAP.values():
        all_ft.update(data.get("filetypes", set()))
    return sorted(list(all_ft))

def detect_file_format(path: Path, filetype: Optional[str] = None) -> Optional[str]:
    """
    检测文件格式。优先使用强制类型，其次Vim modeline，然后后缀，最后尝试内容探测。
    """
    # 1. 强制文件类型
    if filetype:
        normalized_ft = filetype.lower()
        for fmt, data in FILE_TYPE_MAP.items():
            if normalized_ft in data.get("filetypes", set()):
                return fmt
        print(f"警告: 强制指定的文件类型 '{filetype}' 不在已知配置中。", file=sys.stderr)
        # Fall through to other detection methods if forced type is unknown
        # but maybe the user knows better, let's allow detection to proceed.
        # If you want to strictly return None here, uncomment the next line:
        # return None

    # Helper to read file content safely
    def _safe_read(p: Path) -> Optional[str]:
        try:
            # Try reading a limited amount first for performance/memory
            # Adjust size as needed, 1024 bytes covers typical headers/modelines
            return p.read_text(encoding='utf-8', errors='ignore')
            # return p.read_bytes()[:1024].decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"警告: 无法读取文件内容 {p} 进行检测: {e}", file=sys.stderr)
            return None

    content = _safe_read(path)
    if content is None and not filetype: # Only fail if reading failed AND no forced type
         # If we have a forced type, we might still proceed based on suffix etc.
         # If content is None, modeline/content checks below will be skipped.
         pass # Allow execution to continue to suffix check

    # 2. Vim Modeline (only if content was readable)
    if content:
        if modeline_type := _parse_modeline(content):
            for fmt, data in FILE_TYPE_MAP.items():
                if modeline_type in data.get("filetypes", set()):
                    return fmt

    # 3. File Suffix
    suffix = path.suffix.lower()
    if suffix:
        for fmt, data in FILE_TYPE_MAP.items():
            if suffix in data.get("suffixes", set()):
                return fmt

    # 4. Content/Path Heuristics (Shebang, Jenkinsfile)
    if content: # Only if content was readable
        # Check for Jenkinsfile in path components (case-insensitive)
        if any(part.lower() == "jenkinsfile" for part in path.parts):
             for fmt, data in FILE_TYPE_MAP.items():
                 if "jenkinsfile" in data.get("filetypes", set()):
                     return fmt

        # Check shebang in the first line
        first_line = content.split('\n', 1)[0].strip().lower()
        if first_line.startswith("#!"):
            # More specific checks first
            if "python" in first_line: return "format_1" # Assuming format_1 has python
            if "bash" in first_line or "sh" in first_line: return "format_1" # Assuming format_1 has shell types
            if "groovy" in first_line: return "format_2" # Assuming format_2 has groovy
            # Add more specific shebang checks if needed

    # 5. If a filetype was forced but didn't match known types, maybe it's an alias?
    # This part is tricky. We could try a fallback or just return None.
    # For now, if forced type was given but didn't match and other methods failed, return None.
    if filetype:
        # Re-check if the forced type matches *any* suffix config if primary failed
        normalized_ft = filetype.lower()
        possible_suffix = f".{normalized_ft}"
        for fmt, data in FILE_TYPE_MAP.items():
            if possible_suffix in data.get("suffixes", set()):
                print(f"调试: 强制类型 '{filetype}' 未在 filetypes 中找到, 但匹配后缀 '{possible_suffix}' 对应格式 {fmt}", file=sys.stderr)
                return fmt

    # 6. No format detected
    return None

def _preprocess_copyright_text(raw_text: str) -> List[str]:
    """预处理版权文本：合并空行并保留格式"""
    processed: List[str] = []
    prev_blank = False
    for line in raw_text.splitlines(): # Use splitlines to handle different line endings
        stripped = line.rstrip()
        is_blank = not stripped # More robust check for blank line

        # Skip consecutive blank lines
        if is_blank and prev_blank:
            continue

        processed.append(stripped) # Store the right-stripped line
        prev_blank = is_blank

    # Remove leading/trailing blank lines from the processed list
    while processed and not processed[0]:
        processed.pop(0)
    while processed and not processed[-1]:
        processed.pop()

    return processed

# ====================== 核心功能类 ======================
class CopyrightManager:
    def __init__(self, copyright_path: Path):
        """Initializes the manager with the path to the copyright template file."""
        self.copyright_text = self._load_copyright(copyright_path)
        # Build mappings for faster lookups
        self.supported_types = get_supported_filetypes() # Assumes get_supported_filetypes() is defined globally
        self.filetype_map: Dict[str, str] = {} # filetype -> format_key
        self.suffix_map: Dict[str, str] = {} # suffix -> format_key
        # Assumes FILE_TYPE_MAP is defined globally
        for fmt, data in FILE_TYPE_MAP.items():
            for ft in data.get("filetypes", set()): self.filetype_map[ft] = fmt
            for sfx in data.get("suffixes", set()): self.suffix_map[sfx] = fmt

    @staticmethod
    def _load_copyright(path: Path) -> str:
        """Loads the copyright template text from the specified file."""
        try:
            return path.read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"错误：版权文件未找到 - {path}", file=sys.stderr)
            sys.exit(2) # Exit early if copyright template is missing
        except Exception as e:
            print(f"错误: 读取版权文件失败 {path} - {e}", file=sys.stderr)
            sys.exit(3)

    def _format_copyright(self, fmt: str) -> Optional[str]:
        """Generates the *full* formatted copyright string based on the format key (fmt)."""
        # Assumes FILE_TYPE_MAP is defined globally
        if fmt not in FILE_TYPE_MAP:
            print(f"错误: 未知的内部格式键 '{fmt}'", file=sys.stderr)
            return None

        config = FILE_TYPE_MAP[fmt]["config"]
        start_line = config.get("start_line", "")
        end_line = config.get("end_line", "")
        comment_string = config.get("comment_string", "#")
        box_char = config.get("box_char", "=")
        is_block = bool(start_line and end_line)

        lines = []
        # Assumes _preprocess_copyright_text is defined globally or static
        processed_text_lines = _preprocess_copyright_text(self.copyright_text)
        # Assumes LINE_LENGTH is defined globally
        global_line_length = LINE_LENGTH

        if is_block:
            trimmed_comment = comment_string.strip()
            lines.append(start_line)
            left_border_marker = " " + trimmed_comment
            right_border_marker = trimmed_comment
            border_content_width = global_line_length - len(left_border_marker) - len(right_border_marker)
            if border_content_width < 0: border_content_width = 0
            border_line = f"{left_border_marker}{box_char * border_content_width}{right_border_marker}"
            lines.append(border_line)
            left_content_marker = " " + trimmed_comment + " "
            right_content_marker = " " + trimmed_comment
            text_content_width = global_line_length - len(left_content_marker) - len(right_content_marker)
            if text_content_width < 0: text_content_width = 0
            for line in processed_text_lines:
                if not line: lines.append(f"{left_content_marker}{' ' * text_content_width}{right_content_marker}")
                else:
                    wrapped = textwrap.wrap(line, width=text_content_width, replace_whitespace=False, drop_whitespace=False)
                    for part in wrapped: lines.append(f"{left_content_marker}{part.ljust(text_content_width)}{right_content_marker}")
            lines.append(border_line)
            lines.append(end_line)
        else: # Line comment format
            left_marker = comment_string + " "
            right_marker = " " + comment_string
            content_width = global_line_length - len(left_marker) - len(right_marker)
            if content_width < 0: content_width = 0
            border_line = f"{left_marker}{box_char * content_width}{right_marker}"
            lines.append(border_line)
            for line in processed_text_lines:
                if not line: lines.append(f"{left_marker}{' ' * content_width}{right_marker}")
                else:
                    wrapped = textwrap.wrap(line, width=content_width, replace_whitespace=False, drop_whitespace=False)
                    for part in wrapped: lines.append(f"{left_marker}{part.ljust(content_width)}{right_marker}")
            lines.append(border_line)
        return '\n'.join(lines)

    def _generate_formatted_middle(self, fmt: str) -> Optional[List[str]]:
        """Generates the middle part (borders and text) of a formatted copyright block."""
        # Assumes FILE_TYPE_MAP is defined globally
        if fmt not in FILE_TYPE_MAP:
            print(f"错误: (内部) 未知的格式键 '{fmt}' 用于生成中间部分", file=sys.stderr)
            return None

        config = FILE_TYPE_MAP[fmt]["config"]
        comment_string = config.get("comment_string", "* ") # Default relevant for block
        box_char = config.get("box_char", "*")        # Default relevant for block
        # Assumes LINE_LENGTH is defined globally
        global_line_length = LINE_LENGTH

        trimmed_comment = comment_string.strip()
        middle_lines = []

        # Border Line Calculation: " *=============================*"
        left_border_marker = " " + trimmed_comment
        right_border_marker = trimmed_comment
        border_content_width = global_line_length - len(left_border_marker) - len(right_border_marker)
        if border_content_width < 0: border_content_width = 0
        border_line = f"{left_border_marker}{box_char * border_content_width}{right_border_marker}"
        middle_lines.append(border_line) # Top Border

        # Content Line Calculation: " * Text Content                  *"
        left_content_marker = " " + trimmed_comment + " "
        right_content_marker = " " + trimmed_comment
        text_content_width = global_line_length - len(left_content_marker) - len(right_content_marker)
        if text_content_width < 0: text_content_width = 0

        # Add formatted text lines
        # Assumes _preprocess_copyright_text is defined globally or static
        processed_text_lines = _preprocess_copyright_text(self.copyright_text)
        for line in processed_text_lines:
            if not line:
                middle_lines.append(f"{left_content_marker}{' ' * text_content_width}{right_content_marker}")
            else:
                wrapped_lines = textwrap.wrap(line, width=text_content_width, replace_whitespace=False, drop_whitespace=False)
                for text_part in wrapped_lines:
                    formatted_line = f"{left_content_marker}{text_part.ljust(text_content_width)}{right_content_marker}"
                    middle_lines.append(formatted_line)

        # Bottom Border Line (same as top)
        middle_lines.append(border_line)

        return middle_lines

    def format_for_file(self, path: Path, forced_filetype: Optional[str] = None) -> Optional[str]:
        """Generates the formatted copyright for a specific file, detecting its format."""
        if not path.is_file():
            print(f"错误：目标不是一个有效的文件 - {path}", file=sys.stderr)
            return None
        # Assumes detect_file_format is defined globally
        fmt = detect_file_format(path, forced_filetype)
        if fmt:
            return self._format_copyright(fmt) # Calls the full formatter
        else:
            if not forced_filetype:
                 print(f"信息: 自动检测无法确定支持的文件类型: {path}", file=sys.stderr)
            else:
                 print(f"信息: 强制类型 '{forced_filetype}' 或自动检测均未匹配支持格式: {path}", file=sys.stderr)
            return None

    def detect_copyright_structure(self, content: str, fmt: str) -> Tuple[int, int, int, int]:
        """
        Detects the start, top border, bottom border, and end line indices.
        Returns (start_idx, top_border_idx, bottom_border_idx, end_idx).
        For line comments, top/bottom border indices will be -1.
        Returns (-1, -1, -1, -1) if not found. (Revision 4)
        """
        # Assumes FILE_TYPE_MAP is defined globally
        if fmt not in FILE_TYPE_MAP: return (-1, -1, -1, -1)
        config = FILE_TYPE_MAP[fmt]["config"]
        lines = content.splitlines(); start_idx, end_idx = -1, -1
        top_border_idx, bottom_border_idx = -1, -1 # Initialize to -1

        comment, box_char = config.get("comment_string", "#"), config.get("box_char", "=")
        start_marker, end_marker = config.get("start_line", ""), config.get("end_line", "")
        is_block = bool(start_marker and end_marker)

        # --- Define Patterns ---
        esc_comment_rstrip = re.escape(comment.rstrip())
        esc_comment_base = re.escape(comment.strip())
        esc_box = re.escape(box_char)
        block_border_pat = re.compile(r"^\s*" + esc_comment_rstrip + r".*" + esc_box + r".*" + esc_comment_base + r"\s*$")
        line_border_pat = re.compile(r"^\s*" + esc_comment_rstrip + r"\s+" + esc_box + r"+\s+" + esc_comment_base + r"\s*$")
        # --- End Pattern Definitions ---

        if is_block:
            # --- Block Comment Detection ---
            start_pat = re.compile(r"^\s*" + re.escape(start_marker) + r"\s*$")
            end_pat = re.compile(r"^\s*" + re.escape(end_marker) + r"\s*$")

            found_start = -1
            found_top = -1
            found_bottom = -1
            found_end = -1

            # 1. Find first start marker '/**' & adjacent top border
            for i, line in enumerate(lines):
                if start_pat.match(line.strip()):
                    if i + 1 < len(lines) and block_border_pat.match(lines[i+1].strip()):
                         found_start = i
                         found_top = i + 1
                         break
            if found_start == -1: return (-1, -1, -1, -1)

            # 2. Find the *last* end marker '**/' *after* the found top border
            for i in range(len(lines) - 1, found_top, -1):
                 if end_pat.match(lines[i].strip()):
                      found_end = i
                      break
            if found_end == -1: return (-1, -1, -1, -1)

            # 3. Find the *last* bottom border *between* top border (exclusive) and end marker (exclusive)
            for i in range(found_end - 1, found_top, -1):
                 if block_border_pat.match(lines[i].strip()):
                      found_bottom = i
                      break
            if found_bottom == -1: return (-1, -1, -1, -1)

            # 4. Basic structural check passed
            if found_start < found_top < found_bottom < found_end:
                 start_idx = found_start
                 top_border_idx = found_top
                 bottom_border_idx = found_bottom
                 end_idx = found_end
            else: return (-1,-1,-1,-1)
            # --- End Block Comment Detection ---

        else:
            # --- Line Comment Detection ---
            simple_content_pat = re.compile(r"^\s*" + esc_comment_rstrip) # Define locally needed pattern
            p_start, p_end = -1, -1
            for i, line in enumerate(lines):
                if line_border_pat.match(line.strip()): p_start = i; break
            if p_start != -1:
                top_border = lines[p_start].strip()
                for i in range(p_start+1, len(lines)):
                    s_line = lines[i].strip()
                    if s_line == top_border: p_end = i; break
                    elif not simple_content_pat.match(lines[i]) and s_line: break
            if p_start!=-1 and p_end!=-1:
                valid = all(simple_content_pat.match(lines[j]) or not lines[j].strip() for j in range(p_start+1, p_end))
                if valid:
                    start_idx = p_start
                    end_idx = p_end
                    # top_border_idx and bottom_border_idx remain -1
            # --- End Line Comment Detection ---

        return (start_idx, top_border_idx, bottom_border_idx, end_idx)

    def _get_current_copyright(self, content: str, fmt: str) -> Optional[str]:
        """Gets the existing copyright block content (including borders) from the file content."""
        # Unpack all four, though only start/end are used here
        start, _, _, end = self.detect_copyright_structure(content, fmt)
        if start == -1:
            return None
        return '\n'.join(content.splitlines()[start : end + 1])

    def delete_copyright(self, path: Path, forced_type: Optional[str] = None) -> Tuple[bool, str]:
        """
        Deletes copyright block. For blocks with extra lines after bottom border,
        only deletes from top border to bottom border inclusive.
        """
        try:
            content = path.read_text(encoding='utf-8')
            # Assumes detect_file_format is defined globally
            fmt = detect_file_format(path, forced_type)
            if not fmt: return False, "unsupported_format"

            # Get all indices
            start, top_border, bottom_border, end = self.detect_copyright_structure(content, fmt)

            if start == -1:
                return False, "not_found" # No block detected

            lines = content.splitlines()
            lines_before = []
            lines_after = []

            # Determine if it's a block format
            # Assumes FILE_TYPE_MAP is defined globally
            config = FILE_TYPE_MAP.get(fmt, {}).get("config", {})
            is_block = bool(config.get("start_line") and config.get("end_line"))

            if is_block:
                 # Use indices returned by detect_copyright_structure
                 is_standard_block = (end == bottom_border + 1) if bottom_border != -1 else False # Check if standard

                 if is_standard_block:
                     # --- Standard Block: Delete from start to end ---
                     lines_before = lines[:start]
                     lines_after = lines[end + 1:]
                 else: # Non-standard block (end > bottom_border + 1) or potential issue
                     # Check if detection was successful (bottom_border found)
                     if bottom_border != -1:
                          # --- Non-Standard Block: Delete from top_border to bottom_border ---
                          lines_before = lines[:top_border]
                          lines_after = lines[bottom_border + 1 :]
                     else:
                           # Should not happen if start != -1 for block, but handle defensively
                           print(f"警告: 在 {path} 中检测到块结构，但无法确定标准性，将删除整个块。", file=sys.stderr)
                           lines_before = lines[:start]
                           lines_after = lines[end + 1:]
            else: # Line Comment or Non-Block
                 # --- Delete from start to end ---
                 lines_before = lines[:start]
                 lines_after = lines[end + 1:]

            # --- Reconstruct content with spacing logic ---
            new_lines = lines_before
            last_line_kept = lines_before[-1] if lines_before else None
            first_line_after = lines_after[0] if lines_after else None
            # Determine original start of deletion for import check
            original_delete_start = start
            if is_block and bottom_border != -1 and not is_standard_block:
                 original_delete_start = top_border # Deletion starts at top border in this case

            needs_blank = False
            if last_line_kept is not None and first_line_after is not None and first_line_after.strip():
                if last_line_kept.startswith("#!"): needs_blank = True
                elif last_line_kept.strip().startswith("package "): needs_blank = True
                elif last_line_kept.strip().startswith("import "):
                     imports_existed_before = any(l.strip().startswith("import ") for l in lines[:original_delete_start])
                     if imports_existed_before: needs_blank = True

            if needs_blank and not (new_lines and not new_lines[-1].strip()):
                new_lines.append("")
            # --- End Spacing Logic ---

            new_lines.extend(lines_after)

            final_content = '\n'.join(new_lines) + ('\n' if not new_lines or new_lines[-1] else '') # Ensure trailing newline
            path.write_text(final_content, encoding='utf-8');
            return True, "deleted"

        except FileNotFoundError: return False, "file_not_found"
        except Exception as e: print(f"错误: 删除版权时出错 {path} - {e}", file=sys.stderr); return False, f"error: {str(e)}"


    def check_copyright_status(self, path: Path, forced_type: Optional[str] = None) -> Tuple[bool, str]:
        """
        Checks copyright status: "match", "mismatch", "not_found", "unsupported_format", "error: <msg>"
        """
        try:
            # Assumes detect_file_format is defined globally
            fmt = detect_file_format(path, forced_type);
            if not fmt: return False, "unsupported_format"
            expected = self._format_copyright(fmt)
            if not expected: return False, "error: could not generate expected format"
            content = path.read_text(encoding='utf-8')
            # _get_current_copyright uses the updated 4-tuple detect internally
            current = self._get_current_copyright(content, fmt)
            if not current: return False, "not_found"
            # Exact comparison of the full block
            if current == expected: return True, "match"
            else: return False, "mismatch"
        except FileNotFoundError: return False, "error: file_not_found"
        except Exception as e: print(f"错误: 检查版权时出错 {path} - {e}", file=sys.stderr); return False, f"error: {str(e)}"

    def _insert_copyright(self, path: Path, content: str, formatted: str) -> Tuple[bool, str]:
        """Inserts the *full* formatted copyright block into the file content."""
        try:
            lines = content.splitlines(); insert_pos = 0; prefix_lines = []
            # Handle Shebang, encoding, package
            if lines and lines[0].startswith("#!"): prefix_lines.append(lines[0]); insert_pos = 1
            if len(lines) > insert_pos and re.match(r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)", lines[insert_pos]):
                 prefix_lines.append(lines[insert_pos]); insert_pos += 1
            elif len(lines) > insert_pos and lines[insert_pos].strip().startswith("package "):
                 prefix_lines.append(lines[insert_pos]); insert_pos += 1
            # Add blank line after prefix if needed
            if prefix_lines and len(lines) > insert_pos and lines[insert_pos].strip(): prefix_lines.append("")
            suffix_lines = lines[insert_pos:]
            # Construct new content with blank line after copyright if needed
            new_lines = prefix_lines + [formatted]
            if suffix_lines and suffix_lines[0].strip(): new_lines.append("")
            new_lines.extend(suffix_lines)
            final_content = '\n'.join(new_lines) + ('\n' if not new_lines or new_lines[-1] else '') # Ensure trailing newline
            path.write_text(final_content, encoding='utf-8'); return True, "inserted"
        except Exception as e: print(f"错误: 插入版权时出错 {path} - {e}", file=sys.stderr); return False, f"error: {str(e)}"

    def update_copyright(self, path: Path, forced_type: Optional[str] = None) -> Tuple[bool, str]:
        """Updates the copyright. Replaces content between borders for block, replaces all for line."""
        try:
            # Assumes detect_file_format is defined globally
            fmt = detect_file_format(path, forced_type)
            if not fmt: return False, "unsupported_format"

            # Assumes FILE_TYPE_MAP is defined globally
            config = FILE_TYPE_MAP.get(fmt, {}).get("config", {})
            is_block = bool(config.get("start_line") and config.get("end_line"))

            content = path.read_text(encoding='utf-8')
            # Unpack all four indices now
            start, top_border, bottom_border, end = self.detect_copyright_structure(content, fmt)

            if start == -1: # Not found, insert new full block
                 print(f"信息: 更新时未找到现有版权块，将尝试插入新版权: {path}", file=sys.stderr)
                 new_formatted_full = self._format_copyright(fmt)
                 if not new_formatted_full: return False, "generate_failed"
                 # Pass original content to _insert_copyright
                 return self._insert_copyright(path, content, new_formatted_full)

            # --- Found existing block ---
            lines = content.splitlines()

            if is_block:
                # --- Block Comment Update Logic ---
                # Check if detection gave valid border indices
                if top_border == -1 or bottom_border == -1:
                     print(f"警告: 在 {path} 中检测到块结构，但无法确定边框，将替换整个块。", file=sys.stderr)
                     # Fallback to replacing the whole block if borders weren't reliably found
                     is_block = False # Treat as non-block for replacement logic below
                else:
                    # Proceed with replacing middle part
                    # if '--verbose' in sys.argv or '-v' in sys.argv: # Optional verbose msg
                    #     print(f"调试: 检测到块注释格式，更新中间部分 ({start+1} to {bottom_border}): {path}", file=sys.stderr)
                    new_middle_lines = self._generate_formatted_middle(fmt)
                    if new_middle_lines is None: return False, "generate_failed"

                    lines_before_start = lines[:start]
                    original_start_line = lines[start]
                    original_after_bottom_border = lines[bottom_border + 1 : end]
                    original_end_line = lines[end]
                    lines_after_end = lines[end + 1:]

                    updated_lines = ( lines_before_start + [original_start_line] + new_middle_lines +
                                      original_after_bottom_border + [original_end_line] + lines_after_end )
            # --- Fallthrough or Line Comment Update Logic ---
            if not is_block: # Handles actual line comments OR fallback from block
                new_formatted_full = self._format_copyright(fmt)
                if not new_formatted_full: return False, "generate_failed"

                lines_before = lines[:start]
                lines_after = lines[end + 1:]
                new_block_lines = new_formatted_full.splitlines()
                updated_lines = lines_before + new_block_lines
                # Add blank line after if needed (check last line of new block)
                if lines_after and lines_after[0].strip():
                     if not (lines_before and not lines_before[-1].strip()):
                           if new_block_lines and new_block_lines[-1].strip():
                                updated_lines.append("")
                updated_lines.extend(lines_after)
            # --- End Update Logic ---

            # Write the result
            final_content = '\n'.join(updated_lines) + ('\n' if not updated_lines or updated_lines[-1] else '') # Ensure trailing newline
            path.write_text(final_content, encoding='utf-8')
            return True, "updated"

        except FileNotFoundError: return False, "file_not_found"
        except Exception as e: print(f"错误: 更新版权时出错 {path} - {e}", file=sys.stderr); return False, f"error: {str(e)}"


    def add_copyright(self, path: Path, forced_type: Optional[str] = None) -> Tuple[bool, str]:
        """Adds copyright: Skips if match, updates if mismatch, inserts if not found."""
        try:
             # Use '_' for the unused 'matches' boolean value
             _, status = self.check_copyright_status(path, forced_type)

             if status == "match":
                 return True, "skipped" # Already exists and matches
             elif status == "mismatch":
                 print(f"信息: 版权不匹配，将尝试更新: {path}", file=sys.stderr)
                 return self.update_copyright(path, forced_type) # Uses the NEW update logic
             elif status == "not_found":
                  print(f"信息: 未找到版权，将尝试添加: {path}", file=sys.stderr)
                  # Assumes detect_file_format is defined globally
                  fmt = detect_file_format(path, forced_type)
                  if not fmt: return False, "unsupported_format"
                  formatted = self._format_copyright(fmt) # Add needs full format
                  if not formatted: return False, "generate_failed"
                  content = path.read_text(encoding='utf-8')
                  return self._insert_copyright(path, content, formatted) # Insert uses full format
             elif status == "unsupported_format":
                 return False, "unsupported_format"
             else: # Handle errors from check_copyright_status ("error: <msg>")
                 return False, status
        except FileNotFoundError:
            return False, "file_not_found"
        except Exception as e:
            print(f"错误: 添加版权时出错 {path} - {e}", file=sys.stderr)
            return False, f"error: {str(e)}"
