# -*- coding: utf-8 -*-

# libs/helper.py
import argparse
import re

# ====================== ANSI COLOR CONFIGURATION ======================
COLOR_DEBUG = "\x1b[3;37m"
COLOR_RESET = "\x1b[0m"
COLOR_YELLOW = "\x1b[33m"
COLOR_CYAN = "\x1b[3;36m"
COLOR_BOLD = "\x1b[1m"

# ====================== UTILITY CLASS ======================
class ColorHelpFormatter(argparse.HelpFormatter):
    """A help formatter with precise alignment and color support."""

    def __init__(self, prog):
        super().__init__(
            prog,
            max_help_position=40,
            width=90,
            indent_increment=2
        )
        self._action_max_length = self._max_help_position

    # --- colorization helpers ---
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

    # --- section formatting overrides ---
    def add_usage(self, usage, actions, groups, prefix=None):
        """Adds the 'USAGE' header before the formatted usage string."""
        if prefix is None:
            prefix = self._bold("USAGE") + "\n"
        super().add_usage(usage, actions, groups, prefix)

    def _format_usage(self, usage, actions, groups, prefix):
        """Formats the usage block with specific indentation and alignment."""
        usage_str = super()._format_usage(usage, actions, groups, prefix=None)
        usage_str = re.sub(r'^[Uu]sage:\s*', '', usage_str).strip()

        lines = usage_str.split('\n')
        if not lines or not lines[0]:
            return self._bold("USAGE") + "\n\n"

        # indent the first line of the usage string.
        line_2 = "  " + lines[0]

        # calculate alignment for subsequent lines based on the start of the arguments.
        content_start_index = 2
        align_char_match = re.search(r'(\[|\b[A-Z]{2,})', line_2[content_start_index:])

        if align_char_match:
            indent_pos = content_start_index + align_char_match.start()
            indent = ' ' * indent_pos
        else:
            indent = " " * content_start_index # fallback indent

        # build the final output lines for the usage section.
        output_lines = [self._bold("USAGE"), line_2]
        for i in range(1, len(lines)):
            stripped_line = lines[i].lstrip()
            if stripped_line:
                output_lines.append(indent + stripped_line)

        # join lines and add two newlines for spacing.
        return '\n'.join(output_lines) + "\n\n"

    def format_description(self, description):
        """Formats the description, ensuring left alignment and appropriate spacing."""
        if not description:
            return ""
        # _format_usage adds a blank line before the description.
        # this method adds a newline for spacing after it.
        return description.lstrip() + "\n"

    def _format_heading(self, heading):
        """Formats argument group headings."""
        return f"{heading}\n"

    def _format_action(self, action):
        """Formats a single action (option or positional argument) line."""
        parts = self._format_action_invocation(action)
        invoc_length = len(self._strip_colors(parts))
        action_header = f"{'':<{self._current_indent}}{parts}"

        help_text = self._expand_help(action)
        if not help_text:
            return action_header + "\n"

        # calculate position and width for the help text.
        help_position = min(self._action_max_length + 2, self._max_help_position)
        help_start_col = self._current_indent + help_position
        padding = max(help_start_col - (self._current_indent + invoc_length), 2)
        help_width = max(self._width - help_start_col, 10)

        # wrap the help text.
        help_lines = self._split_lines(help_text, help_width)
        if not help_lines:
            return action_header + "\n"

        # construct the final formatted lines for the action.
        first_help_line = f"{action_header}{' ' * padding}{help_lines[0]}"
        subsequent_lines = [f"{' ' * help_start_col}{line}" for line in help_lines[1:]]
        all_lines = [first_help_line] + subsequent_lines

        # ensure the entire formatted action ends with a newline.
        return '\n'.join(all_lines) + '\n'

    def _format_action_invocation(self, action):
        """Formats the '-f, --foo FOO' part of the action line with colors."""
        if not action.option_strings: # positional argument
            metavar = self._format_args(action, action.dest.upper())
            return self._cyan(metavar)

        # option argument
        parts = [self._yellow(s) for s in action.option_strings]
        if action.nargs != 0:
            metavar = action.metavar or action.dest.upper()
            if metavar:
                parts.append(self._cyan(metavar))
        return ' '.join(parts)

# Note: _split_lines, _expand_help, and _format_args are inherited from
# argparse.HelpFormatter and handle text wrapping, placeholder expansion,
# and argument formatting respectively.

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
