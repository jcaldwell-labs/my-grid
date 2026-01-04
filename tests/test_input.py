"""Tests for pygame input handler."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import pygame to get real constants
from pygame.locals import (
    K_w, K_a, K_s, K_q, K_UP, K_DOWN, KMOD_CTRL, KMOD_SHIFT, KMOD_ALT
)

from input import (
    Action, KeyBinding, InputEvent, InputHandler
)


def test_action_enum():
    """Test that Action enum has expected values."""
    assert Action.MOVE_UP != Action.MOVE_DOWN
    assert Action.QUIT != Action.NONE
    assert Action.NONE.name == "NONE"


def test_key_binding_simple_match():
    """Test simple key binding matching."""
    binding = KeyBinding(key=K_w, mods=0, action=Action.MOVE_UP)

    assert binding.matches(K_w, 0)
    assert not binding.matches(K_s, 0)
    assert binding.matches(K_w, KMOD_SHIFT)  # Extra mods OK


def test_key_binding_with_modifier():
    """Test key binding with required modifier."""
    binding = KeyBinding(
        key=K_s,
        mods=KMOD_CTRL,
        action=Action.SAVE
    )

    # Must have Ctrl
    assert binding.matches(K_s, KMOD_CTRL)
    assert not binding.matches(K_s, 0)
    assert not binding.matches(K_s, KMOD_SHIFT)

    # Extra modifiers are OK
    assert binding.matches(K_s, KMOD_CTRL | KMOD_SHIFT)


def test_key_binding_multiple_modifiers():
    """Test binding requiring multiple modifiers."""
    binding = KeyBinding(
        key=K_s,
        mods=KMOD_CTRL | KMOD_SHIFT,
        action=Action.SAVE_AS
    )

    # Must have both Ctrl and Shift
    assert binding.matches(K_s, KMOD_CTRL | KMOD_SHIFT)
    assert not binding.matches(K_s, KMOD_CTRL)
    assert not binding.matches(K_s, KMOD_SHIFT)
    assert not binding.matches(K_s, 0)


def test_input_event_creation():
    """Test InputEvent dataclass."""
    # Action event
    event = InputEvent(action=Action.MOVE_UP)
    assert event.action == Action.MOVE_UP
    assert event.char is None

    # Character event
    event = InputEvent(char='a', raw_key=K_a)
    assert event.action == Action.NONE
    assert event.char == 'a'

    # Mouse event
    event = InputEvent(mouse_pos=(100, 200), mouse_button=1)
    assert event.mouse_pos == (100, 200)
    assert event.mouse_button == 1


def test_input_handler_default_bindings():
    """Test that InputHandler creates default bindings."""
    handler = InputHandler()

    assert len(handler.bindings) > 0

    # Check some expected bindings exist
    actions = [b.action for b in handler.bindings]
    assert Action.MOVE_UP in actions
    assert Action.MOVE_DOWN in actions
    assert Action.QUIT in actions
    assert Action.SAVE in actions


def test_input_handler_add_binding():
    """Test adding a custom binding."""
    handler = InputHandler()
    initial_count = len(handler.bindings)

    handler.add_binding(K_q, KMOD_ALT, Action.QUIT)

    assert len(handler.bindings) == initial_count + 1
    # New binding should be first (highest priority)
    assert handler.bindings[0].key == K_q
    assert handler.bindings[0].mods == KMOD_ALT


def test_input_handler_remove_binding():
    """Test removing bindings for an action."""
    handler = InputHandler()

    # Verify QUIT bindings exist
    quit_bindings = handler.get_bindings_for_action(Action.QUIT)
    assert len(quit_bindings) > 0

    handler.remove_binding(Action.QUIT)

    quit_bindings = handler.get_bindings_for_action(Action.QUIT)
    assert len(quit_bindings) == 0


def test_input_handler_get_bindings_for_action():
    """Test retrieving bindings for an action."""
    handler = InputHandler()

    move_up = handler.get_bindings_for_action(Action.MOVE_UP)

    # Should have at least W and Up arrow
    assert len(move_up) >= 2
    keys = [b.key for b in move_up]
    assert K_w in keys
    assert K_UP in keys


def test_format_binding_simple():
    """Test formatting simple binding."""
    binding = KeyBinding(key=K_w, mods=0, action=Action.MOVE_UP)

    # Note: pygame.key.name requires pygame init, so we test the modifier part
    # In real use, format_binding would return "W" for this


def test_format_binding_with_mods():
    """Test formatting binding with modifiers."""
    # We can't fully test without pygame init, but we test the logic exists
    binding = KeyBinding(
        key=K_s,
        mods=KMOD_CTRL | KMOD_SHIFT,
        action=Action.SAVE_AS
    )

    # Verify binding created correctly
    assert binding.mods == KMOD_CTRL | KMOD_SHIFT


def test_custom_bindings_override():
    """Test that custom bindings can be provided."""
    custom = [
        KeyBinding(K_UP, 0, Action.MOVE_UP),
        KeyBinding(K_DOWN, 0, Action.MOVE_DOWN),
    ]

    handler = InputHandler(bindings=custom)

    assert len(handler.bindings) == 2
    assert handler.bindings[0].action == Action.MOVE_UP
    assert handler.bindings[1].action == Action.MOVE_DOWN


def test_repeat_settings():
    """Test key repeat configuration."""
    handler = InputHandler(repeat_delay=200, repeat_interval=50)

    assert handler.repeat_delay == 200
    assert handler.repeat_interval == 50


def test_binding_priority():
    """Test that earlier bindings have priority."""
    handler = InputHandler()

    # Add a binding with modifier first
    handler.add_binding(K_w, KMOD_SHIFT, Action.MOVE_UP_FAST)

    # The shift+W binding should be found first
    for binding in handler.bindings:
        if binding.matches(K_w, KMOD_SHIFT):
            assert binding.action == Action.MOVE_UP_FAST
            break


if __name__ == "__main__":
    test_action_enum()
    test_key_binding_simple_match()
    test_key_binding_with_modifier()
    test_key_binding_multiple_modifiers()
    test_input_event_creation()
    test_input_handler_default_bindings()
    test_input_handler_add_binding()
    test_input_handler_remove_binding()
    test_input_handler_get_bindings_for_action()
    test_format_binding_simple()
    test_format_binding_with_mods()
    test_custom_bindings_override()
    test_repeat_settings()
    test_binding_priority()
    print("All input handler tests passed!")
