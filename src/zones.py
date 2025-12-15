"""
Zone management for spatial document workspace.

Zones are named rectangular regions on the canvas that serve as
logical document areas. Users can jump between zones instantly
using bookmarks or zone commands.
"""

from dataclasses import dataclass, field
from typing import Iterator
import math


@dataclass
class Zone:
    """
    A named rectangular region on the canvas.

    Zones define logical areas like "INBOX", "WORKSPACE", "NOTES", etc.
    Each zone can have an associated bookmark for quick navigation.
    """
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str = ""
    border_style: str | None = None  # boxes style name for border
    bookmark: str | None = None      # Associated bookmark key (a-z, 0-9)

    def contains(self, cx: int, cy: int) -> bool:
        """Check if a canvas coordinate is within this zone."""
        return (self.x <= cx < self.x + self.width and
                self.y <= cy < self.y + self.height)

    def center(self) -> tuple[int, int]:
        """Get the center coordinates of this zone."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def top_left(self) -> tuple[int, int]:
        """Get the top-left corner coordinates."""
        return (self.x, self.y)

    def bottom_right(self) -> tuple[int, int]:
        """Get the bottom-right corner coordinates."""
        return (self.x + self.width - 1, self.y + self.height - 1)

    def distance_to(self, cx: int, cy: int) -> float:
        """
        Calculate distance from a point to this zone.

        Returns 0 if point is inside the zone.
        Otherwise returns distance to nearest edge.
        """
        if self.contains(cx, cy):
            return 0.0

        # Find nearest point on zone boundary
        nearest_x = max(self.x, min(cx, self.x + self.width - 1))
        nearest_y = max(self.y, min(cy, self.y + self.height - 1))

        return math.sqrt((cx - nearest_x) ** 2 + (cy - nearest_y) ** 2)

    def direction_from(self, cx: int, cy: int) -> str:
        """
        Get direction arrow from a point to this zone's center.

        Returns one of: ← → ↑ ↓ ↖ ↗ ↙ ↘ or · if at center.
        """
        center_x, center_y = self.center()
        dx = center_x - cx
        dy = center_y - cy

        if abs(dx) < 5 and abs(dy) < 5:
            return '·'

        # Determine primary direction
        if abs(dx) > abs(dy) * 2:
            # Primarily horizontal
            return '→' if dx > 0 else '←'
        elif abs(dy) > abs(dx) * 2:
            # Primarily vertical
            return '↓' if dy > 0 else '↑'
        else:
            # Diagonal
            if dx > 0 and dy > 0:
                return '↘'
            elif dx > 0 and dy < 0:
                return '↗'
            elif dx < 0 and dy > 0:
                return '↙'
            else:
                return '↖'

    def to_dict(self) -> dict:
        """Serialize zone to dictionary for JSON export."""
        data = {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
        if self.description:
            data["description"] = self.description
        if self.border_style:
            data["border_style"] = self.border_style
        if self.bookmark:
            data["bookmark"] = self.bookmark
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Zone":
        """Deserialize zone from dictionary."""
        return cls(
            name=data["name"],
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            description=data.get("description", ""),
            border_style=data.get("border_style"),
            bookmark=data.get("bookmark"),
        )


class ZoneManager:
    """
    Manages a collection of named zones on the canvas.

    Provides operations for creating, finding, and navigating between zones.
    """

    def __init__(self):
        self._zones: dict[str, Zone] = {}

    def create(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        description: str = "",
        border_style: str | None = None,
        bookmark: str | None = None,
    ) -> Zone:
        """
        Create a new zone.

        Args:
            name: Unique zone name (case-insensitive)
            x, y: Top-left corner coordinates
            width, height: Zone dimensions
            description: Optional description
            border_style: Optional boxes style for border
            bookmark: Optional bookmark key to associate

        Returns:
            The created Zone

        Raises:
            ValueError: If zone name already exists
        """
        key = name.lower()
        if key in self._zones:
            raise ValueError(f"Zone '{name}' already exists")

        zone = Zone(
            name=name,
            x=x,
            y=y,
            width=width,
            height=height,
            description=description,
            border_style=border_style,
            bookmark=bookmark,
        )
        self._zones[key] = zone
        return zone

    def delete(self, name: str) -> bool:
        """
        Delete a zone by name.

        Returns True if zone was deleted, False if not found.
        """
        key = name.lower()
        if key in self._zones:
            del self._zones[key]
            return True
        return False

    def get(self, name: str) -> Zone | None:
        """Get a zone by name (case-insensitive)."""
        return self._zones.get(name.lower())

    def find_at(self, x: int, y: int) -> Zone | None:
        """
        Find the zone containing a canvas coordinate.

        If multiple zones overlap at this point, returns the first found.
        Returns None if no zone contains the point.
        """
        for zone in self._zones.values():
            if zone.contains(x, y):
                return zone
        return None

    def list_all(self) -> list[Zone]:
        """Get all zones sorted by name."""
        return sorted(self._zones.values(), key=lambda z: z.name.lower())

    def nearest(
        self,
        x: int,
        y: int,
        exclude_current: bool = True
    ) -> tuple[Zone, float, str] | None:
        """
        Find the nearest zone to a canvas coordinate.

        Args:
            x, y: Canvas coordinates
            exclude_current: If True, exclude zone containing the point

        Returns:
            Tuple of (zone, distance, direction_arrow) or None if no zones.
        """
        current_zone = self.find_at(x, y) if exclude_current else None

        nearest_zone = None
        nearest_dist = float('inf')

        for zone in self._zones.values():
            if zone is current_zone:
                continue

            dist = zone.distance_to(x, y)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_zone = zone

        if nearest_zone is None:
            return None

        direction = nearest_zone.direction_from(x, y)
        return (nearest_zone, nearest_dist, direction)

    def rename(self, old_name: str, new_name: str) -> bool:
        """
        Rename a zone.

        Returns True if renamed, False if old name not found or new name exists.
        """
        old_key = old_name.lower()
        new_key = new_name.lower()

        if old_key not in self._zones:
            return False
        if new_key in self._zones and old_key != new_key:
            return False

        zone = self._zones.pop(old_key)
        zone.name = new_name
        self._zones[new_key] = zone
        return True

    def resize(self, name: str, width: int, height: int) -> bool:
        """
        Resize a zone.

        Returns True if resized, False if zone not found.
        """
        zone = self.get(name)
        if zone is None:
            return False
        zone.width = width
        zone.height = height
        return True

    def move(self, name: str, x: int, y: int) -> bool:
        """
        Move a zone to new coordinates.

        Returns True if moved, False if zone not found.
        """
        zone = self.get(name)
        if zone is None:
            return False
        zone.x = x
        zone.y = y
        return True

    def set_bookmark(self, name: str, bookmark: str | None) -> bool:
        """
        Associate a bookmark with a zone.

        Returns True if set, False if zone not found.
        """
        zone = self.get(name)
        if zone is None:
            return False
        zone.bookmark = bookmark
        return True

    def find_by_bookmark(self, bookmark: str) -> Zone | None:
        """Find zone associated with a bookmark key."""
        for zone in self._zones.values():
            if zone.bookmark == bookmark:
                return zone
        return None

    def clear(self) -> None:
        """Remove all zones."""
        self._zones.clear()

    def __len__(self) -> int:
        return len(self._zones)

    def __iter__(self) -> Iterator[Zone]:
        return iter(self._zones.values())

    def __contains__(self, name: str) -> bool:
        return name.lower() in self._zones

    def to_dict(self) -> dict:
        """Serialize all zones to dictionary for JSON export."""
        return {
            "zones": [zone.to_dict() for zone in self.list_all()]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ZoneManager":
        """Deserialize zones from dictionary."""
        manager = cls()
        for zone_data in data.get("zones", []):
            zone = Zone.from_dict(zone_data)
            manager._zones[zone.name.lower()] = zone
        return manager
