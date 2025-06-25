# -*- coding: utf-8 -*-

import argparse
import re

# ====================== ANSI 颜色配置 ======================
COLOR_DEBUG = "\x1b[3;37m"
COLOR_RESET = "\x1b[0m"
COLOR_YELLOW = "\x1b[33m"
COLOR_CYAN = "\x1b[3;36m"
COLOR_BOLD = "\x1b[1m"

# ====================== 工具类 ======================
class ColorHelpFormatter(argparse.HelpFormatter):
    """带精确对齐和颜色支持的帮助格式化器"""

    def __init__(self, prog):
        super().__init__(
            prog,
            max_help_position=40, # Max position for the end of the option string
            width=90,            # Total width
            indent_increment=2   # Default indent increment (used by some base methods)
        )
        # Store action max length for consistent help positioning
        # This needs to be calculated dynamically if actions change,
        # but for typical usage, calculating it once might suffice.
        # We might need to override _add_item or similar if dynamic calculation is critical.
        # For now, rely on max_help_position primarily.
        self._action_max_length = self._max_help_position # Use max_help_position as a reference


    # --- Colorization Helpers ---
    def _colorize(self, text, color):
        """Applies ANSI color codes."""
        return f"{color}{text}{COLOR_RESET}"

    def _bold(self, text):
        """Applies bold formatting."""
        return self._colorize(text, COLOR_BOLD)

    def _yellow(self, text):
        """Applies yellow color."""
        return self._colorize(text, COLOR_YELLOW)

    def _cyan(self, text):
        """Applies cyan color."""
        return self._colorize(text, COLOR_CYAN)

    @staticmethod
    def _strip_colors(text):
        """Removes ANSI color codes from text."""
        return re.sub(r'\x1b\[[0-9;]*m', '', text)


    # --- Section Formatting Overrides ---

    def add_usage(self, usage, actions, groups, prefix=None):
        """Adds the 'USAGE' header before the formatted usage string."""
        if prefix is None:
            # Only add the header text, let _format_usage handle the content and indentation
            prefix = self._bold("USAGE") + "\n"
        super().add_usage(usage, actions, groups, prefix)

    def _format_usage(self, usage, actions, groups, prefix):
        """Formats the usage block with specific indentation and alignment."""
        # Get the default formatted usage string (likely contains 'usage: prog ...')
        # Pass prefix=None as add_usage already handled the bold USAGE conceptually
        usage_str = super()._format_usage(usage, actions, groups, prefix=None)

        # Remove the 'usage: ' prefix if present (case-insensitive)
        usage_str = re.sub(r'^[Uu]sage:\s*', '', usage_str).strip()

        lines = usage_str.split('\n')
        if not lines or not lines[0]: # Handle empty or effectively empty usage
            # Return header with blank line after if usage is empty
            return self._bold("USAGE") + "\n\n"

        # The first line contains the program name and initial args/options
        # Indent it by 2 spaces relative to the USAGE header
        line_2 = "  " + lines[0]

        # --- Calculate alignment for subsequent lines ---
        content_start_index = 2 # Because we added "  " to line_2
        # Look for the first '[' or an all-caps word (potential positional arg)
        # Search *after* the initial indent to find the start of the actual arguments
        align_char_match = re.search(r'(\[|\b[A-Z]{2,})', line_2[content_start_index:])

        indent_pos = -1
        if align_char_match:
            # Calculate the absolute column position for the indent
            indent_pos = content_start_index + align_char_match.start()

        # If no alignment character found, use a fallback indent
        if indent_pos == -1:
             # Fallback: Align with the start of the content in line_2
             indent = " " * content_start_index
        else:
            indent = ' ' * indent_pos
        # --- End of alignment calculation ---

        # Build the final output lines for the usage section
        output_lines = [
            self._bold("USAGE"), # Header line (added by add_usage, but kept here conceptually)
            line_2              # First line of usage (indented, no 'usage:' prefix)
        ]

        # Add subsequent lines (original lines[1:]) with the calculated indent
        for i in range(1, len(lines)):
            stripped_line = lines[i].lstrip() # Remove existing indent/whitespace
            if stripped_line: # Avoid adding purely empty lines with just indent
                output_lines.append(indent + stripped_line)

        # Join lines and add TWO newlines at the end for the blank line before description
        return '\n'.join(output_lines) + "\n\n"


    def format_description(self, description):
        """Formats the description, ensuring left alignment and appropriate spacing."""
        if not description:
            return ""
        # _format_usage adds the blank line *before* the description.
        # This method returns the description + one newline for spacing *after* it.
        return description.lstrip() + "\n"


    def _format_heading(self, heading):
        """Formats argument group headings."""
        # Boldness/Color is applied in main.py when creating groups
        return f"{heading}\n"


    def _format_action(self, action):
        """Formats a single action (option or positional argument) line."""
        # Get the part containing the option strings/metavar (e.g., '-f FILE')
        parts = self._format_action_invocation(action)
        # Calculate the display length (stripping color codes) for alignment
        invoc_length = len(self._strip_colors(parts))
        # Current indent level for this action
        action_header = f"{'':<{self._current_indent}}{parts}"

        # Get the help text
        help_text = self._expand_help(action)
        if not help_text:
            # If no help text, just return the header ending with a newline
            return action_header + "\n"

        # --- Calculate position and width for help text ---
        # Determine where help text should start (aligned column)
        help_position = min(self._action_max_length + 2, self._max_help_position)
        help_start_col = self._current_indent + help_position

        # Calculate padding needed between invocation and help text
        invocation_end_col = self._current_indent + invoc_length
        # Ensure at least 2 spaces padding
        padding = max(help_start_col - invocation_end_col, 2)

        # Calculate the available width for wrapping the help text
        # Ensure a minimum reasonable width for wrapping
        help_width = max(self._width - help_start_col, 10)

        # Wrap the help text lines
        help_lines = self._split_lines(help_text, help_width)
        if not help_lines: # Should not happen if help_text exists, but be safe
             return action_header + "\n"

        # Construct the final formatted lines
        # First line: header + padding + first help line
        first_help_line = f"{action_header}{' ' * padding}{help_lines[0]}"

        # Subsequent lines: indented to align with the first help line
        subsequent_lines = [f"{' ' * help_start_col}{line}" for line in help_lines[1:]]

        # Combine all lines for this action
        all_lines = [first_help_line] + subsequent_lines

        # Ensure the entire formatted action ends with a newline for separation
        return '\n'.join(all_lines) + '\n'


    def _format_action_invocation(self, action):
        """Formats the '-f, --foo FOO' part of the action line with colors."""
        if not action.option_strings: # Positional argument
             # Use _format_args to handle nargs properly (e.g., [FOO ...])
             metavar = self._format_args(action, action.dest.upper())
             # Use cyan for positional arguments
             return self._cyan(metavar)

        # Option argument
        parts = []
        # Add short/long option strings (e.g., -f, --file) in yellow
        parts.extend([self._yellow(s) for s in action.option_strings])

        # Add metavar (e.g., FILE) in cyan if it's expected
        # Check if the action takes an argument (nargs != 0)
        if action.nargs != 0:
             metavar = action.metavar or action.dest.upper()
             if metavar:
                  parts.append(self._cyan(metavar))

        return ' '.join(parts)

# Note: _split_lines is inherited from argparse.HelpFormatter and usually uses textwrap.
# Note: _expand_help is inherited and handles %(default)s, %(prog)s etc.
# Note: _format_args is inherited and formats metavar based on nargs.
