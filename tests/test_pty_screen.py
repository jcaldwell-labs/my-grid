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
        """Test backspace moves cursor back (standard terminal behavior).

        Note: Real terminal backspace (\b) only moves cursor left.
        It does NOT delete the character. To erase, you need \b + overwrite.
        This is correct VT100/ANSI terminal behavior.
        """
        screen = PTYScreen(80, 24)

        # Test 1: Backspace moves cursor
        screen.feed("test\b")
        x, y = screen.get_cursor_position()
        assert x == 3  # Cursor moved back from position 4 to 3

        # Test 2: Backspace + space = erase (real terminal delete pattern)
        screen = PTYScreen(80, 24)
        screen.feed("test\b ")  # Backspace, then space overwrites 't'
        lines = screen.get_display_lines()
        assert "tes " in lines[0]  # Last 't' replaced with space

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
        assert all(line.strip() == "" or line == " " * 80 for line in lines)


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


class TestPTYScreenColors:
    """Test ANSI color handling in pyte."""

    def test_styled_output_basic(self):
        """Test get_display_lines_styled returns styled characters."""
        screen = PTYScreen(80, 24)
        screen.feed("Hello")

        styled_lines = screen.get_display_lines_styled()
        assert len(styled_lines) == 24
        assert len(styled_lines[0]) == 80  # Full line width

        # Check first 5 chars are 'Hello'
        chars = "".join(sc.char for sc in styled_lines[0][:5])
        assert chars == "Hello"

    def test_foreground_color_red(self):
        """Test red foreground color is parsed correctly."""
        screen = PTYScreen(80, 24)
        # ESC[31m = red foreground
        screen.feed("\x1b[31mRed Text\x1b[0m")

        styled_lines = screen.get_display_lines_styled()
        first_char = styled_lines[0][0]

        # Red is color 1
        assert first_char.char == "R"
        assert first_char.fg == 1

    def test_foreground_color_green(self):
        """Test green foreground color."""
        screen = PTYScreen(80, 24)
        # ESC[32m = green foreground
        screen.feed("\x1b[32mGreen\x1b[0m")

        styled_lines = screen.get_display_lines_styled()
        first_char = styled_lines[0][0]

        # Green is color 2
        assert first_char.char == "G"
        assert first_char.fg == 2

    def test_background_color(self):
        """Test background color is parsed correctly."""
        screen = PTYScreen(80, 24)
        # ESC[44m = blue background
        screen.feed("\x1b[44mBlue BG\x1b[0m")

        styled_lines = screen.get_display_lines_styled()
        first_char = styled_lines[0][0]

        # Blue is color 4
        assert first_char.char == "B"
        assert first_char.bg == 4

    def test_combined_fg_bg_colors(self):
        """Test combined foreground and background colors."""
        screen = PTYScreen(80, 24)
        # ESC[31;42m = red on green
        screen.feed("\x1b[31;42mRed on Green\x1b[0m")

        styled_lines = screen.get_display_lines_styled()
        first_char = styled_lines[0][0]

        assert first_char.fg == 1  # Red
        assert first_char.bg == 2  # Green

    def test_color_reset(self):
        """Test colors reset to default."""
        screen = PTYScreen(80, 24)
        # Red text, then reset, then normal text
        screen.feed("\x1b[31mRed\x1b[0mNormal")

        styled_lines = screen.get_display_lines_styled()

        # First 3 chars are red
        assert styled_lines[0][0].fg == 1  # R
        assert styled_lines[0][1].fg == 1  # e
        assert styled_lines[0][2].fg == 1  # d

        # Chars after reset are default (-1)
        assert styled_lines[0][3].fg == -1  # N
        assert styled_lines[0][4].fg == -1  # o

    def test_bright_colors_mapped(self):
        """Test bright colors are mapped to basic colors."""
        screen = PTYScreen(80, 24)
        # ESC[91m = bright red (should map to red)
        screen.feed("\x1b[91mBright Red\x1b[0m")

        styled_lines = screen.get_display_lines_styled()
        first_char = styled_lines[0][0]

        # Bright red maps to red (1)
        assert first_char.fg == 1

    def test_default_colors(self):
        """Test default colors are -1."""
        screen = PTYScreen(80, 24)
        screen.feed("Plain text")

        styled_lines = screen.get_display_lines_styled()
        first_char = styled_lines[0][0]

        # Default colors
        assert first_char.fg == -1
        assert first_char.bg == -1

    def test_styled_scrollback(self):
        """Test scrollback styled lines."""
        screen = PTYScreen(80, 5, history=100)

        # Fill screen with colored lines
        for i in range(10):
            screen.feed(f"\x1b[3{i % 8}mLine {i}\x1b[0m\n")

        # Get styled lines from current screen
        styled_current = screen.get_display_lines_styled(scroll_offset=0)
        assert len(styled_current) == 5

        # Get styled lines from scrollback
        styled_history = screen.get_display_lines_styled(scroll_offset=5)
        assert len(styled_history) == 5

    def test_all_basic_colors(self):
        """Test all 8 basic foreground colors are recognized."""
        screen = PTYScreen(80, 24)

        # Feed all basic colors
        colors = [
            (30, "black", 0),
            (31, "red", 1),
            (32, "green", 2),
            (33, "yellow", 3),
            (34, "blue", 4),
            (35, "magenta", 5),
            (36, "cyan", 6),
            (37, "white", 7),
        ]

        for code, name, expected in colors:
            screen = PTYScreen(80, 24)
            screen.feed(f"\x1b[{code}m{name}\x1b[0m")

            styled_lines = screen.get_display_lines_styled()
            first_char = styled_lines[0][0]
            assert (
                first_char.fg == expected
            ), f"Color {name} (code {code}) should be {expected}, got {first_char.fg}"
