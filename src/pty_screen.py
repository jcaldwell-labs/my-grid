"""PTY screen management using pyte terminal emulator.

This module provides a clean wrapper around pyte for proper terminal
emulation in PTY zones. Handles all cursor control, backspace, escape
sequences, and provides scrollback history.
"""

import pyte
from dataclasses import dataclass


@dataclass
class StyledChar:
    """A character with color information from pyte terminal."""

    char: str
    fg: int = -1  # Foreground color (-1 = default, 0-7 = colors)
    bg: int = -1  # Background color (-1 = default, 0-7 = colors)


def _map_pyte_color(pyte_color: str) -> int:
    """
    Map pyte color to my-grid 8-color palette (0-7).

    pyte uses color names like 'default', 'black', 'red', etc.
    We map these to 0-7 for curses.

    Returns:
        Color code 0-7, or -1 for default
    """
    if not pyte_color or pyte_color == "default":
        return -1

    color_map = {
        "black": 0,
        "red": 1,
        "green": 2,
        "yellow": 3,
        "brown": 3,  # pyte uses 'brown' for ANSI yellow (code 33)
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7,
    }

    # Handle basic colors
    if pyte_color in color_map:
        return color_map[pyte_color]

    # Handle bright variants (map to same basic color for 8-color mode)
    if pyte_color.startswith("bright"):
        base_color = pyte_color.replace("bright", "").strip()
        return color_map.get(base_color, -1)

    # Unknown color - use default
    return -1


class PTYScreen:
    """Wrapper around pyte for PTY zone terminal emulation."""

    def __init__(self, width: int, height: int, history: int = 1000):
        """
        Initialize PTY screen with pyte terminal emulator.

        Args:
            width: Screen width in characters
            height: Screen height in characters
            history: Lines of scrollback history to maintain
        """
        self.width = width
        self.height = height
        self.history_size = history

        # Create pyte screen with history support
        self.screen = pyte.HistoryScreen(width, height, history=history)

        # Create stream processor (feeds data to screen)
        self.stream = pyte.Stream(self.screen)

    def feed(self, data: str) -> None:
        """
        Feed terminal data to the emulator.

        Handles all ANSI/VT100 escape sequences, cursor control,
        backspace, line editing, etc.

        Args:
            data: Raw terminal output (may include escape sequences)
        """
        self.stream.feed(data)

    def get_display_lines(self, scroll_offset: int = 0) -> list[str]:
        """
        Get current display lines with optional scrollback (plain text).

        DEPRECATED: Use get_display_lines_styled() for color support.

        Args:
            scroll_offset: Lines to scroll back from bottom
                          0 = current screen (default)
                          N = scroll back N lines into history

        Returns:
            List of strings, one per screen line
        """
        if scroll_offset == 0:
            # Current screen - most common case
            return self._get_current_screen()
        else:
            # Scrolled back into history
            return self._get_scrolled_screen(scroll_offset)

    def get_display_lines_styled(
        self, scroll_offset: int = 0
    ) -> list[list[StyledChar]]:
        """
        Get current display lines with colors and optional scrollback.

        Args:
            scroll_offset: Lines to scroll back from bottom
                          0 = current screen (default)
                          N = scroll back N lines into history

        Returns:
            List of lines, each line is a list of StyledChar with color info
        """
        if scroll_offset == 0:
            # Current screen - most common case
            return self._get_current_screen_styled()
        else:
            # Scrolled back into history
            return self._get_scrolled_screen_styled(scroll_offset)

    def _get_current_screen(self) -> list[str]:
        """Get current screen display."""
        lines = []
        for y in range(self.height):
            # Get line from screen buffer
            line_chars = []
            for x in range(self.width):
                char = self.screen.buffer[y][x]
                # char is a pyte.Char object with .data attribute
                line_chars.append(char.data)
            lines.append("".join(line_chars))
        return lines

    def _get_scrolled_screen(self, scroll_offset: int) -> list[str]:
        """Get screen display scrolled back into history."""
        # Get history lines (StaticDefaultDict objects) and convert to strings
        history_lines = []
        for line_dict in self.screen.history.top:
            line_chars = [line_dict[x].data for x in range(self.width)]
            history_lines.append("".join(line_chars))

        # Get current screen lines
        current_lines = self._get_current_screen()

        # Combine: history + current
        all_lines = history_lines + current_lines

        # Calculate which lines to show
        total = len(all_lines)
        start = max(0, total - self.height - scroll_offset)
        end = start + self.height

        return all_lines[start:end]

    def _get_current_screen_styled(self) -> list[list[StyledChar]]:
        """Get current screen display with color information."""
        lines = []
        for y in range(self.height):
            line_chars = []
            for x in range(self.width):
                char_obj = self.screen.buffer[y][x]
                # Extract character and colors from pyte Char object
                fg = _map_pyte_color(char_obj.fg)
                bg = _map_pyte_color(char_obj.bg)
                line_chars.append(StyledChar(char_obj.data, fg, bg))
            lines.append(line_chars)
        return lines

    def _get_scrolled_screen_styled(self, scroll_offset: int) -> list[list[StyledChar]]:
        """Get screen display scrolled back into history with colors."""
        # Note: pyte history stores StaticDefaultDict objects, not plain strings
        # Each history line is a dict where keys are column indices and values
        # are Char objects. Colors ARE preserved in history!

        # Get history lines (StaticDefaultDict objects)
        history_lines = list(self.screen.history.top)

        # Convert history to styled format WITH colors from Char objects
        styled_history = []
        for line_dict in history_lines:
            styled_line = []
            for x in range(self.width):
                char_obj = line_dict[x]  # StaticDefaultDict returns Char or default
                # Extract character and colors from pyte Char object
                fg = _map_pyte_color(char_obj.fg)
                bg = _map_pyte_color(char_obj.bg)
                styled_line.append(StyledChar(char_obj.data, fg, bg))
            styled_history.append(styled_line)

        # Get current screen with colors
        current_styled = self._get_current_screen_styled()

        # Combine: history + current
        all_lines = styled_history + current_styled

        # Calculate which lines to show
        total = len(all_lines)
        start = max(0, total - self.height - scroll_offset)
        end = start + self.height

        return all_lines[start:end]

    def get_cursor_position(self) -> tuple[int, int]:
        """
        Get current cursor position.

        Returns:
            (x, y) tuple - cursor coordinates
        """
        return (self.screen.cursor.x, self.screen.cursor.y)

    def get_total_lines(self) -> int:
        """
        Get total lines including scrollback history.

        Returns:
            Total number of lines (screen + history)
        """
        return len(self.screen.history.top) + self.height

    def resize(self, width: int, height: int) -> None:
        """
        Resize the terminal screen.

        Args:
            width: New width in characters
            height: New height in characters
        """
        self.width = width
        self.height = height
        self.screen.resize(height, width)

    def reset(self) -> None:
        """Reset the screen (clear display and history)."""
        self.screen.reset()

    def get_line_with_colors(self, y: int) -> list[tuple[str, int, int]]:
        """
        Get a line with color information.

        Args:
            y: Line number (0-based)

        Returns:
            List of (char, fg_color, bg_color) tuples

        Note: For future color support. Currently my-grid ANSI parsing
        handles colors, but this could be enhanced to use pyte's color info.
        """
        line_data = []
        if 0 <= y < self.height:
            for x in range(self.width):
                char = self.screen.buffer[y][x]
                # char has .fg (foreground) and .bg (background) attributes
                # These are pyte color codes that could be mapped to curses colors
                line_data.append((char.data, 0, 0))  # TODO: Map char.fg/bg
        return line_data
