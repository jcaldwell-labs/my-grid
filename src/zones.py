"""
Zone management for spatial document workspace.

Zones are named rectangular regions on the canvas that serve as
logical document areas. Users can jump between zones instantly
using bookmarks or zone commands.

Zone types enable dynamic content:
- STATIC: Plain text (default)
- PIPE: One-shot command output
- WATCH: Periodic refresh command
- PTY: Live interactive terminal
- FIFO: Named pipe listener
- SOCKET: Network port listener
- CLIPBOARD: Yank/paste buffer
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Any
import math


class ZoneType(Enum):
    """Types of zones with different behaviors."""
    STATIC = "static"       # Plain text region (default)
    PIPE = "pipe"           # One-shot command output
    WATCH = "watch"         # Periodic refresh command
    PTY = "pty"             # Live terminal session
    FIFO = "fifo"           # Named pipe listener
    SOCKET = "socket"       # Network port listener
    CLIPBOARD = "clipboard" # Yank/paste buffer


@dataclass
class ZoneConfig:
    """Configuration for dynamic zone types."""
    zone_type: ZoneType = ZoneType.STATIC

    # For PIPE/WATCH zones
    command: str | None = None
    refresh_interval: float | None = None  # seconds, for WATCH

    # For PTY zones
    shell: str = "/bin/bash"

    # For FIFO/SOCKET zones
    path: str | None = None  # FIFO path or "host:port"
    port: int | None = None  # For SOCKET

    # Display options
    scroll: bool = True      # Auto-scroll to bottom on new content
    wrap: bool = False       # Wrap long lines
    max_lines: int = 1000    # Buffer limit for output

    # State
    paused: bool = False     # Pause refresh for WATCH zones
    focused: bool = False    # PTY zone has keyboard focus

    def to_dict(self) -> dict:
        """Serialize config to dictionary."""
        data = {"zone_type": self.zone_type.value}
        if self.command:
            data["command"] = self.command
        if self.refresh_interval is not None:
            data["refresh_interval"] = self.refresh_interval
        if self.shell != "/bin/bash":
            data["shell"] = self.shell
        if self.path:
            data["path"] = self.path
        if self.port is not None:
            data["port"] = self.port
        if not self.scroll:
            data["scroll"] = self.scroll
        if self.wrap:
            data["wrap"] = self.wrap
        if self.max_lines != 1000:
            data["max_lines"] = self.max_lines
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ZoneConfig":
        """Deserialize config from dictionary."""
        zone_type = ZoneType(data.get("zone_type", "static"))
        return cls(
            zone_type=zone_type,
            command=data.get("command"),
            refresh_interval=data.get("refresh_interval"),
            shell=data.get("shell", "/bin/bash"),
            path=data.get("path"),
            port=data.get("port"),
            scroll=data.get("scroll", True),
            wrap=data.get("wrap", False),
            max_lines=data.get("max_lines", 1000),
        )


@dataclass
class Zone:
    """
    A named rectangular region on the canvas.

    Zones define logical areas like "INBOX", "WORKSPACE", "NOTES", etc.
    Each zone can have an associated bookmark for quick navigation.

    Dynamic zones (PIPE, WATCH, PTY, etc.) have a config and content buffer.
    """
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str = ""
    border_style: str | None = None  # boxes style name for border
    bookmark: str | None = None      # Associated bookmark key (a-z, 0-9)
    config: ZoneConfig = field(default_factory=ZoneConfig)

    # Content buffer for dynamic zones (not serialized - regenerated at runtime)
    _content_lines: list[str] = field(default_factory=list, repr=False)
    _runtime_data: dict = field(default_factory=dict, repr=False)  # PTY handle, etc.

    @property
    def zone_type(self) -> ZoneType:
        """Convenience property for zone type."""
        return self.config.zone_type

    @property
    def is_dynamic(self) -> bool:
        """True if zone has dynamic content (not STATIC)."""
        return self.config.zone_type != ZoneType.STATIC

    @property
    def content_lines(self) -> list[str]:
        """Get content lines for dynamic zones."""
        return self._content_lines

    def set_content(self, lines: list[str]) -> None:
        """Set content for dynamic zone, respecting max_lines."""
        max_lines = self.config.max_lines
        if len(lines) > max_lines:
            lines = lines[-max_lines:]  # Keep most recent
        self._content_lines = lines

    def append_content(self, line: str) -> None:
        """Append a line to dynamic zone content."""
        self._content_lines.append(line)
        max_lines = self.config.max_lines
        if len(self._content_lines) > max_lines:
            self._content_lines = self._content_lines[-max_lines:]

    def clear_content(self) -> None:
        """Clear dynamic zone content."""
        self._content_lines.clear()

    def type_indicator(self) -> str:
        """Get short indicator for zone type."""
        indicators = {
            ZoneType.STATIC: "S",
            ZoneType.PIPE: "P",
            ZoneType.WATCH: "W",
            ZoneType.PTY: "T",
            ZoneType.FIFO: "F",
            ZoneType.SOCKET: "N",
            ZoneType.CLIPBOARD: "C",
        }
        return indicators.get(self.config.zone_type, "?")

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
        # Only save config if not default static
        if self.config.zone_type != ZoneType.STATIC:
            data["config"] = self.config.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Zone":
        """Deserialize zone from dictionary."""
        config_data = data.get("config")
        config = ZoneConfig.from_dict(config_data) if config_data else ZoneConfig()
        return cls(
            name=data["name"],
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            description=data.get("description", ""),
            border_style=data.get("border_style"),
            bookmark=data.get("bookmark"),
            config=config,
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
        config: ZoneConfig | None = None,
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
            config: Zone configuration for dynamic types

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
            config=config or ZoneConfig(),
        )
        self._zones[key] = zone
        return zone

    def create_pipe(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        command: str,
        bookmark: str | None = None,
    ) -> Zone:
        """Create a PIPE zone that executes a command once."""
        config = ZoneConfig(
            zone_type=ZoneType.PIPE,
            command=command,
        )
        return self.create(name, x, y, width, height, bookmark=bookmark, config=config)

    def create_watch(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        command: str,
        interval: float = 5.0,
        bookmark: str | None = None,
    ) -> Zone:
        """Create a WATCH zone that periodically refreshes."""
        config = ZoneConfig(
            zone_type=ZoneType.WATCH,
            command=command,
            refresh_interval=interval,
        )
        return self.create(name, x, y, width, height, bookmark=bookmark, config=config)

    def create_pty(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        shell: str = "/bin/bash",
        bookmark: str | None = None,
    ) -> Zone:
        """Create a PTY zone with a live terminal."""
        config = ZoneConfig(
            zone_type=ZoneType.PTY,
            shell=shell,
        )
        return self.create(name, x, y, width, height, bookmark=bookmark, config=config)

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


# =============================================================================
# ZONE EXECUTOR - Runs commands for dynamic zones
# =============================================================================

import subprocess
import threading
import time


class ZoneExecutor:
    """
    Executes commands for PIPE and WATCH zones.

    Handles:
    - One-shot command execution (PIPE)
    - Periodic refresh (WATCH)
    - Background threads for watch zones
    """

    def __init__(self, zone_manager: ZoneManager):
        self.zone_manager = zone_manager
        self._watch_threads: dict[str, threading.Thread] = {}
        self._stop_events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def execute_pipe(self, zone: Zone, timeout: int = 30) -> bool:
        """
        Execute command for a PIPE or WATCH zone and update content.

        Returns True on success, False on error.
        """
        if zone.config.zone_type not in (ZoneType.PIPE, ZoneType.WATCH):
            return False
        if not zone.config.command:
            zone.set_content(["[No command configured]"])
            return False

        try:
            result = subprocess.run(
                zone.config.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr

            lines = output.split("\n")
            # Remove trailing empty lines
            while lines and not lines[-1]:
                lines.pop()

            zone.set_content(lines)
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            zone.set_content([f"[Command timed out after {timeout}s]"])
            return False
        except Exception as e:
            zone.set_content([f"[Error: {e}]"])
            return False

    def refresh_zone(self, name: str) -> bool:
        """Manually refresh a PIPE or WATCH zone."""
        zone = self.zone_manager.get(name)
        if zone is None:
            return False

        if zone.config.zone_type in (ZoneType.PIPE, ZoneType.WATCH):
            return self.execute_pipe(zone)
        return False

    def start_watch(self, zone: Zone) -> None:
        """Start background refresh for a WATCH zone."""
        if zone.config.zone_type != ZoneType.WATCH:
            return

        key = zone.name.lower()

        with self._lock:
            # Stop existing watcher if any
            if key in self._stop_events:
                self._stop_events[key].set()

            stop_event = threading.Event()
            self._stop_events[key] = stop_event

            thread = threading.Thread(
                target=self._watch_loop,
                args=(zone, stop_event),
                daemon=True,
                name=f"watch-{key}"
            )
            self._watch_threads[key] = thread
            thread.start()

    def stop_watch(self, name: str) -> None:
        """Stop background refresh for a WATCH zone."""
        key = name.lower()

        with self._lock:
            if key in self._stop_events:
                self._stop_events[key].set()
                del self._stop_events[key]
            if key in self._watch_threads:
                del self._watch_threads[key]

    def pause_zone(self, name: str) -> bool:
        """Pause a WATCH zone refresh."""
        zone = self.zone_manager.get(name)
        if zone and zone.config.zone_type == ZoneType.WATCH:
            zone.config.paused = True
            return True
        return False

    def resume_zone(self, name: str) -> bool:
        """Resume a WATCH zone refresh."""
        zone = self.zone_manager.get(name)
        if zone and zone.config.zone_type == ZoneType.WATCH:
            zone.config.paused = False
            return True
        return False

    def _watch_loop(self, zone: Zone, stop_event: threading.Event) -> None:
        """Background loop for WATCH zone refresh."""
        interval = zone.config.refresh_interval or 5.0

        # Initial execution
        self.execute_pipe(zone)

        while not stop_event.is_set():
            # Wait for interval or stop
            if stop_event.wait(timeout=interval):
                break

            # Skip if paused
            if zone.config.paused:
                continue

            # Execute command
            self.execute_pipe(zone)

    def stop_all(self) -> None:
        """Stop all watch threads."""
        with self._lock:
            for stop_event in self._stop_events.values():
                stop_event.set()
            self._stop_events.clear()
            self._watch_threads.clear()
