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
- PAGER: Paginated file viewer with ANSI color support
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Any
import math
import re
import shlex


# Regex to match ANSI escape sequences
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b[>=]")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _ANSI_ESCAPE_RE.sub("", text)


@dataclass
class StyledChar:
    """A character with color information for ANSI-parsed content."""

    char: str
    fg: int = -1  # Foreground color (-1 = default, 0-7 = colors)
    bg: int = -1  # Background color (-1 = default, 0-7 = colors)


def _map_256_to_8(color256: int) -> int:
    """
    Map a 256-color palette index to basic 8-color index.

    256-color palette:
    - 0-7: standard colors (map directly)
    - 8-15: bright colors (map to 0-7)
    - 16-231: 6x6x6 RGB cube
    - 232-255: grayscale ramp
    """
    if color256 < 0:
        return -1
    if color256 < 8:
        return color256
    if color256 < 16:
        return color256 - 8
    if color256 < 232:
        # 6x6x6 color cube: 16 + 36*r + 6*g + b where r,g,b in 0-5
        idx = color256 - 16
        r = idx // 36
        g = (idx % 36) // 6
        b = idx % 6
        # Map to basic color based on RGB values
        # Threshold at 3 (midpoint of 0-5)
        r_bit = 1 if r >= 3 else 0
        g_bit = 1 if g >= 3 else 0
        b_bit = 1 if b >= 3 else 0
        # Map to 8-color: 0=black, 1=red, 2=green, 3=yellow, 4=blue, 5=magenta, 6=cyan, 7=white
        return r_bit | (g_bit << 1) | (b_bit << 2)
    else:
        # Grayscale: 232-255 maps to 24 levels
        gray = color256 - 232  # 0-23
        return 7 if gray >= 12 else 0  # white or black


def parse_ansi_line(line: str) -> list[StyledChar]:
    """
    Parse a line containing ANSI escape codes and return styled characters.

    Handles SGR (Select Graphic Rendition) codes:
    - 0: Reset to default
    - 1: Bold (maps to bright colors +8, but we ignore for basic 8-color)
    - 30-37: Foreground colors (black, red, green, yellow, blue, magenta, cyan, white)
    - 40-47: Background colors
    - 38;5;N: 256-color foreground (mapped to 8 colors)
    - 48;5;N: 256-color background (mapped to 8 colors)
    - 90-97: Bright foreground colors (map to 0-7)
    - 100-107: Bright background colors (map to 0-7)

    Args:
        line: Text line potentially containing ANSI escape sequences

    Returns:
        List of StyledChar, one per visible character
    """
    result: list[StyledChar] = []
    fg, bg = -1, -1
    i = 0

    while i < len(line):
        # Check for ANSI escape sequence
        if line[i : i + 2] == "\x1b[":
            # Find the end of the escape sequence (letter terminates it)
            j = i + 2
            while j < len(line) and line[j] not in "ABCDEFGHJKSTfmsu":
                j += 1

            if j < len(line) and line[j] == "m":
                # SGR sequence - parse color codes
                codes_str = line[i + 2 : j]
                if codes_str:
                    codes = codes_str.split(";")
                    idx = 0
                    while idx < len(codes):
                        try:
                            code = int(codes[idx]) if codes[idx] else 0
                        except ValueError:
                            code = 0

                        if code == 0:
                            # Reset
                            fg, bg = -1, -1
                        elif code == 1:
                            # Bold - ignore for now (would need bright colors)
                            pass
                        elif code == 38 and idx + 2 < len(codes):
                            # Extended foreground color
                            try:
                                mode = int(codes[idx + 1]) if codes[idx + 1] else 0
                                if mode == 5 and idx + 2 < len(codes):
                                    # 256-color mode
                                    color = int(codes[idx + 2]) if codes[idx + 2] else 0
                                    fg = _map_256_to_8(color)
                                    idx += 2  # Skip the mode and color params
                            except (ValueError, IndexError):
                                pass
                        elif code == 48 and idx + 2 < len(codes):
                            # Extended background color
                            try:
                                mode = int(codes[idx + 1]) if codes[idx + 1] else 0
                                if mode == 5 and idx + 2 < len(codes):
                                    # 256-color mode
                                    color = int(codes[idx + 2]) if codes[idx + 2] else 0
                                    bg = _map_256_to_8(color)
                                    idx += 2  # Skip the mode and color params
                            except (ValueError, IndexError):
                                pass
                        elif 30 <= code <= 37:
                            # Standard foreground colors
                            fg = code - 30
                        elif 40 <= code <= 47:
                            # Standard background colors
                            bg = code - 40
                        elif 90 <= code <= 97:
                            # Bright foreground (map to standard)
                            fg = code - 90
                        elif 100 <= code <= 107:
                            # Bright background (map to standard)
                            bg = code - 100
                        elif code == 39:
                            # Default foreground
                            fg = -1
                        elif code == 49:
                            # Default background
                            bg = -1

                        idx += 1

                i = j + 1
                continue
            else:
                # Non-SGR escape sequence, skip it
                i = j + 1 if j < len(line) else j
                continue

        # Regular character
        char = line[i]
        if char not in ("\r", "\n"):
            result.append(StyledChar(char, fg, bg))
        i += 1

    return result


def parse_ansi_content(content: str) -> list[list[StyledChar]]:
    """
    Parse multi-line content with ANSI codes.

    Args:
        content: Multi-line text with ANSI escape sequences

    Returns:
        List of styled lines, each line is a list of StyledChar
    """
    lines = content.split("\n")
    return [parse_ansi_line(line) for line in lines]


# Border style character sets
# Includes corners, edges, and junction characters for DRAW mode
BORDER_STYLES = {
    "ascii": {
        "tl": "+",
        "tr": "+",
        "bl": "+",
        "br": "+",
        "horiz": "-",
        "vert": "|",
        "cross": "+",
        "tee_down": "+",
        "tee_up": "+",
        "tee_right": "+",
        "tee_left": "+",
        "focused_tl": "#",
        "focused_tr": "#",
        "focused_bl": "#",
        "focused_br": "#",
        "focused_horiz": "=",
        "focused_vert": "#",
    },
    "unicode": {
        "tl": "┌",
        "tr": "┐",
        "bl": "└",
        "br": "┘",
        "horiz": "─",
        "vert": "│",
        "cross": "┼",
        "tee_down": "┬",
        "tee_up": "┴",
        "tee_right": "├",
        "tee_left": "┤",
        "focused_tl": "╔",
        "focused_tr": "╗",
        "focused_bl": "╚",
        "focused_br": "╝",
        "focused_horiz": "═",
        "focused_vert": "║",
    },
    "rounded": {
        "tl": "╭",
        "tr": "╮",
        "bl": "╰",
        "br": "╯",
        "horiz": "─",
        "vert": "│",
        "cross": "┼",
        "tee_down": "┬",
        "tee_up": "┴",
        "tee_right": "├",
        "tee_left": "┤",
        "focused_tl": "╔",
        "focused_tr": "╗",
        "focused_bl": "╚",
        "focused_br": "╝",
        "focused_horiz": "═",
        "focused_vert": "║",
    },
    "double": {
        "tl": "╔",
        "tr": "╗",
        "bl": "╚",
        "br": "╝",
        "horiz": "═",
        "vert": "║",
        "cross": "╬",
        "tee_down": "╦",
        "tee_up": "╩",
        "tee_right": "╠",
        "tee_left": "╣",
        "focused_tl": "╬",
        "focused_tr": "╬",
        "focused_bl": "╬",
        "focused_br": "╬",
        "focused_horiz": "═",
        "focused_vert": "║",
    },
    "heavy": {
        "tl": "┏",
        "tr": "┓",
        "bl": "┗",
        "br": "┛",
        "horiz": "━",
        "vert": "┃",
        "cross": "╋",
        "tee_down": "┳",
        "tee_up": "┻",
        "tee_right": "┣",
        "tee_left": "┫",
        "focused_tl": "╋",
        "focused_tr": "╋",
        "focused_bl": "╋",
        "focused_br": "╋",
        "focused_horiz": "━",
        "focused_vert": "┃",
    },
}

# Current border style (can be changed globally)
_current_border_style = "ascii"


def get_border_style() -> str:
    """Get current border style name."""
    return _current_border_style


def set_border_style(style: str) -> bool:
    """Set border style. Returns True if valid style."""
    global _current_border_style
    if style in BORDER_STYLES:
        _current_border_style = style
        return True
    return False


def list_border_styles() -> list[str]:
    """List available border styles."""
    return list(BORDER_STYLES.keys())


def get_border_chars() -> dict[str, str]:
    """Get character set for current border style."""
    return BORDER_STYLES.get(_current_border_style, BORDER_STYLES["ascii"])


class ZoneType(Enum):
    """Types of zones with different behaviors."""

    STATIC = "static"  # Plain text region (default)
    PIPE = "pipe"  # One-shot command output
    WATCH = "watch"  # Periodic refresh command
    PTY = "pty"  # Live terminal session
    FIFO = "fifo"  # Named pipe listener
    SOCKET = "socket"  # Network port listener
    CLIPBOARD = "clipboard"  # Yank/paste buffer
    PAGER = "pager"  # Paginated file viewer with colors


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

    # For PAGER zones
    file_path: str | None = None  # Source file to display
    renderer: str = "auto"  # "glow", "bat", "plain", or "auto"
    scroll_offset: int = 0  # Current scroll position (line number)
    search_term: str | None = None  # Active search term
    search_matches: list[int] = field(default_factory=list)  # Line numbers with matches
    search_index: int = 0  # Current match index

    # For PTY zones
    pty_scroll_offset: int = 0  # Scroll position in PTY history buffer
    pty_auto_scroll: bool = True  # Auto-scroll to bottom on new output

    # Display options
    scroll: bool = True  # Auto-scroll to bottom on new content
    wrap: bool = False  # Wrap long lines
    max_lines: int = 1000  # Buffer limit for output

    # State
    paused: bool = False  # Pause refresh for WATCH zones
    focused: bool = False  # PTY/PAGER zone has keyboard focus

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
        # PAGER fields
        if self.file_path:
            data["file_path"] = self.file_path
        if self.renderer != "auto":
            data["renderer"] = self.renderer
        if self.scroll_offset != 0:
            data["scroll_offset"] = self.scroll_offset
        if self.search_term:
            data["search_term"] = self.search_term
        # Display options
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
            # PAGER fields
            file_path=data.get("file_path"),
            renderer=data.get("renderer", "auto"),
            scroll_offset=data.get("scroll_offset", 0),
            search_term=data.get("search_term"),
            # Display options
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
    bookmark: str | None = None  # Associated bookmark key (a-z, 0-9)
    config: ZoneConfig = field(default_factory=ZoneConfig)

    # Content buffer for dynamic zones (not serialized - regenerated at runtime)
    _content_lines: list[str] = field(default_factory=list, repr=False)
    _styled_content: list[list[StyledChar]] = field(
        default_factory=list, repr=False
    )  # PAGER parsed content
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
            ZoneType.PAGER: "R",  # R for Reader
        }
        return indicators.get(self.config.zone_type, "?")

    def set_styled_content(self, styled_lines: list[list[StyledChar]]) -> None:
        """Set parsed ANSI content for PAGER zones."""
        self._styled_content = styled_lines

    def render_to_canvas(self, canvas) -> None:
        """
        Render zone content to canvas.

        For dynamic zones, writes content lines to the zone area.
        For PAGER zones, renders styled content with colors and scroll offset.
        Draws border if configured.
        """
        if not self.is_dynamic:
            return

        # Clear zone area first (content area, not border)
        content_x = self.x + 1
        content_y = self.y + 1
        content_w = self.width - 2
        content_h = self.height - 2

        for row in range(content_h):
            for col in range(content_w):
                canvas.clear(content_x + col, content_y + row)

        # PAGER zones use styled content with scroll offset
        if self.config.zone_type == ZoneType.PAGER:
            self._render_pager_content(
                canvas, content_x, content_y, content_w, content_h
            )
            return

        # PTY zones with styled content (pyte colors) - render directly
        if self.config.zone_type == ZoneType.PTY and self._styled_content:
            self._render_pty_styled_content(
                canvas, content_x, content_y, content_w, content_h
            )
            return

        # Other dynamic zones: parse ANSI codes and render with colors
        # PTY zones support scrollback, others auto-scroll
        total_lines = len(self._content_lines)

        if self.config.zone_type == ZoneType.PTY:
            # PTY zones: Use scroll offset if set, otherwise auto-scroll
            if self.config.pty_auto_scroll:
                # Auto-scroll: show last N lines
                start_line = max(0, total_lines - content_h)
                visible_lines = self._content_lines[start_line:]
            else:
                # Manual scroll mode: use pty_scroll_offset
                start_line = self.config.pty_scroll_offset
                end_line = start_line + content_h
                visible_lines = self._content_lines[start_line:end_line]
        else:
            # Other zones: auto-scroll
            if total_lines > content_h:
                visible_lines = self._content_lines[-content_h:]
            else:
                visible_lines = self._content_lines

        for row, line in enumerate(visible_lines):
            # Parse ANSI codes to preserve colors
            styled_chars = parse_ansi_line(line)

            for col, sc in enumerate(styled_chars):
                if col >= content_w:
                    break  # Line too long
                if sc.char not in (" ", "\t", "\n", "\r"):
                    # Render with color if specified (use -1 for default, not None)
                    fg = sc.fg if sc.fg >= 0 else -1
                    bg = sc.bg if sc.bg >= 0 else -1
                    canvas.set(content_x + col, content_y + row, sc.char, fg=fg, bg=bg)

    def _render_pty_styled_content(
        self, canvas, content_x: int, content_y: int, content_w: int, content_h: int
    ) -> None:
        """Render PTY zone with styled content from pyte (with colors)."""
        if not self._styled_content:
            return

        # PTY styled content is already at the correct scroll offset
        # (handled by pyte when we call get_display_lines_styled)
        visible_lines = self._styled_content[:content_h]

        for row, styled_line in enumerate(visible_lines):
            for col, sc in enumerate(styled_line):
                if col >= content_w:
                    break  # Line too long

                # Skip whitespace characters (but render them if they have background color)
                if sc.char in (" ", "\t", "\n", "\r") and sc.bg == -1:
                    continue

                # Render character with pyte colors
                canvas.set(
                    content_x + col, content_y + row, sc.char, fg=sc.fg, bg=sc.bg
                )

    def _render_pager_content(
        self, canvas, content_x: int, content_y: int, content_w: int, content_h: int
    ) -> None:
        """Render PAGER zone with styled content, colors, and scroll offset."""
        if not self._styled_content:
            return

        # Get visible lines based on scroll offset
        start = self.config.scroll_offset
        total_lines = len(self._styled_content)
        # Clamp scroll offset to valid range
        max_offset = max(0, total_lines - content_h)
        if start > max_offset:
            start = max_offset
            self.config.scroll_offset = start

        visible_lines = self._styled_content[start : start + content_h]

        # Check if we have search matches to highlight
        search_term = self.config.search_term
        search_lines = (
            set(self.config.search_matches) if self.config.search_matches else set()
        )

        # Render content (leave 1 char on right for scrollbar if needed)
        text_width = content_w - 1 if total_lines > content_h else content_w

        for row, styled_line in enumerate(visible_lines):
            line_num = start + row
            is_match_line = line_num in search_lines

            for col, sc in enumerate(styled_line):
                if col >= text_width:
                    break  # Line too long

                if sc.char in (" ", "\t", "\n", "\r"):
                    continue

                # Use character's colors, or highlight if on search match line
                fg, bg = sc.fg, sc.bg
                if is_match_line and search_term:
                    # Highlight search match lines with inverted colors
                    bg = 6  # Cyan background for match lines

                canvas.set(content_x + col, content_y + row, sc.char, fg=fg, bg=bg)

        # Draw scroll indicator on right edge if content overflows
        if total_lines > content_h:
            self._render_scroll_indicator(
                canvas,
                content_x + content_w - 1,
                content_y,
                content_h,
                start,
                total_lines,
            )

    def _render_scroll_indicator(
        self, canvas, x: int, y: int, height: int, scroll_offset: int, total_lines: int
    ) -> None:
        """Render a scrollbar/position indicator on the right edge."""
        # Calculate thumb position and size
        # Thumb size: proportional to visible/total ratio, min 1 char
        thumb_ratio = height / total_lines
        thumb_size = max(1, int(height * thumb_ratio))

        # Thumb position: based on scroll offset
        scroll_range = total_lines - height
        if scroll_range > 0:
            scroll_ratio = scroll_offset / scroll_range
            track_space = height - thumb_size
            thumb_pos = int(scroll_ratio * track_space)
        else:
            thumb_pos = 0

        # Draw the scrollbar
        # Track character (light shade), Thumb character (full block)
        TRACK = "░"  # Light shade
        THUMB = "█"  # Full block

        for row in range(height):
            if thumb_pos <= row < thumb_pos + thumb_size:
                canvas.set(x, y + row, THUMB, fg=7)  # White thumb
            else:
                canvas.set(x, y + row, TRACK, fg=0)  # Dark track

    @property
    def pager_line_count(self) -> int:
        """Get total number of lines in PAGER content."""
        return len(self._styled_content)

    @property
    def pager_visible_lines(self) -> int:
        """Get number of visible lines in PAGER zone."""
        return self.height - 2  # Minus border

    def draw_border(self, canvas, focused: bool = False) -> None:
        """
        Draw zone border on canvas.

        Args:
            canvas: Canvas to draw on
            focused: If True, use highlight style
        """
        x, y = self.x, self.y
        w, h = self.width, self.height

        # Get border characters from current style
        style = BORDER_STYLES.get(_current_border_style, BORDER_STYLES["ascii"])
        if focused:
            tl = style["focused_tl"]
            tr = style["focused_tr"]
            bl = style["focused_bl"]
            br = style["focused_br"]
            horiz = style["focused_horiz"]
            vert = style["focused_vert"]
        else:
            tl = style["tl"]
            tr = style["tr"]
            bl = style["bl"]
            br = style["br"]
            horiz = style["horiz"]
            vert = style["vert"]

        # Top border with zone info
        header = f"[{self.type_indicator()}] {self.name}"
        if self.config.paused:
            header += " (paused)"
        elif self.config.zone_type == ZoneType.WATCH and self.config.refresh_interval:
            header += f" ({self.config.refresh_interval}s)"

        # Draw top left corner
        canvas.set(x, y, tl)
        # Draw header
        for i, char in enumerate(header[: w - 4]):
            canvas.set(x + 1 + i, y, char)
        # Fill rest of top border
        for i in range(len(header) + 1, w - 1):
            canvas.set(x + i, y, horiz)
        # Top right corner
        canvas.set(x + w - 1, y, tr)

        # Sides
        for row in range(1, h - 1):
            canvas.set(x, y + row, vert)
            canvas.set(x + w - 1, y + row, vert)

        # Bottom border
        canvas.set(x, y + h - 1, bl)
        for i in range(1, w - 1):
            canvas.set(x + i, y + h - 1, horiz)
        canvas.set(x + w - 1, y + h - 1, br)

    def clear_from_canvas(self, canvas) -> None:
        """Clear this zone's region from the canvas."""
        for row in range(self.height):
            for col in range(self.width):
                canvas.clear(self.x + col, self.y + row)

    def contains(self, cx: int, cy: int) -> bool:
        """Check if a canvas coordinate is within this zone."""
        return (
            self.x <= cx < self.x + self.width and self.y <= cy < self.y + self.height
        )

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
            return "·"

        # Determine primary direction
        if abs(dx) > abs(dy) * 2:
            # Primarily horizontal
            return "→" if dx > 0 else "←"
        elif abs(dy) > abs(dx) * 2:
            # Primarily vertical
            return "↓" if dy > 0 else "↑"
        else:
            # Diagonal
            if dx > 0 and dy > 0:
                return "↘"
            elif dx > 0 and dy < 0:
                return "↗"
            elif dx < 0 and dy > 0:
                return "↙"
            else:
                return "↖"

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

    def create_clipboard(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        bookmark: str | None = None,
    ) -> Zone:
        """Create a CLIPBOARD zone for yank/paste operations."""
        config = ZoneConfig(
            zone_type=ZoneType.CLIPBOARD,
        )
        return self.create(
            name,
            x,
            y,
            width,
            height,
            description="Clipboard buffer",
            bookmark=bookmark,
            config=config,
        )

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
        self, x: int, y: int, exclude_current: bool = True
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
        nearest_dist = float("inf")

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

    def clear_with_canvas(self, canvas) -> None:
        """Remove all zones and clear their canvas regions."""
        for zone in self._zones.values():
            zone.clear_from_canvas(canvas)
        self._zones.clear()

    def __len__(self) -> int:
        return len(self._zones)

    def __iter__(self) -> Iterator[Zone]:
        return iter(self._zones.values())

    def __contains__(self, name: str) -> bool:
        return name.lower() in self._zones

    def render_all_zones(self, canvas, focused_zone: str | None = None) -> None:
        """
        Render all dynamic zones to the canvas.

        Args:
            canvas: Canvas to render to
            focused_zone: Name of focused zone (for highlight)
        """
        for zone in self._zones.values():
            is_focused = focused_zone and zone.name.lower() == focused_zone.lower()
            # Draw border for all zones
            zone.draw_border(canvas, focused=is_focused)
            # Render content for dynamic zones
            if zone.is_dynamic:
                zone.render_to_canvas(canvas)

    def to_dict(self) -> dict:
        """Serialize all zones to dictionary for JSON export."""
        return {"zones": [zone.to_dict() for zone in self.list_all()]}

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
                timeout=timeout,
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
                name=f"watch-{key}",
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


# =============================================================================
# PTY HANDLER - Live terminal embedding for PTY zones
# =============================================================================

import os
import sys
import signal
import struct

# Only import Unix-specific modules on Unix-like systems
try:
    import fcntl
    import termios
    import select
    import pty

    PTY_AVAILABLE = True
    PTYScreen = None  # Will import lazily when needed
except ImportError:
    fcntl = None
    termios = None
    select = None
    PTYScreen = None
    PTY_AVAILABLE = False


class PTYHandler:
    """
    Handles PTY (pseudo-terminal) zones with live shell sessions.

    Features:
    - Spawns shell process connected to PTY
    - Background thread reads PTY output
    - Basic ANSI escape sequence handling
    - Focus mechanism for keyboard forwarding
    - Clean process shutdown
    """

    def __init__(self, zone_manager: ZoneManager):
        self.zone_manager = zone_manager
        self._pty_data: dict[str, dict] = (
            {}
        )  # zone_name -> {fd, pid, thread, stop_event}
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        """Check if PTY is available on this platform."""
        return PTY_AVAILABLE

    def create_pty(self, zone: Zone) -> bool:
        """
        Create a PTY session for a zone.

        Returns True on success, False on error.
        """
        if not PTY_AVAILABLE:
            zone.set_content(["[PTY not available on this platform]"])
            return False

        if zone.config.zone_type != ZoneType.PTY:
            return False

        key = zone.name.lower()

        # Clean up existing PTY if any
        self.stop_pty(zone.name)

        try:
            # Create PTY master/slave pair
            master_fd, slave_fd = pty.openpty()

            # Set terminal size based on zone dimensions
            content_w = zone.width - 2  # Account for border
            content_h = zone.height - 2
            self._set_winsize(master_fd, content_h, content_w)

            # Fork process (don't set master attrs - let shell handle echo)
            pid = os.fork()

            if pid == 0:
                # Child process
                os.close(master_fd)
                os.setsid()

                # Set up slave as controlling terminal
                fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)

                # Redirect stdin/stdout/stderr to slave
                os.dup2(slave_fd, 0)
                os.dup2(slave_fd, 1)
                os.dup2(slave_fd, 2)

                if slave_fd > 2:
                    os.close(slave_fd)

                # Set environment
                env = os.environ.copy()
                env["TERM"] = "xterm-256color"
                env["COLUMNS"] = str(content_w)
                env["LINES"] = str(content_h)
                env["PS1"] = "$ "  # Simple prompt for better display

                # Execute shell in interactive mode
                shell = zone.config.shell or "/bin/bash"
                # Add -i for interactive mode (enables echo and proper TTY behavior)
                os.execvpe(shell, [shell, "-i"], env)

            else:
                # Parent process
                os.close(slave_fd)

                # Set master to non-blocking
                flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
                fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                # Create pyte terminal emulator screen
                try:
                    # Import from src package
                    from src.pty_screen import PTYScreen as PTYScreenClass

                    screen = PTYScreenClass(content_w, content_h, history=1000)
                    zone.append_content(
                        f"[PTY: Using pyte terminal emulator - {content_w}x{content_h}]"
                    )
                except ImportError as e:
                    zone.set_content(
                        [
                            f"[PTY: pyte import failed - {e}]",
                            "[Falling back to line-based mode]",
                        ]
                    )
                    screen = None  # Will use old reader
                except Exception as e:
                    zone.set_content([f"[PTY: pyte initialization failed - {e}]"])
                    screen = None

                # Start reader thread (use pyte if available, else fallback)
                stop_event = threading.Event()
                if screen is not None:
                    # Use pyte terminal emulator
                    reader_thread = threading.Thread(
                        target=self._pty_reader_pyte,
                        args=(zone, master_fd, stop_event, screen),
                        daemon=True,
                        name=f"pty-{key}",
                    )
                else:
                    # Fallback to old line-based reader
                    reader_thread = threading.Thread(
                        target=self._pty_reader,
                        args=(zone, master_fd, stop_event),
                        daemon=True,
                        name=f"pty-{key}",
                    )

                with self._lock:
                    self._pty_data[key] = {
                        "fd": master_fd,
                        "pid": pid,
                        "thread": reader_thread,
                        "stop_event": stop_event,
                        "screen": screen,  # Store pyte screen
                    }

                reader_thread.start()
                return True

        except Exception as e:
            zone.set_content([f"[PTY error: {e}]"])
            return False

    def _set_winsize(self, fd: int, rows: int, cols: int) -> None:
        """Set terminal window size."""
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    def _pty_reader_pyte(
        self, zone: Zone, fd: int, stop_event: threading.Event, screen
    ) -> None:
        """Background thread that reads PTY output using pyte terminal emulator.

        This is the NEW implementation using proper terminal emulation.
        Handles all cursor control, backspace, escape sequences correctly.

        Args:
            zone: Zone to update
            fd: PTY master file descriptor
            stop_event: Threading event for shutdown
            screen: PTYScreen instance for terminal emulation
        """

        while not stop_event.is_set():
            try:
                # Use select with faster timeout for responsive updates
                readable, _, _ = select.select([fd], [], [], 0.05)

                if not readable:
                    continue

                # Read data from PTY
                data = os.read(fd, 4096)
                if not data:
                    # EOF - process exited
                    # Get final screen state WITH COLORS
                    final_styled = screen.get_display_lines_styled(scroll_offset=0)
                    # Add exit message as plain text line
                    from src.pty_screen import StyledChar

                    exit_line = [StyledChar(ch, -1, -1) for ch in "[Process exited]"]
                    zone.set_styled_content(final_styled + [exit_line])
                    break

                # Decode and feed to pyte (handles ALL terminal sequences!)
                text = data.decode("utf-8", errors="replace")
                screen.feed(text)

                # Get current display from pyte screen WITH COLORS
                if zone.config.pty_auto_scroll:
                    # Show current screen (normal mode)
                    styled_lines = screen.get_display_lines_styled(scroll_offset=0)
                else:
                    # Show scrolled view
                    styled_lines = screen.get_display_lines_styled(
                        scroll_offset=zone.config.pty_scroll_offset
                    )

                # Update zone content with styled characters (colors preserved!)
                # This is key: pyte maintains the screen state, we just display it
                zone.set_styled_content(styled_lines)

            except OSError:
                # FD closed or error
                break
            except Exception as e:
                # On error, try to preserve screen state
                try:
                    from src.pty_screen import StyledChar

                    styled_lines = screen.get_display_lines_styled(scroll_offset=0)
                    error_msg = f"[PTY error: {e}]"
                    error_line = [StyledChar(ch, 1, -1) for ch in error_msg]  # Red text
                    zone.set_styled_content(styled_lines + [error_line])
                except (ImportError, AttributeError, TypeError) as inner_e:
                    from src.pty_screen import StyledChar

                    error_msg = f"[PTY error: {e}]"
                    error_line = [StyledChar(ch, 1, -1) for ch in error_msg]
                    zone.set_styled_content([error_line])
                break

    def _pty_reader(self, zone: Zone, fd: int, stop_event: threading.Event) -> None:
        """OLD: Line-based PTY reader (DEPRECATED - kept for reference).

        This old implementation doesn't work for interactive apps.
        Use _pty_reader_pyte instead.
        """
        buffer = ""
        showing_incomplete = False

        while not stop_event.is_set():
            try:
                # Use select with timeout for responsive shutdown
                readable, _, _ = select.select([fd], [], [], 0.1)

                if not readable:
                    continue

                data = os.read(fd, 4096)
                if not data:
                    # EOF - process exited
                    if buffer.strip():
                        zone.append_content(buffer)
                    zone.append_content("[Process exited]")
                    break

                # Decode and process output
                text = data.decode("utf-8", errors="replace")
                buffer += text

                # Split on newlines
                parts = buffer.split("\n")

                # Remove previous incomplete line if we had one
                if showing_incomplete and zone._content_lines:
                    zone._content_lines.pop()
                    showing_incomplete = False

                # Add all complete lines (everything except the last element)
                for line in parts[:-1]:
                    # Remove carriage returns
                    clean_line = line.replace("\r", "")
                    zone.append_content(clean_line)

                # Keep the incomplete part in buffer
                buffer = parts[-1]

                # Show the incomplete line (what you're currently typing!)
                if buffer:
                    # Don't show if it's just \r or whitespace
                    display_buffer = buffer.replace("\r", "")
                    if display_buffer:
                        zone.append_content(display_buffer)
                        showing_incomplete = True

            except OSError:
                # FD closed or error
                break
            except Exception as e:
                zone.append_content(f"[Read error: {e}]")
                break

    def get_screen(self, name: str):
        """
        Get pyte screen for a PTY zone (if using pyte).

        Args:
            name: Zone name

        Returns:
            PTYScreen instance or None
        """
        key = name.lower()
        with self._lock:
            data = self._pty_data.get(key)
            if data:
                return data.get("screen")
        return None

    def _strip_ansi(self, text: str) -> str:
        """Strip ANSI escape sequences from text (basic implementation)."""
        import re

        # Remove common ANSI sequences
        ansi_pattern = re.compile(
            r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[()][AB012]"
        )
        result = ansi_pattern.sub("", text)
        # Remove carriage returns
        result = result.replace("\r", "")
        return result

    def send_input(self, name: str, text: str) -> bool:
        """
        Send input text to a PTY zone.

        Args:
            name: Zone name
            text: Text to send (use \\n for newline)

        Returns True on success.
        """
        key = name.lower()

        with self._lock:
            data = self._pty_data.get(key)
            if not data:
                return False

            try:
                os.write(data["fd"], text.encode("utf-8"))
                return True
            except OSError:
                return False

    def resize_pty(self, name: str, rows: int, cols: int) -> bool:
        """Resize PTY terminal."""
        key = name.lower()

        with self._lock:
            data = self._pty_data.get(key)
            if not data:
                return False

            try:
                self._set_winsize(data["fd"], rows, cols)
                return True
            except OSError:
                return False

    def stop_pty(self, name: str) -> None:
        """Stop PTY session and clean up."""
        key = name.lower()

        with self._lock:
            data = self._pty_data.pop(key, None)

        if data:
            # Signal thread to stop
            data["stop_event"].set()

            # Close FD
            try:
                os.close(data["fd"])
            except OSError:
                pass

            # Terminate process
            try:
                os.kill(data["pid"], signal.SIGTERM)
                # Give it a moment, then SIGKILL if needed
                os.waitpid(data["pid"], os.WNOHANG)
            except OSError:
                pass

    def stop_all(self) -> None:
        """Stop all PTY sessions."""
        with self._lock:
            keys = list(self._pty_data.keys())

        for key in keys:
            self.stop_pty(key)

    def is_active(self, name: str) -> bool:
        """Check if PTY is active for a zone."""
        key = name.lower()
        with self._lock:
            return key in self._pty_data


# =============================================================================
# CLIPBOARD HELPER - Yank/paste operations
# =============================================================================


class Clipboard:
    """
    Helper for clipboard operations within the canvas.

    Can yank regions from canvas, zone content, or arbitrary text.
    Stores content in an internal buffer and optionally in a CLIPBOARD zone.
    """

    def __init__(self):
        self._buffer: list[str] = []
        self._source: str = ""  # Description of where content came from

    @property
    def content(self) -> list[str]:
        """Get clipboard content as list of lines."""
        return self._buffer.copy()

    @property
    def text(self) -> str:
        """Get clipboard content as single string."""
        return "\n".join(self._buffer)

    @property
    def source(self) -> str:
        """Get description of content source."""
        return self._source

    @property
    def is_empty(self) -> bool:
        """Check if clipboard is empty."""
        return len(self._buffer) == 0 or (
            len(self._buffer) == 1 and not self._buffer[0]
        )

    def clear(self) -> None:
        """Clear clipboard contents."""
        self._buffer = []
        self._source = ""

    def set_content(self, lines: list[str], source: str = "") -> None:
        """Set clipboard content directly."""
        self._buffer = [line for line in lines]
        self._source = source

    def yank_region(
        self,
        canvas,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> int:
        """
        Yank a rectangular region from the canvas.

        Args:
            canvas: Canvas to yank from
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner

        Returns number of lines yanked.
        """
        # Ensure x1,y1 is top-left
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        lines = []
        for y in range(y1, y2 + 1):
            line = ""
            for x in range(x1, x2 + 1):
                char = canvas.get_char(x, y)
                line += char
            # Strip trailing spaces but keep line structure
            lines.append(line.rstrip())

        self._buffer = lines
        self._source = f"region ({x1},{y1})-({x2},{y2})"
        return len(lines)

    def yank_zone(self, zone: Zone) -> int:
        """
        Yank content from a zone.

        Args:
            zone: Zone to yank content from

        Returns number of lines yanked.
        """
        self._buffer = zone.content_lines.copy()
        self._source = f"zone {zone.name}"
        return len(self._buffer)

    def yank_zone_visual(self, zone: Zone, canvas) -> int:
        """
        Yank the visual representation of a zone from canvas.

        This yanks what's actually drawn on canvas, including border.

        Args:
            zone: Zone to yank
            canvas: Canvas to read from

        Returns number of lines yanked.
        """
        return self.yank_region(
            canvas, zone.x, zone.y, zone.x + zone.width - 1, zone.y + zone.height - 1
        )

    def paste_to_canvas(
        self,
        canvas,
        x: int,
        y: int,
        skip_spaces: bool = False,
    ) -> tuple[int, int]:
        """
        Paste clipboard content to canvas at position.

        Args:
            canvas: Canvas to paste to
            x, y: Top-left position for paste
            skip_spaces: If True, don't overwrite with spaces

        Returns (width, height) of pasted region.
        """
        if self.is_empty:
            return (0, 0)

        max_width = 0
        for row, line in enumerate(self._buffer):
            for col, char in enumerate(line):
                if skip_spaces and char == " ":
                    continue
                canvas.set(x + col, y + row, char)
            max_width = max(max_width, len(line))

        return (max_width, len(self._buffer))

    def update_clipboard_zone(self, zone: Zone) -> None:
        """Update a CLIPBOARD zone with current buffer content."""
        if zone.zone_type != ZoneType.CLIPBOARD:
            return
        zone.set_content(self._buffer)

    def to_system_clipboard(self) -> bool:
        """
        Copy buffer to system clipboard (if available).

        Returns True on success, False if not available.
        """
        try:
            import subprocess

            text = self.text

            # Try different clipboard commands
            # WSL: prefer clip.exe for Windows clipboard integration
            for cmd in [
                ["clip.exe"],  # WSL -> Windows
                ["xclip", "-selection", "clipboard"],
                ["xsel", "--clipboard", "--input"],
                ["pbcopy"],  # macOS
                ["clip"],
            ]:  # Windows native
                try:
                    proc = subprocess.run(
                        cmd, input=text.encode("utf-8"), capture_output=True, timeout=5
                    )
                    if proc.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def from_system_clipboard(self) -> bool:
        """
        Read content from system clipboard (if available).

        Returns True on success, False if not available.
        """
        try:
            import subprocess

            # Try different clipboard commands
            # WSL: prefer powershell.exe for Windows clipboard integration
            for cmd in [
                ["powershell.exe", "-command", "Get-Clipboard"],  # WSL -> Windows
                ["xclip", "-selection", "clipboard", "-o"],
                ["xsel", "--clipboard", "--output"],
                ["pbpaste"],  # macOS
                ["powershell", "-command", "Get-Clipboard"],
            ]:  # Windows native
                try:
                    proc = subprocess.run(cmd, capture_output=True, timeout=5)
                    if proc.returncode == 0:
                        text = proc.stdout.decode("utf-8", errors="replace")
                        self._buffer = text.split("\n")
                        # Remove trailing empty line from clipboard
                        if self._buffer and not self._buffer[-1]:
                            self._buffer.pop()
                        self._source = "system clipboard"
                        return True
                except FileNotFoundError:
                    continue
                except Exception:
                    continue
            return False
        except Exception:
            return False


# =============================================================================
# PAGER HANDLER - Paginated file viewer with renderer selection
# =============================================================================

import shutil

# Renderer configurations for different file types
PAGER_RENDERERS = {
    "glow": {
        "command": "glow -s dark {file}",
        # Pipe file content to glow since it needs stdin when no tty
        "wsl_command": "wsl bash -c \"cat '{file}' | glow -s dark -\"",
        "extensions": [".md", ".markdown", ".mkd", ".mdx"],
        "check": "glow --version",
        "wsl_check": "wsl bash -c 'which glow'",
        "description": "Markdown renderer with styles",
    },
    "bat": {
        "command": "bat --color=always --style=plain --paging=never {file}",
        # bat --force-colorization helps when no tty
        "wsl_command": "wsl bash -c \"bat --color=always --style=plain --paging=never --force-colorization '{file}'\"",
        "extensions": [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".c",
            ".h",
            ".cpp",
            ".hpp",
            ".cs",
            ".rb",
            ".php",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".yaml",
            ".yml",
            ".json",
            ".toml",
            ".xml",
            ".html",
            ".css",
            ".scss",
            ".sql",
            ".lua",
            ".vim",
            ".conf",
            ".ini",
            ".dockerfile",
            ".makefile",
        ],
        "check": "bat --version",
        "wsl_check": "wsl bash -c 'which bat'",
        "description": "Syntax-highlighted code viewer",
    },
    "plain": {
        # Use cat which works in git bash; 'type' is a bash builtin there
        "command": "cat {file}",
        "wsl_command": "wsl bash -c \"cat '{file}'\"",
        "extensions": ["*"],  # Fallback for any file
        "check": None,  # Always available
        "wsl_check": None,
        "description": "Plain text (no highlighting)",
    },
}

# Cache for renderer availability checks
_renderer_available_cache: dict[str, bool] = {}


def check_renderer_available(renderer_name: str, use_wsl: bool = False) -> bool:
    """
    Check if a renderer is available on the system.

    Args:
        renderer_name: Name of renderer ("glow", "bat", "plain")
        use_wsl: If True, check in WSL environment

    Returns:
        True if renderer is available
    """
    cache_key = f"{renderer_name}:{'wsl' if use_wsl else 'native'}"
    if cache_key in _renderer_available_cache:
        return _renderer_available_cache[cache_key]

    if renderer_name not in PAGER_RENDERERS:
        return False

    config = PAGER_RENDERERS[renderer_name]
    check_cmd = config.get("wsl_check" if use_wsl else "check")

    if check_cmd is None:
        # Plain text is always available
        _renderer_available_cache[cache_key] = True
        return True

    try:
        result = subprocess.run(check_cmd, shell=True, capture_output=True, timeout=5)
        available = result.returncode == 0
        _renderer_available_cache[cache_key] = available
        return available
    except Exception:
        _renderer_available_cache[cache_key] = False
        return False


def select_renderer(
    file_path: str, preferred: str = "auto", use_wsl: bool = False
) -> str:
    """
    Select the best renderer for a file based on extension.

    Args:
        file_path: Path to the file
        preferred: Preferred renderer ("auto", "glow", "bat", "plain")
        use_wsl: If True, check WSL availability

    Returns:
        Renderer name ("glow", "bat", or "plain")
    """
    # If specific renderer requested and available, use it
    if preferred != "auto" and preferred in PAGER_RENDERERS:
        if check_renderer_available(preferred, use_wsl):
            return preferred
        # Fall through to auto-detection if preferred not available

    # Get file extension
    _, ext = os.path.splitext(file_path.lower())

    # Check each renderer in preference order
    for renderer_name in ["glow", "bat"]:
        config = PAGER_RENDERERS[renderer_name]
        if ext in config["extensions"]:
            if check_renderer_available(renderer_name, use_wsl):
                return renderer_name

    # Fallback to plain
    return "plain"


def render_file_content(
    file_path: str, renderer: str = "auto", use_wsl: bool = False
) -> str:
    """
    Render file content using the specified renderer.

    Args:
        file_path: Path to the file to render
        renderer: Renderer to use ("auto", "glow", "bat", "plain")
        use_wsl: If True, use WSL commands

    Returns:
        Rendered content with ANSI codes, or error message
    """
    # Select renderer if auto
    if renderer == "auto":
        renderer = select_renderer(file_path, "auto", use_wsl)

    if renderer not in PAGER_RENDERERS:
        return f"[Unknown renderer: {renderer}]"

    config = PAGER_RENDERERS[renderer]

    # Build command
    cmd_template = config.get("wsl_command" if use_wsl else "command")
    if not cmd_template:
        return f"[No command for renderer: {renderer}]"

    # Handle WSL path conversion if needed
    render_path = file_path
    if use_wsl and os.name == "nt":
        # Convert Windows path to WSL path
        # C:\Users\foo -> /mnt/c/Users/foo
        if len(file_path) >= 2 and file_path[1] == ":":
            drive = file_path[0].lower()
            rest = file_path[2:].replace("\\", "/")
            render_path = f"/mnt/{drive}{rest}"

    # Security: Quote file path to prevent command injection (Issue #66)
    # The {file} placeholder in command templates gets user-provided paths.
    # Some templates (notably WSL commands) already wrap {file} in quotes;
    # in those cases, avoid double-quoting to keep the shell syntax valid.
    if "'{file}'" in cmd_template or '"{file}"' in cmd_template:
        formatted_path = render_path
    else:
        formatted_path = shlex.quote(render_path)
    cmd = cmd_template.format(file=formatted_path)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode == 0:
            return result.stdout
        else:
            # Return stderr if command failed
            return f"[Renderer error: {result.stderr.strip() or 'Unknown error'}]"

    except subprocess.TimeoutExpired:
        return "[Render timeout]"
    except FileNotFoundError:
        return f"[File not found: {file_path}]"
    except Exception as e:
        return f"[Render error: {e}]"


def load_pager_content(zone: "Zone", use_wsl: bool = False) -> bool:
    """
    Load and render content for a PAGER zone.

    Args:
        zone: The PAGER zone to load content for
        use_wsl: If True, use WSL for rendering

    Returns:
        True on success, False on error
    """
    if zone.config.zone_type != ZoneType.PAGER:
        return False

    file_path = zone.config.file_path
    if not file_path:
        zone.set_content(["[No file path configured]"])
        return False

    # Check if file exists (native check)
    if not os.path.exists(file_path):
        zone.set_content([f"[File not found: {file_path}]"])
        return False

    # Render content
    renderer = zone.config.renderer
    content = render_file_content(file_path, renderer, use_wsl)

    # Parse ANSI codes into styled content
    styled_lines = parse_ansi_content(content)
    zone.set_styled_content(styled_lines)

    # Also store plain lines for search
    plain_lines = content.split("\n")
    zone._content_lines = plain_lines

    return True


def get_available_renderers(use_wsl: bool = False) -> list[tuple[str, str, bool]]:
    """
    Get list of all renderers with availability status.

    Args:
        use_wsl: If True, check WSL availability

    Returns:
        List of (name, description, available) tuples
    """
    result = []
    for name, config in PAGER_RENDERERS.items():
        available = check_renderer_available(name, use_wsl)
        result.append((name, config["description"], available))
    return result


# =============================================================================
# FIFO HANDLER - Named pipe listener for external process integration
# =============================================================================

import stat
import socket as sock_module


class FIFOHandler:
    """
    Handles FIFO (named pipe) zones for receiving data from external processes.

    Features:
    - Creates named pipe at specified path
    - Background thread reads from FIFO
    - Displays incoming data in zone
    - Clean resource cleanup
    """

    def __init__(self, zone_manager: ZoneManager):
        self.zone_manager = zone_manager
        self._fifo_data: dict[str, dict] = {}  # zone_name -> {path, thread, stop_event}
        self._lock = threading.Lock()

    def create_fifo(self, zone: Zone) -> bool:
        """
        Create a FIFO listener for a zone.

        Returns True on success, False on error.
        """
        if zone.config.zone_type != ZoneType.FIFO:
            return False

        if not zone.config.path:
            zone.set_content(["[FIFO error: no path specified]"])
            return False

        # FIFO only available on Unix
        if os.name == "nt":
            zone.set_content(["[FIFO not available on Windows]"])
            return False

        key = zone.name.lower()
        fifo_path = zone.config.path

        # Clean up existing FIFO if any
        self.stop_fifo(zone.name)

        try:
            # Create FIFO if it doesn't exist
            if os.path.exists(fifo_path):
                if not stat.S_ISFIFO(os.stat(fifo_path).st_mode):
                    zone.set_content([f"[Path exists but is not a FIFO: {fifo_path}]"])
                    return False
            else:
                os.mkfifo(fifo_path, 0o666)

            # Start reader thread
            stop_event = threading.Event()
            reader_thread = threading.Thread(
                target=self._fifo_reader,
                args=(zone, fifo_path, stop_event),
                daemon=True,
                name=f"fifo-{key}",
            )

            with self._lock:
                self._fifo_data[key] = {
                    "path": fifo_path,
                    "thread": reader_thread,
                    "stop_event": stop_event,
                    "created": True,  # We created this FIFO
                }

            reader_thread.start()
            zone.set_content([f"[Listening on {fifo_path}]"])
            return True

        except Exception as e:
            zone.set_content([f"[FIFO error: {e}]"])
            return False

    def _fifo_reader(self, zone: Zone, path: str, stop_event: threading.Event) -> None:
        """Background thread that reads from FIFO."""
        content_h = zone.height - 2

        while not stop_event.is_set():
            try:
                # Open FIFO for reading (blocks until writer connects)
                # Use non-blocking with select for responsive shutdown
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)

                try:
                    while not stop_event.is_set():
                        # Use select with timeout
                        readable, _, _ = select.select([fd], [], [], 0.5)

                        if not readable:
                            continue

                        data = os.read(fd, 4096)
                        if not data:
                            # EOF - writer closed, reopen
                            break

                        # Process incoming data
                        text = data.decode("utf-8", errors="replace")
                        for line in text.split("\n"):
                            if line:  # Skip empty lines
                                zone.append_content(line.rstrip())

                        # Note: zone.append_content() already handles max_lines trimming

                finally:
                    os.close(fd)

            except OSError as e:
                if stop_event.is_set():
                    break
                # Brief sleep before retry
                stop_event.wait(1.0)
            except Exception as e:
                zone.append_content(f"[FIFO error: {e}]")
                break

    def stop_fifo(self, name: str) -> None:
        """Stop FIFO listener and clean up."""
        key = name.lower()

        with self._lock:
            data = self._fifo_data.pop(key, None)

        if data:
            # Signal thread to stop
            data["stop_event"].set()

            # Optionally remove FIFO file if we created it
            if data.get("created"):
                try:
                    os.unlink(data["path"])
                except OSError:
                    pass

    def stop_all(self) -> None:
        """Stop all FIFO listeners."""
        with self._lock:
            keys = list(self._fifo_data.keys())

        for key in keys:
            self.stop_fifo(key)

    def is_active(self, name: str) -> bool:
        """Check if FIFO is active for a zone."""
        key = name.lower()
        with self._lock:
            return key in self._fifo_data


# =============================================================================
# SOCKET HANDLER - TCP listener for network integration
# =============================================================================


class SocketHandler:
    """
    Handles Socket zones for receiving data over TCP.

    Features:
    - Listens on specified TCP port
    - Accepts connections and reads data
    - Displays incoming data in zone
    - Clean resource cleanup
    """

    def __init__(self, zone_manager: ZoneManager):
        self.zone_manager = zone_manager
        self._socket_data: dict[str, dict] = (
            {}
        )  # zone_name -> {socket, thread, stop_event}
        self._lock = threading.Lock()

    def create_socket(self, zone: Zone) -> bool:
        """
        Create a socket listener for a zone.

        Returns True on success, False on error.
        """
        if zone.config.zone_type != ZoneType.SOCKET:
            return False

        if not zone.config.port:
            zone.set_content(["[Socket error: no port specified]"])
            return False

        key = zone.name.lower()
        port = zone.config.port

        # Clean up existing socket if any
        self.stop_socket(zone.name)

        try:
            # Create and bind socket
            server = sock_module.socket(sock_module.AF_INET, sock_module.SOCK_STREAM)
            server.setsockopt(sock_module.SOL_SOCKET, sock_module.SO_REUSEADDR, 1)
            server.settimeout(1.0)  # For responsive shutdown
            server.bind(("0.0.0.0", port))
            server.listen(5)

            # Start listener thread
            stop_event = threading.Event()
            listener_thread = threading.Thread(
                target=self._socket_listener,
                args=(zone, server, stop_event),
                daemon=True,
                name=f"socket-{key}",
            )

            with self._lock:
                self._socket_data[key] = {
                    "socket": server,
                    "port": port,
                    "thread": listener_thread,
                    "stop_event": stop_event,
                }

            listener_thread.start()
            zone.set_content([f"[Listening on port {port}]"])
            return True

        except Exception as e:
            zone.set_content([f"[Socket error: {e}]"])
            return False

    def _socket_listener(
        self, zone: Zone, server: sock_module.socket, stop_event: threading.Event
    ) -> None:
        """Background thread that accepts connections and reads data."""
        content_h = zone.height - 2

        while not stop_event.is_set():
            try:
                # Accept connection (with timeout for responsive shutdown)
                try:
                    client, addr = server.accept()
                except sock_module.timeout:
                    continue

                client.settimeout(5.0)

                try:
                    # Read data from client
                    data = b""
                    while True:
                        chunk = client.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                        if len(data) > 65536:  # Limit to 64KB
                            break

                    if data:
                        text = data.decode("utf-8", errors="replace")
                        # Add source info
                        zone.append_content(f"[{addr[0]}:{addr[1]}]")
                        for line in text.split("\n"):
                            if line.strip():
                                zone.append_content(line.rstrip())

                        # Note: zone.append_content() already handles max_lines trimming

                finally:
                    client.close()

            except sock_module.timeout:
                continue
            except Exception as e:
                if not stop_event.is_set():
                    zone.append_content(f"[Socket error: {e}]")

    def stop_socket(self, name: str) -> None:
        """Stop socket listener and clean up."""
        key = name.lower()

        with self._lock:
            data = self._socket_data.pop(key, None)

        if data:
            # Signal thread to stop
            data["stop_event"].set()

            # Close socket
            try:
                data["socket"].close()
            except OSError:
                pass

    def stop_all(self) -> None:
        """Stop all socket listeners."""
        with self._lock:
            keys = list(self._socket_data.keys())

        for key in keys:
            self.stop_socket(key)

    def is_active(self, name: str) -> bool:
        """Check if socket is active for a zone."""
        key = name.lower()
        with self._lock:
            return key in self._socket_data
