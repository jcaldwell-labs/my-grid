"""Tests for external tool integration."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import external
from external import (
    ExternalToolResult,
    tool_available,
    get_boxes_styles,
    draw_box,
    remove_box,
    get_figlet_fonts,
    draw_figlet,
    pipe_command,
    write_lines_to_canvas,
    get_tool_status,
)


# =============================================================================
# Mock Canvas for testing
# =============================================================================


class MockCanvas:
    """Simple mock canvas for testing."""

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
# ExternalToolResult Tests
# =============================================================================


class TestExternalToolResult:
    """Tests for ExternalToolResult dataclass."""

    def test_success_result(self):
        result = ExternalToolResult(success=True, lines=["line1", "line2"])
        assert result.success is True
        assert result.lines == ["line1", "line2"]
        assert result.error == ""

    def test_error_result(self):
        result = ExternalToolResult(
            success=False, lines=[], error="Something went wrong"
        )
        assert result.success is False
        assert result.lines == []
        assert result.error == "Something went wrong"


# =============================================================================
# tool_available Tests
# =============================================================================


class TestToolAvailable:
    """Tests for tool_available function."""

    def test_tool_available_true(self):
        with patch("shutil.which", return_value="/usr/bin/boxes"):
            assert tool_available("boxes") is True

    def test_tool_available_false(self):
        with patch("shutil.which", return_value=None):
            assert tool_available("nonexistent") is False


# =============================================================================
# Boxes Integration Tests
# =============================================================================


class TestGetBoxesStyles:
    """Tests for get_boxes_styles function."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset the boxes styles cache before each test."""
        external._boxes_styles_cache = None
        yield
        external._boxes_styles_cache = None

    def test_get_boxes_styles_tool_not_available(self):
        with patch.object(external, "tool_available", return_value=False):
            styles = get_boxes_styles()
            assert styles == []
            # Check cache was set
            assert external._boxes_styles_cache == []

    def test_get_boxes_styles_success(self):
        mock_result = MagicMock()
        mock_result.stdout = """ansi
c (alias: cc, c-ansi)
html
java-doc
simple"""
        mock_result.returncode = 0

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                styles = get_boxes_styles()
                assert "ansi" in styles
                assert "c" in styles
                assert "html" in styles
                assert "simple" in styles

    def test_get_boxes_styles_cached(self):
        external._boxes_styles_cache = ["cached1", "cached2"]
        # Should return cached value without calling subprocess
        styles = get_boxes_styles()
        assert styles == ["cached1", "cached2"]

    def test_get_boxes_styles_timeout(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("boxes", 5)
            ):
                styles = get_boxes_styles()
                assert styles == []
                assert external._boxes_styles_cache == []

    def test_get_boxes_styles_subprocess_error(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.SubprocessError("Error")
            ):
                styles = get_boxes_styles()
                assert styles == []


class TestDrawBox:
    """Tests for draw_box function."""

    def test_draw_box_tool_not_available(self):
        with patch.object(external, "tool_available", return_value=False):
            result = draw_box("Hello")
            assert result.success is False
            assert result.lines == []
            assert "boxes command not found" in result.error

    def test_draw_box_success(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """+-------+
| Hello |
+-------+
"""

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = draw_box("Hello", style="ansi")
                assert result.success is True
                assert len(result.lines) == 3
                assert "+-------+" in result.lines[0]
                assert "Hello" in result.lines[1]

    def test_draw_box_error_returncode(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Unknown style"

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = draw_box("Hello", style="invalid")
                assert result.success is False
                assert "Unknown style" in result.error

    def test_draw_box_error_returncode_no_stderr(self):
        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stderr = ""

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = draw_box("Hello", style="invalid")
                assert result.success is False
                assert "exited with code 2" in result.error

    def test_draw_box_timeout(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("boxes", 5)
            ):
                result = draw_box("Hello")
                assert result.success is False
                assert "timed out" in result.error

    def test_draw_box_subprocess_error(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run",
                side_effect=subprocess.SubprocessError("Process error"),
            ):
                result = draw_box("Hello")
                assert result.success is False
                assert "Process error" in result.error


class TestRemoveBox:
    """Tests for remove_box function."""

    def test_remove_box_tool_not_available(self):
        with patch.object(external, "tool_available", return_value=False):
            result = remove_box("+---+\n|Hi|\n+---+")
            assert result.success is False
            assert "boxes command not found" in result.error

    def test_remove_box_success(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello World\n"

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = remove_box("+-------+\n| Hello |\n+-------+", style="ansi")
                assert result.success is True
                assert result.lines == ["Hello World"]

    def test_remove_box_error_returncode(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid box format"

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = remove_box("invalid", style="ansi")
                assert result.success is False
                assert "Invalid box format" in result.error

    def test_remove_box_timeout(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("boxes", 5)
            ):
                result = remove_box("+---+\n|Hi|\n+---+")
                assert result.success is False

    def test_remove_box_subprocess_error(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.SubprocessError("Error")
            ):
                result = remove_box("+---+\n|Hi|\n+---+")
                assert result.success is False


# =============================================================================
# Figlet Integration Tests
# =============================================================================


class TestGetFigletFonts:
    """Tests for get_figlet_fonts function."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset the figlet fonts cache before each test."""
        external._figlet_fonts_cache = None
        yield
        external._figlet_fonts_cache = None

    def test_get_figlet_fonts_tool_not_available(self):
        with patch.object(external, "tool_available", return_value=False):
            fonts = get_figlet_fonts()
            assert fonts == []
            assert external._figlet_fonts_cache == []

    def test_get_figlet_fonts_success(self):
        mock_result = MagicMock()
        mock_result.stdout = "/usr/share/figlet/fonts"
        mock_result.returncode = 0

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                fonts = get_figlet_fonts()
                # Should return the hardcoded list of common fonts
                assert "standard" in fonts
                assert "banner" in fonts
                assert "big" in fonts
                assert "slant" in fonts

    def test_get_figlet_fonts_cached(self):
        external._figlet_fonts_cache = ["custom1", "custom2"]
        fonts = get_figlet_fonts()
        assert fonts == ["custom1", "custom2"]

    def test_get_figlet_fonts_timeout(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("figlet", 5)
            ):
                fonts = get_figlet_fonts()
                assert fonts == []

    def test_get_figlet_fonts_subprocess_error(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.SubprocessError("Error")
            ):
                fonts = get_figlet_fonts()
                assert fonts == []


class TestDrawFiglet:
    """Tests for draw_figlet function."""

    def test_draw_figlet_tool_not_available(self):
        with patch.object(external, "tool_available", return_value=False):
            result = draw_figlet("Hello")
            assert result.success is False
            assert "figlet command not found" in result.error

    def test_draw_figlet_success_standard_font(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """ _   _      _ _
| | | | ___| | | ___
| |_| |/ _ \\ | |/ _ \\
|  _  |  __/ | | (_) |
|_| |_|\\___|_|_|\\___/
"""

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = draw_figlet("Hello", font="standard")
                assert result.success is True
                assert len(result.lines) > 0
                # Should not include -f flag for standard font
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert "-f" not in cmd

    def test_draw_figlet_success_custom_font(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "BIG HELLO\n"

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = draw_figlet("Hello", font="banner")
                assert result.success is True
                # Should include -f flag for non-standard font
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert "-f" in cmd
                assert "banner" in cmd

    def test_draw_figlet_error_returncode(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Unknown font"

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = draw_figlet("Hello", font="invalid")
                assert result.success is False
                assert "Unknown font" in result.error

    def test_draw_figlet_error_returncode_no_stderr(self):
        mock_result = MagicMock()
        mock_result.returncode = 3
        mock_result.stderr = ""

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = draw_figlet("Hello", font="invalid")
                assert result.success is False
                assert "exited with code 3" in result.error

    def test_draw_figlet_timeout(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("figlet", 5)
            ):
                result = draw_figlet("Hello")
                assert result.success is False
                assert "timed out" in result.error

    def test_draw_figlet_subprocess_error(self):
        with patch.object(external, "tool_available", return_value=True):
            with patch(
                "subprocess.run", side_effect=subprocess.SubprocessError("Figlet error")
            ):
                result = draw_figlet("Hello")
                assert result.success is False
                assert "Figlet error" in result.error


# =============================================================================
# Pipe Command Tests
# =============================================================================


class TestPipeCommand:
    """Tests for pipe_command function."""

    def test_pipe_command_success(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "line1\nline2\nline3\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = pipe_command("echo test")
            assert result.success is True
            assert result.lines == ["line1", "line2", "line3"]
            assert result.error == ""

    def test_pipe_command_with_stderr(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output\n"
        mock_result.stderr = "warning\n"

        with patch("subprocess.run", return_value=mock_result):
            result = pipe_command("some command")
            assert result.success is True
            assert "output" in result.lines[0]
            assert "--- stderr ---" in "\n".join(result.lines)
            assert "warning" in "\n".join(result.lines)

    def test_pipe_command_only_stderr(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = "error output\n"

        with patch("subprocess.run", return_value=mock_result):
            result = pipe_command("some command")
            assert result.success is True
            assert "error output" in result.lines[0]

    def test_pipe_command_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "command failed\n"

        with patch("subprocess.run", return_value=mock_result):
            result = pipe_command("bad command")
            assert result.success is False
            assert "Exit code: 1" in result.error

    def test_pipe_command_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
            result = pipe_command("slow command", timeout=10)
            assert result.success is False
            assert "timed out after 10s" in result.error

    def test_pipe_command_subprocess_error(self):
        with patch(
            "subprocess.run",
            side_effect=subprocess.SubprocessError("Subprocess failed"),
        ):
            result = pipe_command("broken command")
            assert result.success is False
            assert "Subprocess failed" in result.error

    def test_pipe_command_custom_timeout(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "done\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = pipe_command("test", timeout=30)
            assert result.success is True
            mock_run.assert_called_once()
            _, kwargs = mock_run.call_args
            assert kwargs["timeout"] == 30

    def test_pipe_command_shell_false(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "result\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = pipe_command("echo test", shell=False)
            assert result.success is True
            mock_run.assert_called_once()
            _, kwargs = mock_run.call_args
            assert kwargs["shell"] is False


# =============================================================================
# Canvas Helper Tests
# =============================================================================


class TestWriteLinesToCanvas:
    """Tests for write_lines_to_canvas function."""

    def test_write_lines_empty(self):
        canvas = MockCanvas()
        width, height = write_lines_to_canvas(canvas, [], 0, 0)
        assert width == 0
        assert height == 0
        assert len(canvas._cells) == 0

    def test_write_lines_single_line(self):
        canvas = MockCanvas()
        width, height = write_lines_to_canvas(canvas, ["Hello"], 5, 10)
        assert width == 5
        assert height == 1
        assert canvas.get_char(5, 10) == "H"
        assert canvas.get_char(6, 10) == "e"
        assert canvas.get_char(7, 10) == "l"
        assert canvas.get_char(8, 10) == "l"
        assert canvas.get_char(9, 10) == "o"

    def test_write_lines_multiple_lines(self):
        canvas = MockCanvas()
        lines = ["Hi", "World"]
        width, height = write_lines_to_canvas(canvas, lines, 0, 0)
        assert width == 5  # "World" is longest
        assert height == 2
        assert canvas.get_char(0, 0) == "H"
        assert canvas.get_char(1, 0) == "i"
        assert canvas.get_char(0, 1) == "W"

    def test_write_lines_skips_spaces(self):
        canvas = MockCanvas()
        canvas.set(0, 0, "X")  # Pre-existing character
        lines = ["A B"]
        write_lines_to_canvas(canvas, lines, 0, 0)
        assert canvas.get_char(0, 0) == "A"
        assert canvas.get_char(1, 0) == " "  # Space was skipped, original cleared
        assert canvas.get_char(2, 0) == "B"

    def test_write_lines_clear_area(self):
        canvas = MockCanvas()
        # Pre-populate some cells
        canvas.set(0, 0, "X")
        canvas.set(1, 0, "Y")
        canvas.set(2, 0, "Z")
        canvas.set(0, 1, "A")
        canvas.set(1, 1, "B")

        # Use lines that cover a wider area to test clearing
        lines = ["Hi!", "AB"]  # 3 chars wide, 2 lines tall
        write_lines_to_canvas(canvas, lines, 0, 0, clear_area=True)

        # Verify new content was written
        assert canvas.get_char(0, 0) == "H"
        assert canvas.get_char(1, 0) == "i"
        assert canvas.get_char(2, 0) == "!"
        assert canvas.get_char(0, 1) == "A"
        assert canvas.get_char(1, 1) == "B"
        # Cell at (2, 1) should be cleared since it's within the 3x2 area
        # but no new content was written there (only "AB" which is 2 chars)
        assert (2, 1) not in canvas._cells

    def test_write_lines_at_position(self):
        canvas = MockCanvas()
        lines = ["Test"]
        width, height = write_lines_to_canvas(canvas, lines, 100, 200)
        assert width == 4
        assert height == 1
        assert canvas.get_char(100, 200) == "T"
        assert canvas.get_char(103, 200) == "t"


# =============================================================================
# Tool Status Tests
# =============================================================================


class TestGetToolStatus:
    """Tests for get_tool_status function."""

    def test_get_tool_status_all_available(self):
        with patch.object(external, "tool_available", return_value=True):
            status = get_tool_status()
            assert status["boxes"] is True
            assert status["figlet"] is True

    def test_get_tool_status_none_available(self):
        with patch.object(external, "tool_available", return_value=False):
            status = get_tool_status()
            assert status["boxes"] is False
            assert status["figlet"] is False

    def test_get_tool_status_partial(self):
        def mock_available(name):
            return name == "boxes"

        with patch.object(external, "tool_available", side_effect=mock_available):
            status = get_tool_status()
            assert status["boxes"] is True
            assert status["figlet"] is False


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================


class TestEdgeCases:
    """Edge case and integration tests."""

    def test_draw_box_removes_trailing_empty_lines(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "+---+\n|Hi|\n+---+\n\n\n"

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = draw_box("Hi")
                assert result.success is True
                # Trailing empty lines should be removed
                assert result.lines[-1] != ""
                assert len(result.lines) == 3

    def test_draw_figlet_removes_trailing_empty_lines(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ASCII ART\nLINE 2\n\n\n"

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = draw_figlet("Test")
                assert result.success is True
                assert result.lines[-1] != ""
                assert len(result.lines) == 2

    def test_pipe_command_removes_trailing_empty_lines(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "line1\nline2\n\n\n\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = pipe_command("test")
            assert result.success is True
            assert result.lines[-1] != ""
            assert len(result.lines) == 2

    def test_boxes_styles_parsing_filters_non_alphanumeric(self):
        """Test that style parsing correctly handles various line formats."""
        external._boxes_styles_cache = None
        mock_result = MagicMock()
        # Simulate boxes -l output with various formats
        mock_result.stdout = """ansi
--- comment line ---
(skipped line)
c-cmt
simple123
  indented
java-doc (alias: javadoc)"""
        mock_result.returncode = 0

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                styles = get_boxes_styles()
                # Should include alphanumeric styles
                assert "ansi" in styles
                assert "simple123" in styles
                # Should skip lines starting with - or (
                assert "---" not in "".join(styles)
                # Filter out non-alphanumeric first words
                # "c-cmt" starts with c which is alphanumeric
                # "indented" after strip starts with i which is alphanumeric

    def test_remove_box_removes_trailing_empty_lines(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Content\n\n\n"

        with patch.object(external, "tool_available", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                result = remove_box("+---+\n|Hi|\n+---+")
                assert result.success is True
                assert result.lines[-1] != ""
                assert len(result.lines) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
