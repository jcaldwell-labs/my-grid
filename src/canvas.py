"""
Sparse canvas data structure for unlimited ASCII canvas.

Uses a dictionary keyed by (x, y) tuples - only non-empty cells consume memory.
"""

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Cell:
    """A single cell in the canvas."""
    char: str = ' '
    # Future: fg_color, bg_color, attributes

    def is_empty(self) -> bool:
        return self.char == ' ' or self.char == ''


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

    def set(self, x: int, y: int, char: str) -> None:
        """
        Set character at position.

        If char is space/empty, removes the cell to save memory.
        Only stores the first character if string is longer.
        """
        if len(char) == 0 or char == ' ':
            self.clear(x, y)
        else:
            self._cells[(x, y)] = Cell(char=char[0])

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

        return BoundingBox(
            min_x=min(xs),
            min_y=min(ys),
            max_x=max(xs),
            max_y=max(ys)
        )

    def to_dict(self) -> dict:
        """Serialize canvas to dictionary for JSON export."""
        cells_list = [
            {"x": x, "y": y, "char": cell.char}
            for (x, y), cell in self._cells.items()
        ]
        return {"cells": cells_list}

    @classmethod
    def from_dict(cls, data: dict) -> "Canvas":
        """Deserialize canvas from dictionary."""
        canvas = cls()
        for cell_data in data.get("cells", []):
            canvas.set(cell_data["x"], cell_data["y"], cell_data["char"])
        return canvas

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, char: str = '*') -> None:
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
        self, x: int, y: int, width: int, height: int,
        h_char: str = '-', v_char: str = '|', corner_char: str = '+'
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
