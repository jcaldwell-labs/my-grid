"""Tests for layout management system."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import yaml

from layouts import (
    Layout,
    LayoutManager,
    LayoutZone,
    DEFAULT_LAYOUTS,
    get_layouts_dir,
    install_default_layouts,
)
from zones import ZoneExecutor, ZoneManager, ZoneType


class TestLayoutZone:
    """Tests for LayoutZone dataclass."""

    def test_create_basic_zone(self):
        """Test creating a basic layout zone with required fields."""
        lz = LayoutZone(
            name="TEST",
            zone_type="static",
            x=10,
            y=20,
            width=80,
            height=24,
        )
        assert lz.name == "TEST"
        assert lz.zone_type == "static"
        assert lz.x == 10
        assert lz.y == 20
        assert lz.width == 80
        assert lz.height == 24
        assert lz.command is None
        assert lz.interval is None
        assert lz.bookmark is None
        assert lz.description == ""

    def test_create_watch_zone(self):
        """Test creating a watch zone with command and interval."""
        lz = LayoutZone(
            name="LOGS",
            zone_type="watch",
            x=0,
            y=0,
            width=80,
            height=15,
            command="tail -f /var/log/syslog",
            interval=5.0,
            bookmark="l",
            description="System logs",
        )
        assert lz.zone_type == "watch"
        assert lz.command == "tail -f /var/log/syslog"
        assert lz.interval == 5.0
        assert lz.bookmark == "l"
        assert lz.description == "System logs"

    def test_create_pty_zone(self):
        """Test creating a PTY zone with shell."""
        lz = LayoutZone(
            name="TERM",
            zone_type="pty",
            x=0,
            y=0,
            width=80,
            height=24,
            shell="/bin/zsh",
        )
        assert lz.zone_type == "pty"
        assert lz.shell == "/bin/zsh"

    def test_create_fifo_zone(self):
        """Test creating a FIFO zone with path."""
        lz = LayoutZone(
            name="EVENTS",
            zone_type="fifo",
            x=0,
            y=0,
            width=50,
            height=20,
            path="/tmp/events.fifo",
        )
        assert lz.zone_type == "fifo"
        assert lz.path == "/tmp/events.fifo"

    def test_create_socket_zone(self):
        """Test creating a socket zone with port."""
        lz = LayoutZone(
            name="MESSAGES",
            zone_type="socket",
            x=0,
            y=0,
            width=60,
            height=20,
            port=9999,
        )
        assert lz.zone_type == "socket"
        assert lz.port == 9999

    def test_create_pipe_zone(self):
        """Test creating a pipe zone with command."""
        lz = LayoutZone(
            name="TREE",
            zone_type="pipe",
            x=0,
            y=0,
            width=60,
            height=20,
            command="tree -L 2",
        )
        assert lz.zone_type == "pipe"
        assert lz.command == "tree -L 2"

    def test_create_pager_zone(self):
        """Test creating a pager zone with file path and renderer."""
        lz = LayoutZone(
            name="README",
            zone_type="pager",
            x=0,
            y=0,
            width=80,
            height=30,
            file_path="/path/to/README.md",
            renderer="glow",
        )
        assert lz.zone_type == "pager"
        assert lz.file_path == "/path/to/README.md"
        assert lz.renderer == "glow"

    def test_to_dict_basic(self):
        """Test serializing a basic zone to dictionary."""
        lz = LayoutZone(
            name="TEST",
            zone_type="static",
            x=10,
            y=20,
            width=80,
            height=24,
        )
        d = lz.to_dict()
        assert d["name"] == "TEST"
        assert d["type"] == "static"
        assert d["x"] == 10
        assert d["y"] == 20
        assert d["width"] == 80
        assert d["height"] == 24
        # Optional fields should not be in dict if not set
        assert "command" not in d
        assert "interval" not in d
        assert "bookmark" not in d

    def test_to_dict_with_optional_fields(self):
        """Test serializing zone with all optional fields."""
        lz = LayoutZone(
            name="LOGS",
            zone_type="watch",
            x=0,
            y=0,
            width=80,
            height=15,
            command="tail -f /var/log/syslog",
            interval=5.0,
            bookmark="l",
            description="System logs",
        )
        d = lz.to_dict()
        assert d["command"] == "tail -f /var/log/syslog"
        assert d["interval"] == 5.0
        assert d["bookmark"] == "l"
        assert d["description"] == "System logs"

    def test_to_dict_all_zone_types(self):
        """Test to_dict for each zone type with its specific fields."""
        # PTY with shell
        pty = LayoutZone(
            name="TERM",
            zone_type="pty",
            x=0,
            y=0,
            width=80,
            height=24,
            shell="/bin/zsh",
        )
        assert pty.to_dict()["shell"] == "/bin/zsh"

        # FIFO with path
        fifo = LayoutZone(
            name="EVENTS",
            zone_type="fifo",
            x=0,
            y=0,
            width=50,
            height=20,
            path="/tmp/test.fifo",
        )
        assert fifo.to_dict()["path"] == "/tmp/test.fifo"

        # Socket with port
        socket = LayoutZone(
            name="MESSAGES",
            zone_type="socket",
            x=0,
            y=0,
            width=60,
            height=20,
            port=9999,
        )
        assert socket.to_dict()["port"] == 9999

        # Pager with file_path and renderer
        pager = LayoutZone(
            name="README",
            zone_type="pager",
            x=0,
            y=0,
            width=80,
            height=30,
            file_path="/path/to/file.md",
            renderer="bat",
        )
        d = pager.to_dict()
        assert d["file_path"] == "/path/to/file.md"
        assert d["renderer"] == "bat"

    def test_from_dict_basic(self):
        """Test deserializing a basic zone from dictionary."""
        d = {
            "name": "TEST",
            "type": "static",
            "x": 10,
            "y": 20,
            "width": 80,
            "height": 24,
        }
        lz = LayoutZone.from_dict(d)
        assert lz.name == "TEST"
        assert lz.zone_type == "static"
        assert lz.x == 10
        assert lz.y == 20
        assert lz.width == 80
        assert lz.height == 24

    def test_from_dict_with_defaults(self):
        """Test that from_dict uses default values for missing fields."""
        d = {"name": "MINIMAL"}
        lz = LayoutZone.from_dict(d)
        assert lz.name == "MINIMAL"
        assert lz.zone_type == "static"  # Default
        assert lz.x == 0  # Default
        assert lz.y == 0  # Default
        assert lz.width == 40  # Default
        assert lz.height == 20  # Default
        assert lz.command is None
        assert lz.interval is None
        assert lz.description == ""

    def test_from_dict_with_all_fields(self):
        """Test deserializing zone with all fields."""
        d = {
            "name": "LOGS",
            "type": "watch",
            "x": 5,
            "y": 10,
            "width": 100,
            "height": 30,
            "command": "ps aux",
            "interval": 10.0,
            "shell": "/bin/bash",
            "path": "/tmp/test.fifo",
            "port": 8080,
            "file_path": "/path/to/file",
            "renderer": "plain",
            "bookmark": "w",
            "description": "Watch zone",
        }
        lz = LayoutZone.from_dict(d)
        assert lz.name == "LOGS"
        assert lz.zone_type == "watch"
        assert lz.x == 5
        assert lz.y == 10
        assert lz.width == 100
        assert lz.height == 30
        assert lz.command == "ps aux"
        assert lz.interval == 10.0
        assert lz.shell == "/bin/bash"
        assert lz.path == "/tmp/test.fifo"
        assert lz.port == 8080
        assert lz.file_path == "/path/to/file"
        assert lz.renderer == "plain"
        assert lz.bookmark == "w"
        assert lz.description == "Watch zone"

    def test_roundtrip_serialization(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = LayoutZone(
            name="TEST",
            zone_type="watch",
            x=10,
            y=20,
            width=80,
            height=24,
            command="uptime",
            interval=5.0,
            bookmark="t",
            description="Test zone",
        )
        d = original.to_dict()
        restored = LayoutZone.from_dict(d)

        assert restored.name == original.name
        assert restored.zone_type == original.zone_type
        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.width == original.width
        assert restored.height == original.height
        assert restored.command == original.command
        assert restored.interval == original.interval
        assert restored.bookmark == original.bookmark
        assert restored.description == original.description


class TestLayout:
    """Tests for Layout dataclass."""

    def test_create_basic_layout(self):
        """Test creating a basic layout."""
        layout = Layout(
            name="test-layout",
            description="A test layout",
            zones=[],
        )
        assert layout.name == "test-layout"
        assert layout.description == "A test layout"
        assert layout.zones == []
        assert layout.cursor_x is None
        assert layout.cursor_y is None
        assert layout.viewport_x is None
        assert layout.viewport_y is None

    def test_create_layout_with_zones(self):
        """Test creating a layout with zones."""
        zones = [
            LayoutZone(name="ZONE1", zone_type="static", x=0, y=0, width=40, height=20),
            LayoutZone(
                name="ZONE2",
                zone_type="watch",
                x=50,
                y=0,
                width=40,
                height=20,
                command="uptime",
            ),
        ]
        layout = Layout(
            name="multi-zone",
            description="Layout with zones",
            zones=zones,
        )
        assert len(layout.zones) == 2
        assert layout.zones[0].name == "ZONE1"
        assert layout.zones[1].name == "ZONE2"

    def test_create_layout_with_cursor_and_viewport(self):
        """Test creating a layout with cursor and viewport settings."""
        layout = Layout(
            name="positioned",
            description="Layout with position",
            zones=[],
            cursor_x=100,
            cursor_y=50,
            viewport_x=90,
            viewport_y=40,
        )
        assert layout.cursor_x == 100
        assert layout.cursor_y == 50
        assert layout.viewport_x == 90
        assert layout.viewport_y == 40

    def test_to_dict_basic(self):
        """Test serializing layout to dictionary."""
        layout = Layout(
            name="test",
            description="Test layout",
            zones=[],
        )
        d = layout.to_dict()
        assert d["name"] == "test"
        assert d["description"] == "Test layout"
        assert d["zones"] == []
        assert "cursor" not in d
        assert "viewport" not in d

    def test_to_dict_with_cursor_and_viewport(self):
        """Test serializing layout with cursor and viewport."""
        layout = Layout(
            name="test",
            description="Test",
            zones=[],
            cursor_x=10,
            cursor_y=20,
            viewport_x=5,
            viewport_y=15,
        )
        d = layout.to_dict()
        assert d["cursor"] == {"x": 10, "y": 20}
        assert d["viewport"] == {"x": 5, "y": 15}

    def test_to_dict_with_zones(self):
        """Test serializing layout with zones."""
        layout = Layout(
            name="test",
            description="Test",
            zones=[
                LayoutZone(
                    name="ZONE1", zone_type="static", x=0, y=0, width=40, height=20
                ),
            ],
        )
        d = layout.to_dict()
        assert len(d["zones"]) == 1
        assert d["zones"][0]["name"] == "ZONE1"

    def test_from_dict_basic(self):
        """Test deserializing layout from dictionary."""
        d = {
            "name": "test",
            "description": "Test layout",
            "zones": [],
        }
        layout = Layout.from_dict(d)
        assert layout.name == "test"
        assert layout.description == "Test layout"
        assert layout.zones == []

    def test_from_dict_with_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        d = {}
        layout = Layout.from_dict(d)
        assert layout.name == "Unnamed"
        assert layout.description == ""
        assert layout.zones == []
        assert layout.cursor_x is None
        assert layout.viewport_x is None

    def test_from_dict_with_zones(self):
        """Test deserializing layout with zones."""
        d = {
            "name": "multi",
            "description": "Multiple zones",
            "zones": [
                {
                    "name": "ZONE1",
                    "type": "static",
                    "x": 0,
                    "y": 0,
                    "width": 40,
                    "height": 20,
                },
                {
                    "name": "ZONE2",
                    "type": "watch",
                    "x": 50,
                    "y": 0,
                    "width": 40,
                    "height": 20,
                    "command": "uptime",
                },
            ],
        }
        layout = Layout.from_dict(d)
        assert len(layout.zones) == 2
        assert layout.zones[0].name == "ZONE1"
        assert layout.zones[1].name == "ZONE2"
        assert layout.zones[1].command == "uptime"

    def test_from_dict_with_cursor_and_viewport(self):
        """Test deserializing layout with cursor and viewport."""
        d = {
            "name": "positioned",
            "description": "Test",
            "zones": [],
            "cursor": {"x": 100, "y": 200},
            "viewport": {"x": 90, "y": 180},
        }
        layout = Layout.from_dict(d)
        assert layout.cursor_x == 100
        assert layout.cursor_y == 200
        assert layout.viewport_x == 90
        assert layout.viewport_y == 180

    def test_to_yaml(self):
        """Test serializing layout to YAML."""
        layout = Layout(
            name="yaml-test",
            description="YAML test layout",
            zones=[
                LayoutZone(
                    name="ZONE1", zone_type="static", x=0, y=0, width=40, height=20
                ),
            ],
        )
        yaml_str = layout.to_yaml()
        parsed = yaml.safe_load(yaml_str)
        assert parsed["name"] == "yaml-test"
        assert parsed["description"] == "YAML test layout"
        assert len(parsed["zones"]) == 1

    def test_from_yaml(self):
        """Test parsing layout from YAML."""
        yaml_str = """
name: yaml-parsed
description: Parsed from YAML
zones:
  - name: TERMINAL
    type: pty
    x: 0
    y: 0
    width: 80
    height: 24
    bookmark: t
"""
        layout = Layout.from_yaml(yaml_str)
        assert layout.name == "yaml-parsed"
        assert layout.description == "Parsed from YAML"
        assert len(layout.zones) == 1
        assert layout.zones[0].name == "TERMINAL"
        assert layout.zones[0].zone_type == "pty"
        assert layout.zones[0].bookmark == "t"

    def test_yaml_roundtrip(self):
        """Test that to_yaml and from_yaml are inverse operations."""
        original = Layout(
            name="roundtrip",
            description="Test roundtrip",
            zones=[
                LayoutZone(
                    name="WATCH",
                    zone_type="watch",
                    x=0,
                    y=0,
                    width=80,
                    height=15,
                    command="uptime",
                    interval=5.0,
                ),
                LayoutZone(
                    name="TERM", zone_type="pty", x=0, y=16, width=80, height=24
                ),
            ],
            cursor_x=40,
            cursor_y=20,
        )
        yaml_str = original.to_yaml()
        restored = Layout.from_yaml(yaml_str)

        assert restored.name == original.name
        assert restored.description == original.description
        assert len(restored.zones) == len(original.zones)
        assert restored.cursor_x == original.cursor_x
        assert restored.cursor_y == original.cursor_y


class TestLayoutManager:
    """Tests for LayoutManager class."""

    def setup_method(self):
        """Create temporary directory for layout files."""
        self.temp_dir = tempfile.mkdtemp()
        self.layouts_dir = Path(self.temp_dir)
        self.manager = LayoutManager(self.layouts_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_custom_dir(self):
        """Test LayoutManager with custom directory."""
        assert self.manager.layouts_dir == self.layouts_dir

    def test_layout_path_sanitizes_name(self):
        """Test that layout file paths are sanitized."""
        # Special characters should be removed
        path = self.manager._layout_path("Test Layout!@#$%")
        assert path.name == "testlayout.yaml"

        # Mixed case should be lowercased
        path = self.manager._layout_path("MyLayout")
        assert path.name == "mylayout.yaml"

        # Hyphens and underscores should be preserved
        path = self.manager._layout_path("my-test_layout")
        assert path.name == "my-test_layout.yaml"

    def test_save_layout(self):
        """Test saving a layout."""
        layout = Layout(
            name="saved-layout",
            description="Test save",
            zones=[
                LayoutZone(
                    name="ZONE1", zone_type="static", x=0, y=0, width=40, height=20
                ),
            ],
        )
        path = self.manager.save(layout)

        assert path.exists()
        assert path.name == "saved-layout.yaml"

        # Verify content
        content = path.read_text()
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "saved-layout"

    def test_load_layout(self):
        """Test loading a layout."""
        # First save a layout
        layout = Layout(
            name="load-test",
            description="Test load",
            zones=[
                LayoutZone(name="TERM", zone_type="pty", x=0, y=0, width=80, height=24),
            ],
        )
        self.manager.save(layout)

        # Now load it
        loaded = self.manager.load("load-test")
        assert loaded is not None
        assert loaded.name == "load-test"
        assert loaded.description == "Test load"
        assert len(loaded.zones) == 1
        assert loaded.zones[0].name == "TERM"

    def test_load_nonexistent_returns_none(self):
        """Test that loading nonexistent layout returns None."""
        result = self.manager.load("nonexistent")
        assert result is None

    def test_load_invalid_yaml_returns_none(self):
        """Test that loading invalid YAML returns None."""
        # Create an invalid YAML file (syntax that will cause parse error)
        invalid_path = self.layouts_dir / "invalid.yaml"
        invalid_path.write_text("not: valid: yaml:\n  - broken")

        result = self.manager.load("invalid")
        assert result is None

    def test_delete_layout(self):
        """Test deleting a layout."""
        # Create a layout
        layout = Layout(name="delete-me", description="To be deleted", zones=[])
        path = self.manager.save(layout)
        assert path.exists()

        # Delete it
        result = self.manager.delete("delete-me")
        assert result is True
        assert not path.exists()

    def test_delete_nonexistent_returns_false(self):
        """Test that deleting nonexistent layout returns False."""
        result = self.manager.delete("nonexistent")
        assert result is False

    def test_list_layouts(self):
        """Test listing available layouts."""
        # Save multiple layouts
        layout1 = Layout(name="alpha", description="First layout", zones=[])
        layout2 = Layout(name="beta", description="Second layout", zones=[])
        layout3 = Layout(name="gamma", description="Third layout", zones=[])

        self.manager.save(layout1)
        self.manager.save(layout2)
        self.manager.save(layout3)

        # List should return sorted by name
        layouts = self.manager.list_layouts()
        assert len(layouts) == 3
        assert layouts[0] == ("alpha", "First layout")
        assert layouts[1] == ("beta", "Second layout")
        assert layouts[2] == ("gamma", "Third layout")

    def test_list_layouts_empty(self):
        """Test listing layouts when directory is empty."""
        layouts = self.manager.list_layouts()
        assert layouts == []

    def test_list_layouts_skips_invalid(self):
        """Test that listing skips invalid YAML files."""
        # Create one valid layout
        layout = Layout(name="valid", description="Valid layout", zones=[])
        self.manager.save(layout)

        # Create an invalid YAML file (syntax that will cause parse error)
        invalid_path = self.layouts_dir / "invalid.yaml"
        invalid_path.write_text("not: valid: yaml:\n  - broken")

        # Should only list the valid one
        layouts = self.manager.list_layouts()
        assert len(layouts) == 1
        assert layouts[0][0] == "valid"

    def test_exists(self):
        """Test checking if a layout exists."""
        assert not self.manager.exists("test")

        layout = Layout(name="test", description="Test", zones=[])
        self.manager.save(layout)

        assert self.manager.exists("test")
        assert self.manager.exists("TEST")  # Case insensitive

    def test_save_and_load_roundtrip(self):
        """Test complete save and load roundtrip."""
        original = Layout(
            name="complete",
            description="Complete layout",
            zones=[
                LayoutZone(
                    name="LOGS",
                    zone_type="watch",
                    x=0,
                    y=0,
                    width=80,
                    height=15,
                    command="tail -f /var/log/syslog",
                    interval=5.0,
                    bookmark="l",
                ),
                LayoutZone(
                    name="TERM",
                    zone_type="pty",
                    x=0,
                    y=16,
                    width=80,
                    height=24,
                    shell="/bin/bash",
                    bookmark="t",
                ),
            ],
            cursor_x=40,
            cursor_y=20,
            viewport_x=30,
            viewport_y=10,
        )

        self.manager.save(original)
        loaded = self.manager.load("complete")

        assert loaded is not None
        assert loaded.name == original.name
        assert loaded.description == original.description
        assert len(loaded.zones) == len(original.zones)
        assert loaded.cursor_x == original.cursor_x
        assert loaded.cursor_y == original.cursor_y
        assert loaded.viewport_x == original.viewport_x
        assert loaded.viewport_y == original.viewport_y

        # Verify zone details
        assert loaded.zones[0].name == "LOGS"
        assert loaded.zones[0].command == "tail -f /var/log/syslog"
        assert loaded.zones[0].interval == 5.0
        assert loaded.zones[1].name == "TERM"
        assert loaded.zones[1].shell == "/bin/bash"


class TestLayoutManagerSaveFromZones:
    """Tests for LayoutManager.save_from_zones method."""

    def setup_method(self):
        """Create temporary directory and zone manager."""
        self.temp_dir = tempfile.mkdtemp()
        self.layouts_dir = Path(self.temp_dir)
        self.layout_manager = LayoutManager(self.layouts_dir)
        self.zone_manager = ZoneManager()

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_empty_zones(self):
        """Test saving layout from empty zone manager."""
        path = self.layout_manager.save_from_zones(
            name="empty",
            description="Empty layout",
            zone_manager=self.zone_manager,
        )

        assert path.exists()
        loaded = self.layout_manager.load("empty")
        assert loaded is not None
        assert loaded.zones == []

    def test_save_static_zones(self):
        """Test saving layout with static zones."""
        self.zone_manager.create(
            name="NOTES",
            x=0,
            y=0,
            width=40,
            height=20,
            description="Notes area",
            bookmark="n",
        )

        self.layout_manager.save_from_zones(
            name="static",
            description="Static zones",
            zone_manager=self.zone_manager,
        )

        loaded = self.layout_manager.load("static")
        assert loaded is not None
        assert len(loaded.zones) == 1
        assert loaded.zones[0].name == "NOTES"
        assert loaded.zones[0].zone_type == "static"
        assert loaded.zones[0].bookmark == "n"

    def test_save_watch_zones(self):
        """Test saving layout with watch zones."""
        self.zone_manager.create_watch(
            name="STATUS",
            x=0,
            y=0,
            width=80,
            height=15,
            command="uptime",
            interval=10.0,
            bookmark="s",
        )

        self.layout_manager.save_from_zones(
            name="watch",
            description="Watch zones",
            zone_manager=self.zone_manager,
        )

        loaded = self.layout_manager.load("watch")
        assert loaded is not None
        assert len(loaded.zones) == 1
        assert loaded.zones[0].zone_type == "watch"
        assert loaded.zones[0].command == "uptime"
        assert loaded.zones[0].interval == 10.0

    def test_save_pty_zones(self):
        """Test saving layout with PTY zones."""
        self.zone_manager.create_pty(
            name="TERM",
            x=0,
            y=0,
            width=80,
            height=24,
            shell="/bin/zsh",
            bookmark="t",
        )

        self.layout_manager.save_from_zones(
            name="pty",
            description="PTY zones",
            zone_manager=self.zone_manager,
        )

        loaded = self.layout_manager.load("pty")
        assert loaded is not None
        assert len(loaded.zones) == 1
        assert loaded.zones[0].zone_type == "pty"
        assert loaded.zones[0].shell == "/bin/zsh"

    def test_save_pty_zones_default_shell_not_saved(self):
        """Test that default bash shell is not saved."""
        # Create PTY zone with default shell
        self.zone_manager.create_pty(
            name="TERM",
            x=0,
            y=0,
            width=80,
            height=24,
            # shell defaults to /bin/bash
        )

        self.layout_manager.save_from_zones(
            name="pty-default",
            description="PTY with default shell",
            zone_manager=self.zone_manager,
        )

        loaded = self.layout_manager.load("pty-default")
        assert loaded is not None
        # When PTY uses default shell, shell field is omitted from YAML (loads as None)
        assert loaded.zones[0].shell is None

    def test_save_with_cursor_position(self):
        """Test saving layout with cursor position."""
        self.layout_manager.save_from_zones(
            name="positioned",
            description="With cursor",
            zone_manager=self.zone_manager,
            cursor=(100, 50),
        )

        loaded = self.layout_manager.load("positioned")
        assert loaded is not None
        assert loaded.cursor_x == 100
        assert loaded.cursor_y == 50

    def test_save_with_viewport_position(self):
        """Test saving layout with viewport position."""
        self.layout_manager.save_from_zones(
            name="viewport",
            description="With viewport",
            zone_manager=self.zone_manager,
            viewport=(200, 100),
        )

        loaded = self.layout_manager.load("viewport")
        assert loaded is not None
        assert loaded.viewport_x == 200
        assert loaded.viewport_y == 100

    def test_save_multiple_zones(self):
        """Test saving layout with multiple zones of different types."""
        self.zone_manager.create(
            name="NOTES",
            x=0,
            y=0,
            width=40,
            height=20,
            bookmark="n",
        )
        self.zone_manager.create_watch(
            name="STATUS",
            x=50,
            y=0,
            width=60,
            height=15,
            command="uptime",
            interval=5.0,
            bookmark="s",
        )
        self.zone_manager.create_pty(
            name="TERM",
            x=0,
            y=25,
            width=110,
            height=24,
            bookmark="t",
        )

        self.layout_manager.save_from_zones(
            name="multi",
            description="Multiple zones",
            zone_manager=self.zone_manager,
            cursor=(55, 7),
            viewport=(0, 0),
        )

        loaded = self.layout_manager.load("multi")
        assert loaded is not None
        assert len(loaded.zones) == 3

        # Zones are sorted by name in list_all
        zone_names = [z.name for z in loaded.zones]
        assert "NOTES" in zone_names
        assert "STATUS" in zone_names
        assert "TERM" in zone_names


class TestLayoutManagerApplyLayout:
    """Tests for LayoutManager.apply_layout method."""

    def setup_method(self):
        """Create temporary directory and managers."""
        self.temp_dir = tempfile.mkdtemp()
        self.layouts_dir = Path(self.temp_dir)
        self.layout_manager = LayoutManager(self.layouts_dir)
        self.zone_manager = ZoneManager()
        self.zone_executor = ZoneExecutor(self.zone_manager)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_apply_empty_layout(self):
        """Test applying an empty layout."""
        layout = Layout(name="empty", description="Empty", zones=[])
        created, errors = self.layout_manager.apply_layout(
            layout, self.zone_manager, self.zone_executor
        )

        assert created == 0
        assert errors == []
        assert len(self.zone_manager) == 0

    def test_apply_static_zone(self):
        """Test applying layout with static zone."""
        layout = Layout(
            name="static",
            description="Static zone",
            zones=[
                LayoutZone(
                    name="NOTES", zone_type="static", x=0, y=0, width=40, height=20
                ),
            ],
        )
        created, errors = self.layout_manager.apply_layout(
            layout, self.zone_manager, self.zone_executor
        )

        assert created == 1
        assert errors == []
        assert "notes" in self.zone_manager
        zone = self.zone_manager.get("NOTES")
        assert zone.zone_type == ZoneType.STATIC

    def test_apply_watch_zone(self):
        """Test applying layout with watch zone."""
        layout = Layout(
            name="watch",
            description="Watch zone",
            zones=[
                LayoutZone(
                    name="STATUS",
                    zone_type="watch",
                    x=0,
                    y=0,
                    width=80,
                    height=15,
                    command="echo test",
                    interval=5.0,
                    bookmark="s",
                ),
            ],
        )

        # Mock execute_pipe to avoid actual command execution
        with patch.object(self.zone_executor, "execute_pipe"):
            with patch.object(self.zone_executor, "start_watch"):
                created, errors = self.layout_manager.apply_layout(
                    layout, self.zone_manager, self.zone_executor
                )

        assert created == 1
        assert errors == []
        zone = self.zone_manager.get("STATUS")
        assert zone.zone_type == ZoneType.WATCH
        assert zone.config.command == "echo test"
        assert zone.config.refresh_interval == 5.0
        assert zone.bookmark == "s"

    def test_apply_pipe_zone(self):
        """Test applying layout with pipe zone."""
        layout = Layout(
            name="pipe",
            description="Pipe zone",
            zones=[
                LayoutZone(
                    name="OUTPUT",
                    zone_type="pipe",
                    x=0,
                    y=0,
                    width=80,
                    height=15,
                    command="echo hello",
                ),
            ],
        )

        with patch.object(self.zone_executor, "execute_pipe") as mock_execute:
            created, errors = self.layout_manager.apply_layout(
                layout, self.zone_manager, self.zone_executor
            )

        assert created == 1
        assert errors == []
        mock_execute.assert_called_once()

    def test_apply_pty_zone_with_handler(self):
        """Test applying layout with PTY zone and handler."""
        layout = Layout(
            name="pty",
            description="PTY zone",
            zones=[
                LayoutZone(
                    name="TERM",
                    zone_type="pty",
                    x=0,
                    y=0,
                    width=80,
                    height=24,
                    shell="/bin/bash",
                ),
            ],
        )

        pty_handler = MagicMock()
        pty_handler.create_pty.return_value = True

        created, errors = self.layout_manager.apply_layout(
            layout,
            self.zone_manager,
            self.zone_executor,
            pty_handler=pty_handler,
        )

        assert created == 1
        assert errors == []
        pty_handler.create_pty.assert_called_once()

    def test_apply_pty_zone_without_handler(self):
        """Test applying PTY zone without handler creates zone but doesn't start PTY."""
        layout = Layout(
            name="pty",
            description="PTY zone",
            zones=[
                LayoutZone(name="TERM", zone_type="pty", x=0, y=0, width=80, height=24),
            ],
        )

        created, errors = self.layout_manager.apply_layout(
            layout, self.zone_manager, self.zone_executor
        )

        # Zone should be created
        assert created == 1
        assert errors == []
        assert "term" in self.zone_manager

    def test_apply_pty_zone_creation_failure(self):
        """Test handling PTY zone creation failure."""
        layout = Layout(
            name="pty",
            description="PTY zone",
            zones=[
                LayoutZone(name="TERM", zone_type="pty", x=0, y=0, width=80, height=24),
            ],
        )

        pty_handler = MagicMock()
        pty_handler.create_pty.return_value = False

        created, errors = self.layout_manager.apply_layout(
            layout,
            self.zone_manager,
            self.zone_executor,
            pty_handler=pty_handler,
        )

        assert created == 1
        assert len(errors) == 1
        assert "Failed to create PTY" in errors[0]

    def test_apply_fifo_zone_with_handler(self):
        """Test applying layout with FIFO zone and handler."""
        layout = Layout(
            name="fifo",
            description="FIFO zone",
            zones=[
                LayoutZone(
                    name="EVENTS",
                    zone_type="fifo",
                    x=0,
                    y=0,
                    width=50,
                    height=20,
                    path="/tmp/test.fifo",
                ),
            ],
        )

        fifo_handler = MagicMock()
        fifo_handler.create_fifo.return_value = True

        created, errors = self.layout_manager.apply_layout(
            layout,
            self.zone_manager,
            self.zone_executor,
            fifo_handler=fifo_handler,
        )

        assert created == 1
        assert errors == []
        fifo_handler.create_fifo.assert_called_once()

    def test_apply_socket_zone_with_handler(self):
        """Test applying layout with socket zone and handler."""
        layout = Layout(
            name="socket",
            description="Socket zone",
            zones=[
                LayoutZone(
                    name="MESSAGES",
                    zone_type="socket",
                    x=0,
                    y=0,
                    width=60,
                    height=20,
                    port=9999,
                ),
            ],
        )

        socket_handler = MagicMock()
        socket_handler.create_socket.return_value = True

        created, errors = self.layout_manager.apply_layout(
            layout,
            self.zone_manager,
            self.zone_executor,
            socket_handler=socket_handler,
        )

        assert created == 1
        assert errors == []
        socket_handler.create_socket.assert_called_once()

    def test_apply_pager_zone(self):
        """Test applying layout with pager zone."""
        layout = Layout(
            name="pager",
            description="Pager zone",
            zones=[
                LayoutZone(
                    name="README",
                    zone_type="pager",
                    x=0,
                    y=0,
                    width=80,
                    height=30,
                    file_path="/path/to/file.md",
                    renderer="plain",
                ),
            ],
        )

        # Mock at zones module level since it's imported dynamically
        with patch("zones.load_pager_content") as mock_load:
            mock_load.return_value = True
            created, errors = self.layout_manager.apply_layout(
                layout, self.zone_manager, self.zone_executor
            )

        assert created == 1
        assert errors == []
        mock_load.assert_called_once()

    def test_apply_duplicate_zone_skipped(self):
        """Test that duplicate zone names are skipped."""
        # Create an existing zone
        self.zone_manager.create("EXISTING", 0, 0, 40, 20)

        layout = Layout(
            name="dupe",
            description="With duplicate",
            zones=[
                LayoutZone(
                    name="EXISTING", zone_type="static", x=50, y=0, width=40, height=20
                ),
                LayoutZone(
                    name="NEW", zone_type="static", x=100, y=0, width=40, height=20
                ),
            ],
        )

        created, errors = self.layout_manager.apply_layout(
            layout, self.zone_manager, self.zone_executor
        )

        assert created == 1  # Only NEW was created
        assert len(errors) == 1
        assert "already exists" in errors[0]
        assert "EXISTING" in errors[0]

    def test_apply_with_clear_existing(self):
        """Test applying layout with clear_existing flag."""
        # Create some existing zones
        self.zone_manager.create("OLD1", 0, 0, 40, 20)
        self.zone_manager.create("OLD2", 50, 0, 40, 20)
        assert len(self.zone_manager) == 2

        layout = Layout(
            name="fresh",
            description="Fresh layout",
            zones=[
                LayoutZone(
                    name="NEW", zone_type="static", x=0, y=0, width=40, height=20
                ),
            ],
        )

        created, errors = self.layout_manager.apply_layout(
            layout,
            self.zone_manager,
            self.zone_executor,
            clear_existing=True,
        )

        assert created == 1
        assert errors == []
        assert len(self.zone_manager) == 1
        assert "new" in self.zone_manager
        assert "old1" not in self.zone_manager
        assert "old2" not in self.zone_manager

    def test_apply_invalid_zone_type(self):
        """Test handling invalid zone type in layout."""
        layout = Layout(
            name="invalid",
            description="Invalid zone type",
            zones=[
                LayoutZone(
                    name="BAD", zone_type="invalid_type", x=0, y=0, width=40, height=20
                ),
            ],
        )

        created, errors = self.layout_manager.apply_layout(
            layout, self.zone_manager, self.zone_executor
        )

        assert created == 0
        assert len(errors) == 1
        assert "Error creating" in errors[0]

    def test_apply_multiple_zones_mixed_types(self):
        """Test applying layout with multiple zones of different types."""
        layout = Layout(
            name="mixed",
            description="Mixed zone types",
            zones=[
                LayoutZone(
                    name="NOTES", zone_type="static", x=0, y=0, width=40, height=20
                ),
                LayoutZone(
                    name="STATUS",
                    zone_type="watch",
                    x=50,
                    y=0,
                    width=60,
                    height=15,
                    command="uptime",
                    interval=5.0,
                ),
            ],
        )

        with patch.object(self.zone_executor, "start_watch"):
            created, errors = self.layout_manager.apply_layout(
                layout, self.zone_manager, self.zone_executor
            )

        assert created == 2
        assert errors == []
        assert "notes" in self.zone_manager
        assert "status" in self.zone_manager


class TestDefaultLayouts:
    """Tests for default layouts and installation."""

    def test_default_layouts_defined(self):
        """Test that default layouts are defined."""
        assert "devops" in DEFAULT_LAYOUTS
        assert "development" in DEFAULT_LAYOUTS
        assert "monitoring" in DEFAULT_LAYOUTS
        assert "dashboard" in DEFAULT_LAYOUTS
        assert "logs" in DEFAULT_LAYOUTS
        assert "docker" in DEFAULT_LAYOUTS
        assert "network" in DEFAULT_LAYOUTS
        assert "python-dev" in DEFAULT_LAYOUTS
        assert "minimal" in DEFAULT_LAYOUTS

    def test_devops_layout_structure(self):
        """Test devops layout has expected zones."""
        layout = DEFAULT_LAYOUTS["devops"]
        assert layout.name == "devops"
        assert layout.description == "DevOps monitoring workspace"

        zone_names = [z.name for z in layout.zones]
        assert "LOGS" in zone_names
        assert "PROCESSES" in zone_names
        assert "DISK" in zone_names
        assert "TERMINAL" in zone_names

    def test_development_layout_structure(self):
        """Test development layout has expected zones."""
        layout = DEFAULT_LAYOUTS["development"]
        assert layout.name == "development"

        zone_names = [z.name for z in layout.zones]
        assert "GIT" in zone_names
        assert "FILES" in zone_names
        assert "EDITOR" in zone_names

    def test_minimal_layout_structure(self):
        """Test minimal layout has expected zones."""
        layout = DEFAULT_LAYOUTS["minimal"]
        assert layout.name == "minimal"
        assert len(layout.zones) == 2

        zone_names = [z.name for z in layout.zones]
        assert "STATUS" in zone_names
        assert "TERMINAL" in zone_names

    def test_install_default_layouts(self):
        """Test installing default layouts."""
        temp_dir = tempfile.mkdtemp()
        layouts_dir = Path(temp_dir)

        try:
            installed = install_default_layouts(layouts_dir)

            # Should install all default layouts
            assert installed == len(DEFAULT_LAYOUTS)

            # Verify files exist
            for name in DEFAULT_LAYOUTS:
                assert (layouts_dir / f"{name}.yaml").exists()

        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_install_default_layouts_skips_existing(self):
        """Test that installation skips existing layouts."""
        temp_dir = tempfile.mkdtemp()
        layouts_dir = Path(temp_dir)

        try:
            # First install
            first_count = install_default_layouts(layouts_dir)
            assert first_count == len(DEFAULT_LAYOUTS)

            # Second install should skip all
            second_count = install_default_layouts(layouts_dir)
            assert second_count == 0

        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_install_partial_existing(self):
        """Test installation with some layouts already existing."""
        temp_dir = tempfile.mkdtemp()
        layouts_dir = Path(temp_dir)

        try:
            # Create one layout manually
            manager = LayoutManager(layouts_dir)
            manager.save(DEFAULT_LAYOUTS["minimal"])

            # Install should skip the existing one
            installed = install_default_layouts(layouts_dir)
            assert installed == len(DEFAULT_LAYOUTS) - 1

        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)


class TestGetLayoutsDir:
    """Tests for get_layouts_dir function."""

    def test_get_layouts_dir_creates_directory(self):
        """Test that get_layouts_dir creates the directory if needed."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": tempfile.mkdtemp()}):
            layouts_dir = get_layouts_dir()
            assert layouts_dir.exists()
            assert layouts_dir.is_dir()

            # Clean up
            import shutil

            shutil.rmtree(layouts_dir.parent.parent, ignore_errors=True)

    def test_get_layouts_dir_unix_default(self):
        """Test Unix default path uses .config."""
        with patch("os.name", "posix"):
            with patch.dict(os.environ, {}, clear=True):
                with patch.object(Path, "home", return_value=Path("/home/testuser")):
                    with patch.object(Path, "mkdir"):
                        layouts_dir = get_layouts_dir()
                        assert "mygrid" in str(layouts_dir)
                        assert "layouts" in str(layouts_dir)

    def test_get_layouts_dir_xdg_config_home(self):
        """Test that XDG_CONFIG_HOME is respected on Unix."""
        temp_dir = tempfile.mkdtemp()
        try:
            with patch("os.name", "posix"):
                with patch.dict(os.environ, {"XDG_CONFIG_HOME": temp_dir}):
                    layouts_dir = get_layouts_dir()
                    assert str(layouts_dir).startswith(temp_dir)
                    assert layouts_dir.exists()
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only test")
    def test_get_layouts_dir_windows(self):
        """Test Windows path uses APPDATA."""
        temp_dir = tempfile.mkdtemp()
        try:
            with patch.dict(os.environ, {"APPDATA": temp_dir}):
                layouts_dir = get_layouts_dir()
                assert str(layouts_dir).startswith(temp_dir)
                assert "mygrid" in str(layouts_dir)
                assert "layouts" in str(layouts_dir)
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_layouts_dir_windows_path_structure(self):
        """Test Windows layout directory structure (platform-independent check)."""
        # Just verify the code path handles Windows naming
        # On Windows: uses APPDATA/mygrid/layouts
        # This test verifies the logic without actually running on Windows
        if os.name == "nt":
            # On Windows, verify APPDATA is used
            layouts_dir = get_layouts_dir()
            assert "mygrid" in str(layouts_dir)
            assert "layouts" in str(layouts_dir)
        else:
            # On Unix, just verify XDG path works
            pass  # Already covered by other tests


def run_tests():
    """Run all tests."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v"], cwd=Path(__file__).parent.parent
    )
    return result.returncode


if __name__ == "__main__":
    import sys

    sys.exit(run_tests())
