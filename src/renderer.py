"""
Curses-based terminal renderer for the ASCII canvas.

Renders the visible portion of the canvas through the viewport.
"""

import curses
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from canvas import Canvas
    from viewport import Viewport


@dataclass
class GridSettings:
    """Configuration for grid overlay rendering."""
    show_origin: bool = True
    show_major_lines: bool = False
    show_minor_lines: bool = False

    major_interval: int = 10  # Major grid markers every N cells
    minor_interval: int = 5   # Minor markers between major

    # Characters for grid display
    origin_char: str = '+'
    major_char: str = '+'      # Major intersection marker
    minor_char: str = '·'      # Minor intersection marker (subtle dot)
    axis_h_char: str = '-'     # Horizontal axis line (through origin)
    axis_v_char: str = '|'     # Vertical axis line (through origin)


@dataclass
class RenderStyle:
    """Visual style configuration."""
    cursor_char: str | None = None  # None = show cell content, str = override
    empty_char: str = ' '

    # Color pairs (initialized in setup)
    # 0 = default, 1 = cursor, 2 = origin, 3 = major grid, 4 = minor grid
    use_colors: bool = True


class Renderer:
    """
    Curses-based renderer for ASCII canvas.

    Handles all terminal output including canvas content,
    cursor display, grid overlay, and status line.
    """

    def __init__(self, stdscr: "curses.window"):
        self.stdscr = stdscr
        self.grid = GridSettings()
        self.style = RenderStyle()
        self._setup_curses()

    def _setup_curses(self) -> None:
        """Initialize curses settings."""
        curses.curs_set(0)  # Hide hardware cursor
        self.stdscr.keypad(True)
        self.stdscr.nodelay(False)  # Blocking input by default

        # Setup colors if available
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            # Define color pairs
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Cursor
            curses.init_pair(2, curses.COLOR_YELLOW, -1)                  # Origin
            curses.init_pair(3, curses.COLOR_BLUE, -1)                    # Major grid
            curses.init_pair(4, curses.COLOR_BLACK, -1)                   # Minor grid (dim)
            curses.init_pair(5, curses.COLOR_GREEN, -1)                   # Status line

    def get_terminal_size(self) -> tuple[int, int]:
        """Get current terminal dimensions (height, width)."""
        return self.stdscr.getmaxyx()

    def render(
        self,
        canvas: "Canvas",
        viewport: "Viewport",
        status_line: str | None = None
    ) -> None:
        """
        Render the complete frame.

        Args:
            canvas: The canvas to render
            viewport: The viewport defining visible area
            status_line: Optional status text for bottom line
        """
        self.stdscr.erase()

        height, width = self.get_terminal_size()

        # Reserve bottom line for status if provided
        render_height = height - 1 if status_line else height

        # Render each cell in the viewport
        for sy in range(min(render_height, viewport.height)):
            for sx in range(min(width, viewport.width)):
                cx, cy = viewport.screen_to_canvas(sx, sy)
                char, attr = self._get_cell_display(canvas, viewport, cx, cy, sx, sy)

                try:
                    self.stdscr.addch(sy, sx, char, attr)
                except curses.error:
                    # Ignore errors at bottom-right corner
                    pass

        # Render status line
        if status_line:
            self._render_status_line(status_line, height - 1, width)

        self.stdscr.refresh()

    def _get_cell_display(
        self,
        canvas: "Canvas",
        viewport: "Viewport",
        cx: int, cy: int,
        sx: int, sy: int
    ) -> tuple[str, int]:
        """
        Determine what character and attributes to display at a position.

        Returns (char, curses_attr) tuple.
        """
        attr = curses.A_NORMAL
        char = canvas.get_char(cx, cy)

        # Check if this is the cursor position
        is_cursor = (cx == viewport.cursor.x and cy == viewport.cursor.y)
        if is_cursor:
            if self.style.cursor_char:
                char = self.style.cursor_char
            attr = curses.color_pair(1) | curses.A_BOLD
            return char if char != ' ' else self.style.empty_char, attr

        # Check for origin
        if self.grid.show_origin:
            if cx == viewport.origin.x and cy == viewport.origin.y:
                if char == ' ':
                    char = self.grid.origin_char
                attr = curses.color_pair(2) | curses.A_BOLD
                return char, attr

        # Check for grid lines (only show if cell is empty)
        if char == ' ':
            grid_char, grid_attr = self._get_grid_char(cx, cy, viewport)
            if grid_char:
                return grid_char, grid_attr

        # Regular cell
        if char == ' ':
            char = self.style.empty_char

        return char, attr

    def _get_grid_char(
        self,
        cx: int, cy: int,
        viewport: "Viewport"
    ) -> tuple[str | None, int]:
        """
        Get grid overlay character for a position.

        Grid shows intersection markers only (not full lines):
        - Major markers ('+') at every major_interval (default 10)
        - Minor markers ('·') at every minor_interval (default 5)

        Returns (char, attr) or (None, 0) if no grid at this position.
        """
        # Calculate position relative to origin
        rel_x = cx - viewport.origin.x
        rel_y = cy - viewport.origin.y

        # Check if on axis lines (through origin)
        on_x_axis = (rel_y == 0)
        on_y_axis = (rel_x == 0)

        # Check grid intervals
        on_major_x = rel_x % self.grid.major_interval == 0 if self.grid.major_interval > 0 else False
        on_major_y = rel_y % self.grid.major_interval == 0 if self.grid.major_interval > 0 else False
        on_minor_x = rel_x % self.grid.minor_interval == 0 if self.grid.minor_interval > 0 else False
        on_minor_y = rel_y % self.grid.minor_interval == 0 if self.grid.minor_interval > 0 else False

        # Major grid - show markers at intersections of major intervals
        if self.grid.show_major_lines:
            if on_major_x and on_major_y:
                return self.grid.major_char, curses.color_pair(3) | curses.A_DIM

        # Minor grid - show subtle dots at intersections of minor intervals
        # (but not where major markers already are)
        if self.grid.show_minor_lines:
            if on_minor_x and on_minor_y:
                # Skip if this is a major intersection
                if not (on_major_x and on_major_y and self.grid.show_major_lines):
                    return self.grid.minor_char, curses.color_pair(4) | curses.A_DIM

        return None, 0

    def _render_status_line(self, text: str, y: int, width: int) -> None:
        """Render status line at bottom of screen."""
        # Truncate if too long
        if len(text) > width - 1:
            text = text[:width - 4] + "..."

        # Pad to fill width
        text = text.ljust(width - 1)

        try:
            self.stdscr.addstr(y, 0, text, curses.color_pair(5))
        except curses.error:
            pass

    def render_message(self, message: str, row: int = 0) -> None:
        """Render a message overlay (e.g., for command mode)."""
        height, width = self.get_terminal_size()
        if row < 0:
            row = height + row  # Support negative indexing

        text = message[:width - 1]
        try:
            self.stdscr.addstr(row, 0, text, curses.A_BOLD)
            self.stdscr.clrtoeol()
            self.stdscr.refresh()
        except curses.error:
            pass

    def get_input(self) -> int:
        """Get a single keypress. Returns curses key code."""
        return self.stdscr.getch()

    def get_string_input(self, prompt: str, y: int = -1) -> str:
        """
        Get string input from user with echo.

        Args:
            prompt: Prompt to display
            y: Row to display on (-1 for bottom)

        Returns:
            User input string
        """
        height, width = self.get_terminal_size()
        if y < 0:
            y = height + y

        curses.echo()
        curses.curs_set(1)

        try:
            self.stdscr.addstr(y, 0, prompt)
            self.stdscr.clrtoeol()
            self.stdscr.refresh()

            input_str = self.stdscr.getstr(y, len(prompt), width - len(prompt) - 1)
            return input_str.decode('utf-8')
        except curses.error:
            return ""
        finally:
            curses.noecho()
            curses.curs_set(0)

    def flash(self) -> None:
        """Flash the screen (visual bell)."""
        curses.flash()

    def cleanup(self) -> None:
        """Restore terminal state."""
        curses.curs_set(1)
        curses.echo()
        curses.endwin()


def create_status_line(viewport: "Viewport", mode: str = "NAV") -> str:
    """
    Create a formatted status line string.

    Args:
        viewport: Current viewport state
        mode: Current editor mode

    Returns:
        Formatted status string
    """
    cursor = viewport.cursor
    origin = viewport.origin

    return (
        f" [{mode}] "
        f"Cursor: ({cursor.x}, {cursor.y}) | "
        f"Origin: ({origin.x}, {origin.y}) | "
        f"View: ({viewport.x}, {viewport.y})"
    )


def run_with_curses(func):
    """
    Decorator to run a function with curses wrapper.

    Usage:
        @run_with_curses
        def main(stdscr):
            renderer = Renderer(stdscr)
            ...
    """
    def wrapper(*args, **kwargs):
        return curses.wrapper(lambda stdscr: func(stdscr, *args, **kwargs))
    return wrapper
