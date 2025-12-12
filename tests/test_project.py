"""Tests for project save/load functionality."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from canvas import Canvas
from viewport import Viewport, YAxisDirection
from renderer import GridSettings
from project import (
    Project, ProjectMetadata, PROJECT_VERSION,
    suggest_filename
)


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
        import time
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
        self.canvas.set(0, 0, 'A')
        self.canvas.set(10, 5, 'B')
        self.canvas.set(-5, -5, 'C')

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
        assert new_canvas.get_char(0, 0) == 'A'
        assert new_canvas.get_char(10, 5) == 'B'
        assert new_canvas.get_char(-5, -5) == 'C'
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
        loaded = Project.load(filepath, new_canvas, new_viewport, grid_settings=new_grid)

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
        lines = content.strip().split('\n')
        assert lines[0] == "Hello"
        assert lines[1] == "World"

    def test_export_text_preserves_spacing(self):
        filepath = Path(self.temp_dir) / "spaced.txt"

        self.canvas.set(0, 0, 'A')
        self.canvas.set(5, 0, 'B')  # Gap of 4 spaces

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

        assert new_canvas.get_char(0, 0) == 'L'
        assert new_canvas.get_char(5, 0) == '1'
        assert new_canvas.get_char(0, 1) == 'L'
        assert new_canvas.get_char(2, 2) == 'I'  # "  Indented"

        # Import should mark as dirty (needs Save As)
        assert project.dirty
        assert project.filepath is None

    def test_import_text_with_offset(self):
        filepath = Path(self.temp_dir) / "offset.txt"
        filepath.write_text("X")

        new_canvas = Canvas()
        new_viewport = Viewport()
        project = Project.import_text(
            filepath, new_canvas, new_viewport,
            start_x=10, start_y=20
        )

        assert new_canvas.get_char(10, 20) == 'X'
        assert new_canvas.is_empty_at(0, 0)

    def test_load_nonexistent_file(self):
        try:
            Project.load(
                Path(self.temp_dir) / "nonexistent.json",
                self.canvas,
                self.viewport
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
        with open(filepath, 'w') as f:
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


if __name__ == "__main__":
    run_tests()
    print("All project tests passed!")
