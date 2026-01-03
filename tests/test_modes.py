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
