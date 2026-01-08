"""Tests for mode state machine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from canvas import Canvas
from viewport import Viewport
from input import Action, InputEvent
from modes import (
    Mode,
    ModeConfig,
    CommandBuffer,
    ModeResult,
    ModeStateMachine,
    Selection,
    Bookmark,
    BookmarkManager,
)


# Helper to create input events
def action_event(action: Action) -> InputEvent:
    return InputEvent(action=action)


def char_event(char: str) -> InputEvent:
    return InputEvent(char=char)


class TestCommandBuffer:
    """Tests for CommandBuffer."""

    def test_insert(self):
        buf = CommandBuffer()
        buf.insert("a")
        buf.insert("b")
        buf.insert("c")
        assert buf.text == "abc"
        assert buf.cursor_pos == 3

    def test_insert_middle(self):
        buf = CommandBuffer()
        buf.text = "ac"
        buf.cursor_pos = 1
        buf.insert("b")
        assert buf.text == "abc"

    def test_backspace(self):
        buf = CommandBuffer()
        buf.text = "abc"
        buf.cursor_pos = 3
        buf.backspace()
        assert buf.text == "ab"
        assert buf.cursor_pos == 2

    def test_backspace_at_start(self):
        buf = CommandBuffer()
        buf.text = "abc"
        buf.cursor_pos = 0
        buf.backspace()
        assert buf.text == "abc"
        assert buf.cursor_pos == 0

    def test_delete(self):
        buf = CommandBuffer()
        buf.text = "abc"
        buf.cursor_pos = 1
        buf.delete()
        assert buf.text == "ac"

    def test_move_cursor(self):
        buf = CommandBuffer()
        buf.text = "abc"
        buf.cursor_pos = 1

        buf.move_right()
        assert buf.cursor_pos == 2

        buf.move_left()
        assert buf.cursor_pos == 1

        buf.move_start()
        assert buf.cursor_pos == 0

        buf.move_end()
        assert buf.cursor_pos == 3

    def test_submit(self):
        buf = CommandBuffer()
        buf.text = "test command"
        buf.cursor_pos = 12

        result = buf.submit()
        assert result == "test command"
        assert buf.text == ""
        assert buf.cursor_pos == 0
        assert "test command" in buf.history

    def test_history_navigation(self):
        buf = CommandBuffer()
        buf.history = ["first", "second", "third"]

        buf.history_prev()
        assert buf.text == "third"

        buf.history_prev()
        assert buf.text == "second"

        buf.history_next()
        assert buf.text == "third"

        buf.history_next()
        assert buf.text == ""

    def test_clear(self):
        buf = CommandBuffer()
        buf.text = "test"
        buf.cursor_pos = 4
        buf.history_index = 2

        buf.clear()
        assert buf.text == ""
        assert buf.cursor_pos == 0
        assert buf.history_index == -1


class TestModeStateMachine:
    """Tests for ModeStateMachine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.sm = ModeStateMachine(self.canvas, self.viewport)

    def test_initial_mode(self):
        assert self.sm.mode == Mode.NAV
        assert self.sm.mode_name == "NAV"

    def test_set_mode(self):
        self.sm.set_mode(Mode.EDIT)
        assert self.sm.mode == Mode.EDIT

    def test_toggle_pan_mode(self):
        assert self.sm.mode == Mode.NAV

        self.sm.toggle_pan_mode()
        assert self.sm.mode == Mode.PAN

        self.sm.toggle_pan_mode()
        assert self.sm.mode == Mode.NAV

    # NAV mode tests
    def test_nav_cursor_movement(self):
        result = self.sm.process(action_event(Action.MOVE_RIGHT))
        assert result.handled
        assert self.viewport.cursor.x == 1

        result = self.sm.process(action_event(Action.MOVE_DOWN))
        assert self.viewport.cursor.y == 1

    def test_nav_fast_movement(self):
        result = self.sm.process(action_event(Action.MOVE_RIGHT_FAST))
        assert self.viewport.cursor.x == 10  # Default fast step

    def test_nav_enter_edit_mode(self):
        result = self.sm.process(action_event(Action.ENTER_EDIT_MODE))
        assert result.mode_changed
        assert result.new_mode == Mode.EDIT
        assert self.sm.mode == Mode.EDIT

    def test_nav_toggle_pan(self):
        result = self.sm.process(action_event(Action.TOGGLE_PAN_MODE))
        assert result.mode_changed
        assert self.sm.mode == Mode.PAN

    def test_nav_enter_command_mode(self):
        result = self.sm.process(action_event(Action.ENTER_COMMAND_MODE))
        assert result.mode_changed
        assert self.sm.mode == Mode.COMMAND

    def test_nav_center_cursor(self):
        self.viewport.cursor.set(100, 100)
        result = self.sm.process(action_event(Action.CENTER_CURSOR))
        assert result.handled
        # Viewport should have moved to center on cursor
        assert self.viewport.is_visible(100, 100)

    def test_nav_pan_viewport(self):
        initial_x = self.viewport.x
        result = self.sm.process(action_event(Action.PAN_RIGHT))
        assert self.viewport.x > initial_x

    # PAN mode tests
    def test_pan_mode_movement_pans_viewport(self):
        self.sm.set_mode(Mode.PAN)
        initial_x = self.viewport.x

        result = self.sm.process(action_event(Action.MOVE_RIGHT))
        assert self.viewport.x > initial_x

    def test_pan_mode_exit(self):
        self.sm.set_mode(Mode.PAN)
        result = self.sm.process(action_event(Action.EXIT_MODE))
        assert self.sm.mode == Mode.NAV

    # EDIT mode tests
    def test_edit_mode_typing(self):
        self.sm.set_mode(Mode.EDIT)
        self.viewport.cursor.set(5, 5)

        result = self.sm.process(char_event("X"))
        assert result.handled
        assert self.canvas.get_char(5, 5) == "X"
        # Cursor should advance
        assert self.viewport.cursor.x == 6

    def test_edit_mode_backspace(self):
        self.sm.set_mode(Mode.EDIT)
        self.viewport.cursor.set(5, 5)
        self.canvas.set(4, 5, "A")

        result = self.sm.process(action_event(Action.BACKSPACE))
        assert result.handled
        assert self.viewport.cursor.x == 4
        assert self.canvas.is_empty_at(4, 5)

    def test_edit_mode_delete(self):
        self.sm.set_mode(Mode.EDIT)
        self.viewport.cursor.set(5, 5)
        self.canvas.set(5, 5, "A")

        result = self.sm.process(action_event(Action.DELETE_CHAR))
        assert self.canvas.is_empty_at(5, 5)

    def test_edit_mode_newline(self):
        self.sm.set_mode(Mode.EDIT)
        self.viewport.cursor.set(10, 5)

        result = self.sm.process(action_event(Action.NEWLINE))
        assert self.viewport.cursor.y == 6
        assert self.viewport.cursor.x == 0  # Reset to origin X

    def test_edit_mode_exit(self):
        self.sm.set_mode(Mode.EDIT)
        result = self.sm.process(action_event(Action.EXIT_MODE))
        assert self.sm.mode == Mode.NAV

    def test_edit_mode_cursor_movement(self):
        self.sm.set_mode(Mode.EDIT)
        result = self.sm.process(action_event(Action.MOVE_RIGHT))
        assert self.viewport.cursor.x == 1

    # COMMAND mode tests
    def test_command_mode_typing(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.process(char_event("g"))
        self.sm.process(char_event("o"))
        self.sm.process(char_event("t"))
        self.sm.process(char_event("o"))

        assert self.sm.command_buffer.text == "goto"

    def test_command_mode_backspace(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "test"
        self.sm.command_buffer.cursor_pos = 4

        self.sm.process(action_event(Action.BACKSPACE))
        assert self.sm.command_buffer.text == "tes"

    def test_command_mode_submit(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "goto 10 20"
        self.sm.command_buffer.cursor_pos = 10

        result = self.sm.process(action_event(Action.NEWLINE))
        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert self.viewport.cursor.x == 10
        assert self.viewport.cursor.y == 20

    def test_command_mode_exit(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "partial"

        result = self.sm.process(action_event(Action.EXIT_MODE))
        assert self.sm.mode == Mode.NAV
        assert self.sm.command_buffer.text == ""

    def test_command_mode_history(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.history = ["old command"]

        self.sm.process(action_event(Action.MOVE_UP))
        assert self.sm.command_buffer.text == "old command"

    # Built-in commands
    def test_command_quit(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "q"
        result = self.sm.process(action_event(Action.NEWLINE))
        assert result.quit

    def test_command_goto(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "g 50 100"
        self.sm.command_buffer.cursor_pos = 8

        result = self.sm.process(action_event(Action.NEWLINE))
        assert self.viewport.cursor.x == 50
        assert self.viewport.cursor.y == 100

    def test_command_origin_here(self):
        self.viewport.cursor.set(25, 30)
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "origin here"
        self.sm.command_buffer.cursor_pos = 11

        result = self.sm.process(action_event(Action.NEWLINE))
        assert self.viewport.origin.x == 25
        assert self.viewport.origin.y == 30

    def test_command_origin_coords(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "origin 100 200"
        self.sm.command_buffer.cursor_pos = 14

        result = self.sm.process(action_event(Action.NEWLINE))
        assert self.viewport.origin.x == 100
        assert self.viewport.origin.y == 200

    def test_command_clear(self):
        self.canvas.set(0, 0, "X")
        self.canvas.set(10, 10, "Y")
        assert self.canvas.cell_count == 2

        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "clear"
        self.sm.command_buffer.cursor_pos = 5

        result = self.sm.process(action_event(Action.NEWLINE))
        assert self.canvas.cell_count == 0

    def test_unknown_command(self):
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "invalidcmd"
        self.sm.command_buffer.cursor_pos = 10

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Unknown command" in result.message

    # Universal actions
    def test_quit_from_any_mode(self):
        for mode in [Mode.NAV, Mode.PAN, Mode.EDIT, Mode.COMMAND]:
            self.sm.set_mode(mode)
            result = self.sm.process(action_event(Action.QUIT))
            assert result.quit

    # Custom command registration
    def test_register_custom_command(self):
        def custom_handler(args):
            return ModeResult(message=f"Custom: {args}")

        self.sm.register_command("custom", custom_handler)

        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "custom arg1 arg2"
        self.sm.command_buffer.cursor_pos = 16

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Custom" in result.message


class TestSelection:
    """Tests for the Selection dataclass."""

    def test_selection_properties(self):
        """Test basic Selection properties."""
        sel = Selection(anchor_x=5, anchor_y=10, cursor_x=15, cursor_y=20)
        assert sel.x1 == 5
        assert sel.y1 == 10
        assert sel.x2 == 15
        assert sel.y2 == 20
        assert sel.width == 11  # 15 - 5 + 1
        assert sel.height == 11  # 20 - 10 + 1

    def test_selection_inverted(self):
        """Test Selection with cursor before anchor (inverted)."""
        sel = Selection(anchor_x=15, anchor_y=20, cursor_x=5, cursor_y=10)
        # x1, y1 should still be the min values
        assert sel.x1 == 5
        assert sel.y1 == 10
        assert sel.x2 == 15
        assert sel.y2 == 20
        assert sel.width == 11
        assert sel.height == 11

    def test_selection_zero_size(self):
        """Test Selection with cursor at anchor (single cell)."""
        sel = Selection(anchor_x=5, anchor_y=5, cursor_x=5, cursor_y=5)
        assert sel.x1 == 5
        assert sel.y1 == 5
        assert sel.x2 == 5
        assert sel.y2 == 5
        assert sel.width == 1
        assert sel.height == 1

    def test_selection_contains(self):
        """Test contains() method."""
        sel = Selection(anchor_x=5, anchor_y=5, cursor_x=10, cursor_y=10)
        # Inside
        assert sel.contains(7, 7)
        # Edges
        assert sel.contains(5, 5)
        assert sel.contains(10, 10)
        assert sel.contains(5, 10)
        assert sel.contains(10, 5)
        # Outside
        assert not sel.contains(4, 7)
        assert not sel.contains(11, 7)
        assert not sel.contains(7, 4)
        assert not sel.contains(7, 11)

    def test_selection_update_cursor(self):
        """Test update_cursor() method."""
        sel = Selection(anchor_x=5, anchor_y=5, cursor_x=5, cursor_y=5)
        sel.update_cursor(10, 15)
        assert sel.cursor_x == 10
        assert sel.cursor_y == 15
        assert sel.anchor_x == 5  # Anchor unchanged
        assert sel.anchor_y == 5


class TestVisualMode:
    """Tests for VISUAL mode (Issue #53).

    Test cases from VISUAL-MODE-TEST-PLAN.md:
    - TC1: Enter/Exit VISUAL mode
    - TC2: Extend selection with movement
    - TC3: Shrink selection
    - TC4: Yank selection to clipboard
    - TC5: Delete selection (clear cells)
    - TC6: Fill selection with character
    - TC7: Selection highlighting (renderer test - not covered here)

    Edge cases:
    - EC1: Zero-size selection (cursor == anchor)
    - EC5: Selection inversion (cursor past anchor)
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.sm = ModeStateMachine(self.canvas, self.viewport)

    # TC1: Enter/Exit VISUAL mode
    def test_enter_visual_mode(self):
        """TC1a: Enter VISUAL mode from NAV with 'v' key."""
        self.viewport.cursor.set(10, 20)
        result = self.sm.process(char_event("v"))

        assert result.mode_changed
        assert result.new_mode == Mode.VISUAL
        assert self.sm.mode == Mode.VISUAL
        assert self.sm.selection is not None
        # Selection starts with anchor and cursor at same position
        assert self.sm.selection.anchor_x == 10
        assert self.sm.selection.anchor_y == 20
        assert self.sm.selection.cursor_x == 10
        assert self.sm.selection.cursor_y == 20
        assert "VISUAL" in result.message
        assert "(1x1)" in result.message

    def test_exit_visual_mode_esc(self):
        """TC1b: Exit VISUAL mode with ESC, selection cleared."""
        self.viewport.cursor.set(10, 20)
        self.sm.process(char_event("v"))  # Enter VISUAL
        assert self.sm.selection is not None

        result = self.sm.process(action_event(Action.EXIT_MODE))
        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert self.sm.selection is None
        assert "cancelled" in result.message.lower()

    def test_enter_visual_creates_fresh_selection(self):
        """TC1c: Entering VISUAL again creates fresh selection."""
        self.viewport.cursor.set(10, 20)
        self.sm.process(char_event("v"))  # Enter VISUAL
        self.sm.process(action_event(Action.MOVE_RIGHT))  # Extend
        self.sm.process(action_event(Action.EXIT_MODE))  # Exit

        # Enter again at different position
        self.viewport.cursor.set(50, 60)
        result = self.sm.process(char_event("v"))
        assert result.mode_changed

        assert self.sm.selection.anchor_x == 50
        assert self.sm.selection.anchor_y == 60
        assert self.sm.selection.width == 1
        assert self.sm.selection.height == 1

    # TC2: Extend selection with movement
    def test_extend_selection_right(self):
        """TC2a: Moving right extends selection."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("v"))

        result = self.sm.process(action_event(Action.MOVE_RIGHT))
        assert self.sm.selection.width == 2
        assert self.sm.selection.height == 1
        assert self.viewport.cursor.x == 11
        assert "(2x1)" in result.message

    def test_extend_selection_down(self):
        """TC2b: Moving down extends selection."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("v"))

        result = self.sm.process(action_event(Action.MOVE_DOWN))
        assert self.sm.selection.width == 1
        assert self.sm.selection.height == 2
        assert self.viewport.cursor.y == 11
        assert "(1x2)" in result.message

    def test_extend_selection_diagonal(self):
        """TC2c: Moving in multiple directions creates rectangle."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("v"))

        self.sm.process(action_event(Action.MOVE_RIGHT))
        self.sm.process(action_event(Action.MOVE_RIGHT))
        result = self.sm.process(action_event(Action.MOVE_DOWN))

        assert self.sm.selection.width == 3
        assert self.sm.selection.height == 2
        assert "(3x2)" in result.message

    def test_extend_selection_fast_movement(self):
        """TC2d: Fast movement extends selection by fast_step."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("v"))

        result = self.sm.process(action_event(Action.MOVE_RIGHT_FAST))
        assert result.handled
        assert self.sm.selection.width == 11  # 10 + 1
        assert self.viewport.cursor.x == 20

    # TC3: Shrink selection
    def test_shrink_selection(self):
        """TC3: Moving back towards anchor shrinks selection."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("v"))
        self.sm.process(action_event(Action.MOVE_RIGHT))
        self.sm.process(action_event(Action.MOVE_RIGHT))
        assert self.sm.selection.width == 3

        # Move back
        result = self.sm.process(action_event(Action.MOVE_LEFT))
        assert self.sm.selection.width == 2
        assert "(2x1)" in result.message

    # TC4: Yank selection
    def test_yank_selection(self):
        """TC4: Yank selection returns command with coordinates."""
        self.viewport.cursor.set(5, 10)
        self.sm.process(char_event("v"))
        self.sm.process(action_event(Action.MOVE_RIGHT))
        self.sm.process(action_event(Action.MOVE_RIGHT))
        self.sm.process(action_event(Action.MOVE_DOWN))

        result = self.sm.process(char_event("y"))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert self.sm.selection is None
        assert result.command is not None
        assert "yank_selection" in result.command
        assert "5" in result.command  # x1
        assert "10" in result.command  # y1
        assert "3" in result.command  # width
        assert "2" in result.command  # height

    # TC5: Delete selection
    def test_delete_selection(self):
        """TC5: Delete selection returns command with coordinates."""
        self.viewport.cursor.set(5, 10)
        self.sm.process(char_event("v"))
        self.sm.process(action_event(Action.MOVE_RIGHT))
        self.sm.process(action_event(Action.MOVE_DOWN))

        result = self.sm.process(char_event("d"))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert self.sm.selection is None
        assert result.command is not None
        assert "delete_selection" in result.command
        assert "5" in result.command  # x1
        assert "10" in result.command  # y1

    # TC6: Fill selection
    def test_fill_selection(self):
        """TC6: Fill selection enters COMMAND mode with pre-filled buffer."""
        self.viewport.cursor.set(5, 10)
        self.sm.process(char_event("v"))
        self.sm.process(action_event(Action.MOVE_RIGHT))
        self.sm.process(action_event(Action.MOVE_DOWN))

        result = self.sm.process(char_event("f"))

        assert result.mode_changed
        assert self.sm.mode == Mode.COMMAND
        assert self.sm.selection is None
        assert "fill" in self.sm.command_buffer.text
        assert "5 10" in self.sm.command_buffer.text  # x1, y1
        assert "Fill" in result.message

    # EC1: Zero-size selection
    def test_zero_size_selection(self):
        """EC1: Selection with cursor at anchor works correctly."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("v"))

        # Selection should be 1x1
        assert self.sm.selection.width == 1
        assert self.sm.selection.height == 1
        assert self.sm.selection.contains(10, 10)
        assert not self.sm.selection.contains(11, 10)

        # Yank should still work
        result = self.sm.process(char_event("y"))
        assert "1" in result.command  # width
        assert "1" in result.command  # height

    # EC5: Selection inversion
    def test_selection_inversion(self):
        """EC5: Selection works when cursor moves before anchor."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("v"))

        # Move cursor before anchor
        self.sm.process(action_event(Action.MOVE_LEFT))
        self.sm.process(action_event(Action.MOVE_UP))

        # Selection should correctly compute bounds
        assert self.sm.selection.x1 == 9  # cursor moved left
        assert self.sm.selection.y1 == 9  # cursor moved up
        assert self.sm.selection.x2 == 10  # anchor
        assert self.sm.selection.y2 == 10  # anchor
        assert self.sm.selection.width == 2
        assert self.sm.selection.height == 2

    def test_visual_mode_recovery_without_selection(self):
        """Test graceful recovery if selection is None in VISUAL mode."""
        self.sm.set_mode(Mode.VISUAL)
        self.sm.selection = None  # Simulate bug

        result = self.sm.process(action_event(Action.MOVE_RIGHT))
        # Should recover to NAV mode
        assert result.mode_changed
        assert self.sm.mode == Mode.NAV

    # Mouse drag selection tests (Issue #13)
    def test_mouse_drag_selection_programmatic(self):
        """Test creating selection via programmatic approach (simulates mouse drag)."""
        # Simulates what _handle_mouse_event does when drag starts
        start_x, start_y = 10, 20
        end_x, end_y = 30, 35

        # Create selection anchored at drag start
        self.sm.selection = Selection(
            anchor_x=start_x,
            anchor_y=start_y,
            cursor_x=start_x,
            cursor_y=start_y,
        )
        self.sm.set_mode(Mode.VISUAL)

        assert self.sm.mode == Mode.VISUAL
        assert self.sm.selection.width == 1
        assert self.sm.selection.height == 1

        # Simulate drag movement - update cursor position
        self.sm.selection.update_cursor(end_x, end_y)

        # Selection should span from start to end
        assert self.sm.selection.anchor_x == start_x
        assert self.sm.selection.anchor_y == start_y
        assert self.sm.selection.cursor_x == end_x
        assert self.sm.selection.cursor_y == end_y
        assert self.sm.selection.width == 21  # 30 - 10 + 1
        assert self.sm.selection.height == 16  # 35 - 20 + 1

    def test_mouse_drag_selection_yank(self):
        """Test yanking a mouse-drag created selection."""
        # Create selection via programmatic approach (like mouse drag)
        self.sm.selection = Selection(anchor_x=5, anchor_y=5, cursor_x=15, cursor_y=10)
        self.sm.set_mode(Mode.VISUAL)

        # Yank the selection
        result = self.sm.process(char_event("y"))

        # Should return to NAV mode with yank command
        assert self.sm.mode == Mode.NAV
        assert self.sm.selection is None
        assert "yank_selection" in result.command
        assert "5 5 11 6" in result.command  # x1=5, y1=5, w=11, h=6

    def test_mouse_click_updates_existing_selection(self):
        """Test that clicking while in visual mode updates selection endpoint."""
        # Start with a selection
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("v"))  # Enter VISUAL

        # Simulate click at different position - programmatically update selection
        new_x, new_y = 25, 30
        self.sm.selection.update_cursor(new_x, new_y)
        self.viewport.cursor.set(new_x, new_y)

        # Selection should update to new cursor position
        assert self.sm.selection.anchor_x == 10  # Anchor unchanged
        assert self.sm.selection.anchor_y == 10
        assert self.sm.selection.cursor_x == 25
        assert self.sm.selection.cursor_y == 30
        assert self.sm.selection.width == 16  # 25 - 10 + 1
        assert self.sm.selection.height == 21  # 30 - 10 + 1


class TestBookmarkManager:
    """Tests for BookmarkManager class."""

    def test_set_and_get_bookmark(self):
        """Test setting and getting bookmarks."""
        mgr = BookmarkManager()
        mgr.set("a", 10, 20, "test mark")

        bm = mgr.get("a")
        assert bm is not None
        assert bm.x == 10
        assert bm.y == 20
        assert bm.name == "test mark"

    def test_set_lowercase_conversion(self):
        """Test that keys are converted to lowercase."""
        mgr = BookmarkManager()
        mgr.set("A", 10, 20)

        # Should be retrievable as lowercase
        assert mgr.get("a") is not None
        assert mgr.get("A") is not None

    def test_set_numeric_keys(self):
        """Test setting bookmarks with numeric keys."""
        mgr = BookmarkManager()
        mgr.set("0", 0, 0)
        mgr.set("9", 90, 90)

        assert mgr.get("0") is not None
        assert mgr.get("9") is not None

    def test_set_invalid_key(self):
        """Test that invalid keys are rejected."""
        mgr = BookmarkManager()
        # Multi-character keys should be ignored
        mgr.set("ab", 10, 20)
        assert mgr.get("ab") is None

        # Special characters should be ignored
        mgr.set("!", 10, 20)
        assert mgr.get("!") is None

    def test_get_nonexistent(self):
        """Test getting a non-existent bookmark."""
        mgr = BookmarkManager()
        assert mgr.get("z") is None

    def test_delete_bookmark(self):
        """Test deleting a bookmark."""
        mgr = BookmarkManager()
        mgr.set("a", 10, 20)
        assert mgr.get("a") is not None

        result = mgr.delete("a")
        assert result is True
        assert mgr.get("a") is None

    def test_delete_nonexistent(self):
        """Test deleting a non-existent bookmark."""
        mgr = BookmarkManager()
        result = mgr.delete("z")
        assert result is False

    def test_clear_all(self):
        """Test clearing all bookmarks."""
        mgr = BookmarkManager()
        mgr.set("a", 10, 20)
        mgr.set("b", 30, 40)
        mgr.set("c", 50, 60)

        mgr.clear()

        assert mgr.get("a") is None
        assert mgr.get("b") is None
        assert mgr.get("c") is None

    def test_list_all(self):
        """Test listing all bookmarks."""
        mgr = BookmarkManager()
        mgr.set("c", 50, 60)
        mgr.set("a", 10, 20)
        mgr.set("b", 30, 40)

        all_marks = mgr.list_all()
        assert len(all_marks) == 3
        # Should be sorted by key
        assert all_marks[0][0] == "a"
        assert all_marks[1][0] == "b"
        assert all_marks[2][0] == "c"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        mgr = BookmarkManager()
        mgr.set("a", 10, 20, "first")
        mgr.set("b", 30, 40)

        data = mgr.to_dict()
        assert "a" in data
        assert data["a"]["x"] == 10
        assert data["a"]["y"] == 20
        assert data["a"]["name"] == "first"
        assert "b" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "a": {"x": 10, "y": 20, "name": "first"},
            "b": {"x": 30, "y": 40},
        }

        mgr = BookmarkManager.from_dict(data)

        bm_a = mgr.get("a")
        assert bm_a is not None
        assert bm_a.x == 10
        assert bm_a.y == 20
        assert bm_a.name == "first"

        bm_b = mgr.get("b")
        assert bm_b is not None
        assert bm_b.x == 30
        assert bm_b.y == 40


class TestMarkMode:
    """Tests for MARK_SET and MARK_JUMP modes."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.sm = ModeStateMachine(self.canvas, self.viewport)

    def test_enter_mark_set_mode(self):
        """Test entering MARK_SET mode with 'm' key."""
        result = self.sm.process(char_event("m"))

        assert result.mode_changed
        assert result.new_mode == Mode.MARK_SET
        assert self.sm.mode == Mode.MARK_SET
        assert "Set mark" in result.message

    def test_enter_mark_jump_mode(self):
        """Test entering MARK_JUMP mode with apostrophe key."""
        result = self.sm.process(char_event("'"))

        assert result.mode_changed
        assert result.new_mode == Mode.MARK_JUMP
        assert self.sm.mode == Mode.MARK_JUMP
        assert "Jump to mark" in result.message

    def test_set_mark_with_letter(self):
        """Test setting a mark with a letter key."""
        self.viewport.cursor.set(25, 50)
        self.sm.process(char_event("m"))  # Enter MARK_SET

        result = self.sm.process(char_event("a"))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert "Mark 'a' set" in result.message

        # Verify bookmark was set
        bm = self.sm.bookmarks.get("a")
        assert bm is not None
        assert bm.x == 25
        assert bm.y == 50

    def test_set_mark_with_number(self):
        """Test setting a mark with a number key."""
        self.viewport.cursor.set(100, 200)
        self.sm.process(char_event("m"))  # Enter MARK_SET

        result = self.sm.process(char_event("5"))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV

        bm = self.sm.bookmarks.get("5")
        assert bm is not None
        assert bm.x == 100
        assert bm.y == 200

    def test_cancel_mark_set(self):
        """Test cancelling mark set with invalid key."""
        self.sm.process(char_event("m"))  # Enter MARK_SET

        # Press an invalid key (e.g., special character via action)
        result = self.sm.process(action_event(Action.EXIT_MODE))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert "Cancelled" in result.message

    def test_jump_to_mark(self):
        """Test jumping to a set mark."""
        # Set a bookmark
        self.sm.bookmarks.set("b", 75, 125)

        self.sm.process(char_event("'"))  # Enter MARK_JUMP
        result = self.sm.process(char_event("b"))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert self.viewport.cursor.x == 75
        assert self.viewport.cursor.y == 125
        assert "Jumped to mark 'b'" in result.message

    def test_jump_to_nonexistent_mark(self):
        """Test jumping to a non-existent mark."""
        self.sm.process(char_event("'"))  # Enter MARK_JUMP
        result = self.sm.process(char_event("z"))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert "not set" in result.message

    def test_cancel_mark_jump(self):
        """Test cancelling mark jump with ESC."""
        self.sm.process(char_event("'"))  # Enter MARK_JUMP
        result = self.sm.process(action_event(Action.EXIT_MODE))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV
        assert "Cancelled" in result.message


class TestDrawMode:
    """Tests for DRAW mode (line drawing)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.sm = ModeStateMachine(self.canvas, self.viewport)

    def test_enter_draw_mode_with_D(self):
        """Test entering DRAW mode with 'D' key."""
        result = self.sm.process(char_event("D"))

        assert result.mode_changed
        assert result.new_mode == Mode.DRAW
        assert self.sm.mode == Mode.DRAW
        assert "DRAW" in result.message
        assert "pen DOWN" in result.message

    def test_enter_draw_mode_with_action(self):
        """Test entering DRAW mode with ENTER_DRAW_MODE action."""
        result = self.sm.process(action_event(Action.ENTER_DRAW_MODE))

        assert result.mode_changed
        assert result.new_mode == Mode.DRAW
        assert self.sm.mode == Mode.DRAW

    def test_exit_draw_mode(self):
        """Test exiting DRAW mode with ESC."""
        self.sm.process(char_event("D"))  # Enter DRAW
        result = self.sm.process(action_event(Action.EXIT_MODE))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV

    def test_draw_horizontal_line(self):
        """Test drawing a horizontal line."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("D"))  # Enter DRAW

        # Draw right
        self.sm.process(action_event(Action.MOVE_RIGHT))
        self.sm.process(action_event(Action.MOVE_RIGHT))

        # Check that characters were drawn
        assert self.canvas.get_char(10, 10) is not None
        assert self.canvas.get_char(11, 10) is not None
        assert self.viewport.cursor.x == 12

    def test_draw_vertical_line(self):
        """Test drawing a vertical line."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("D"))  # Enter DRAW

        # Draw down
        self.sm.process(action_event(Action.MOVE_DOWN))
        self.sm.process(action_event(Action.MOVE_DOWN))

        # Check that characters were drawn
        assert self.canvas.get_char(10, 10) is not None
        assert self.canvas.get_char(10, 11) is not None
        assert self.viewport.cursor.y == 12

    def test_pen_toggle(self):
        """Test toggling pen up/down with spacebar."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("D"))  # Enter DRAW with pen DOWN

        # Toggle pen up
        result = self.sm.process(char_event(" "))
        assert "pen UP" in result.message

        # Move without drawing
        self.sm.process(action_event(Action.MOVE_RIGHT))

        # No character should be drawn at starting position when pen is up
        # (pen was toggled before any movement)
        assert self.viewport.cursor.x == 11

    def test_toggle_draw_pen_method(self):
        """Test the toggle_draw_pen method directly."""
        self.sm.process(char_event("D"))  # Enter DRAW

        # Initially pen is down
        assert self.sm._draw_pen_down is True

        result = self.sm.toggle_draw_pen()
        assert result is False  # Pen is now up
        assert self.sm._draw_pen_down is False

        result = self.sm.toggle_draw_pen()
        assert result is True  # Pen is now down
        assert self.sm._draw_pen_down is True

    def test_pen_toggle_resets_direction(self):
        """Test that lifting pen resets last direction."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("D"))  # Enter DRAW

        # Draw to set a direction
        self.sm.process(action_event(Action.MOVE_RIGHT))
        assert self.sm._draw_last_dir == (1, 0)

        # Toggle pen up - should reset direction
        self.sm.toggle_draw_pen()
        assert self.sm._draw_last_dir is None

    def test_draw_corner(self):
        """Test drawing a corner (direction change)."""
        self.viewport.cursor.set(10, 10)
        self.sm.process(char_event("D"))  # Enter DRAW

        # Draw right then down to create corner
        self.sm.process(action_event(Action.MOVE_RIGHT))
        self.sm.process(action_event(Action.MOVE_DOWN))

        # Both positions should have characters
        assert self.canvas.get_char(10, 10) is not None
        assert self.canvas.get_char(11, 10) is not None

    def test_pen_toggled_this_frame_guard(self):
        """Test the frame guard for pen toggle."""
        self.sm.process(char_event("D"))  # Enter DRAW

        # First toggle should work
        assert self.sm._pen_toggled_this_frame is False
        self.sm.toggle_draw_pen()
        assert self.sm._pen_toggled_this_frame is True

        # Second toggle in same frame should be blocked by spacebar handler
        initial_state = self.sm._draw_pen_down
        self.sm.process(char_event(" "))
        assert self.sm._draw_pen_down == initial_state  # Should not change

        # Reset guard
        self.sm.reset_pen_toggle_guard()
        assert self.sm._pen_toggled_this_frame is False

    def test_reset_pen_toggle_guard(self):
        """Test the reset_pen_toggle_guard method."""
        self.sm._pen_toggled_this_frame = True
        self.sm.reset_pen_toggle_guard()
        assert self.sm._pen_toggled_this_frame is False


class TestDrawModeLineCharacters:
    """Tests for Draw mode line character selection and junction detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.sm = ModeStateMachine(self.canvas, self.viewport)

    def test_get_draw_char_horizontal(self):
        """Test getting horizontal line character."""
        # Going right with previous direction right
        char = self.sm._get_draw_char(10, 10, (1, 0), (1, 0))
        # Should be horizontal line character
        assert char is not None
        assert len(char) == 1

    def test_get_draw_char_vertical(self):
        """Test getting vertical line character."""
        # Going down with previous direction down
        char = self.sm._get_draw_char(10, 10, (0, 1), (0, 1))
        # Should be vertical line character
        assert char is not None
        assert len(char) == 1

    def test_get_draw_char_corner_right_down(self):
        """Test getting corner character (right then down)."""
        # Going down after going right
        char = self.sm._get_draw_char(10, 10, (1, 0), (0, 1))
        assert char is not None

    def test_get_draw_char_corner_down_right(self):
        """Test getting corner character (down then right)."""
        # Going right after going down
        char = self.sm._get_draw_char(10, 10, (0, 1), (1, 0))
        assert char is not None

    def test_get_draw_char_no_previous_direction(self):
        """Test getting character with no previous direction."""
        # Starting fresh (no from_dir)
        char = self.sm._get_draw_char(10, 10, None, (1, 0))
        assert char is not None

    def test_get_draw_char_with_existing_line(self):
        """Test junction when crossing existing line."""
        # Put a horizontal line character first
        self.canvas.set(10, 10, "-")

        # Draw down through it
        char = self.sm._get_draw_char(10, 10, (0, -1), (0, 1))
        # Should create a junction character
        assert char is not None

    def test_char_to_bits_horizontal(self):
        """Test char_to_bits for horizontal line."""
        from zones import get_border_chars

        chars = get_border_chars()

        bits = self.sm._char_to_bits(chars.get("horiz", "-"), chars)
        # Should have LEFT and RIGHT bits set (4 | 8 = 12)
        assert bits == 12

    def test_char_to_bits_vertical(self):
        """Test char_to_bits for vertical line."""
        from zones import get_border_chars

        chars = get_border_chars()

        bits = self.sm._char_to_bits(chars.get("vert", "|"), chars)
        # Should have UP and DOWN bits set (1 | 2 = 3)
        assert bits == 3

    def test_char_to_bits_cross(self):
        """Test char_to_bits for cross junction."""
        from zones import get_border_chars

        chars = get_border_chars()

        bits = self.sm._char_to_bits(chars.get("cross", "+"), chars)
        # Should have all bits set (1 | 2 | 4 | 8 = 15)
        assert bits == 15

    def test_char_to_bits_unknown_char(self):
        """Test char_to_bits for unknown character."""
        from zones import get_border_chars

        chars = get_border_chars()

        bits = self.sm._char_to_bits("X", chars)
        assert bits == 0


class TestCommandModeEdgeCases:
    """Tests for Command mode edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.sm = ModeStateMachine(self.canvas, self.viewport)

    def test_empty_command(self):
        """Test submitting empty command."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = ""

        result = self.sm.process(action_event(Action.NEWLINE))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV

    def test_whitespace_only_command(self):
        """Test submitting whitespace-only command."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "   "
        self.sm.command_buffer.cursor_pos = 3

        result = self.sm.process(action_event(Action.NEWLINE))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV

    def test_command_delete_char(self):
        """Test delete key in command mode."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "test"
        self.sm.command_buffer.cursor_pos = 2

        result = self.sm.process(action_event(Action.DELETE_CHAR))

        assert result.handled
        assert self.sm.command_buffer.text == "tet"

    def test_command_cursor_movement(self):
        """Test cursor movement in command mode."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "test"
        self.sm.command_buffer.cursor_pos = 2

        # Move left
        self.sm.process(action_event(Action.MOVE_LEFT))
        assert self.sm.command_buffer.cursor_pos == 1

        # Move right
        self.sm.process(action_event(Action.MOVE_RIGHT))
        assert self.sm.command_buffer.cursor_pos == 2

    def test_command_history_down(self):
        """Test history navigation down in command mode."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.history = ["first", "second"]

        # Go up twice
        self.sm.process(action_event(Action.MOVE_UP))
        self.sm.process(action_event(Action.MOVE_UP))
        assert self.sm.command_buffer.text == "first"

        # Go down
        self.sm.process(action_event(Action.MOVE_DOWN))
        assert self.sm.command_buffer.text == "second"

    def test_command_unhandled_action(self):
        """Test unhandled action in command mode."""
        self.sm.set_mode(Mode.COMMAND)

        # PAN actions should not be handled in command mode
        result = self.sm.process(action_event(Action.PAN_UP))
        assert result.handled is False

    def test_goto_invalid_coords(self):
        """Test goto with invalid coordinates."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "goto abc def"
        self.sm.command_buffer.cursor_pos = 12

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Usage" in result.message

    def test_goto_insufficient_args(self):
        """Test goto with insufficient arguments."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "goto 10"
        self.sm.command_buffer.cursor_pos = 7

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Usage" in result.message

    def test_origin_invalid_coords(self):
        """Test origin with invalid coordinates."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "origin abc def"
        self.sm.command_buffer.cursor_pos = 14

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Usage" in result.message

    def test_origin_no_args(self):
        """Test origin with no arguments (defaults to cursor)."""
        self.viewport.cursor.set(42, 84)
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "origin"
        self.sm.command_buffer.cursor_pos = 6

        self.sm.process(action_event(Action.NEWLINE))
        assert self.viewport.origin.x == 42
        assert self.viewport.origin.y == 84

    def test_help_command(self):
        """Test help command."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "help"
        self.sm.command_buffer.cursor_pos = 4

        result = self.sm.process(action_event(Action.NEWLINE))
        assert result.command == "help"

    def test_help_alias_question(self):
        """Test help command with ? alias."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "?"
        self.sm.command_buffer.cursor_pos = 1

        result = self.sm.process(action_event(Action.NEWLINE))
        assert result.command == "help"

    def test_help_alias_h(self):
        """Test help command with h alias."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "h"
        self.sm.command_buffer.cursor_pos = 1

        result = self.sm.process(action_event(Action.NEWLINE))
        assert result.command == "help"

    def test_wq_command(self):
        """Test save and quit command."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "wq"
        self.sm.command_buffer.cursor_pos = 2

        result = self.sm.process(action_event(Action.NEWLINE))
        assert result.quit is True
        assert result.command == "save"


class TestBookmarkCommands:
    """Tests for bookmark-related commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.sm = ModeStateMachine(self.canvas, self.viewport)

    def test_marks_command_empty(self):
        """Test marks command with no bookmarks."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "marks"
        self.sm.command_buffer.cursor_pos = 5

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "No marks set" in result.message

    def test_marks_command_with_bookmarks(self):
        """Test marks command with bookmarks."""
        self.sm.bookmarks.set("a", 10, 20)
        self.sm.bookmarks.set("b", 30, 40)

        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "marks"
        self.sm.command_buffer.cursor_pos = 5

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Marks:" in result.message
        assert "a:" in result.message
        assert "b:" in result.message

    def test_mark_command_at_cursor(self):
        """Test mark command at cursor position."""
        self.viewport.cursor.set(55, 66)

        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "mark z"
        self.sm.command_buffer.cursor_pos = 6

        self.sm.process(action_event(Action.NEWLINE))

        bm = self.sm.bookmarks.get("z")
        assert bm is not None
        assert bm.x == 55
        assert bm.y == 66

    def test_mark_command_with_coords(self):
        """Test mark command with coordinates."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "mark x 100 200"
        self.sm.command_buffer.cursor_pos = 14

        self.sm.process(action_event(Action.NEWLINE))

        bm = self.sm.bookmarks.get("x")
        assert bm is not None
        assert bm.x == 100
        assert bm.y == 200

    def test_mark_command_no_key(self):
        """Test mark command without key."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "mark"
        self.sm.command_buffer.cursor_pos = 4

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Usage" in result.message

    def test_mark_command_invalid_key(self):
        """Test mark command with invalid key."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "mark !"
        self.sm.command_buffer.cursor_pos = 6

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "must be a-z or 0-9" in result.message

    def test_mark_command_invalid_coords(self):
        """Test mark command with invalid coordinates."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "mark a abc def"
        self.sm.command_buffer.cursor_pos = 14

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Invalid coordinates" in result.message

    def test_delmark_command(self):
        """Test delmark command."""
        self.sm.bookmarks.set("a", 10, 20)

        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "delmark a"
        self.sm.command_buffer.cursor_pos = 9

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "deleted" in result.message
        assert self.sm.bookmarks.get("a") is None

    def test_delmark_command_nonexistent(self):
        """Test delmark command for non-existent mark."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "delmark z"
        self.sm.command_buffer.cursor_pos = 9

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "not found" in result.message

    def test_delmark_command_no_key(self):
        """Test delmark command without key."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "delmark"
        self.sm.command_buffer.cursor_pos = 7

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "Usage" in result.message

    def test_delmarks_command(self):
        """Test delmarks command (delete all)."""
        self.sm.bookmarks.set("a", 10, 20)
        self.sm.bookmarks.set("b", 30, 40)
        self.sm.bookmarks.set("c", 50, 60)

        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "delmarks"
        self.sm.command_buffer.cursor_pos = 8

        result = self.sm.process(action_event(Action.NEWLINE))
        assert "All marks deleted" in result.message
        assert len(self.sm.bookmarks.list_all()) == 0


class TestModeStateMachineEdgeCases:
    """Tests for ModeStateMachine edge cases and state transitions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.canvas = Canvas()
        self.viewport = Viewport(width=80, height=24)
        self.sm = ModeStateMachine(self.canvas, self.viewport)

    def test_mode_name_property(self):
        """Test mode_name property for all modes."""
        for mode in Mode:
            self.sm.set_mode(mode)
            assert self.sm.mode_name == mode.name

    def test_set_mode_clears_command_buffer(self):
        """Test that leaving COMMAND mode clears the buffer."""
        self.sm.set_mode(Mode.COMMAND)
        self.sm.command_buffer.text = "some text"
        self.sm.command_buffer.cursor_pos = 9

        self.sm.set_mode(Mode.NAV)

        assert self.sm.command_buffer.text == ""
        assert self.sm.command_buffer.cursor_pos == 0

    def test_set_mode_captures_edit_start_x(self):
        """Test that entering EDIT mode captures starting X."""
        self.viewport.cursor.set(42, 10)
        self.sm.set_mode(Mode.EDIT)

        assert self.sm._edit_start_x == 42

    def test_edit_mode_newline_uses_start_x(self):
        """Test that newline in EDIT mode returns to start X."""
        self.viewport.cursor.set(25, 10)
        self.sm.set_mode(Mode.EDIT)

        # Move cursor and type
        self.viewport.cursor.set(40, 10)

        # Press Enter
        self.sm.process(action_event(Action.NEWLINE))

        assert self.viewport.cursor.x == 25
        assert self.viewport.cursor.y == 11

    def test_toggle_pan_mode_from_other_modes(self):
        """Test toggle_pan_mode only works from NAV/PAN."""
        self.sm.set_mode(Mode.EDIT)
        self.sm.toggle_pan_mode()
        assert self.sm.mode == Mode.EDIT  # Should not change

    def test_pan_mode_toggle_pan(self):
        """Test toggling pan mode from within PAN mode."""
        self.sm.set_mode(Mode.PAN)
        result = self.sm.process(action_event(Action.TOGGLE_PAN_MODE))

        assert result.mode_changed
        assert self.sm.mode == Mode.NAV

    def test_pan_mode_enter_edit(self):
        """Test entering EDIT mode from PAN mode."""
        self.sm.set_mode(Mode.PAN)
        result = self.sm.process(action_event(Action.ENTER_EDIT_MODE))

        assert result.mode_changed
        assert self.sm.mode == Mode.EDIT

    def test_pan_mode_enter_command(self):
        """Test entering COMMAND mode from PAN mode."""
        self.sm.set_mode(Mode.PAN)
        result = self.sm.process(action_event(Action.ENTER_COMMAND_MODE))

        assert result.mode_changed
        assert self.sm.mode == Mode.COMMAND

    def test_pan_mode_centering(self):
        """Test centering actions in PAN mode."""
        self.sm.set_mode(Mode.PAN)
        self.viewport.cursor.set(100, 100)

        result = self.sm.process(action_event(Action.CENTER_CURSOR))
        assert result.handled

        result = self.sm.process(action_event(Action.CENTER_ORIGIN))
        assert result.handled

    def test_pan_mode_unhandled(self):
        """Test unhandled action in PAN mode."""
        self.sm.set_mode(Mode.PAN)

        result = self.sm.process(action_event(Action.HELP))
        assert result.handled is False

    def test_nav_mode_center_origin(self):
        """Test centering on origin in NAV mode."""
        self.sm.process(action_event(Action.CENTER_ORIGIN))
        # Should not crash; viewport centered on origin

    def test_nav_mode_all_pan_directions(self):
        """Test all viewport pan directions in NAV mode."""
        actions = [Action.PAN_UP, Action.PAN_DOWN, Action.PAN_LEFT, Action.PAN_RIGHT]
        for action in actions:
            result = self.sm.process(action_event(action))
            assert result.handled

    def test_nav_mode_unhandled_action(self):
        """Test unhandled action in NAV mode."""
        result = self.sm.process(action_event(Action.NONE))
        assert result.handled is False

    def test_nav_mode_undo_command(self):
        """Test undo triggers command in NAV mode."""
        result = self.sm.process(char_event("u"))
        assert result.command == "undo"

    def test_edit_mode_unhandled_action(self):
        """Test unhandled action in EDIT mode."""
        self.sm.set_mode(Mode.EDIT)

        result = self.sm.process(action_event(Action.HELP))
        assert result.handled is False

    def test_draw_mode_unhandled_action(self):
        """Test unhandled action in DRAW mode."""
        self.sm.process(char_event("D"))

        result = self.sm.process(action_event(Action.HELP))
        assert result.handled is False


class TestModeConfig:
    """Tests for ModeConfig dataclass."""

    def test_default_config(self):
        """Test default ModeConfig values."""
        config = ModeConfig()

        assert config.move_step == 1
        assert config.move_fast_step == 10
        assert config.pan_step == 5
        assert config.auto_advance is True
        assert config.advance_direction == (1, 0)
        assert config.scroll_margin == 3

    def test_custom_config(self):
        """Test custom ModeConfig values."""
        config = ModeConfig(
            move_step=2,
            move_fast_step=20,
            pan_step=10,
            auto_advance=False,
            advance_direction=(0, 1),
            scroll_margin=5,
        )

        assert config.move_step == 2
        assert config.move_fast_step == 20
        assert config.pan_step == 10
        assert config.auto_advance is False
        assert config.advance_direction == (0, 1)
        assert config.scroll_margin == 5


class TestModeResult:
    """Tests for ModeResult dataclass."""

    def test_default_result(self):
        """Test default ModeResult values."""
        result = ModeResult()

        assert result.handled is True
        assert result.mode_changed is False
        assert result.new_mode is None
        assert result.command is None
        assert result.message is None
        assert result.message_frames == 2
        assert result.quit is False

    def test_custom_result(self):
        """Test custom ModeResult values."""
        result = ModeResult(
            handled=False,
            mode_changed=True,
            new_mode=Mode.EDIT,
            command="test",
            message="Test message",
            message_frames=5,
            quit=True,
        )

        assert result.handled is False
        assert result.mode_changed is True
        assert result.new_mode == Mode.EDIT
        assert result.command == "test"
        assert result.message == "Test message"
        assert result.message_frames == 5
        assert result.quit is True


class TestBookmarkDataclass:
    """Tests for Bookmark dataclass."""

    def test_bookmark_creation(self):
        """Test Bookmark creation with all fields."""
        bm = Bookmark(x=10, y=20, name="test")

        assert bm.x == 10
        assert bm.y == 20
        assert bm.name == "test"

    def test_bookmark_default_name(self):
        """Test Bookmark with default name."""
        bm = Bookmark(x=10, y=20)

        assert bm.name == ""


def test_command_buffer():
    """Run CommandBuffer tests."""
    tests = TestCommandBuffer()
    tests.test_insert()
    tests.test_insert_middle()
    tests.test_backspace()
    tests.test_backspace_at_start()
    tests.test_delete()
    tests.test_move_cursor()
    tests.test_submit()
    tests.test_history_navigation()
    tests.test_clear()


def test_mode_state_machine():
    """Run ModeStateMachine tests."""
    tests = TestModeStateMachine()

    tests.setup_method()
    tests.test_initial_mode()

    tests.setup_method()
    tests.test_set_mode()

    tests.setup_method()
    tests.test_toggle_pan_mode()

    tests.setup_method()
    tests.test_nav_cursor_movement()

    tests.setup_method()
    tests.test_nav_fast_movement()

    tests.setup_method()
    tests.test_nav_enter_edit_mode()

    tests.setup_method()
    tests.test_nav_toggle_pan()

    tests.setup_method()
    tests.test_nav_enter_command_mode()

    tests.setup_method()
    tests.test_nav_center_cursor()

    tests.setup_method()
    tests.test_nav_pan_viewport()

    tests.setup_method()
    tests.test_pan_mode_movement_pans_viewport()

    tests.setup_method()
    tests.test_pan_mode_exit()

    tests.setup_method()
    tests.test_edit_mode_typing()

    tests.setup_method()
    tests.test_edit_mode_backspace()

    tests.setup_method()
    tests.test_edit_mode_delete()

    tests.setup_method()
    tests.test_edit_mode_newline()

    tests.setup_method()
    tests.test_edit_mode_exit()

    tests.setup_method()
    tests.test_edit_mode_cursor_movement()

    tests.setup_method()
    tests.test_command_mode_typing()

    tests.setup_method()
    tests.test_command_mode_backspace()

    tests.setup_method()
    tests.test_command_mode_submit()

    tests.setup_method()
    tests.test_command_mode_exit()

    tests.setup_method()
    tests.test_command_mode_history()

    tests.setup_method()
    tests.test_command_quit()

    tests.setup_method()
    tests.test_command_goto()

    tests.setup_method()
    tests.test_command_origin_here()

    tests.setup_method()
    tests.test_command_origin_coords()

    tests.setup_method()
    tests.test_command_clear()

    tests.setup_method()
    tests.test_unknown_command()

    tests.setup_method()
    tests.test_quit_from_any_mode()

    tests.setup_method()
    tests.test_register_custom_command()


if __name__ == "__main__":
    test_command_buffer()
    test_mode_state_machine()
    print("All mode tests passed!")
