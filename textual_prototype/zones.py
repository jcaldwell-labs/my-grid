"""
Zone management for Textual prototype.

Zones are named rectangular regions on the canvas that can contain:
- STATIC: Plain text content
- PIPE: One-shot command output
- WATCH: Periodically refreshed command output
- PTY: Live interactive terminal session
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Any
import subprocess
import shlex
import os
import sys
import fcntl
import select
import threading

# Check if PTY is available (Unix only)
try:
    import pty
    import pyte

    PTY_AVAILABLE = True
except ImportError:
    PTY_AVAILABLE = False


class ZoneType(Enum):
    """Types of zones with different content behaviors."""

    STATIC = auto()  # Plain text, user-editable
    PIPE = auto()  # One-shot command output
    WATCH = auto()  # Periodic command refresh
    PTY = auto()  # Live interactive terminal


# Type indicators shown in zone borders
ZONE_TYPE_INDICATORS = {
    ZoneType.STATIC: "S",
    ZoneType.PIPE: "P",
    ZoneType.WATCH: "W",
    ZoneType.PTY: "T",
}


@dataclass
class Zone:
    """
    A named rectangular region on the canvas.

    Attributes:
        name: Unique identifier for the zone
        x: Left edge canvas coordinate
        y: Top edge canvas coordinate
        width: Zone width in characters
        height: Zone height in characters
        zone_type: Type of zone (STATIC, PIPE, WATCH)
        content: Current text content (list of lines)
        command: Shell command for PIPE/WATCH zones
        interval: Refresh interval in seconds for WATCH zones
    """

    name: str
    x: int
    y: int
    width: int
    height: int
    zone_type: ZoneType = ZoneType.STATIC
    content: list[str] = field(default_factory=list)
    command: str = ""
    interval: float = 5.0  # Default 5 second refresh for WATCH zones

    # PTY-specific fields (only used when zone_type == PTY)
    pty_fd: int = -1  # PTY master file descriptor
    pty_pid: int = -1  # Child process PID
    pty_screen: Any = None  # pyte.HistoryScreen instance
    pty_stream: Any = None  # pyte.Stream instance
    pty_stop_event: Any = None  # threading.Event for stopping reader thread
    pty_reader_thread: Any = None  # Background reader thread
    focused: bool = False  # Whether this PTY has keyboard focus

    @property
    def type_indicator(self) -> str:
        """Get the single-char type indicator for border display."""
        return ZONE_TYPE_INDICATORS.get(self.zone_type, "?")

    @property
    def inner_width(self) -> int:
        """Width available for content (minus borders)."""
        return max(0, self.width - 2)

    @property
    def inner_height(self) -> int:
        """Height available for content (minus borders)."""
        return max(0, self.height - 2)

    @property
    def content_x(self) -> int:
        """X coordinate where content starts (after left border)."""
        return self.x + 1

    @property
    def content_y(self) -> int:
        """Y coordinate where content starts (after top border)."""
        return self.y + 1

    def contains_point(self, px: int, py: int) -> bool:
        """Check if a canvas point is within this zone's bounds."""
        return (
            self.x <= px < self.x + self.width and self.y <= py < self.y + self.height
        )

    def is_border(self, px: int, py: int) -> bool:
        """Check if a point is on the zone's border."""
        if not self.contains_point(px, py):
            return False
        return (
            px == self.x
            or px == self.x + self.width - 1
            or py == self.y
            or py == self.y + self.height - 1
        )

    def get_border_char(self, px: int, py: int) -> str | None:
        """
        Get the border character for a position, or None if not a border.

        Uses unicode box-drawing characters for cleaner appearance.
        """
        if not self.is_border(px, py):
            return None

        # Corners
        if px == self.x and py == self.y:
            return "┌"
        if px == self.x + self.width - 1 and py == self.y:
            return "┐"
        if px == self.x and py == self.y + self.height - 1:
            return "└"
        if px == self.x + self.width - 1 and py == self.y + self.height - 1:
            return "┘"

        # Top edge with name and type indicator
        if py == self.y:
            # Calculate position for "[TYPE] NAME" in top border
            rel_x = px - self.x
            header = f"[{self.type_indicator}] {self.name}"
            if 2 <= rel_x < 2 + len(header):
                return header[rel_x - 2]
            return "─"

        # Bottom edge
        if py == self.y + self.height - 1:
            return "─"

        # Left/right edges
        if px == self.x or px == self.x + self.width - 1:
            return "│"

        return None

    def get_content_char(self, px: int, py: int) -> str | None:
        """
        Get the content character at a position, or None if outside content area.

        Returns space for empty content areas within the zone.
        """
        # Check if in content area (not border)
        if self.is_border(px, py) or not self.contains_point(px, py):
            return None

        # Calculate content-relative position
        content_row = py - self.content_y
        content_col = px - self.content_x

        # Get character from content
        if 0 <= content_row < len(self.content):
            line = self.content[content_row]
            if 0 <= content_col < len(line):
                return line[content_col]

        return " "  # Empty space within zone

    def set_content(self, text: str) -> None:
        """Set zone content from a text string, splitting into lines."""
        lines = text.split("\n")
        # Truncate lines to fit zone width and limit to zone height
        self.content = []
        for line in lines[: self.inner_height]:
            self.content.append(line[: self.inner_width])

    def execute_command(self) -> str:
        """
        Execute the zone's command and return output.

        For PIPE and WATCH zones only.
        """
        if not self.command:
            return ""

        try:
            # Use shell=True to allow piping and complex commands
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
            )
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            return output.strip()
        except subprocess.TimeoutExpired:
            return "[Command timed out]"
        except Exception as e:
            return f"[Error: {e}]"

    def refresh(self) -> None:
        """Refresh zone content by re-executing command (for PIPE/WATCH)."""
        if self.zone_type in (ZoneType.PIPE, ZoneType.WATCH):
            output = self.execute_command()
            self.set_content(output)

    # PTY methods
    def start_pty(self, shell: str = "/bin/bash") -> bool:
        """
        Start a PTY session for this zone.

        Args:
            shell: Path to shell executable

        Returns:
            True if PTY started successfully, False otherwise
        """
        if not PTY_AVAILABLE:
            self.set_content("[PTY not available on this platform]")
            return False

        if self.zone_type != ZoneType.PTY:
            return False

        # Get content dimensions (inside borders)
        content_w = self.inner_width
        content_h = self.inner_height

        try:
            # Create pyte screen and stream for terminal emulation
            self.pty_screen = pyte.HistoryScreen(content_w, content_h, history=1000)
            self.pty_stream = pyte.Stream(self.pty_screen)

            # Fork PTY
            pid, fd = pty.fork()

            if pid == 0:
                # Child process - exec shell
                os.environ["TERM"] = "xterm-256color"
                os.environ["COLUMNS"] = str(content_w)
                os.environ["LINES"] = str(content_h)
                os.execlp(shell, shell)
            else:
                # Parent process
                self.pty_pid = pid
                self.pty_fd = fd

                # Set non-blocking mode on PTY
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                # Start background reader thread
                self.pty_stop_event = threading.Event()
                self.pty_reader_thread = threading.Thread(
                    target=self._pty_reader_loop,
                    daemon=True,
                )
                self.pty_reader_thread.start()

                return True

        except Exception as e:
            self.set_content(f"[PTY error: {e}]")
            return False

    def _pty_reader_loop(self) -> None:
        """Background thread that reads PTY output and feeds to pyte."""
        while not self.pty_stop_event.is_set():
            try:
                # Wait for data with timeout
                readable, _, _ = select.select([self.pty_fd], [], [], 0.1)
                if readable:
                    data = os.read(self.pty_fd, 4096)
                    if data:
                        # Feed data to pyte terminal emulator
                        self.pty_stream.feed(data.decode("utf-8", errors="replace"))
                        # Update content from pyte screen
                        self._update_content_from_pty()
            except OSError:
                # PTY closed
                break
            except Exception:
                pass

    def _update_content_from_pty(self) -> None:
        """Update zone content from pyte screen buffer."""
        if not self.pty_screen:
            return

        lines = []
        for y in range(self.pty_screen.lines):
            line_chars = []
            for x in range(self.pty_screen.columns):
                char = self.pty_screen.buffer[y][x]
                line_chars.append(char.data)
            lines.append("".join(line_chars))
        self.content = lines

    def write_to_pty(self, text: str) -> bool:
        """
        Send text to the PTY.

        Args:
            text: Text to send (can include escape sequences)

        Returns:
            True if successful, False otherwise
        """
        if self.pty_fd < 0:
            return False

        try:
            os.write(self.pty_fd, text.encode("utf-8"))
            return True
        except OSError:
            return False

    def stop_pty(self) -> None:
        """Stop the PTY session and clean up resources."""
        if self.pty_stop_event:
            self.pty_stop_event.set()

        if self.pty_reader_thread:
            self.pty_reader_thread.join(timeout=1.0)
            self.pty_reader_thread = None

        if self.pty_fd >= 0:
            try:
                os.close(self.pty_fd)
            except OSError:
                pass
            self.pty_fd = -1

        if self.pty_pid > 0:
            try:
                os.kill(self.pty_pid, 9)
                os.waitpid(self.pty_pid, os.WNOHANG)
            except (OSError, ChildProcessError):
                pass
            self.pty_pid = -1

        self.pty_screen = None
        self.pty_stream = None
        self.pty_stop_event = None
        self.focused = False

    def is_pty_active(self) -> bool:
        """Check if PTY is currently active."""
        return self.pty_fd >= 0 and self.pty_pid > 0


class ZoneManager:
    """
    Manages a collection of zones.

    Provides zone lookup, creation, deletion, and spatial queries.
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
        zone_type: ZoneType = ZoneType.STATIC,
        command: str = "",
        interval: float = 5.0,
    ) -> Zone:
        """
        Create a new zone and add it to the manager.

        Args:
            name: Unique name for the zone
            x, y: Top-left corner position
            width, height: Zone dimensions
            zone_type: Type of zone
            command: Shell command for PIPE/WATCH zones
            interval: Refresh interval for WATCH zones

        Returns:
            The created Zone object
        """
        zone = Zone(
            name=name.upper(),  # Zone names are always uppercase
            x=x,
            y=y,
            width=width,
            height=height,
            zone_type=zone_type,
            command=command,
            interval=interval,
        )

        # Execute command immediately for PIPE/WATCH zones
        if zone_type in (ZoneType.PIPE, ZoneType.WATCH):
            zone.refresh()

        self._zones[zone.name] = zone
        return zone

    def get(self, name: str) -> Zone | None:
        """Get a zone by name (case-insensitive)."""
        return self._zones.get(name.upper())

    def delete(self, name: str) -> bool:
        """Delete a zone by name. Returns True if deleted, False if not found."""
        name = name.upper()
        if name in self._zones:
            zone = self._zones[name]
            # Clean up PTY if active
            if zone.zone_type == ZoneType.PTY and zone.is_pty_active():
                zone.stop_pty()
            del self._zones[name]
            return True
        return False

    def list_zones(self) -> list[Zone]:
        """Get all zones as a list."""
        return list(self._zones.values())

    def get_zone_at(self, x: int, y: int) -> Zone | None:
        """Get the zone containing the given canvas point, if any."""
        for zone in self._zones.values():
            if zone.contains_point(x, y):
                return zone
        return None

    def get_watch_zones(self) -> list[Zone]:
        """Get all WATCH zones (for periodic refresh scheduling)."""
        return [z for z in self._zones.values() if z.zone_type == ZoneType.WATCH]

    def clear(self) -> None:
        """Remove all zones."""
        self._zones.clear()

    def __len__(self) -> int:
        return len(self._zones)

    def __iter__(self):
        return iter(self._zones.values())

    def __contains__(self, name: str) -> bool:
        return name.upper() in self._zones
