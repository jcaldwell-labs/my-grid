"""
Canvas widget for Textual - renders the sparse canvas using Rich Text.

This widget imports and uses the existing Canvas and Viewport classes,
providing a bridge between the core data structures and Textual's
Rich-based rendering system.
"""

import sys
from pathlib import Path

# Add src to path to import existing modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.style import Style
from rich.text import Text
from textual.widget import Widget
from textual.geometry import Size

from canvas import Canvas, Cell
from viewport import Viewport
from .zones import ZoneManager, Zone


# Map curses color numbers to Rich color names
CURSES_TO_RICH_COLOR = {
    -1: "default",
    0: "black",
    1: "red",
    2: "green",
    3: "yellow",
    4: "blue",
    5: "magenta",
    6: "cyan",
    7: "white",
}


class CanvasWidget(Widget):
    """
    A Textual widget that renders a Canvas through a Viewport.

    Uses Rich Text for styling:
    - Cursor shown with reverse video
    - Origin marker shown in yellow
    - Cell colors mapped from curses constants to Rich colors
    - Grid markers at configurable intervals
    - Selection highlighting for visual mode
    """

    DEFAULT_CSS = """
    CanvasWidget {
        width: 100%;
        height: 100%;
    }
    """

    def __init__(
        self,
        canvas: Canvas | None = None,
        viewport: Viewport | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.canvas = canvas or Canvas()
        self.viewport = viewport or Viewport()

        # Grid settings
        self.show_origin = True
        self.show_major_grid = False
        self.show_minor_grid = False
        self.major_interval = 10
        self.minor_interval = 5

        # Selection for visual mode (x1, y1, x2, y2) - all inclusive
        self.selection: tuple[int, int, int, int] | None = None

        # Zone manager
        self.zone_manager = ZoneManager()

        # Style settings
        self.cursor_style = Style(reverse=True, bold=True)
        self.origin_style = Style(color="yellow", bold=True)
        self.major_grid_style = Style(color="blue", dim=True)
        self.minor_grid_style = Style(color="bright_black", dim=True)
        self._visual_selection_style = Style(bgcolor="cyan", color="black")
        self._zone_border_style = Style(color="green")
        self._zone_content_style = Style(color="white")
        self._pty_focused_border_style = Style(color="bright_green", bold=True)

    def get_content_width(self, container: Size, viewport_size: Size) -> int:
        """Return the width needed to render the widget."""
        return container.width

    def get_content_height(
        self, container: Size, viewport_size: Size, width: int
    ) -> int:
        """Return the height needed to render the widget."""
        return container.height

    def render(self) -> Text:
        """Render the canvas as Rich Text."""
        # Get widget size and update viewport dimensions
        width = self.size.width
        height = self.size.height

        if width <= 0 or height <= 0:
            return Text("")

        self.viewport.resize(width, height)

        # Build the display line by line
        lines = []

        for sy in range(height):
            line = Text()
            for sx in range(width):
                # Convert screen position to canvas coordinates
                cx, cy = self.viewport.screen_to_canvas(sx, sy)

                # Get the character and style for this position
                char, style = self._get_cell_display(cx, cy)

                line.append(char, style)

            lines.append(line)

        # Join lines with newlines (except last line to avoid extra newline)
        result = Text()
        for i, line in enumerate(lines):
            result.append_text(line)
            if i < len(lines) - 1:
                result.append("\n")

        return result

    def _get_cell_display(self, cx: int, cy: int) -> tuple[str, Style]:
        """
        Determine what character and style to display at canvas position.

        Priority:
        1. Cursor (reverse video)
        2. Selection (cyan background)
        3. Zone borders and content (green)
        4. Origin marker (yellow +)
        5. Cell content with colors
        6. Grid markers
        7. Empty space

        Returns:
            Tuple of (character, Rich Style)
        """
        cell = self.canvas.get(cx, cy)
        char = cell.char if cell.char else " "

        # 1. Check cursor position
        if cx == self.viewport.cursor.x and cy == self.viewport.cursor.y:
            # Show zone border/content under cursor with reverse style
            zone = self.zone_manager.get_zone_at(cx, cy)
            if zone:
                border_char = zone.get_border_char(cx, cy)
                if border_char:
                    return border_char, self.cursor_style
                content_char = zone.get_content_char(cx, cy)
                if content_char:
                    return content_char, self.cursor_style
            return char if char != " " else " ", self.cursor_style

        # 2. Check selection
        if self.selection is not None:
            x1, y1, x2, y2 = self.selection
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                return char, self._visual_selection_style

        # 3. Check zone borders and content
        zone = self.zone_manager.get_zone_at(cx, cy)
        if zone:
            border_char = zone.get_border_char(cx, cy)
            if border_char:
                # Use bright style for focused PTY zones
                border_style = (
                    self._pty_focused_border_style
                    if zone.focused
                    else self._zone_border_style
                )
                return border_char, border_style
            content_char = zone.get_content_char(cx, cy)
            if content_char:
                return content_char, self._zone_content_style

        # 4. Check origin marker
        if self.show_origin:
            if cx == self.viewport.origin.x and cy == self.viewport.origin.y:
                display_char = char if char != " " else "+"
                return display_char, self.origin_style

        # 5. Check cell colors
        if cell.has_color():
            style = self._cell_color_to_style(cell.fg, cell.bg)
            return char, style

        # 6. Check grid markers (only for empty cells)
        if char == " ":
            grid_char, grid_style = self._get_grid_marker(cx, cy)
            if grid_char:
                return grid_char, grid_style

        # 7. Regular character
        return char, Style()

    def _cell_color_to_style(self, fg: int, bg: int) -> Style:
        """Convert curses color numbers to Rich Style."""
        fg_color = CURSES_TO_RICH_COLOR.get(fg, "default")
        bg_color = CURSES_TO_RICH_COLOR.get(bg, "default")

        # Rich uses None for default colors
        fg_color = None if fg_color == "default" else fg_color
        bg_color = None if bg_color == "default" else bg_color

        return Style(color=fg_color, bgcolor=bg_color)

    def _get_grid_marker(self, cx: int, cy: int) -> tuple[str | None, Style]:
        """
        Get grid marker character and style for position.

        Returns (None, Style()) if no marker at this position.
        """
        # Calculate position relative to origin
        rel_x = cx - self.viewport.origin.x
        rel_y = cy - self.viewport.origin.y

        # Check major grid
        if self.show_major_grid and self.major_interval > 0:
            if rel_x % self.major_interval == 0 and rel_y % self.major_interval == 0:
                return "+", self.major_grid_style

        # Check minor grid
        if self.show_minor_grid and self.minor_interval > 0:
            if rel_x % self.minor_interval == 0 and rel_y % self.minor_interval == 0:
                # Don't show minor where major would be
                if (
                    not self.show_major_grid
                    or rel_x % self.major_interval != 0
                    or rel_y % self.major_interval != 0
                ):
                    return "·", self.minor_grid_style

        return None, Style()

    def move_cursor(self, dx: int, dy: int) -> None:
        """Move the cursor by delta and ensure it's visible."""
        self.viewport.move_cursor(dx, dy)
        self.viewport.ensure_cursor_visible(margin=2)
        self.refresh()

    def toggle_major_grid(self) -> None:
        """Toggle major grid display."""
        self.show_major_grid = not self.show_major_grid
        self.refresh()

    def toggle_minor_grid(self) -> None:
        """Toggle minor grid display."""
        self.show_minor_grid = not self.show_minor_grid
        self.refresh()

    def toggle_origin(self) -> None:
        """Toggle origin marker display."""
        self.show_origin = not self.show_origin
        self.refresh()

    def set_char(self, char: str) -> None:
        """Set a character at the current cursor position."""
        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
        self.canvas.set(cx, cy, char)
        self.refresh()

    def delete_char(self) -> None:
        """Delete the character at the current cursor position."""
        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
        self.canvas.clear(cx, cy)
        self.refresh()

    def set_selection(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Set the selection region (inclusive bounds)."""
        # Normalize so x1 <= x2 and y1 <= y2
        self.selection = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.refresh()

    def clear_selection(self) -> None:
        """Clear the selection."""
        self.selection = None
        self.refresh()

    def get_selection_bounds(self) -> tuple[int, int, int, int] | None:
        """Get the current selection bounds, or None if no selection."""
        return self.selection

    def yank_region(self, x1: int, y1: int, x2: int, y2: int) -> list[list[str]]:
        """
        Yank (copy) a region from the canvas.

        Returns a 2D list of characters.
        """
        result = []
        for y in range(y1, y2 + 1):
            row = []
            for x in range(x1, x2 + 1):
                cell = self.canvas.get(x, y)
                row.append(cell.char if cell.char else " ")
            result.append(row)
        return result

    def delete_region(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Delete (clear) a region on the canvas."""
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.canvas.clear(x, y)
        self.refresh()

    def paste_region(self, data: list[list[str]], x: int, y: int) -> None:
        """Paste a 2D list of characters at the given position."""
        for row_idx, row in enumerate(data):
            for col_idx, char in enumerate(row):
                if char and char != " ":
                    self.canvas.set(x + col_idx, y + row_idx, char)
        self.refresh()
