"""
Viewport for viewing a portion of the infinite canvas.

Handles coordinate transforms between canvas space and screen space.
"""

from dataclasses import dataclass, field
from enum import Enum, auto


class YAxisDirection(Enum):
    """Direction of Y axis increase."""
    DOWN = auto()   # Screen-style: Y increases downward
    UP = auto()     # Mathematical: Y increases upward


@dataclass
class Origin:
    """Configurable origin point for the canvas."""
    x: int = 0
    y: int = 0

    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy

    def set(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


@dataclass
class Cursor:
    """Cursor position in canvas coordinates."""
    x: int = 0
    y: int = 0

    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy

    def set(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def to_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)


@dataclass
class Viewport:
    """
    A window into the infinite canvas.

    The viewport has a position (top-left corner in canvas space)
    and dimensions (width/height in characters).

    Screen coordinates: (0,0) is top-left of terminal, Y increases down.
    Canvas coordinates: Can be any integer, Y direction is configurable.
    """
    # Viewport position in canvas space (top-left corner)
    x: int = 0
    y: int = 0

    # Viewport size in characters
    width: int = 80
    height: int = 24

    # Cursor in canvas coordinates
    cursor: Cursor = field(default_factory=Cursor)

    # Canvas origin point
    origin: Origin = field(default_factory=Origin)

    # Y-axis direction for canvas coordinates
    y_direction: YAxisDirection = YAxisDirection.DOWN

    def canvas_to_screen(self, cx: int, cy: int) -> tuple[int, int] | None:
        """
        Convert canvas coordinates to screen coordinates.

        Returns None if the point is outside the viewport.
        """
        # Apply Y-direction transformation
        if self.y_direction == YAxisDirection.UP:
            # Flip Y around the viewport center
            cy = -cy

        sx = cx - self.x
        sy = cy - self.y

        if 0 <= sx < self.width and 0 <= sy < self.height:
            return (sx, sy)
        return None

    def screen_to_canvas(self, sx: int, sy: int) -> tuple[int, int]:
        """Convert screen coordinates to canvas coordinates."""
        cx = sx + self.x
        cy = sy + self.y

        if self.y_direction == YAxisDirection.UP:
            cy = -cy

        return (cx, cy)

    def is_visible(self, cx: int, cy: int) -> bool:
        """Check if canvas coordinate is visible in viewport."""
        return self.canvas_to_screen(cx, cy) is not None

    def pan(self, dx: int, dy: int) -> None:
        """Pan the viewport by delta in canvas units."""
        self.x += dx
        self.y += dy

    def pan_to(self, x: int, y: int) -> None:
        """Pan viewport to specific canvas position (top-left)."""
        self.x = x
        self.y = y

    def center_on(self, cx: int, cy: int) -> None:
        """Center the viewport on a canvas coordinate."""
        if self.y_direction == YAxisDirection.UP:
            cy = -cy
        self.x = cx - self.width // 2
        self.y = cy - self.height // 2

    def center_on_cursor(self) -> None:
        """Center the viewport on the cursor."""
        self.center_on(self.cursor.x, self.cursor.y)

    def center_on_origin(self) -> None:
        """Center the viewport on the canvas origin."""
        self.center_on(self.origin.x, self.origin.y)

    def move_cursor(self, dx: int, dy: int) -> None:
        """Move cursor by delta."""
        self.cursor.move(dx, dy)

    def move_cursor_to(self, x: int, y: int) -> None:
        """Move cursor to specific canvas position."""
        self.cursor.set(x, y)

    def cursor_screen_pos(self) -> tuple[int, int] | None:
        """Get cursor position in screen coordinates."""
        return self.canvas_to_screen(self.cursor.x, self.cursor.y)

    def ensure_cursor_visible(self, margin: int = 0) -> None:
        """
        Scroll viewport to ensure cursor is visible.

        Args:
            margin: Minimum distance from cursor to viewport edge
        """
        cx, cy = self.cursor.x, self.cursor.y

        if self.y_direction == YAxisDirection.UP:
            cy = -cy

        # Check horizontal bounds
        if cx < self.x + margin:
            self.x = cx - margin
        elif cx >= self.x + self.width - margin:
            self.x = cx - self.width + margin + 1

        # Check vertical bounds
        if cy < self.y + margin:
            self.y = cy - margin
        elif cy >= self.y + self.height - margin:
            self.y = cy - self.height + margin + 1

    def visible_range(self) -> tuple[int, int, int, int]:
        """
        Get the visible canvas coordinate range.

        Returns: (min_x, min_y, max_x, max_y) in canvas coordinates
        """
        min_x = self.x
        max_x = self.x + self.width - 1

        if self.y_direction == YAxisDirection.DOWN:
            min_y = self.y
            max_y = self.y + self.height - 1
        else:
            # Y-up: screen top is higher Y in canvas
            min_y = -(self.y + self.height - 1)
            max_y = -self.y

        return (min_x, min_y, max_x, max_y)

    def resize(self, width: int, height: int) -> None:
        """Resize the viewport (e.g., terminal resize)."""
        self.width = max(1, width)
        self.height = max(1, height)

    def origin_screen_pos(self) -> tuple[int, int] | None:
        """Get origin position in screen coordinates (for drawing origin marker)."""
        return self.canvas_to_screen(self.origin.x, self.origin.y)

    def to_dict(self) -> dict:
        """Serialize viewport state for JSON export."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "cursor": {"x": self.cursor.x, "y": self.cursor.y},
            "origin": {"x": self.origin.x, "y": self.origin.y},
            "y_direction": self.y_direction.name
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Viewport":
        """Deserialize viewport from dictionary."""
        viewport = cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 80),
            height=data.get("height", 24)
        )

        if "cursor" in data:
            viewport.cursor = Cursor(
                x=data["cursor"].get("x", 0),
                y=data["cursor"].get("y", 0)
            )

        if "origin" in data:
            viewport.origin = Origin(
                x=data["origin"].get("x", 0),
                y=data["origin"].get("y", 0)
            )

        if "y_direction" in data:
            viewport.y_direction = YAxisDirection[data["y_direction"]]

        return viewport
