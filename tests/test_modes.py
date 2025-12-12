"""Tests for mode state machine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from canvas import Canvas
from viewport import Viewport
from input import Action, InputEvent
from modes import (
    Mode, ModeConfig, CommandBuffer, ModeResult, ModeStateMachine
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
        buf.insert('a')
        buf.insert('b')
        buf.insert('c')
        assert buf.text == "abc"
        assert buf.cursor_pos == 3

    def test_insert_middle(self):
        buf = CommandBuffer()
        buf.text = "ac"
        buf.cursor_pos = 1
        buf.insert('b')
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

        result = self.sm.process(char_event('X'))
        assert result.handled
        assert self.canvas.get_char(5, 5) == 'X'
        # Cursor should advance
        assert self.viewport.cursor.x == 6

    def test_edit_mode_backspace(self):
        self.sm.set_mode(Mode.EDIT)
        self.viewport.cursor.set(5, 5)
        self.canvas.set(4, 5, 'A')

        result = self.sm.process(action_event(Action.BACKSPACE))
        assert result.handled
        assert self.viewport.cursor.x == 4
        assert self.canvas.is_empty_at(4, 5)

    def test_edit_mode_delete(self):
        self.sm.set_mode(Mode.EDIT)
        self.viewport.cursor.set(5, 5)
        self.canvas.set(5, 5, 'A')

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
        self.sm.process(char_event('g'))
        self.sm.process(char_event('o'))
        self.sm.process(char_event('t'))
        self.sm.process(char_event('o'))

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
        self.canvas.set(0, 0, 'X')
        self.canvas.set(10, 10, 'Y')
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
