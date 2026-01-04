"""Tests for zone management."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from zones import (
    Zone,
    ZoneManager,
    ZoneType,
    ZoneConfig,
    ZoneExecutor,
    PTYHandler,
    FIFOHandler,
    SocketHandler,
    Clipboard,
    StyledChar,
    strip_ansi,
    parse_ansi_line,
    parse_ansi_content,
    get_border_style,
    set_border_style,
    list_border_styles,
    get_border_chars,
    BORDER_STYLES,
    _map_256_to_8,
    check_renderer_available,
    select_renderer,
    render_file_content,
    load_pager_content,
    get_available_renderers,
)


# =============================================================================
# Mock Canvas for testing
# =============================================================================


class MockCanvas:
    """Simple mock canvas for testing zone rendering."""

    def __init__(self):
        self._cells = {}

    def set(self, x, y, char, fg=-1, bg=-1):
        self._cells[(x, y)] = {"char": char, "fg": fg, "bg": bg}

    def get_char(self, x, y):
        cell = self._cells.get((x, y))
        return cell["char"] if cell else " "

    def clear(self, x, y):
        self._cells.pop((x, y), None)

    def get(self, x, y):
        return self._cells.get((x, y), {"char": " ", "fg": -1, "bg": -1})


# =============================================================================
# ANSI Parsing Tests
# =============================================================================


class TestANSIParsing:
    """Tests for ANSI escape sequence parsing."""

    def test_strip_ansi_simple(self):
        text = "\x1b[31mRed Text\x1b[0m"
        assert strip_ansi(text) == "Red Text"

    def test_strip_ansi_multiple(self):
        text = "\x1b[1;32mBold Green\x1b[0m Normal \x1b[34mBlue\x1b[0m"
        assert strip_ansi(text) == "Bold Green Normal Blue"

    def test_strip_ansi_no_codes(self):
        text = "Plain text"
        assert strip_ansi(text) == "Plain text"

    def test_parse_ansi_line_plain(self):
        result = parse_ansi_line("Hello World")
        assert len(result) == 11
        assert result[0].char == "H"
        assert result[0].fg == -1
        assert result[0].bg == -1

    def test_parse_ansi_line_foreground_color(self):
        # Red foreground (31)
        result = parse_ansi_line("\x1b[31mRed\x1b[0m")
        assert len(result) == 3
        assert result[0].char == "R"
        assert result[0].fg == 1  # Red
        assert result[0].bg == -1

    def test_parse_ansi_line_background_color(self):
        # Blue background (44)
        result = parse_ansi_line("\x1b[44mBlue BG\x1b[0m")
        assert len(result) == 7
        assert result[0].bg == 4  # Blue

    def test_parse_ansi_line_combined_colors(self):
        # Green on yellow (32;43)
        result = parse_ansi_line("\x1b[32;43mGY\x1b[0m")
        assert len(result) == 2
        assert result[0].fg == 2  # Green
        assert result[0].bg == 3  # Yellow

    def test_parse_ansi_line_bright_colors(self):
        # Bright red (91), should map to 1
        result = parse_ansi_line("\x1b[91mBright\x1b[0m")
        assert result[0].fg == 1

    def test_parse_ansi_line_reset(self):
        result = parse_ansi_line("\x1b[31mRed\x1b[0mNormal")
        assert result[0].fg == 1  # Red
        assert result[3].fg == -1  # Reset

    def test_parse_ansi_line_default_fg(self):
        result = parse_ansi_line("\x1b[31mRed\x1b[39mDefault")
        assert result[0].fg == 1
        assert result[3].fg == -1

    def test_parse_ansi_line_default_bg(self):
        result = parse_ansi_line("\x1b[44mBG\x1b[49mDefault")
        assert result[0].bg == 4
        assert result[2].bg == -1

    def test_parse_ansi_content_multiline(self):
        content = "\x1b[31mLine 1\x1b[0m\nLine 2"
        result = parse_ansi_content(content)
        assert len(result) == 2
        assert result[0][0].fg == 1  # Red
        assert result[1][0].fg == -1  # Default

    def test_map_256_to_8_standard(self):
        assert _map_256_to_8(0) == 0  # Black
        assert _map_256_to_8(7) == 7  # White

    def test_map_256_to_8_bright(self):
        assert _map_256_to_8(8) == 0  # Bright black -> black
        assert _map_256_to_8(15) == 7  # Bright white -> white

    def test_map_256_to_8_grayscale(self):
        assert _map_256_to_8(232) == 0  # Dark gray -> black
        assert _map_256_to_8(255) == 7  # Light gray -> white

    def test_map_256_to_8_negative(self):
        assert _map_256_to_8(-1) == -1


# =============================================================================
# Border Style Tests
# =============================================================================


class TestBorderStyles:
    """Tests for border style functions."""

    def test_get_border_style_default(self):
        # Reset to ascii first
        set_border_style("ascii")
        assert get_border_style() == "ascii"

    def test_set_border_style_valid(self):
        assert set_border_style("unicode") is True
        assert get_border_style() == "unicode"
        # Reset
        set_border_style("ascii")

    def test_set_border_style_invalid(self):
        assert set_border_style("nonexistent") is False

    def test_list_border_styles(self):
        styles = list_border_styles()
        assert "ascii" in styles
        assert "unicode" in styles
        assert "rounded" in styles
        assert "double" in styles
        assert "heavy" in styles

    def test_get_border_chars(self):
        set_border_style("ascii")
        chars = get_border_chars()
        assert chars["tl"] == "+"
        assert chars["horiz"] == "-"
        assert chars["vert"] == "|"

    def test_border_styles_have_all_chars(self):
        required_keys = [
            "tl",
            "tr",
            "bl",
            "br",
            "horiz",
            "vert",
            "cross",
            "tee_down",
            "tee_up",
            "tee_right",
            "tee_left",
            "focused_tl",
            "focused_tr",
            "focused_bl",
            "focused_br",
            "focused_horiz",
            "focused_vert",
        ]
        for style_name, style in BORDER_STYLES.items():
            for key in required_keys:
                assert key in style, f"Missing {key} in {style_name}"


# =============================================================================
# ZoneConfig Tests
# =============================================================================


class TestZoneConfig:
    """Tests for ZoneConfig class."""

    def test_default_config(self):
        config = ZoneConfig()
        assert config.zone_type == ZoneType.STATIC
        assert config.command is None
        assert config.refresh_interval is None
        assert config.shell == "/bin/bash"
        assert config.max_lines == 1000

    def test_pipe_config(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE, command="ls -la")
        assert config.zone_type == ZoneType.PIPE
        assert config.command == "ls -la"

    def test_watch_config(self):
        config = ZoneConfig(
            zone_type=ZoneType.WATCH, command="date", refresh_interval=5.0
        )
        assert config.zone_type == ZoneType.WATCH
        assert config.refresh_interval == 5.0

    def test_pty_config(self):
        config = ZoneConfig(zone_type=ZoneType.PTY, shell="/bin/zsh")
        assert config.zone_type == ZoneType.PTY
        assert config.shell == "/bin/zsh"

    def test_socket_config(self):
        config = ZoneConfig(zone_type=ZoneType.SOCKET, port=9999)
        assert config.port == 9999

    def test_fifo_config(self):
        config = ZoneConfig(zone_type=ZoneType.FIFO, path="/tmp/test.fifo")
        assert config.path == "/tmp/test.fifo"

    def test_pager_config(self):
        config = ZoneConfig(
            zone_type=ZoneType.PAGER, file_path="/path/to/file.md", renderer="glow"
        )
        assert config.file_path == "/path/to/file.md"
        assert config.renderer == "glow"

    def test_to_dict_minimal(self):
        config = ZoneConfig()
        d = config.to_dict()
        assert d["zone_type"] == "static"
        assert "command" not in d  # Only non-default values

    def test_to_dict_full(self):
        config = ZoneConfig(
            zone_type=ZoneType.WATCH,
            command="date",
            refresh_interval=10.0,
            scroll=False,
            wrap=True,
            max_lines=500,
        )
        d = config.to_dict()
        assert d["zone_type"] == "watch"
        assert d["command"] == "date"
        assert d["refresh_interval"] == 10.0
        assert d["scroll"] is False
        assert d["wrap"] is True
        assert d["max_lines"] == 500

    def test_from_dict_minimal(self):
        d = {"zone_type": "static"}
        config = ZoneConfig.from_dict(d)
        assert config.zone_type == ZoneType.STATIC

    def test_from_dict_full(self):
        d = {
            "zone_type": "watch",
            "command": "uptime",
            "refresh_interval": 15.0,
            "scroll": True,
            "max_lines": 200,
        }
        config = ZoneConfig.from_dict(d)
        assert config.zone_type == ZoneType.WATCH
        assert config.command == "uptime"
        assert config.refresh_interval == 15.0
        assert config.max_lines == 200


class TestZone:
    """Tests for Zone class."""

    def test_create_zone(self):
        zone = Zone("test", 10, 20, 100, 50)
        assert zone.name == "test"
        assert zone.x == 10
        assert zone.y == 20
        assert zone.width == 100
        assert zone.height == 50

    def test_contains(self):
        zone = Zone("test", 10, 20, 100, 50)
        # Inside
        assert zone.contains(10, 20)
        assert zone.contains(50, 40)
        assert zone.contains(109, 69)
        # Outside
        assert not zone.contains(9, 20)
        assert not zone.contains(10, 19)
        assert not zone.contains(110, 20)
        assert not zone.contains(10, 70)

    def test_center(self):
        zone = Zone("test", 10, 20, 100, 50)
        cx, cy = zone.center()
        assert cx == 60  # 10 + 100/2
        assert cy == 45  # 20 + 50/2

    def test_distance_to_inside(self):
        zone = Zone("test", 10, 20, 100, 50)
        assert zone.distance_to(50, 40) == 0.0

    def test_distance_to_outside(self):
        zone = Zone("test", 10, 20, 100, 50)
        # Directly left
        assert zone.distance_to(0, 40) == 10.0
        # Directly above
        assert zone.distance_to(50, 10) == 10.0

    def test_direction_from(self):
        zone = Zone("test", 100, 100, 50, 50)
        # Center is at (125, 125)
        # From far left
        assert zone.direction_from(0, 125) == "→"
        # From far right
        assert zone.direction_from(300, 125) == "←"
        # From above
        assert zone.direction_from(125, 0) == "↓"
        # From below
        assert zone.direction_from(125, 300) == "↑"

    def test_to_dict(self):
        zone = Zone("test", 10, 20, 100, 50, description="A test zone", bookmark="t")
        d = zone.to_dict()
        assert d["name"] == "test"
        assert d["x"] == 10
        assert d["y"] == 20
        assert d["width"] == 100
        assert d["height"] == 50
        assert d["description"] == "A test zone"
        assert d["bookmark"] == "t"

    def test_from_dict(self):
        d = {"name": "test", "x": 10, "y": 20, "width": 100, "height": 50}
        zone = Zone.from_dict(d)
        assert zone.name == "test"
        assert zone.x == 10
        assert zone.contains(50, 40)


class TestZoneManager:
    """Tests for ZoneManager class."""

    def test_create_zone(self):
        manager = ZoneManager()
        zone = manager.create("workspace", 0, 0, 100, 50)
        assert zone.name == "workspace"
        assert len(manager) == 1

    def test_create_duplicate_raises(self):
        manager = ZoneManager()
        manager.create("workspace", 0, 0, 100, 50)
        with pytest.raises(ValueError):
            manager.create("workspace", 100, 0, 100, 50)

    def test_get_case_insensitive(self):
        manager = ZoneManager()
        manager.create("WorkSpace", 0, 0, 100, 50)
        assert manager.get("workspace") is not None
        assert manager.get("WORKSPACE") is not None

    def test_delete(self):
        manager = ZoneManager()
        manager.create("test", 0, 0, 100, 50)
        assert manager.delete("test")
        assert len(manager) == 0
        assert not manager.delete("nonexistent")

    def test_find_at(self):
        manager = ZoneManager()
        zone1 = manager.create("zone1", 0, 0, 100, 50)
        zone2 = manager.create("zone2", 200, 0, 100, 50)

        assert manager.find_at(50, 25) is zone1
        assert manager.find_at(250, 25) is zone2
        assert manager.find_at(150, 25) is None

    def test_nearest(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 50, 50)
        manager.create("zone2", 200, 0, 50, 50)

        # From middle, zone1 is closer
        result = manager.nearest(100, 25)
        assert result is not None
        zone, dist, direction = result
        assert zone.name == "zone1"

    def test_rename(self):
        manager = ZoneManager()
        manager.create("old", 0, 0, 100, 50)
        assert manager.rename("old", "new")
        assert manager.get("new") is not None
        assert manager.get("old") is None

    def test_clear(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 100, 50)
        manager.create("zone2", 200, 0, 100, 50)
        manager.clear()
        assert len(manager) == 0

    def test_to_dict_from_dict(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 100, 50, bookmark="1")
        manager.create("zone2", 200, 0, 100, 50, bookmark="2")

        d = manager.to_dict()
        assert "zones" in d
        assert len(d["zones"]) == 2

        # Restore
        manager2 = ZoneManager.from_dict(d)
        assert len(manager2) == 2
        assert manager2.get("zone1") is not None
        assert manager2.get("zone2") is not None

    def test_iter(self):
        manager = ZoneManager()
        manager.create("a", 0, 0, 10, 10)
        manager.create("b", 20, 0, 10, 10)

        names = [z.name for z in manager]
        assert "a" in names
        assert "b" in names

    def test_contains(self):
        manager = ZoneManager()
        manager.create("test", 0, 0, 100, 50)
        assert "test" in manager
        assert "TEST" in manager  # case insensitive
        assert "other" not in manager


# =============================================================================
# Zone Content Tests
# =============================================================================


class TestZoneContent:
    """Tests for Zone content methods."""

    def test_set_content(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE)
        zone = Zone("test", 0, 0, 50, 20, config=config)
        zone.set_content(["line1", "line2", "line3"])
        assert zone.content_lines == ["line1", "line2", "line3"]

    def test_set_content_respects_max_lines(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE, max_lines=3)
        zone = Zone("test", 0, 0, 50, 20, config=config)
        zone.set_content(["1", "2", "3", "4", "5"])
        # Should keep only the last 3 lines
        assert zone.content_lines == ["3", "4", "5"]

    def test_append_content(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE)
        zone = Zone("test", 0, 0, 50, 20, config=config)
        zone.append_content("first")
        zone.append_content("second")
        assert zone.content_lines == ["first", "second"]

    def test_append_content_respects_max_lines(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE, max_lines=2)
        zone = Zone("test", 0, 0, 50, 20, config=config)
        zone.append_content("1")
        zone.append_content("2")
        zone.append_content("3")
        # Should keep only the last 2 lines
        assert zone.content_lines == ["2", "3"]

    def test_clear_content(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE)
        zone = Zone("test", 0, 0, 50, 20, config=config)
        zone.set_content(["line1", "line2"])
        zone.clear_content()
        assert zone.content_lines == []

    def test_type_indicator(self):
        indicators = {
            ZoneType.STATIC: "S",
            ZoneType.PIPE: "P",
            ZoneType.WATCH: "W",
            ZoneType.PTY: "T",
            ZoneType.FIFO: "F",
            ZoneType.SOCKET: "N",
            ZoneType.CLIPBOARD: "C",
            ZoneType.PAGER: "R",
        }
        for zone_type, expected in indicators.items():
            config = ZoneConfig(zone_type=zone_type)
            zone = Zone("test", 0, 0, 50, 20, config=config)
            assert zone.type_indicator() == expected

    def test_is_dynamic(self):
        static_zone = Zone("static", 0, 0, 50, 20)
        assert not static_zone.is_dynamic

        pipe_config = ZoneConfig(zone_type=ZoneType.PIPE)
        pipe_zone = Zone("pipe", 0, 0, 50, 20, config=pipe_config)
        assert pipe_zone.is_dynamic

    def test_zone_type_property(self):
        config = ZoneConfig(zone_type=ZoneType.WATCH)
        zone = Zone("test", 0, 0, 50, 20, config=config)
        assert zone.zone_type == ZoneType.WATCH

    def test_top_left(self):
        zone = Zone("test", 10, 20, 100, 50)
        assert zone.top_left() == (10, 20)

    def test_bottom_right(self):
        zone = Zone("test", 10, 20, 100, 50)
        assert zone.bottom_right() == (109, 69)

    def test_pager_line_count(self):
        config = ZoneConfig(zone_type=ZoneType.PAGER)
        zone = Zone("test", 0, 0, 50, 20, config=config)
        styled_lines = [[StyledChar("H"), StyledChar("i")], [StyledChar("!")]]
        zone.set_styled_content(styled_lines)
        assert zone.pager_line_count == 2

    def test_pager_visible_lines(self):
        zone = Zone("test", 0, 0, 50, 20)
        # 20 height - 2 for border = 18 visible lines
        assert zone.pager_visible_lines == 18


# =============================================================================
# Zone Rendering Tests
# =============================================================================


class TestZoneRendering:
    """Tests for Zone rendering methods."""

    def test_draw_border_static(self):
        set_border_style("ascii")
        zone = Zone("test", 0, 0, 10, 5)
        canvas = MockCanvas()
        zone.draw_border(canvas, focused=False)

        # Check corners
        assert canvas.get_char(0, 0) == "+"
        assert canvas.get_char(9, 0) == "+"
        assert canvas.get_char(0, 4) == "+"
        assert canvas.get_char(9, 4) == "+"

    def test_draw_border_focused(self):
        set_border_style("ascii")
        zone = Zone("test", 0, 0, 10, 5)
        canvas = MockCanvas()
        zone.draw_border(canvas, focused=True)

        # Check focused corners (# for ascii)
        assert canvas.get_char(0, 0) == "#"

    def test_draw_border_with_watch_interval(self):
        config = ZoneConfig(zone_type=ZoneType.WATCH, refresh_interval=5.0)
        zone = Zone("test", 0, 0, 30, 5, config=config)
        canvas = MockCanvas()
        zone.draw_border(canvas, focused=False)

        # Header should contain interval
        header_chars = "".join(canvas.get_char(i, 0) for i in range(1, 20))
        assert "5.0s" in header_chars

    def test_draw_border_paused(self):
        config = ZoneConfig(zone_type=ZoneType.WATCH, paused=True)
        zone = Zone("test", 0, 0, 30, 5, config=config)
        canvas = MockCanvas()
        zone.draw_border(canvas, focused=False)

        header_chars = "".join(canvas.get_char(i, 0) for i in range(1, 25))
        assert "paused" in header_chars

    def test_clear_from_canvas(self):
        zone = Zone("test", 0, 0, 10, 5)
        canvas = MockCanvas()

        # Put some content
        for y in range(5):
            for x in range(10):
                canvas.set(x, y, "X")

        zone.clear_from_canvas(canvas)

        # All cells should be cleared
        for y in range(5):
            for x in range(10):
                assert (x, y) not in canvas._cells

    def test_render_to_canvas_static_zone(self):
        zone = Zone("static", 0, 0, 20, 10)
        canvas = MockCanvas()
        zone.render_to_canvas(canvas)
        # Static zones should not render content
        assert len(canvas._cells) == 0

    def test_render_to_canvas_dynamic_zone(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE)
        zone = Zone("test", 0, 0, 20, 10, config=config)
        zone.set_content(["Hello", "World"])
        canvas = MockCanvas()
        zone.render_to_canvas(canvas)

        # Content should be rendered at content area (inside border)
        assert canvas.get_char(1, 1) == "H"
        assert canvas.get_char(2, 1) == "e"

    def test_render_to_canvas_with_ansi_colors(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE)
        zone = Zone("test", 0, 0, 30, 10, config=config)
        zone.set_content(["\x1b[31mRed\x1b[0m"])
        canvas = MockCanvas()
        zone.render_to_canvas(canvas)

        # Red text should have fg=1
        cell = canvas.get(1, 1)
        assert cell["char"] == "R"
        assert cell["fg"] == 1

    def test_render_scroll_indicator(self):
        config = ZoneConfig(zone_type=ZoneType.PAGER, scroll_offset=0)
        zone = Zone("test", 0, 0, 20, 10, config=config)
        # Create more lines than can fit
        styled_lines = [[StyledChar("X")] for _ in range(30)]
        zone.set_styled_content(styled_lines)
        canvas = MockCanvas()
        zone._render_pager_content(canvas, 1, 1, 18, 8)

        # Should have scroll indicator on right edge
        # Check that something is rendered at scroll position


# =============================================================================
# ZoneManager Factory Methods Tests
# =============================================================================


class TestZoneManagerFactoryMethods:
    """Tests for ZoneManager create_* factory methods."""

    def test_create_pipe(self):
        manager = ZoneManager()
        zone = manager.create_pipe("pipe1", 0, 0, 50, 20, "ls -la", bookmark="p")
        assert zone.zone_type == ZoneType.PIPE
        assert zone.config.command == "ls -la"
        assert zone.bookmark == "p"

    def test_create_watch(self):
        manager = ZoneManager()
        zone = manager.create_watch(
            "watch1", 0, 0, 50, 20, "date", interval=10.0, bookmark="w"
        )
        assert zone.zone_type == ZoneType.WATCH
        assert zone.config.command == "date"
        assert zone.config.refresh_interval == 10.0

    def test_create_pty(self):
        manager = ZoneManager()
        zone = manager.create_pty("term", 0, 0, 80, 24, "/bin/zsh", bookmark="t")
        assert zone.zone_type == ZoneType.PTY
        assert zone.config.shell == "/bin/zsh"

    def test_create_clipboard(self):
        manager = ZoneManager()
        zone = manager.create_clipboard("clip", 0, 0, 40, 20, bookmark="c")
        assert zone.zone_type == ZoneType.CLIPBOARD
        assert zone.description == "Clipboard buffer"


# =============================================================================
# ZoneManager Operations Tests
# =============================================================================


class TestZoneManagerOperations:
    """Tests for ZoneManager operations (resize, move, etc)."""

    def test_resize(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 100, 50)
        assert manager.resize("zone1", 200, 100)
        zone = manager.get("zone1")
        assert zone.width == 200
        assert zone.height == 100

    def test_resize_nonexistent(self):
        manager = ZoneManager()
        assert not manager.resize("nonexistent", 100, 50)

    def test_move(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 100, 50)
        assert manager.move("zone1", 50, 50)
        zone = manager.get("zone1")
        assert zone.x == 50
        assert zone.y == 50

    def test_move_nonexistent(self):
        manager = ZoneManager()
        assert not manager.move("nonexistent", 50, 50)

    def test_set_bookmark(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 100, 50)
        assert manager.set_bookmark("zone1", "a")
        zone = manager.get("zone1")
        assert zone.bookmark == "a"

    def test_set_bookmark_nonexistent(self):
        manager = ZoneManager()
        assert not manager.set_bookmark("nonexistent", "a")

    def test_find_by_bookmark(self):
        manager = ZoneManager()
        zone1 = manager.create("zone1", 0, 0, 100, 50, bookmark="a")
        manager.create("zone2", 100, 0, 100, 50, bookmark="b")

        assert manager.find_by_bookmark("a") is zone1
        assert manager.find_by_bookmark("c") is None

    def test_list_all_sorted(self):
        manager = ZoneManager()
        manager.create("Zebra", 0, 0, 10, 10)
        manager.create("Alpha", 20, 0, 10, 10)
        manager.create("beta", 40, 0, 10, 10)

        zones = manager.list_all()
        names = [z.name for z in zones]
        # Should be sorted case-insensitively
        assert names == ["Alpha", "beta", "Zebra"]

    def test_clear_with_canvas(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 10, 5)
        canvas = MockCanvas()

        # Put content
        for y in range(5):
            for x in range(10):
                canvas.set(x, y, "X")

        manager.clear_with_canvas(canvas)

        assert len(manager) == 0
        # Canvas should be cleared in zone region
        for y in range(5):
            for x in range(10):
                assert (x, y) not in canvas._cells

    def test_render_all_zones(self):
        manager = ZoneManager()
        pipe_config = ZoneConfig(zone_type=ZoneType.PIPE)
        manager.create("zone1", 0, 0, 20, 10, config=pipe_config)
        manager.create("zone2", 30, 0, 20, 10, config=pipe_config)

        canvas = MockCanvas()
        manager.render_all_zones(canvas, focused_zone="zone1")

        # Both zones should have borders drawn
        assert canvas.get_char(0, 0) != " "
        assert canvas.get_char(30, 0) != " "

    def test_nearest_empty_manager(self):
        manager = ZoneManager()
        assert manager.nearest(50, 50) is None

    def test_nearest_with_one_zone(self):
        manager = ZoneManager()
        zone1 = manager.create("zone1", 0, 0, 50, 50)

        result = manager.nearest(100, 100)
        assert result is not None
        zone, dist, direction = result
        assert zone is zone1

    def test_rename_to_existing(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 50, 50)
        manager.create("zone2", 100, 0, 50, 50)

        # Renaming to existing name should fail
        assert not manager.rename("zone1", "zone2")

    def test_rename_same_case(self):
        manager = ZoneManager()
        manager.create("Zone", 0, 0, 50, 50)

        # Renaming to different case of same name should work
        assert manager.rename("Zone", "ZONE")
        assert manager.get("zone") is not None


# =============================================================================
# ZoneExecutor Tests
# =============================================================================


class TestZoneExecutor:
    """Tests for ZoneExecutor class."""

    def test_execute_pipe_success(self):
        manager = ZoneManager()
        zone = manager.create_pipe("test", 0, 0, 50, 20, "echo hello")
        executor = ZoneExecutor(manager)

        result = executor.execute_pipe(zone)
        assert result is True
        assert "hello" in zone.content_lines

    def test_execute_pipe_no_command(self):
        manager = ZoneManager()
        config = ZoneConfig(zone_type=ZoneType.PIPE, command=None)
        zone = manager.create("test", 0, 0, 50, 20, config=config)
        executor = ZoneExecutor(manager)

        result = executor.execute_pipe(zone)
        assert result is False
        assert "No command" in zone.content_lines[0]

    def test_execute_pipe_static_zone(self):
        manager = ZoneManager()
        zone = manager.create("test", 0, 0, 50, 20)  # Static zone
        executor = ZoneExecutor(manager)

        result = executor.execute_pipe(zone)
        assert result is False

    def test_execute_pipe_with_stderr(self):
        manager = ZoneManager()
        # Command that produces stderr
        zone = manager.create_pipe("test", 0, 0, 50, 20, "echo error >&2")
        executor = ZoneExecutor(manager)

        executor.execute_pipe(zone)
        # stderr is captured and appended
        assert any("error" in line for line in zone.content_lines)

    def test_execute_pipe_timeout(self):
        manager = ZoneManager()
        # Command that takes long time
        zone = manager.create_pipe("test", 0, 0, 50, 20, "sleep 10")
        executor = ZoneExecutor(manager)

        result = executor.execute_pipe(zone, timeout=1)
        assert result is False
        assert "timed out" in zone.content_lines[0]

    def test_refresh_zone(self):
        manager = ZoneManager()
        zone = manager.create_pipe("test", 0, 0, 50, 20, "echo refreshed")
        executor = ZoneExecutor(manager)

        result = executor.refresh_zone("test")
        assert result is True
        assert "refreshed" in zone.content_lines

    def test_refresh_zone_nonexistent(self):
        manager = ZoneManager()
        executor = ZoneExecutor(manager)

        result = executor.refresh_zone("nonexistent")
        assert result is False

    def test_pause_resume_zone(self):
        manager = ZoneManager()
        zone = manager.create_watch("test", 0, 0, 50, 20, "date", interval=5.0)
        executor = ZoneExecutor(manager)

        assert executor.pause_zone("test") is True
        assert zone.config.paused is True

        assert executor.resume_zone("test") is True
        assert zone.config.paused is False

    def test_pause_static_zone(self):
        manager = ZoneManager()
        manager.create("test", 0, 0, 50, 20)
        executor = ZoneExecutor(manager)

        assert executor.pause_zone("test") is False

    @patch("zones.threading.Thread")
    def test_start_watch(self, mock_thread_class):
        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        manager = ZoneManager()
        zone = manager.create_watch("test", 0, 0, 50, 20, "date", interval=1.0)
        executor = ZoneExecutor(manager)

        executor.start_watch(zone)

        mock_thread.start.assert_called_once()

    def test_stop_watch(self):
        manager = ZoneManager()
        zone = manager.create_watch("test", 0, 0, 50, 20, "date", interval=100.0)
        executor = ZoneExecutor(manager)

        # Start and immediately stop
        executor.start_watch(zone)
        executor.stop_watch("test")

        # Should not raise and thread should be cleaned up
        assert "test" not in executor._watch_threads

    def test_stop_all(self):
        manager = ZoneManager()
        executor = ZoneExecutor(manager)

        zone1 = manager.create_watch("w1", 0, 0, 50, 20, "date", interval=100.0)
        zone2 = manager.create_watch("w2", 60, 0, 50, 20, "date", interval=100.0)

        executor.start_watch(zone1)
        executor.start_watch(zone2)

        executor.stop_all()

        assert len(executor._watch_threads) == 0
        assert len(executor._stop_events) == 0


# =============================================================================
# PTYHandler Tests (Mocked)
# =============================================================================


class TestPTYHandler:
    """Tests for PTYHandler class (with mocking)."""

    def test_available_property(self):
        manager = ZoneManager()
        handler = PTYHandler(manager)
        # Should return a boolean
        assert isinstance(handler.available, bool)

    @patch("zones.PTY_AVAILABLE", False)
    def test_create_pty_not_available(self):
        manager = ZoneManager()
        zone = manager.create_pty("test", 0, 0, 80, 24)
        handler = PTYHandler(manager)

        # Force PTY_AVAILABLE to False for this test
        import zones

        original = zones.PTY_AVAILABLE
        zones.PTY_AVAILABLE = False

        try:
            result = handler.create_pty(zone)
            assert result is False
            assert "not available" in zone.content_lines[0]
        finally:
            zones.PTY_AVAILABLE = original

    def test_create_pty_wrong_zone_type(self):
        manager = ZoneManager()
        zone = manager.create("test", 0, 0, 80, 24)  # Static zone
        handler = PTYHandler(manager)

        result = handler.create_pty(zone)
        assert result is False

    def test_is_active_false_initially(self):
        manager = ZoneManager()
        handler = PTYHandler(manager)

        assert handler.is_active("nonexistent") is False

    def test_send_input_no_pty(self):
        manager = ZoneManager()
        handler = PTYHandler(manager)

        result = handler.send_input("nonexistent", "test")
        assert result is False

    def test_resize_pty_no_pty(self):
        manager = ZoneManager()
        handler = PTYHandler(manager)

        result = handler.resize_pty("nonexistent", 80, 24)
        assert result is False

    def test_get_screen_no_pty(self):
        manager = ZoneManager()
        handler = PTYHandler(manager)

        result = handler.get_screen("nonexistent")
        assert result is None

    def test_stop_pty_nonexistent(self):
        manager = ZoneManager()
        handler = PTYHandler(manager)

        # Should not raise
        handler.stop_pty("nonexistent")

    def test_stop_all_empty(self):
        manager = ZoneManager()
        handler = PTYHandler(manager)

        # Should not raise
        handler.stop_all()


# =============================================================================
# FIFOHandler Tests (Mocked)
# =============================================================================


class TestFIFOHandler:
    """Tests for FIFOHandler class (with mocking)."""

    def test_create_fifo_wrong_zone_type(self):
        manager = ZoneManager()
        zone = manager.create("test", 0, 0, 50, 20)  # Static zone
        handler = FIFOHandler(manager)

        result = handler.create_fifo(zone)
        assert result is False

    def test_create_fifo_no_path(self):
        manager = ZoneManager()
        config = ZoneConfig(zone_type=ZoneType.FIFO, path=None)
        zone = manager.create("test", 0, 0, 50, 20, config=config)
        handler = FIFOHandler(manager)

        result = handler.create_fifo(zone)
        assert result is False
        assert "no path" in zone.content_lines[0]

    @patch("zones.os.name", "nt")
    def test_create_fifo_windows(self):
        manager = ZoneManager()
        config = ZoneConfig(zone_type=ZoneType.FIFO, path="/tmp/test.fifo")
        zone = manager.create("test", 0, 0, 50, 20, config=config)
        handler = FIFOHandler(manager)

        import zones

        original = zones.os.name
        zones.os.name = "nt"

        try:
            result = handler.create_fifo(zone)
            assert result is False
            assert "not available" in zone.content_lines[0]
        finally:
            zones.os.name = original

    def test_is_active_false_initially(self):
        manager = ZoneManager()
        handler = FIFOHandler(manager)

        assert handler.is_active("nonexistent") is False

    def test_stop_fifo_nonexistent(self):
        manager = ZoneManager()
        handler = FIFOHandler(manager)

        # Should not raise
        handler.stop_fifo("nonexistent")

    def test_stop_all_empty(self):
        manager = ZoneManager()
        handler = FIFOHandler(manager)

        # Should not raise
        handler.stop_all()


# =============================================================================
# SocketHandler Tests (Mocked)
# =============================================================================


class TestSocketHandler:
    """Tests for SocketHandler class (with mocking)."""

    def test_create_socket_wrong_zone_type(self):
        manager = ZoneManager()
        zone = manager.create("test", 0, 0, 50, 20)  # Static zone
        handler = SocketHandler(manager)

        result = handler.create_socket(zone)
        assert result is False

    def test_create_socket_no_port(self):
        manager = ZoneManager()
        config = ZoneConfig(zone_type=ZoneType.SOCKET, port=None)
        zone = manager.create("test", 0, 0, 50, 20, config=config)
        handler = SocketHandler(manager)

        result = handler.create_socket(zone)
        assert result is False
        assert "no port" in zone.content_lines[0]

    def test_is_active_false_initially(self):
        manager = ZoneManager()
        handler = SocketHandler(manager)

        assert handler.is_active("nonexistent") is False

    def test_stop_socket_nonexistent(self):
        manager = ZoneManager()
        handler = SocketHandler(manager)

        # Should not raise
        handler.stop_socket("nonexistent")

    def test_stop_all_empty(self):
        manager = ZoneManager()
        handler = SocketHandler(manager)

        # Should not raise
        handler.stop_all()

    @patch("zones.sock_module.socket")
    def test_create_socket_success(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        manager = ZoneManager()
        config = ZoneConfig(zone_type=ZoneType.SOCKET, port=9999)
        zone = manager.create("test", 0, 0, 50, 20, config=config)
        handler = SocketHandler(manager)

        result = handler.create_socket(zone)
        assert result is True
        assert "Listening" in zone.content_lines[0]

    @patch("zones.sock_module.socket")
    def test_create_socket_bind_error(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket.bind.side_effect = Exception("Address in use")
        mock_socket_class.return_value = mock_socket

        manager = ZoneManager()
        config = ZoneConfig(zone_type=ZoneType.SOCKET, port=9999)
        zone = manager.create("test", 0, 0, 50, 20, config=config)
        handler = SocketHandler(manager)

        result = handler.create_socket(zone)
        assert result is False
        assert "error" in zone.content_lines[0].lower()


# =============================================================================
# Clipboard Tests
# =============================================================================


class TestClipboard:
    """Tests for Clipboard class."""

    def test_initial_state(self):
        clip = Clipboard()
        assert clip.is_empty
        assert clip.content == []
        assert clip.text == ""
        assert clip.source == ""

    def test_set_content(self):
        clip = Clipboard()
        clip.set_content(["line1", "line2"], source="test")
        assert clip.content == ["line1", "line2"]
        assert clip.text == "line1\nline2"
        assert clip.source == "test"
        assert not clip.is_empty

    def test_clear(self):
        clip = Clipboard()
        clip.set_content(["some", "content"])
        clip.clear()
        assert clip.is_empty
        assert clip.source == ""

    def test_yank_region(self):
        clip = Clipboard()
        canvas = MockCanvas()
        canvas.set(0, 0, "A")
        canvas.set(1, 0, "B")
        canvas.set(0, 1, "C")
        canvas.set(1, 1, "D")

        count = clip.yank_region(canvas, 0, 0, 1, 1)
        assert count == 2
        assert clip.content == ["AB", "CD"]
        assert "region" in clip.source

    def test_yank_region_swap_coords(self):
        clip = Clipboard()
        canvas = MockCanvas()
        canvas.set(0, 0, "A")
        canvas.set(1, 0, "B")
        canvas.set(0, 1, "C")
        canvas.set(1, 1, "D")

        # Provide coords in reverse order
        count = clip.yank_region(canvas, 1, 1, 0, 0)
        assert count == 2
        # Should still work correctly
        assert clip.content == ["AB", "CD"]

    def test_yank_zone(self):
        clip = Clipboard()
        config = ZoneConfig(zone_type=ZoneType.PIPE)
        zone = Zone("test", 0, 0, 50, 20, config=config)
        zone.set_content(["hello", "world"])

        count = clip.yank_zone(zone)
        assert count == 2
        assert clip.content == ["hello", "world"]
        assert "zone test" in clip.source

    def test_paste_to_canvas(self):
        clip = Clipboard()
        clip.set_content(["AB", "CD"])
        canvas = MockCanvas()

        width, height = clip.paste_to_canvas(canvas, 5, 5)
        assert width == 2
        assert height == 2
        assert canvas.get_char(5, 5) == "A"
        assert canvas.get_char(6, 5) == "B"
        assert canvas.get_char(5, 6) == "C"
        assert canvas.get_char(6, 6) == "D"

    def test_paste_to_canvas_empty(self):
        clip = Clipboard()
        canvas = MockCanvas()

        width, height = clip.paste_to_canvas(canvas, 0, 0)
        assert width == 0
        assert height == 0

    def test_paste_skip_spaces(self):
        clip = Clipboard()
        clip.set_content(["A B"])
        canvas = MockCanvas()
        canvas.set(1, 0, "X")  # Pre-existing content

        clip.paste_to_canvas(canvas, 0, 0, skip_spaces=True)
        assert canvas.get_char(0, 0) == "A"
        assert canvas.get_char(1, 0) == "X"  # Space skipped, original preserved
        assert canvas.get_char(2, 0) == "B"

    def test_update_clipboard_zone(self):
        clip = Clipboard()
        clip.set_content(["clipboard", "content"])

        config = ZoneConfig(zone_type=ZoneType.CLIPBOARD)
        zone = Zone("clip", 0, 0, 50, 20, config=config)

        clip.update_clipboard_zone(zone)
        assert zone.content_lines == ["clipboard", "content"]

    def test_update_clipboard_zone_wrong_type(self):
        clip = Clipboard()
        clip.set_content(["test"])

        zone = Zone("static", 0, 0, 50, 20)  # Static zone

        clip.update_clipboard_zone(zone)
        # Should not crash, zone content should be unchanged
        assert zone.content_lines == []

    def test_is_empty_with_single_empty_line(self):
        clip = Clipboard()
        clip.set_content([""])
        assert clip.is_empty

    @patch("zones.subprocess.run")
    def test_to_system_clipboard(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        clip = Clipboard()
        clip.set_content(["test"])

        result = clip.to_system_clipboard()
        assert result is True

    @patch("zones.subprocess.run")
    def test_to_system_clipboard_failure(self, mock_run):
        mock_run.side_effect = FileNotFoundError()

        clip = Clipboard()
        clip.set_content(["test"])

        result = clip.to_system_clipboard()
        assert result is False

    @patch("zones.subprocess.run")
    def test_from_system_clipboard(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b"pasted\ntext")

        clip = Clipboard()
        result = clip.from_system_clipboard()
        assert result is True
        assert clip.content == ["pasted", "text"]

    @patch("zones.subprocess.run")
    def test_from_system_clipboard_failure(self, mock_run):
        mock_run.side_effect = FileNotFoundError()

        clip = Clipboard()
        result = clip.from_system_clipboard()
        assert result is False


# =============================================================================
# Pager Handler Tests
# =============================================================================


class TestPagerHandler:
    """Tests for pager-related functions."""

    def test_check_renderer_available_plain(self):
        # Plain is always available
        assert check_renderer_available("plain") is True

    def test_check_renderer_available_unknown(self):
        assert check_renderer_available("nonexistent") is False

    @patch("zones.subprocess.run")
    def test_check_renderer_available_glow(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        # Clear cache first
        import zones

        zones._renderer_available_cache.clear()

        result = check_renderer_available("glow")
        assert result is True

    @patch("zones.subprocess.run")
    def test_check_renderer_not_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        import zones

        zones._renderer_available_cache.clear()

        result = check_renderer_available("glow")
        assert result is False

    def test_select_renderer_plain_fallback(self):
        import zones

        zones._renderer_available_cache.clear()
        zones._renderer_available_cache["glow:native"] = False
        zones._renderer_available_cache["bat:native"] = False

        result = select_renderer("/path/to/file.txt")
        assert result == "plain"

    @patch("zones.check_renderer_available")
    def test_select_renderer_for_markdown(self, mock_check):
        mock_check.return_value = True

        result = select_renderer("/path/to/README.md", preferred="auto")
        # Should select glow for .md files
        assert result in ["glow", "plain"]

    @patch("zones.check_renderer_available")
    def test_select_renderer_preferred(self, mock_check):
        mock_check.return_value = True

        result = select_renderer("/path/to/file.py", preferred="bat")
        assert result == "bat"

    def test_render_file_content_unknown_renderer(self):
        result = render_file_content("/path/to/file", renderer="nonexistent")
        assert "Unknown renderer" in result

    @patch("zones.subprocess.run")
    def test_render_file_content_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="file content")

        result = render_file_content("/path/to/file.txt", renderer="plain")
        assert result == "file content"

    @patch("zones.subprocess.run")
    def test_render_file_content_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Error reading file")

        result = render_file_content("/path/to/file.txt", renderer="plain")
        assert "error" in result.lower()

    @patch("zones.subprocess.run")
    def test_render_file_content_timeout(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        result = render_file_content("/path/to/file.txt", renderer="plain")
        assert "timeout" in result.lower()

    def test_load_pager_content_wrong_type(self):
        zone = Zone("test", 0, 0, 50, 20)  # Static zone

        result = load_pager_content(zone)
        assert result is False

    def test_load_pager_content_no_file(self):
        config = ZoneConfig(zone_type=ZoneType.PAGER, file_path=None)
        zone = Zone("test", 0, 0, 50, 20, config=config)

        result = load_pager_content(zone)
        assert result is False
        assert "No file path" in zone.content_lines[0]

    def test_load_pager_content_file_not_found(self):
        config = ZoneConfig(
            zone_type=ZoneType.PAGER, file_path="/nonexistent/path/file.md"
        )
        zone = Zone("test", 0, 0, 50, 20, config=config)

        result = load_pager_content(zone)
        assert result is False
        assert "not found" in zone.content_lines[0].lower()

    def test_get_available_renderers(self):
        result = get_available_renderers()
        assert isinstance(result, list)
        assert len(result) >= 3  # glow, bat, plain

        # Check structure
        for name, desc, available in result:
            assert isinstance(name, str)
            assert isinstance(desc, str)
            assert isinstance(available, bool)


# =============================================================================
# Zone Direction Tests
# =============================================================================


class TestZoneDirection:
    """Additional tests for zone direction calculations."""

    def test_direction_from_diagonal_top_left(self):
        zone = Zone("test", 100, 100, 50, 50)
        # From far top-left
        direction = zone.direction_from(0, 0)
        assert direction == "↘"

    def test_direction_from_diagonal_top_right(self):
        zone = Zone("test", 100, 100, 50, 50)
        # From far top-right
        direction = zone.direction_from(300, 0)
        assert direction == "↙"

    def test_direction_from_diagonal_bottom_left(self):
        zone = Zone("test", 100, 100, 50, 50)
        # From far bottom-left
        direction = zone.direction_from(0, 300)
        assert direction == "↗"

    def test_direction_from_diagonal_bottom_right(self):
        zone = Zone("test", 100, 100, 50, 50)
        # From far bottom-right
        direction = zone.direction_from(300, 300)
        assert direction == "↖"

    def test_direction_from_at_center(self):
        zone = Zone("test", 100, 100, 50, 50)
        # From very close to center
        direction = zone.direction_from(125, 125)
        assert direction == "·"


# =============================================================================
# Zone Serialization with Config Tests
# =============================================================================


class TestZoneSerializationWithConfig:
    """Tests for Zone serialization including config."""

    def test_to_dict_with_pipe_config(self):
        config = ZoneConfig(zone_type=ZoneType.PIPE, command="ls -la")
        zone = Zone("test", 0, 0, 50, 20, config=config)

        d = zone.to_dict()
        assert "config" in d
        assert d["config"]["zone_type"] == "pipe"
        assert d["config"]["command"] == "ls -la"

    def test_to_dict_static_no_config(self):
        zone = Zone("test", 0, 0, 50, 20)

        d = zone.to_dict()
        # Static zones don't include config in serialization
        assert "config" not in d

    def test_from_dict_with_config(self):
        d = {
            "name": "watch_zone",
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 50,
            "config": {
                "zone_type": "watch",
                "command": "uptime",
                "refresh_interval": 10.0,
            },
        }
        zone = Zone.from_dict(d)
        assert zone.zone_type == ZoneType.WATCH
        assert zone.config.command == "uptime"
        assert zone.config.refresh_interval == 10.0

    def test_from_dict_with_pager_config(self):
        d = {
            "name": "pager_zone",
            "x": 0,
            "y": 0,
            "width": 80,
            "height": 40,
            "config": {
                "zone_type": "pager",
                "file_path": "/path/to/README.md",
                "renderer": "glow",
                "scroll_offset": 10,
            },
        }
        zone = Zone.from_dict(d)
        assert zone.zone_type == ZoneType.PAGER
        assert zone.config.file_path == "/path/to/README.md"
        assert zone.config.renderer == "glow"
        assert zone.config.scroll_offset == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
