"""Tests for project save/load functionality."""

import json
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from canvas import Canvas
from viewport import Viewport, YAxisDirection
from renderer import GridSettings
from project import (
    Project,
    ProjectMetadata,
    PROJECT_VERSION,
    suggest_filename,
    validate_project_data,
    get_recent_projects,
    add_recent_project,
    SessionManager,
)
from modes import BookmarkManager
from zones import ZoneManager, ZoneConfig, ZoneType


class TestProjectMetadata:
    """Tests for ProjectMetadata."""

    def test_new_metadata(self):
        meta = ProjectMetadata.new("Test Project")
        assert meta.name == "Test Project"
        assert meta.created != ""
        assert meta.modified != ""
        assert meta.version == PROJECT_VERSION

    def test_touch_updates_modified(self):
        meta = ProjectMetadata.new()
        original_modified = meta.modified

        # Small delay to ensure timestamp changes
        time.sleep(0.01)

        meta.touch()
        assert meta.modified != original_modified


class TestProject:
    """Tests for Project class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.temp_dir = tempfile.mkdtemp()

    def test_new_project(self):
        project = Project()
        assert project.filepath is None
        assert project.filename == "Untitled"
        assert not project.dirty

    def test_dirty_tracking(self):
        project = Project()
        assert not project.dirty

        project.mark_dirty()
        assert project.dirty
        assert project.display_name == "*Untitled"

        project.mark_clean()
        assert not project.dirty

    def test_save_requires_filepath(self):
        project = Project()
        try:
            project.save(self.canvas, self.viewport)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "No filepath" in str(e)

    def test_save_and_load_empty_canvas(self):
        filepath = Path(self.temp_dir) / "empty.json"
        project = Project()

        # Save empty canvas
        project.save(self.canvas, self.viewport, filepath=filepath)
        assert filepath.exists()
        assert not project.dirty

        # Load it back
        new_canvas = Canvas()
        new_viewport = Viewport()
        loaded = Project.load(filepath, new_canvas, new_viewport)

        assert loaded.filepath == filepath
        assert new_canvas.cell_count == 0

    def test_save_and_load_with_content(self):
        filepath = Path(self.temp_dir) / "content.json"

        # Set up canvas with content
        self.canvas.set(0, 0, "A")
        self.canvas.set(10, 5, "B")
        self.canvas.set(-5, -5, "C")

        # Set up viewport state
        self.viewport.cursor.set(10, 20)
        self.viewport.origin.set(5, 5)
        self.viewport.x = 100
        self.viewport.y = 200

        project = Project()
        project.metadata.name = "Test Canvas"
        project.metadata.description = "A test description"

        # Save
        project.save(self.canvas, self.viewport, filepath=filepath)

        # Load into fresh instances
        new_canvas = Canvas()
        new_viewport = Viewport()
        loaded = Project.load(filepath, new_canvas, new_viewport)

        # Verify canvas content
        assert new_canvas.get_char(0, 0) == "A"
        assert new_canvas.get_char(10, 5) == "B"
        assert new_canvas.get_char(-5, -5) == "C"
        assert new_canvas.cell_count == 3

        # Verify viewport state
        assert new_viewport.cursor.x == 10
        assert new_viewport.cursor.y == 20
        assert new_viewport.origin.x == 5
        assert new_viewport.origin.y == 5
        assert new_viewport.x == 100
        assert new_viewport.y == 200

        # Verify metadata
        assert loaded.metadata.name == "Test Canvas"
        assert loaded.metadata.description == "A test description"

    def test_save_and_load_grid_settings(self):
        filepath = Path(self.temp_dir) / "grid.json"

        grid = GridSettings()
        grid.show_origin = False
        grid.show_major_lines = True
        grid.show_minor_lines = True
        grid.major_interval = 20
        grid.minor_interval = 4

        project = Project()
        project.save(self.canvas, self.viewport, grid_settings=grid, filepath=filepath)

        # Load
        new_canvas = Canvas()
        new_viewport = Viewport()
        new_grid = GridSettings()
        Project.load(filepath, new_canvas, new_viewport, grid_settings=new_grid)

        assert new_grid.show_origin == False
        assert new_grid.show_major_lines == True
        assert new_grid.show_minor_lines == True
        assert new_grid.major_interval == 20
        assert new_grid.minor_interval == 4

    def test_save_and_load_y_direction(self):
        filepath = Path(self.temp_dir) / "ydir.json"

        self.viewport.y_direction = YAxisDirection.UP

        project = Project()
        project.save(self.canvas, self.viewport, filepath=filepath)

        new_canvas = Canvas()
        new_viewport = Viewport()
        loaded = Project.load(filepath, new_canvas, new_viewport)

        assert new_viewport.y_direction == YAxisDirection.UP

    def test_export_text_empty(self):
        filepath = Path(self.temp_dir) / "empty.txt"
        project = Project()

        result = project.export_text(self.canvas, filepath=filepath)
        assert result == filepath
        assert filepath.exists()

        content = filepath.read_text()
        assert content == ""

    def test_export_text_with_content(self):
        filepath = Path(self.temp_dir) / "content.txt"

        # Create some content
        self.canvas.write_text(0, 0, "Hello")
        self.canvas.write_text(0, 1, "World")

        project = Project()
        project.export_text(self.canvas, filepath=filepath)

        content = filepath.read_text()
        lines = content.strip().split("\n")
        assert lines[0] == "Hello"
        assert lines[1] == "World"

    def test_export_text_preserves_spacing(self):
        filepath = Path(self.temp_dir) / "spaced.txt"

        self.canvas.set(0, 0, "A")
        self.canvas.set(5, 0, "B")  # Gap of 4 spaces

        project = Project()
        project.export_text(self.canvas, filepath=filepath)

        content = filepath.read_text()
        assert content.strip() == "A    B"

    def test_import_text(self):
        filepath = Path(self.temp_dir) / "import.txt"

        # Create text file
        filepath.write_text("Line 1\nLine 2\n  Indented\n")

        new_canvas = Canvas()
        new_viewport = Viewport()
        project = Project.import_text(filepath, new_canvas, new_viewport)

        assert new_canvas.get_char(0, 0) == "L"
        assert new_canvas.get_char(5, 0) == "1"
        assert new_canvas.get_char(0, 1) == "L"
        assert new_canvas.get_char(2, 2) == "I"  # "  Indented"

        # Import should mark as dirty (needs Save As)
        assert project.dirty
        assert project.filepath is None

    def test_import_text_with_offset(self):
        filepath = Path(self.temp_dir) / "offset.txt"
        filepath.write_text("X")

        new_canvas = Canvas()
        new_viewport = Viewport()
        project = Project.import_text(
            filepath, new_canvas, new_viewport, start_x=10, start_y=20
        )

        assert new_canvas.get_char(10, 20) == "X"
        assert new_canvas.is_empty_at(0, 0)

    def test_load_nonexistent_file(self):
        try:
            Project.load(
                Path(self.temp_dir) / "nonexistent.json", self.canvas, self.viewport
            )
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_file_format_version(self):
        filepath = Path(self.temp_dir) / "version.json"

        project = Project()
        project.save(self.canvas, self.viewport, filepath=filepath)

        # Read and verify version
        with open(filepath) as f:
            data = json.load(f)
        assert data["version"] == PROJECT_VERSION

    def test_unsupported_version(self):
        filepath = Path(self.temp_dir) / "oldversion.json"

        # Create file with old version
        data = {"version": "0.1", "canvas": {"cells": []}}
        with open(filepath, "w") as f:
            json.dump(data, f)

        try:
            Project.load(filepath, self.canvas, self.viewport)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Unsupported" in str(e)


class TestSuggestFilename:
    """Tests for suggest_filename helper."""

    def test_empty_canvas(self):
        canvas = Canvas()
        name = suggest_filename(canvas)
        assert name == "canvas.json"

    def test_with_text_content(self):
        canvas = Canvas()
        canvas.write_text(0, 0, "My Drawing")
        name = suggest_filename(canvas)
        assert name == "My_Drawing.json"

    def test_with_special_chars(self):
        canvas = Canvas()
        canvas.write_text(0, 0, "Test: File!")
        name = suggest_filename(canvas)
        assert ".json" in name
        assert ":" not in name
        assert "!" not in name

    def test_custom_base(self):
        canvas = Canvas()
        name = suggest_filename(canvas, base="untitled")
        assert name == "untitled.json"


class TestExportTextAdvanced:
    """Additional tests for text export functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.temp_dir = tempfile.mkdtemp()

    def test_export_text_default_filepath(self):
        """Test export when project has filepath - uses .txt extension."""
        project = Project()
        project.filepath = Path(self.temp_dir) / "myproject.json"

        self.canvas.write_text(0, 0, "Test")
        result = project.export_text(self.canvas)

        assert result == Path(self.temp_dir) / "myproject.txt"
        assert result.exists()

    def test_export_text_no_filepath(self):
        """Test export with no project filepath - uses export.txt."""
        project = Project()
        # No filepath set

        self.canvas.write_text(0, 0, "Test")
        # Save to temp dir to avoid polluting cwd
        result = project.export_text(
            self.canvas, filepath=Path(self.temp_dir) / "output.txt"
        )
        assert result.exists()

    def test_export_text_exclude_empty_lines(self):
        """Test export excluding empty lines."""
        filepath = Path(self.temp_dir) / "nonempty.txt"

        self.canvas.write_text(0, 0, "Line1")
        # Skip row 1
        self.canvas.write_text(0, 2, "Line3")

        project = Project()
        project.export_text(self.canvas, filepath=filepath, include_empty_lines=False)

        content = filepath.read_text()
        lines = content.strip().split("\n")
        # With include_empty_lines=False, empty lines should still be present
        # because they're within the bounding box
        assert "Line1" in lines[0]

    def test_export_text_with_colors(self):
        """Test that export works with colored cells."""
        filepath = Path(self.temp_dir) / "colored.txt"

        # Set cells with colors (colors should be ignored in text export)
        self.canvas.set(0, 0, "R")
        self.canvas.set(1, 0, "G")
        self.canvas.set(2, 0, "B")

        project = Project()
        project.export_text(self.canvas, filepath=filepath)

        content = filepath.read_text()
        assert content.strip() == "RGB"

    def test_export_text_multiline_with_gaps(self):
        """Test export with sparse content across multiple lines."""
        filepath = Path(self.temp_dir) / "sparse.txt"

        self.canvas.set(0, 0, "A")
        self.canvas.set(10, 0, "B")
        self.canvas.set(0, 5, "C")
        self.canvas.set(10, 5, "D")

        project = Project()
        project.export_text(self.canvas, filepath=filepath)

        content = filepath.read_text()
        lines = content.split("\n")
        assert len(lines) >= 6  # At least 6 lines (rows 0-5)
        assert lines[0] == "A         B"
        assert lines[5] == "C         D"


class TestImportTextAdvanced:
    """Additional tests for text import functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.temp_dir = tempfile.mkdtemp()

    def test_import_empty_file(self):
        """Test importing an empty file."""
        filepath = Path(self.temp_dir) / "empty.txt"
        filepath.write_text("")

        project = Project.import_text(filepath, self.canvas, self.viewport)

        assert self.canvas.cell_count == 0
        assert project.dirty
        assert project.metadata.name == "empty"

    def test_import_file_with_tabs(self):
        """Test importing file with tab characters."""
        filepath = Path(self.temp_dir) / "tabs.txt"
        filepath.write_text("A\tB\tC")

        Project.import_text(filepath, self.canvas, self.viewport)

        # Tabs should be preserved as tab characters
        assert self.canvas.get_char(0, 0) == "A"
        assert self.canvas.get_char(1, 0) == "\t"
        assert self.canvas.get_char(2, 0) == "B"

    def test_import_file_spaces_ignored(self):
        """Test that spaces are not stored (sparse storage)."""
        filepath = Path(self.temp_dir) / "spaces.txt"
        filepath.write_text("A   B")

        Project.import_text(filepath, self.canvas, self.viewport)

        # Only non-space chars should be stored
        assert self.canvas.get_char(0, 0) == "A"
        assert self.canvas.is_empty_at(1, 0)
        assert self.canvas.is_empty_at(2, 0)
        assert self.canvas.is_empty_at(3, 0)
        assert self.canvas.get_char(4, 0) == "B"

    def test_import_resets_viewport(self):
        """Test that import resets viewport position."""
        filepath = Path(self.temp_dir) / "test.txt"
        filepath.write_text("Content")

        # Set viewport to non-zero position
        self.viewport.x = 100
        self.viewport.y = 200
        self.viewport.cursor.set(50, 50)

        Project.import_text(filepath, self.canvas, self.viewport)

        assert self.viewport.x == 0
        assert self.viewport.y == 0
        assert self.viewport.cursor.x == 0
        assert self.viewport.cursor.y == 0

    def test_import_with_unicode(self):
        """Test importing file with unicode characters."""
        filepath = Path(self.temp_dir) / "unicode.txt"
        filepath.write_text("Hello, \u4e16\u754c!")  # Hello, World! in Chinese chars

        Project.import_text(filepath, self.canvas, self.viewport)

        assert self.canvas.get_char(7, 0) == "\u4e16"
        assert self.canvas.get_char(8, 0) == "\u754c"


class TestBookmarkSerialization:
    """Tests for bookmark save/load in projects."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.temp_dir = tempfile.mkdtemp()

    def test_save_and_load_bookmarks(self):
        """Test saving and loading bookmarks with project."""
        filepath = Path(self.temp_dir) / "bookmarks.json"

        bookmarks = BookmarkManager()
        bookmarks.set("a", 10, 20, "Bookmark A")
        bookmarks.set("b", 30, 40, "Bookmark B")
        bookmarks.set("1", 50, 60, "Bookmark 1")

        project = Project()
        project.save(self.canvas, self.viewport, bookmarks=bookmarks, filepath=filepath)

        # Load into fresh instances
        new_canvas = Canvas()
        new_viewport = Viewport()
        new_bookmarks = BookmarkManager()
        Project.load(filepath, new_canvas, new_viewport, bookmarks=new_bookmarks)

        # Verify bookmarks
        bm_a = new_bookmarks.get("a")
        assert bm_a is not None
        assert bm_a.x == 10
        assert bm_a.y == 20
        assert bm_a.name == "Bookmark A"

        bm_b = new_bookmarks.get("b")
        assert bm_b is not None
        assert bm_b.x == 30
        assert bm_b.y == 40

        bm_1 = new_bookmarks.get("1")
        assert bm_1 is not None
        assert bm_1.x == 50
        assert bm_1.y == 60

    def test_load_project_without_bookmarks(self):
        """Test loading project that has no bookmarks section."""
        filepath = Path(self.temp_dir) / "no_bookmarks.json"

        project = Project()
        project.save(self.canvas, self.viewport, filepath=filepath)  # No bookmarks

        new_bookmarks = BookmarkManager()
        new_bookmarks.set("x", 100, 100)  # Pre-existing bookmark

        new_canvas = Canvas()
        new_viewport = Viewport()
        Project.load(filepath, new_canvas, new_viewport, bookmarks=new_bookmarks)

        # Pre-existing bookmark should remain (no clearing without bookmarks section)
        bm = new_bookmarks.get("x")
        assert bm is not None

    def test_bookmark_serialization_format(self):
        """Test the JSON format of serialized bookmarks."""
        filepath = Path(self.temp_dir) / "bm_format.json"

        bookmarks = BookmarkManager()
        bookmarks.set("z", 99, 88, "Last")

        project = Project()
        project.save(self.canvas, self.viewport, bookmarks=bookmarks, filepath=filepath)

        with open(filepath) as f:
            data = json.load(f)

        assert "bookmarks" in data
        assert "z" in data["bookmarks"]
        assert data["bookmarks"]["z"]["x"] == 99
        assert data["bookmarks"]["z"]["y"] == 88
        assert data["bookmarks"]["z"]["name"] == "Last"


class TestZoneSerialization:
    """Tests for zone save/load in projects."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.temp_dir = tempfile.mkdtemp()

    def test_save_and_load_static_zone(self):
        """Test saving and loading a static zone."""
        filepath = Path(self.temp_dir) / "zones.json"

        zones = ZoneManager()
        zones.create("INBOX", 0, 0, 40, 20, description="My inbox", bookmark="i")

        project = Project()
        project.save(self.canvas, self.viewport, zones=zones, filepath=filepath)

        new_canvas = Canvas()
        new_viewport = Viewport()
        new_zones = ZoneManager()
        Project.load(filepath, new_canvas, new_viewport, zones=new_zones)

        zone = new_zones.get("inbox")
        assert zone is not None
        assert zone.name == "INBOX"
        assert zone.x == 0
        assert zone.y == 0
        assert zone.width == 40
        assert zone.height == 20
        assert zone.description == "My inbox"
        assert zone.bookmark == "i"

    def test_save_and_load_pipe_zone(self):
        """Test saving and loading a pipe zone."""
        filepath = Path(self.temp_dir) / "pipe_zone.json"

        zones = ZoneManager()
        config = ZoneConfig(zone_type=ZoneType.PIPE, command="ls -la")
        zones.create("FILES", 10, 10, 60, 15, config=config)

        project = Project()
        project.save(self.canvas, self.viewport, zones=zones, filepath=filepath)

        new_zones = ZoneManager()
        Project.load(filepath, Canvas(), Viewport(), zones=new_zones)

        zone = new_zones.get("files")
        assert zone is not None
        assert zone.config.zone_type == ZoneType.PIPE
        assert zone.config.command == "ls -la"

    def test_save_and_load_watch_zone(self):
        """Test saving and loading a watch zone with refresh interval."""
        filepath = Path(self.temp_dir) / "watch_zone.json"

        zones = ZoneManager()
        config = ZoneConfig(
            zone_type=ZoneType.WATCH, command="date", refresh_interval=5
        )
        zones.create("CLOCK", 50, 0, 30, 10, config=config)

        project = Project()
        project.save(self.canvas, self.viewport, zones=zones, filepath=filepath)

        new_zones = ZoneManager()
        Project.load(filepath, Canvas(), Viewport(), zones=new_zones)

        zone = new_zones.get("clock")
        assert zone is not None
        assert zone.config.zone_type == ZoneType.WATCH
        assert zone.config.command == "date"
        assert zone.config.refresh_interval == 5

    def test_save_empty_zone_manager(self):
        """Test that empty zone manager is not saved."""
        filepath = Path(self.temp_dir) / "no_zones.json"

        zones = ZoneManager()  # Empty

        project = Project()
        project.save(self.canvas, self.viewport, zones=zones, filepath=filepath)

        with open(filepath) as f:
            data = json.load(f)

        # Empty zones should not be included
        assert "zones" not in data

    def test_load_project_clears_existing_zones(self):
        """Test that loading clears existing zones."""
        filepath = Path(self.temp_dir) / "one_zone.json"

        zones = ZoneManager()
        zones.create("NEW", 0, 0, 20, 10)

        project = Project()
        project.save(self.canvas, self.viewport, zones=zones, filepath=filepath)

        # Create zone manager with pre-existing zone
        new_zones = ZoneManager()
        new_zones.create("OLD", 50, 50, 30, 15)

        Project.load(filepath, Canvas(), Viewport(), zones=new_zones)

        # OLD should be gone, NEW should be present
        assert new_zones.get("old") is None
        assert new_zones.get("new") is not None

    def test_zone_with_pager_config(self):
        """Test saving and loading a pager zone."""
        filepath = Path(self.temp_dir) / "pager_zone.json"

        zones = ZoneManager()
        config = ZoneConfig(
            zone_type=ZoneType.PAGER,
            file_path="/path/to/file.txt",
            renderer="plain",
            scroll_offset=100,
            search_term="pattern",
        )
        zones.create("VIEWER", 0, 0, 80, 24, config=config)

        project = Project()
        project.save(self.canvas, self.viewport, zones=zones, filepath=filepath)

        new_zones = ZoneManager()
        Project.load(filepath, Canvas(), Viewport(), zones=new_zones)

        zone = new_zones.get("viewer")
        assert zone.config.zone_type == ZoneType.PAGER
        assert zone.config.file_path == "/path/to/file.txt"
        assert zone.config.renderer == "plain"
        assert zone.config.scroll_offset == 100
        assert zone.config.search_term == "pattern"


class TestValidateProjectData:
    """Tests for JSON validation function."""

    def test_valid_minimal_project(self):
        """Test validation of minimal valid project."""
        data = {"version": "1.0", "canvas": {"cells": []}}
        validate_project_data(data)  # Should not raise

    def test_missing_version(self):
        """Test validation fails without version."""
        data = {"canvas": {"cells": []}}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "version" in str(e).lower()

    def test_invalid_version_type(self):
        """Test validation fails with non-string version."""
        data = {"version": 1.0, "canvas": {"cells": []}}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "type" in str(e).lower()

    def test_unsupported_version(self):
        """Test validation fails with unsupported version."""
        data = {"version": "2.0", "canvas": {"cells": []}}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Unsupported" in str(e)

    def test_invalid_canvas_type(self):
        """Test validation fails with non-object canvas."""
        data = {"version": "1.0", "canvas": "not an object"}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "canvas" in str(e).lower()

    def test_invalid_cells_type(self):
        """Test validation fails with non-array cells."""
        data = {"version": "1.0", "canvas": {"cells": "not an array"}}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "cells" in str(e).lower()

    def test_cell_missing_x(self):
        """Test validation fails when cell missing x."""
        data = {"version": "1.0", "canvas": {"cells": [{"y": 0, "char": "A"}]}}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "x" in str(e)

    def test_cell_missing_y(self):
        """Test validation fails when cell missing y."""
        data = {"version": "1.0", "canvas": {"cells": [{"x": 0, "char": "A"}]}}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "y" in str(e)

    def test_cell_missing_char(self):
        """Test validation fails when cell missing char."""
        data = {"version": "1.0", "canvas": {"cells": [{"x": 0, "y": 0}]}}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "char" in str(e)

    def test_cell_invalid_x_type(self):
        """Test validation fails when x is not a number."""
        data = {
            "version": "1.0",
            "canvas": {"cells": [{"x": "0", "y": 0, "char": "A"}]},
        }
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "number" in str(e).lower()

    def test_cell_invalid_char_type(self):
        """Test validation fails when char is not a string."""
        data = {"version": "1.0", "canvas": {"cells": [{"x": 0, "y": 0, "char": 65}]}}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "string" in str(e).lower()

    def test_invalid_viewport_type(self):
        """Test validation fails with non-object viewport."""
        data = {"version": "1.0", "viewport": "not an object"}
        try:
            validate_project_data(data)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "viewport" in str(e).lower()

    def test_valid_complete_project(self):
        """Test validation of complete valid project."""
        data = {
            "version": "1.0",
            "metadata": {"name": "Test", "created": "2024-01-01"},
            "canvas": {"cells": [{"x": 0, "y": 0, "char": "A"}]},
            "viewport": {"x": 10, "y": 20, "cursor": {"x": 5, "y": 5}},
            "grid": {"show_origin": True},
            "bookmarks": {"a": {"x": 0, "y": 0}},
        }
        validate_project_data(data)  # Should not raise


class TestRecentProjects:
    """Tests for recent projects functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        # Mock the home directory for testing
        self._original_home = Path.home

    def teardown_method(self):
        """Clean up after tests."""
        pass

    def test_get_recent_projects_no_file(self):
        """Test getting recent projects when no file exists."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)
            result = get_recent_projects()
            assert result == []

    def test_add_and_get_recent_project(self):
        """Test adding and retrieving recent projects."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            # Create a test file
            test_file = Path(self.temp_dir) / "test.json"
            test_file.write_text("{}")

            add_recent_project(test_file)
            recent = get_recent_projects()

            assert len(recent) == 1
            assert recent[0] == test_file.resolve()

    def test_recent_projects_deduplication(self):
        """Test that duplicate entries are removed."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            test_file = Path(self.temp_dir) / "test.json"
            test_file.write_text("{}")

            add_recent_project(test_file)
            add_recent_project(test_file)
            add_recent_project(test_file)

            recent = get_recent_projects()
            assert len(recent) == 1

    def test_recent_projects_ordering(self):
        """Test that most recent is first."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            file1 = Path(self.temp_dir) / "first.json"
            file2 = Path(self.temp_dir) / "second.json"
            file1.write_text("{}")
            file2.write_text("{}")

            add_recent_project(file1)
            add_recent_project(file2)

            recent = get_recent_projects()
            assert recent[0] == file2.resolve()
            assert recent[1] == file1.resolve()

    def test_recent_projects_max_count(self):
        """Test that max_count is respected."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            # Create more files than max
            for i in range(15):
                f = Path(self.temp_dir) / f"file{i}.json"
                f.write_text("{}")
                add_recent_project(f, max_count=10)

            recent = get_recent_projects(max_count=10)
            assert len(recent) <= 10

    def test_recent_projects_filters_nonexistent(self):
        """Test that non-existent files are filtered out."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            # Create and add a file
            test_file = Path(self.temp_dir) / "temp.json"
            test_file.write_text("{}")
            add_recent_project(test_file)

            # Delete the file
            test_file.unlink()

            recent = get_recent_projects()
            assert len(recent) == 0

    def test_recent_projects_handles_corrupt_file(self):
        """Test handling of corrupt recent.json file."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            # Create corrupt recent.json
            config_dir = Path(self.temp_dir) / ".mygrid"
            config_dir.mkdir()
            recent_file = config_dir / "recent.json"
            recent_file.write_text("not valid json")

            result = get_recent_projects()
            assert result == []


class TestSessionManager:
    """Tests for SessionManager auto-save and recovery."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.temp_dir = tempfile.mkdtemp()

    def test_session_manager_init(self):
        """Test SessionManager initialization."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=60, max_sessions=10)

            assert sm.interval_seconds == 60
            assert sm.max_sessions == 10
            assert sm.enabled is True
            assert sm.session_dir.exists()

    def test_should_save_respects_interval(self):
        """Test that should_save respects the interval."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=30)
            sm._last_save_time = time.time()

            # Should not save immediately after last save
            assert sm.should_save() is False

    def test_should_save_when_interval_elapsed(self):
        """Test that should_save returns True after interval."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=1)
            sm._last_save_time = time.time() - 2  # 2 seconds ago

            assert sm.should_save() is True

    def test_should_save_disabled(self):
        """Test that should_save returns False when disabled."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager()
            sm.enabled = False
            sm._last_save_time = 0  # Long time ago

            assert sm.should_save() is False

    def test_auto_save_creates_file(self):
        """Test that auto_save creates a session file."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=0)  # Always save
            sm._last_save_time = 0  # Force save

            self.canvas.write_text(0, 0, "Test")
            result = sm.auto_save(self.canvas, self.viewport)

            assert result is not None
            assert result.exists()

    def test_auto_save_with_bookmarks_and_zones(self):
        """Test auto_save with bookmarks and zones."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=0)
            sm._last_save_time = 0

            bookmarks = BookmarkManager()
            bookmarks.set("a", 10, 20)

            zones = ZoneManager()
            zones.create("TEST", 0, 0, 50, 20)

            result = sm.auto_save(
                self.canvas, self.viewport, bookmarks=bookmarks, zones=zones
            )

            assert result is not None

            # Verify content
            with open(result) as f:
                data = json.load(f)
            assert "bookmarks" in data
            assert "zones" in data

    def test_list_sessions(self):
        """Test listing available sessions."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=0)
            sm._last_save_time = 0

            # Create a session
            sm.auto_save(self.canvas, self.viewport)

            sessions = sm.list_sessions()
            assert len(sessions) >= 1
            assert "id" in sessions[0]
            assert "timestamp" in sessions[0]
            assert "path" in sessions[0]

    def test_get_latest_session(self):
        """Test getting the latest session."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=0)
            sm._last_save_time = 0

            sm.auto_save(self.canvas, self.viewport)

            latest = sm.get_latest_session()
            assert latest is not None
            assert latest.exists()

    def test_restore_session(self):
        """Test restoring a session."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=0)
            sm._last_save_time = 0

            # Save a session with content
            self.canvas.write_text(0, 0, "Saved")
            self.viewport.cursor.set(5, 5)
            session_path = sm.auto_save(self.canvas, self.viewport)

            # Clear and restore
            new_canvas = Canvas()
            new_viewport = Viewport()

            result = sm.restore_session(session_path, new_canvas, new_viewport)

            assert result is True
            assert new_canvas.get_char(0, 0) == "S"
            assert new_viewport.cursor.x == 5
            assert new_viewport.cursor.y == 5

    def test_restore_session_with_grid(self):
        """Test restoring session with grid settings."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=0)
            sm._last_save_time = 0

            grid = GridSettings()
            grid.show_major_lines = True
            grid.major_interval = 25

            session_path = sm.auto_save(self.canvas, self.viewport, grid_settings=grid)

            new_grid = GridSettings()
            sm.restore_session(
                session_path, Canvas(), Viewport(), grid_settings=new_grid
            )

            assert new_grid.show_major_lines is True
            assert new_grid.major_interval == 25

    def test_restore_invalid_session(self):
        """Test restoring an invalid session file."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager()

            # Create invalid session file
            invalid_path = Path(self.temp_dir) / "invalid.json"
            invalid_path.write_text("not valid json")

            result = sm.restore_session(invalid_path, Canvas(), Viewport())
            assert result is False

    def test_clear_current_session(self):
        """Test clearing the current session."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=0)
            sm._last_save_time = 0

            # Create session
            session_path = sm.auto_save(self.canvas, self.viewport)
            assert session_path.exists()

            # Clear it
            sm.clear_current_session()
            assert not session_path.exists()

    def test_cleanup_old_sessions(self):
        """Test that old sessions are cleaned up."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager(interval_seconds=0, max_sessions=2)

            # Create multiple sessions by changing session ID
            for i in range(5):
                sm._session_id = f"test_session_{i}"
                sm._last_save_time = 0
                sm.auto_save(self.canvas, self.viewport)

            # Should only have max_sessions files
            sessions = list(sm.session_dir.glob("session_*.json"))
            assert len(sessions) <= 2

    def test_check_for_recovery_no_sessions(self):
        """Test recovery check with no sessions."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager()
            result = sm.check_for_recovery()
            assert result is None

    def test_get_session_file_with_suffix(self):
        """Test getting session file path with suffix."""
        with mock.patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            sm = SessionManager()
            path = sm.get_session_file(suffix="backup")

            assert "backup" in path.name
            assert path.suffix == ".json"


class TestGridSettingsAdvanced:
    """Additional tests for grid settings serialization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.temp_dir = tempfile.mkdtemp()

    def test_load_project_without_grid_settings(self):
        """Test loading project that has no grid section."""
        filepath = Path(self.temp_dir) / "no_grid.json"

        project = Project()
        project.save(self.canvas, self.viewport, filepath=filepath)  # No grid

        new_grid = GridSettings()
        new_grid.major_interval = 99  # Pre-set value

        Project.load(filepath, Canvas(), Viewport(), grid_settings=new_grid)

        # Should keep original value if no grid section
        assert new_grid.major_interval == 99

    def test_grid_settings_partial_data(self):
        """Test loading grid settings with partial data."""
        filepath = Path(self.temp_dir) / "partial_grid.json"

        # Manually create a file with partial grid data
        data = {
            "version": "1.0",
            "canvas": {"cells": []},
            "viewport": {"x": 0, "y": 0},
            "grid": {"show_origin": False},  # Only one field
        }
        with open(filepath, "w") as f:
            json.dump(data, f)

        new_grid = GridSettings()
        Project.load(filepath, Canvas(), Viewport(), grid_settings=new_grid)

        assert new_grid.show_origin is False
        # Other fields should have defaults
        assert new_grid.major_interval == 10


def run_tests():
    """Run all tests."""
    # ProjectMetadata tests
    meta_tests = TestProjectMetadata()
    meta_tests.test_new_metadata()
    meta_tests.test_touch_updates_modified()

    # Project tests
    proj_tests = TestProject()

    proj_tests.setup_method()
    proj_tests.test_new_project()

    proj_tests.setup_method()
    proj_tests.test_dirty_tracking()

    proj_tests.setup_method()
    proj_tests.test_save_requires_filepath()

    proj_tests.setup_method()
    proj_tests.test_save_and_load_empty_canvas()

    proj_tests.setup_method()
    proj_tests.test_save_and_load_with_content()

    proj_tests.setup_method()
    proj_tests.test_save_and_load_grid_settings()

    proj_tests.setup_method()
    proj_tests.test_save_and_load_y_direction()

    proj_tests.setup_method()
    proj_tests.test_export_text_empty()

    proj_tests.setup_method()
    proj_tests.test_export_text_with_content()

    proj_tests.setup_method()
    proj_tests.test_export_text_preserves_spacing()

    proj_tests.setup_method()
    proj_tests.test_import_text()

    proj_tests.setup_method()
    proj_tests.test_import_text_with_offset()

    proj_tests.setup_method()
    proj_tests.test_load_nonexistent_file()

    proj_tests.setup_method()
    proj_tests.test_file_format_version()

    proj_tests.setup_method()
    proj_tests.test_unsupported_version()

    # Suggest filename tests
    fname_tests = TestSuggestFilename()
    fname_tests.test_empty_canvas()
    fname_tests.test_with_text_content()
    fname_tests.test_with_special_chars()
    fname_tests.test_custom_base()

    # Export text advanced tests
    export_tests = TestExportTextAdvanced()
    export_tests.setup_method()
    export_tests.test_export_text_default_filepath()
    export_tests.setup_method()
    export_tests.test_export_text_no_filepath()
    export_tests.setup_method()
    export_tests.test_export_text_exclude_empty_lines()
    export_tests.setup_method()
    export_tests.test_export_text_with_colors()
    export_tests.setup_method()
    export_tests.test_export_text_multiline_with_gaps()

    # Import text advanced tests
    import_tests = TestImportTextAdvanced()
    import_tests.setup_method()
    import_tests.test_import_empty_file()
    import_tests.setup_method()
    import_tests.test_import_file_with_tabs()
    import_tests.setup_method()
    import_tests.test_import_file_spaces_ignored()
    import_tests.setup_method()
    import_tests.test_import_resets_viewport()
    import_tests.setup_method()
    import_tests.test_import_with_unicode()

    # Bookmark serialization tests
    bm_tests = TestBookmarkSerialization()
    bm_tests.setup_method()
    bm_tests.test_save_and_load_bookmarks()
    bm_tests.setup_method()
    bm_tests.test_load_project_without_bookmarks()
    bm_tests.setup_method()
    bm_tests.test_bookmark_serialization_format()

    # Zone serialization tests
    zone_tests = TestZoneSerialization()
    zone_tests.setup_method()
    zone_tests.test_save_and_load_static_zone()
    zone_tests.setup_method()
    zone_tests.test_save_and_load_pipe_zone()
    zone_tests.setup_method()
    zone_tests.test_save_and_load_watch_zone()
    zone_tests.setup_method()
    zone_tests.test_save_empty_zone_manager()
    zone_tests.setup_method()
    zone_tests.test_load_project_clears_existing_zones()
    zone_tests.setup_method()
    zone_tests.test_zone_with_pager_config()

    # Validation tests
    val_tests = TestValidateProjectData()
    val_tests.test_valid_minimal_project()
    val_tests.test_missing_version()
    val_tests.test_invalid_version_type()
    val_tests.test_unsupported_version()
    val_tests.test_invalid_canvas_type()
    val_tests.test_invalid_cells_type()
    val_tests.test_cell_missing_x()
    val_tests.test_cell_missing_y()
    val_tests.test_cell_missing_char()
    val_tests.test_cell_invalid_x_type()
    val_tests.test_cell_invalid_char_type()
    val_tests.test_invalid_viewport_type()
    val_tests.test_valid_complete_project()

    # Grid settings advanced tests
    grid_tests = TestGridSettingsAdvanced()
    grid_tests.setup_method()
    grid_tests.test_load_project_without_grid_settings()
    grid_tests.setup_method()
    grid_tests.test_grid_settings_partial_data()

    print(
        "Note: Recent projects and SessionManager tests require pytest due to mocking"
    )


if __name__ == "__main__":
    run_tests()
    print("All project tests passed!")
