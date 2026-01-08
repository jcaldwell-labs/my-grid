"""
Sparse canvas data structure for unlimited ASCII canvas.

Uses a dictionary keyed by (x, y) tuples - only non-empty cells consume memory.
"""

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Cell:
    """
    A single cell in the canvas.

    Color values map to curses color constants:
    0=black, 1=red, 2=green, 3=yellow, 4=blue, 5=magenta, 6=cyan, 7=white
    -1=default (terminal default)
    """

    char: str = " "
    fg: int = -1  # Foreground color (-1 = default)
    bg: int = -1  # Background color (-1 = default)

    def is_empty(self) -> bool:
        return self.char == " " or self.char == ""

    def has_color(self) -> bool:
        """Check if cell has non-default colors."""
        return self.fg != -1 or self.bg != -1


# Color name to curses color constant mapping
COLOR_NAMES = {
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7,
    "default": -1,
}

# Reverse mapping
COLOR_NUMBERS = {v: k for k, v in COLOR_NAMES.items()}


def parse_color(color_str: str) -> int:
    """Parse color string to color number. Returns -1 if invalid."""
    color_str = color_str.lower().strip()
    if color_str in COLOR_NAMES:
        return COLOR_NAMES[color_str]
    try:
        num = int(color_str)
        if -1 <= num <= 255:
            return num
        return -1
    except ValueError:
        return -1


@dataclass
class BoundingBox:
    """Axis-aligned bounding box for canvas content."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        return self.max_y - self.min_y + 1

    def contains(self, x: int, y: int) -> bool:
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y


@dataclass
class Canvas:
    """
    Sparse, unlimited ASCII canvas.

    Coordinates can be any integer (positive or negative).
    Only non-empty cells are stored in memory.
    """

    _cells: dict[tuple[int, int], Cell] = field(default_factory=dict)

    def get(self, x: int, y: int) -> Cell:
        """Get cell at position. Returns empty cell if not set."""
        return self._cells.get((x, y), Cell())

    def get_char(self, x: int, y: int) -> str:
        """Get character at position. Returns space if not set."""
        return self.get(x, y).char

    def set(self, x: int, y: int, char: str, fg: int = -1, bg: int = -1) -> None:
        """
        Set character at position with optional colors.

        If char is space/empty and no colors, removes the cell to save memory.
        Only stores the first character if string is longer.

        Args:
            x, y: Position
            char: Character to set
            fg: Foreground color (-1 = default, 0-7 = basic colors)
            bg: Background color (-1 = default, 0-7 = basic colors)
        """
        if len(char) == 0 or char == " ":
            # Keep cell if it has color info
            if fg != -1 or bg != -1:
                self._cells[(x, y)] = Cell(char=" ", fg=fg, bg=bg)
            else:
                self.clear(x, y)
        else:
            self._cells[(x, y)] = Cell(char=char[0], fg=fg, bg=bg)

    def set_color(self, x: int, y: int, fg: int = -1, bg: int = -1) -> None:
        """
        Set color for cell at position without changing character.

        If cell doesn't exist and colors are non-default, creates cell with space.
        If both fg and bg are -1 (default) and cell doesn't exist, this is a no-op.
        If cell exists and both colors are -1, resets to default colors (may delete if space).
        """
        cell = self.get(x, y)
        if fg != -1 or bg != -1:
            self._cells[(x, y)] = Cell(char=cell.char, fg=fg, bg=bg)
        elif (x, y) in self._cells:
            # Reset to default colors
            if cell.char == " ":
                self.clear(x, y)
            else:
                self._cells[(x, y)] = Cell(char=cell.char, fg=-1, bg=-1)

    def clear(self, x: int, y: int) -> None:
        """Remove cell at position."""
        self._cells.pop((x, y), None)

    def clear_all(self) -> None:
        """Clear entire canvas."""
        self._cells.clear()

    def is_empty_at(self, x: int, y: int) -> bool:
        """Check if position is empty (no cell or space)."""
        return (x, y) not in self._cells

    @property
    def cell_count(self) -> int:
        """Number of non-empty cells."""
        return len(self._cells)

    def cells(self) -> Iterator[tuple[int, int, Cell]]:
        """Iterate over all non-empty cells as (x, y, cell)."""
        for (x, y), cell in self._cells.items():
            yield x, y, cell

    def cells_in_rect(
        self, x: int, y: int, width: int, height: int
    ) -> Iterator[tuple[int, int, Cell]]:
        """
        Iterate over cells within a rectangle.

        Yields (x, y, cell) for each position in the rect.
        Empty positions yield Cell() with space character.
        """
        for cy in range(y, y + height):
            for cx in range(x, x + width):
                yield cx, cy, self.get(cx, cy)

    def bounding_box(self) -> BoundingBox | None:
        """
        Get bounding box of all non-empty cells.

        Returns None if canvas is empty.
        """
        if not self._cells:
            return None

        coords = list(self._cells.keys())
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]

        return BoundingBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))

    def to_dict(self) -> dict:
        """Serialize canvas to dictionary for JSON export."""
        cells_list = []
        for (x, y), cell in self._cells.items():
            cell_dict = {"x": x, "y": y, "char": cell.char}
            # Only include color if non-default
            if cell.fg != -1:
                cell_dict["fg"] = cell.fg
            if cell.bg != -1:
                cell_dict["bg"] = cell.bg
            cells_list.append(cell_dict)
        return {"cells": cells_list}

    @classmethod
    def from_dict(cls, data: dict) -> "Canvas":
        """Deserialize canvas from dictionary."""
        canvas = cls()
        for cell_data in data.get("cells", []):
            fg = cell_data.get("fg", -1)
            bg = cell_data.get("bg", -1)
            canvas.set(cell_data["x"], cell_data["y"], cell_data["char"], fg=fg, bg=bg)
        return canvas

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, char: str = "*") -> None:
        """
        Draw a line between two points using Bresenham's algorithm.
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while True:
            self.set(x, y, char)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def draw_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        h_char: str = "-",
        v_char: str = "|",
        corner_char: str = "+",
    ) -> None:
        """Draw a rectangle outline."""
        # Corners
        self.set(x, y, corner_char)
        self.set(x + width - 1, y, corner_char)
        self.set(x, y + height - 1, corner_char)
        self.set(x + width - 1, y + height - 1, corner_char)

        # Horizontal edges
        for cx in range(x + 1, x + width - 1):
            self.set(cx, y, h_char)
            self.set(cx, y + height - 1, h_char)

        # Vertical edges
        for cy in range(y + 1, y + height - 1):
            self.set(x, cy, v_char)
            self.set(x + width - 1, cy, v_char)

    def fill_rect(self, x: int, y: int, width: int, height: int, char: str) -> None:
        """Fill a rectangle with a character."""
        for cy in range(y, y + height):
            for cx in range(x, x + width):
                self.set(cx, cy, char)

    def write_text(self, x: int, y: int, text: str) -> None:
        """Write text horizontally starting at position."""
        for i, char in enumerate(text):
            self.set(x + i, y, char)

    def search_text(
        self, pattern: str, case_sensitive: bool = False
    ) -> list[tuple[int, int, int]]:
        """
        Search for horizontal text pattern in the canvas.

        Finds consecutive characters that match the pattern, reading left-to-right
        on each row. Returns all matches as (x, y, length) tuples.

        Args:
            pattern: Text pattern to search for
            case_sensitive: Whether search is case-sensitive (default: False)

        Returns:
            List of (x, y, length) tuples for each match found
        """
        if not pattern:
            return []

        matches: list[tuple[int, int, int]] = []

        # Get bounding box to know the range to search
        bbox = self.bounding_box()
        if bbox is None:
            return []

        # Normalize pattern for comparison
        search_pattern = pattern if case_sensitive else pattern.lower()

        # For each row in the bounding box, build a string and search
        for row_y in range(bbox.min_y, bbox.max_y + 1):
            # Build string for this row with position tracking
            row_chars: list[tuple[int, str]] = []

            for x in range(bbox.min_x, bbox.max_x + 1):
                cell = self.get(x, row_y)
                char = cell.char if cell.char else " "
                row_chars.append((x, char))

            if not row_chars:
                continue

            # Build the row string
            row_str = "".join(c for _, c in row_chars)
            compare_str = row_str if case_sensitive else row_str.lower()

            # Find all occurrences in this row
            start = 0
            while True:
                idx = compare_str.find(search_pattern, start)
                if idx == -1:
                    break
                # Convert string index to canvas x coordinate
                match_x = row_chars[idx][0]
                matches.append((match_x, row_y, len(pattern)))
                start = idx + 1

        # Sort matches by y, then x (top-to-bottom, left-to-right)
        matches.sort(key=lambda m: (m[1], m[0]))
        return matches
