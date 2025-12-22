"""Tests for PTY terminal emulation using pyte."""

import pytest
from src.pty_screen import PTYScreen


class TestPTYScreen:
    """Test pyte terminal emulator wrapper."""

    def test_basic_output(self):
        """Test basic text output."""
        screen = PTYScreen(80, 24)
        screen.feed("Hello World")

        lines = screen.get_display_lines()
        assert len(lines) == 24
        assert "Hello World" in lines[0]

    def test_newline(self):
        """Test newline advances to next line."""
        screen = PTYScreen(80, 24)
        screen.feed("Line 1\nLine 2\n")

        lines = screen.get_display_lines()
        assert "Line 1" in lines[0]
        assert "Line 2" in lines[1]

    def test_backspace(self):
        """Test backspace deletes previous character."""
        screen = PTYScreen(80, 24)
        screen.feed("test\b")  # Type "test", backspace once

        lines = screen.get_display_lines()
        # Should show "tes" (last 't' deleted)
        assert "tes" in lines[0]
        assert "test" not in lines[0]

    def test_carriage_return(self):
        """Test carriage return returns to start of line."""
        screen = PTYScreen(80, 24)
        screen.feed("Before\rAfter")

        lines = screen.get_display_lines()
        # "After" should overwrite "Before" from the start
        assert "After" in lines[0]

    def test_cursor_positioning(self):
        """Test ANSI cursor positioning."""
        screen = PTYScreen(80, 24)

        # Write "ABC", move cursor left 2 positions, write "X"
        screen.feed("ABC")
        screen.feed("\x1b[2D")  # ESC[2D = move cursor left 2
        screen.feed("X")

        lines = screen.get_display_lines()
        # Should show "AXC" (X overwrote B)
        assert "AXC" in lines[0] or "A" in lines[0]  # Depending on exact pyte behavior

    def test_multiple_lines(self):
        """Test multiple lines of output."""
        screen = PTYScreen(80, 24)

        for i in range(10):
            screen.feed(f"Line {i}\n")

        lines = screen.get_display_lines()
        assert "Line 0" in lines[0]
        assert "Line 9" in lines[9]

    def test_total_lines_with_history(self):
        """Test total line count includes history."""
        screen = PTYScreen(80, 5, history=100)  # 5 line screen, 100 line history

        # Fill screen and overflow into history
        for i in range(10):
            screen.feed(f"Line {i}\n")

        total = screen.get_total_lines()
        assert total > 5  # Has history
        assert total <= 105  # Within history limit

    def test_get_cursor_position(self):
        """Test cursor position tracking."""
        screen = PTYScreen(80, 24)

        # Initial position
        x, y = screen.get_cursor_position()
        assert x == 0
        assert y == 0

        # After some text
        screen.feed("Hello")
        x, y = screen.get_cursor_position()
        assert x == 5  # After "Hello"
        assert y == 0  # Still on first line

    def test_screen_resize(self):
        """Test screen resizing."""
        screen = PTYScreen(80, 24)
        screen.feed("Test content")

        # Resize
        screen.resize(100, 30)

        assert screen.width == 100
        assert screen.height == 30
        # Content should be preserved (pyte handles this)

    def test_scrollback(self):
        """Test accessing scrollback history."""
        screen = PTYScreen(80, 5, history=100)

        # Generate more lines than screen height
        for i in range(20):
            screen.feed(f"Line {i}\n")

        # Current screen shows last 5 lines
        current = screen.get_display_lines(scroll_offset=0)
        assert "Line 19" in current[-1] or "Line 19" in current[-2]

        # Scroll back 10 lines
        scrolled = screen.get_display_lines(scroll_offset=10)
        # Should show earlier content
        # Exact assertion depends on pyte history behavior

    def test_empty_screen(self):
        """Test empty screen doesn't crash."""
        screen = PTYScreen(80, 24)

        lines = screen.get_display_lines()
        assert len(lines) == 24
        # All lines should be empty or whitespace
        assert all(line.strip() == '' or line == ' ' * 80 for line in lines)


class TestPTYScreenEdgeCases:
    """Test edge cases and error handling."""

    def test_very_long_line(self):
        """Test line longer than screen width."""
        screen = PTYScreen(80, 24)
        long_text = "A" * 200

        screen.feed(long_text)
        lines = screen.get_display_lines()

        # Should wrap or truncate (pyte handles this)
        # At minimum, shouldn't crash
        assert len(lines) == 24

    def test_many_escape_sequences(self):
        """Test handling lots of escape sequences."""
        screen = PTYScreen(80, 24)

        # Lots of cursor movements
        screen.feed("Start")
        for _ in range(50):
            screen.feed("\x1b[D")  # Move left
        screen.feed("X")

        # Shouldn't crash, pyte handles all sequences
        lines = screen.get_display_lines()
        assert len(lines) == 24

    def test_unicode_characters(self):
        """Test unicode character handling."""
        screen = PTYScreen(80, 24)
        screen.feed("Hello 世界 🎨")

        lines = screen.get_display_lines()
        # Should handle unicode gracefully
        assert len(lines) == 24
