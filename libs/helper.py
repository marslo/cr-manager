# -*- coding: utf-8 -*-
"""
This module provides a custom argparse.HelpFormatter for colored and well-aligned
help messages in the command-line interface.
"""
import argparse
import re

# ====================== ANSI COLOR CONFIGURATION ======================
COLOR_DEBUG  = "\x1b[3;37m"
COLOR_RESET  = "\x1b[0m"
COLOR_YELLOW = "\x1b[33m"
COLOR_CYAN   = "\x1b[3;36m"
COLOR_BOLD   = "\x1b[1m"

# ====================== UTILITY CLASS ======================
class ColorHelpFormatter( argparse.HelpFormatter ):
    """
    A custom help formatter that provides more control over text alignment
    and adds color to the help output for better readability.
    """

    def __init__(self, prog):
        """Initializes the formatter with specific width and indentation settings."""
        super().__init__(
            prog,
            max_help_position=40,
            width=90,
            indent_increment=2
        )
        self._action_max_length = self._max_help_position

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
        return self._colorize( text, COLOR_CYAN )

    @staticmethod
    def _strip_colors( text: str ) -> str:
        """Removes ANSI color codes from a string to measure its real length."""
        return re.sub( r'\x1b\[[0-9;]*m', '', text )

    # --- section formatting overrides ---
    def add_usage( self, usage, actions, groups, prefix=None ):
        """Overrides the default method to add a bold 'USAGE' prefix."""
        if prefix is None:
            prefix = self._bold("USAGE") + "\n"
        super().add_usage( usage, actions, groups, prefix )

    def _format_usage( self, usage, actions, groups, prefix ):
        """
        Formats the usage block with custom indentation and alignment to ensure
        long usage strings wrap correctly.
        """
        # get the default formatted usage string, but without the "usage: " prefix
        usage_str = super()._format_usage( usage, actions, groups, prefix=None )
        usage_str = re.sub( r'^[Uu]sage:\s*', '', usage_str ).strip()

        lines = usage_str.split('\n')
        if not lines or not lines[0]:
            return self._bold("USAGE") + "\n\n"

        # indent the first line of the usage string slightly
        line_2 = "  " + lines[0]

        # calculate alignment for subsequent lines based on the start of the arguments
        align_char_match = re.search( r'(\[|\b[A-Z]{2,})', line_2 )
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

    def _format_action( self, action: argparse.Action ) -> str:
        """
        Formats a single action ( like '--help' ) and its help text, ensuring
        proper alignment between the action and its description.
        """
        # get the formatted action part, e.g., "-h, --help"
        parts = self._format_action_invocation( action )
        invoc_length = len( self._strip_colors(parts) )
        action_header = f"{'':<{self._current_indent}}{parts}"

        # if there's no help text, just return the action
        help_text = self._expand_help( action )
        if not help_text:
            return action_header + "\n"

        # calculate the starting column and width for the help text
        help_position = min( self._action_max_length + 2, self._max_help_position )
        help_start_col = self._current_indent + help_position
        padding = max( help_start_col - (self._current_indent + invoc_length), 2 )
        help_width = max( self._width - help_start_col, 10 )

        # wrap the help text and combine it with the action header
        help_lines = self._split_lines( help_text, help_width )
        if not help_lines:
            return action_header + "\n"

        first_help_line = f"{action_header}{' ' * padding}{help_lines[0]}"
        subsequent_lines = [ f"{' ' * help_start_col}{line}" for line in help_lines[1:] ]

        return '\n'.join( [first_help_line] + subsequent_lines ) + '\n'

    def _format_action_invocation( self, action: argparse.Action ) -> str:
        """Formats the invocation part of an action ( e.g., '-f, --foo FOO' ) with colors."""
        # for positional arguments like 'files'
        if not action.option_strings:
            metavar = self._format_args( action, action.dest.upper() )
            return self._cyan( metavar )

        # for optional arguments like '--filetype type'
        parts = [ self._yellow(s) for s in action.option_strings ]
        if action.nargs != 0:
            metavar = action.metavar or action.dest.upper()
            if metavar:
                parts.append( self._cyan(metavar) )

        return ' '.join( parts )

# Note: _split_lines, _expand_help, and _format_args are inherited from
# argparse.HelpFormatter and are used here for their default behaviors

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
