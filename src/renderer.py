"""
Curses-based terminal renderer for the ASCII canvas.

Renders the visible portion of the canvas through the viewport.
"""

import curses
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from canvas import Canvas
    from viewport import Viewport
    from modes import Selection


class GridLineMode(Enum):
    """Grid display modes."""
    OFF = auto()      # No grid display
    MARKERS = auto()  # Intersection markers only (default)
    LINES = auto()    # Full grid lines
    DOTS = auto()     # Dots along grid lines


@dataclass
class GridSettings:
    """Configuration for grid overlay rendering."""
    show_origin: bool = True
    show_major_lines: bool = False
    show_minor_lines: bool = False

    major_interval: int = 10  # Major grid markers every N cells
    minor_interval: int = 5   # Minor markers between major

    # Grid line mode
    line_mode: GridLineMode = GridLineMode.MARKERS

    # Ruler and label display
    show_rulers: bool = False       # Edge rulers with tick marks
    show_labels: bool = False       # Coordinate labels at intervals
    label_interval: int = 50        # How often to show coordinate labels

    # Characters for grid display
    origin_char: str = '+'
    major_char: str = '+'      # Major intersection marker
    minor_char: str = '·'      # Minor intersection marker (subtle dot)
    axis_h_char: str = '-'     # Horizontal axis line (through origin)
    axis_v_char: str = '|'     # Vertical axis line (through origin)

    # Line mode characters
    line_h_char: str = '─'     # Horizontal grid line
    line_v_char: str = '│'     # Vertical grid line
    line_cross_char: str = '┼' # Grid line intersection
    line_major_h: str = '═'    # Major horizontal line
    line_major_v: str = '║'    # Major vertical line
    line_major_cross: str = '╬' # Major intersection


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

        # Color pair cache: (fg, bg) -> pair_number
        self._color_pair_cache: dict[tuple[int, int], int] = {}
        self._next_color_pair = 11  # Start after reserved pairs

        # Setup colors if available
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            # Reserved color pairs (1-10)
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Cursor
            curses.init_pair(2, curses.COLOR_YELLOW, -1)                  # Origin
            curses.init_pair(3, curses.COLOR_BLUE, -1)                    # Major grid
            curses.init_pair(4, curses.COLOR_BLACK, -1)                   # Minor grid (dim)
            curses.init_pair(5, curses.COLOR_GREEN, -1)                   # Status line
            curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)    # Visual selection

    def _get_color_pair(self, fg: int, bg: int) -> int:
        """
        Get or create a color pair for the given foreground and background.

        Returns the curses color pair number.
        """
        # Default colors don't need a special pair
        if fg == -1 and bg == -1:
            return 0

        key = (fg, bg)
        if key in self._color_pair_cache:
            return self._color_pair_cache[key]

        # Create new color pair if we have room
        try:
            max_pairs = curses.COLOR_PAIRS
            if self._next_color_pair < max_pairs:
                curses.init_pair(self._next_color_pair, fg, bg)
                self._color_pair_cache[key] = self._next_color_pair
                pair_num = self._next_color_pair
                self._next_color_pair += 1
                return pair_num
        except curses.error:
            pass

        # Fall back to no color if we can't create pair
        return 0

    def get_terminal_size(self) -> tuple[int, int]:
        """Get current terminal dimensions (height, width)."""
        return self.stdscr.getmaxyx()

    def render(
        self,
        canvas: "Canvas",
        viewport: "Viewport",
        status_line: str | None = None,
        selection: "Selection | None" = None
    ) -> None:
        """
        Render the complete frame.

        Args:
            canvas: The canvas to render
            viewport: The viewport defining visible area
            status_line: Optional status text for bottom line
            selection: Optional visual selection to highlight
        """
        self.stdscr.erase()

        height, width = self.get_terminal_size()

        # Calculate render area accounting for rulers and status
        ruler_offset_x = 0
        ruler_offset_y = 0

        if self.grid.show_rulers:
            ruler_offset_x = 6  # Space for Y-axis labels (e.g., "-1234 ")
            ruler_offset_y = 1  # Space for X-axis ruler

        # Reserve bottom line for status if provided
        status_lines = 1 if status_line else 0
        render_height = height - status_lines - ruler_offset_y
        render_width = width - ruler_offset_x

        # Render rulers if enabled
        if self.grid.show_rulers:
            self._render_rulers(viewport, width, height, ruler_offset_x, ruler_offset_y)

        # Render each cell in the viewport
        for sy in range(min(render_height, viewport.height)):
            for sx in range(min(render_width, viewport.width)):
                cx, cy = viewport.screen_to_canvas(sx, sy)
                char, attr = self._get_cell_display(canvas, viewport, cx, cy, sx, sy, selection)

                try:
                    self.stdscr.addch(sy + ruler_offset_y, sx + ruler_offset_x, char, attr)
                except curses.error:
                    # Ignore errors at bottom-right corner
                    pass

        # Render coordinate labels if enabled
        if self.grid.show_labels:
            self._render_coordinate_labels(viewport, width, height, ruler_offset_x, ruler_offset_y)

        # Render status line
        if status_line:
            self._render_status_line(status_line, height - 1, width)

        self.stdscr.refresh()

    def _get_cell_display(
        self,
        canvas: "Canvas",
        viewport: "Viewport",
        cx: int, cy: int,
        sx: int, sy: int,
        selection: "Selection | None" = None
    ) -> tuple[str, int]:
        """
        Determine what character and attributes to display at a position.

        Returns (char, curses_attr) tuple.
        """
        attr = curses.A_NORMAL
        cell = canvas.get(cx, cy)
        char = cell.char

        # Check if this is the cursor position
        is_cursor = (cx == viewport.cursor.x and cy == viewport.cursor.y)
        if is_cursor:
            if self.style.cursor_char:
                char = self.style.cursor_char
            attr = curses.color_pair(1) | curses.A_BOLD
            return char if char != ' ' else self.style.empty_char, attr

        # Check if within visual selection (but not cursor - handled above)
        if selection is not None and selection.contains(cx, cy):
            attr = curses.color_pair(6)  # Visual selection color
            if char == ' ':
                char = self.style.empty_char
            return char, attr

        # Check for origin
        if self.grid.show_origin:
            if cx == viewport.origin.x and cy == viewport.origin.y:
                if char == ' ':
                    char = self.grid.origin_char
                attr = curses.color_pair(2) | curses.A_BOLD
                return char, attr

        # Check for cell colors
        if cell.has_color():
            pair = self._get_color_pair(cell.fg, cell.bg)
            attr = curses.color_pair(pair)
            if char == ' ':
                char = self.style.empty_char
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

        Supports multiple grid modes:
        - MARKERS: Intersection markers only (default)
        - LINES: Full grid lines with box-drawing characters
        - DOTS: Dots along grid lines
        - OFF: No grid display

        Returns (char, attr) or (None, 0) if no grid at this position.
        """
        # If grid is off, return nothing
        if self.grid.line_mode == GridLineMode.OFF:
            return None, 0

        # Calculate position relative to origin
        rel_x = cx - viewport.origin.x
        rel_y = cy - viewport.origin.y

        # Check grid intervals
        major_int = self.grid.major_interval
        minor_int = self.grid.minor_interval

        on_major_x = (rel_x % major_int == 0) if major_int > 0 else False
        on_major_y = (rel_y % major_int == 0) if major_int > 0 else False
        on_minor_x = (rel_x % minor_int == 0) if minor_int > 0 else False
        on_minor_y = (rel_y % minor_int == 0) if minor_int > 0 else False

        # Determine what type of grid position this is
        is_major_intersection = on_major_x and on_major_y
        is_minor_intersection = on_minor_x and on_minor_y
        is_on_major_h = on_major_y  # On a horizontal major line
        is_on_major_v = on_major_x  # On a vertical major line
        is_on_minor_h = on_minor_y  # On a horizontal minor line
        is_on_minor_v = on_minor_x  # On a vertical minor line

        # MARKERS mode - original behavior
        if self.grid.line_mode == GridLineMode.MARKERS:
            if self.grid.show_major_lines and is_major_intersection:
                return self.grid.major_char, curses.color_pair(3) | curses.A_DIM
            if self.grid.show_minor_lines and is_minor_intersection:
                if not (is_major_intersection and self.grid.show_major_lines):
                    return self.grid.minor_char, curses.color_pair(4) | curses.A_DIM
            return None, 0

        # LINES mode - full grid lines with box-drawing characters
        if self.grid.line_mode == GridLineMode.LINES:
            # Major intersections
            if self.grid.show_major_lines and is_major_intersection:
                return self.grid.line_major_cross, curses.color_pair(3)

            # Major lines (not at intersection)
            if self.grid.show_major_lines:
                if is_on_major_h and not is_on_major_v:
                    return self.grid.line_major_h, curses.color_pair(3) | curses.A_DIM
                if is_on_major_v and not is_on_major_h:
                    return self.grid.line_major_v, curses.color_pair(3) | curses.A_DIM

            # Minor intersections
            if self.grid.show_minor_lines and is_minor_intersection:
                if not (is_major_intersection and self.grid.show_major_lines):
                    return self.grid.line_cross_char, curses.color_pair(4) | curses.A_DIM

            # Minor lines (not at intersection)
            if self.grid.show_minor_lines:
                if is_on_minor_h and not (is_on_major_h and self.grid.show_major_lines):
                    return self.grid.line_h_char, curses.color_pair(4) | curses.A_DIM
                if is_on_minor_v and not (is_on_major_v and self.grid.show_major_lines):
                    return self.grid.line_v_char, curses.color_pair(4) | curses.A_DIM

            return None, 0

        # DOTS mode - dots along grid lines
        if self.grid.line_mode == GridLineMode.DOTS:
            if self.grid.show_major_lines:
                if is_on_major_h or is_on_major_v:
                    return '•', curses.color_pair(3) | curses.A_DIM
            if self.grid.show_minor_lines:
                if is_on_minor_h or is_on_minor_v:
                    if not ((is_on_major_h or is_on_major_v) and self.grid.show_major_lines):
                        return '·', curses.color_pair(4) | curses.A_DIM
            return None, 0

        return None, 0

    def _render_rulers(
        self,
        viewport: "Viewport",
        width: int,
        height: int,
        offset_x: int,
        offset_y: int
    ) -> None:
        """
        Render coordinate rulers along the edges.

        Args:
            viewport: Current viewport
            width: Terminal width
            height: Terminal height
            offset_x: X offset for canvas content
            offset_y: Y offset for canvas content
        """
        ruler_attr = curses.color_pair(4) | curses.A_DIM

        # X-axis ruler (top row)
        for sx in range(width - offset_x):
            cx, _ = viewport.screen_to_canvas(sx, 0)

            # Show tick marks at intervals
            if cx % 10 == 0:
                # Show coordinate label every 10 units
                label = str(cx)
                try:
                    # Position label centered on tick
                    label_start = sx + offset_x - len(label) // 2
                    if label_start >= offset_x and label_start + len(label) < width:
                        self.stdscr.addstr(0, label_start, label, ruler_attr)
                except curses.error:
                    pass
            elif cx % 5 == 0:
                # Minor tick
                try:
                    self.stdscr.addch(0, sx + offset_x, '·', ruler_attr)
                except curses.error:
                    pass

        # Y-axis ruler (left column)
        for sy in range(height - offset_y - 1):  # -1 for status line
            _, cy = viewport.screen_to_canvas(0, sy)

            # Show coordinate label at intervals
            if cy % 10 == 0:
                label = f"{cy:>5}"
                try:
                    self.stdscr.addstr(sy + offset_y, 0, label, ruler_attr)
                except curses.error:
                    pass
            elif cy % 5 == 0:
                # Minor tick
                try:
                    self.stdscr.addch(sy + offset_y, 4, '·', ruler_attr)
                except curses.error:
                    pass

    def _render_coordinate_labels(
        self,
        viewport: "Viewport",
        width: int,
        height: int,
        offset_x: int,
        offset_y: int
    ) -> None:
        """
        Render coordinate labels at regular intervals on the canvas.

        These appear as floating labels within the canvas area,
        showing coordinates at label_interval spacing.
        """
        label_attr = curses.color_pair(4) | curses.A_DIM
        interval = self.grid.label_interval

        # Calculate visible canvas range
        min_cx = viewport.x
        max_cx = viewport.x + viewport.width
        min_cy = viewport.y
        max_cy = viewport.y + viewport.height

        # Find first label position >= min
        start_x = ((min_cx // interval) + 1) * interval
        start_y = ((min_cy // interval) + 1) * interval

        # Render X labels (along a horizontal line)
        for cx in range(start_x, max_cx, interval):
            screen_pos = viewport.canvas_to_screen(cx, start_y)
            if screen_pos:
                sx, sy = screen_pos
                label = f"x={cx}"
                try:
                    self.stdscr.addstr(
                        sy + offset_y,
                        sx + offset_x,
                        label,
                        label_attr
                    )
                except curses.error:
                    pass

        # Render Y labels (along a vertical line)
        for cy in range(start_y, max_cy, interval):
            screen_pos = viewport.canvas_to_screen(start_x, cy)
            if screen_pos:
                sx, sy = screen_pos
                label = f"y={cy}"
                try:
                    self.stdscr.addstr(
                        sy + offset_y,
                        sx + offset_x,
                        label,
                        label_attr
                    )
                except curses.error:
                    pass

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
