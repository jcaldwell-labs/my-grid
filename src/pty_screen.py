"""PTY screen management using pyte terminal emulator.

This module provides a clean wrapper around pyte for proper terminal
emulation in PTY zones. Handles all cursor control, backspace, escape
sequences, and provides scrollback history.
"""

import pyte
from typing import Optional


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
        Get current display lines with optional scrollback.

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
            lines.append(''.join(line_chars))
        return lines

    def _get_scrolled_screen(self, scroll_offset: int) -> list[str]:
        """Get screen display scrolled back into history."""
        # Get history lines (deque of lines)
        history_lines = list(self.screen.history.top)

        # Get current screen lines
        current_lines = self._get_current_screen()

        # Combine: history + current
        all_lines = history_lines + current_lines

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
