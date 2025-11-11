# -*- coding: utf-8 -*-
"""
This module provides a custom argparse.HelpFormatter for colored and well-aligned
help messages in the command-line interface.
"""
import argparse
import re
import shutil
from wcwidth import wcswidth

# ====================== ANSI COLOR CONFIGURATION ======================
COLOR_RESET     = "\x1b[0m"
COLOR_BOLD      = "\x1b[0;1m"

COLOR_RED       = "\x1b[0;31m"
COLOR_GREEN     = "\x1b[0;32m"
COLOR_YELLOW    = "\x1b[0;33m"
COLOR_BLUE      = "\x1b[0;34m"
COLOR_MAGENTA   = "\x1b[0;35m"
COLOR_CYAN      = "\x1b[0;36m"
COLOR_GRAY      = "\x1b[0;37m"
COLOR_DEBUG     = "\x1b[0;37;2m"

COLOR_RED_I     = "\x1b[0;31;3m"
COLOR_GREEN_I   = "\x1b[0;32;3m"
COLOR_YELLOW_I  = "\x1b[0;33;3m"
COLOR_BLUE_I    = "\x1b[0;34;3m"
COLOR_CYAN_I    = "\x1b[0;36;3m"
COLOR_MAGENTA_I = "\x1b[0;35;3m"
COLOR_GRAY_I    = "\x1b[0;37;3m"
COLOR_DEBUG_I   = "\x1b[0;37;2;3m"

# ====================== UTILITY CLASS ======================
class ColorHelpFormatter( argparse.HelpFormatter ):
    """
    A custom help formatter that provides more control over text alignment
    and adds color to the help output for better readability.
    """

    def __init__(self, prog):
        """Initializes the formatter with specific width and indentation settings."""
        # Get terminal width dynamically, with a fallback to 120.
        try:
            width = shutil.get_terminal_size(fallback=(120, 24)).columns
        except Exception:              # pylint: disable=broad-exception-caught
            width = 120

        super().__init__(
            prog,
            max_help_position=26,
            width=width,
            indent_increment=2
        )
        self._action_max_length = self._max_help_position

    def _format_args(self, action, default_metavar):
        """
        Overrides the default argument formatting to remove brackets from
        optional positional arguments and respect the user-defined metavar.
        """
        if action.nargs == argparse.ZERO_OR_MORE:
            metavar = action.metavar or default_metavar
            return f'{metavar} ...'

        # for all other cases, use the default implementation from the parent class.
        return super()._format_args(action, default_metavar)

    # --- private colorization helpers ---
    @staticmethod
    def _colorize( text: str, color: str ) -> str:
        """Applies ANSI color codes to a string."""
        return f"{color}{text}{COLOR_RESET}"

    def _bold( self, text: str ) -> str:
        """Applies bold formatting."""
        return self._colorize( text, COLOR_BOLD )

    def _yellow( self, text: str ) -> str:
        """Applies yellow color."""
        return self._colorize( text, COLOR_YELLOW )

    def _cyan( self, text: str ) -> str:
        """Applies cyan color."""
        return self._colorize( text, COLOR_CYAN_I )

    def _magenta( self, text: str ) -> str:
        """Applies magenta color."""
        return self._colorize( text, COLOR_MAGENTA_I )

    @staticmethod
    def _strip_colors( text: str ) -> str:
        """Removes ANSI color codes from a string to measure its real length."""
        return re.sub( r'\x1b\[(([0-9]+)(;[0-9]+)*)?[mGKHfJ]', '', text, flags=re.IGNORECASE )

    # --- section formatting overrides ---
    def add_usage( self, usage, actions, groups, prefix=None ):
        """Overrides the default method to add a bold 'USAGE' prefix."""
        if prefix is None:
            prefix = self._bold("USAGE") + "\n"
        super().add_usage( usage, actions, groups, prefix )

    def _format_usage( self, usage, actions, groups, _ ):
        """
        Formats the usage block to be compact and always show short and long options
        in a [-s|--long] format.
        """
        # get the default formatted usage string, but without the "usage: " prefix
        usage_str = super()._format_usage( usage, actions, groups, prefix=None )
        usage_str = re.sub( r'^[Uu]sage:\s*', '', usage_str ).strip()

        def get_combined_option(action_string):
            """
            Finds the action corresponding to a usage string (e.g., '[-v]')
            and returns a combined string like '[-v | --version]'.
            """
            raw_opt = action_string.strip('[]')

            for action in actions:
                if raw_opt in action.option_strings:
                    opts = action.option_strings
                    if len(opts) == 1: return opts[0]
                    sorted_opts = sorted(opts, key=len)
                    return '|'.join(sorted_opts)

            # if it's not an option string (e.g., a positional argument), return as is.
            return action_string.strip()

        # replace each optional argument in the usage string with its new combined form.
        usage_str = re.sub(r'(?<!\x1b)\[([^\[\]\s]+)\]', lambda m: f"[{get_combined_option(m.group(0))}]", usage_str)

        lines = usage_str.split('\n')
        if not lines or not lines[0]: return self._bold("USAGE") + "\n\n"

        # indent the first line of the usage string slightly
        line_2 = '  ' + lines[0]

        # calculate alignment for subsequent lines based on the start of the arguments
        align_char_match = re.search( r'(\[|\b[A-Z]{2,})', self._strip_colors(line_2) )
        if align_char_match:
            indent_pos = align_char_match.start()
            indent = ' ' * indent_pos
        else:
            indent = ' ' * 4  # fallback indent

        # reconstruct the usage string with the new alignment
        output_lines = [ self._bold("USAGE"), line_2 ]
        for line in lines[1:]:
            stripped_line = line.lstrip()
            if stripped_line:
                output_lines.append( indent + stripped_line )

        return '\n'.join( output_lines ) + "\n\n"

    def format_description( self, description: str ) -> str:
        """Formats the main description, ensuring it's left-aligned."""
        if not description:
            return ""
        return description.lstrip() + "\n"

    def _format_heading( self, heading: str ) -> str:
        """Formats argument group headings ( e.g., 'POSITIONAL ARGUMENTS' )."""
        return f"{heading}\n"

    def _wrap_colored_text(self, text: str, width: int) -> list[str]:
        """
        A color-aware text wrapper that correctly handles ANSI codes and wide characters.
        """
        lines = []
        # process each line separately to respect existing newlines
        for line in text.splitlines():
            words = re.split( r'(\s+)', line )
            current_line = ""
            current_line_len = 0

            for word in words:
                # use wcswidth on the stripped string for accurate display width calculation
                word_clean_len = wcswidth( self._strip_colors(word) )

                if word_clean_len > width:
                    if current_line: lines.append( current_line )
                    lines.append( word )
                    current_line = ''
                    current_line_len = 0
                    continue

                if current_line_len + word_clean_len > width:
                    lines.append(current_line)
                    current_line = word
                    current_line_len = word_clean_len
                else:
                    current_line += word
                    current_line_len += word_clean_len

            if current_line:
                lines.append(current_line)

        return [line.strip() for line in lines if line.strip()]

    def _format_action( self, action: argparse.Action ) -> str:
        """
        Formats a single action, now using a dedicated helper for robust text wrapping.
        """
        parts = self._format_action_invocation( action )
        invoc_length = wcswidth( self._strip_colors(parts) )      # use wcswidth here too for consistency
        action_header = f"{'':<{self._current_indent}}{parts}"

        help_text = self._expand_help( action )
        if not help_text: return action_header + '\n'

        # calculate help text position and width
        help_position = min( self._action_max_length + 2, self._max_help_position )
        help_start_col = self._current_indent + help_position
        padding = max( help_start_col - (self._current_indent + invoc_length), 2 )
        help_width = max( self._width - help_start_col, 10 )

        help_lines = self._wrap_colored_text(help_text, help_width)

        if not help_lines: return action_header + "\n"

        first_help_line = f"{action_header}{' ' * padding}{help_lines[0]}"
        subsequent_lines = [ f"{' ' * help_start_col}{line}" for line in help_lines[1:] ]

        return '\n'.join( [first_help_line] + subsequent_lines ) + '\n'

    def _format_action_invocation( self, action: argparse.Action ) -> str:
        """Formats the invocation part of an action ( e.g., '-f, --foo FOO' ) with colors."""
        # for positional arguments like 'files'
        if not action.option_strings:
            metavar = self._format_args( action, action.dest.upper() )
            return self._cyan( metavar )

        # --- NEW, CORRECTED LOGIC ---
        # 1. Join ONLY the option strings (e.g., -t, --filetype) with a comma.
        option_names = [ self._yellow(s) for s in sorted(action.option_strings, key=len) ]
        invocation = ', '.join(option_names)

        # 2. If the action takes a value, append its metavar with a space.
        if action.nargs != 0:
            metavar = action.metavar or action.dest.upper()
            if metavar:
                invocation += f" {self._magenta(metavar)}" # Note the leading space

        return invocation

# Note: _split_lines and _expand_help are inherited from
# argparse.HelpFormatter and are used here for their default behaviors

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
