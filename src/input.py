"""
Pygame-based input handler for responsive keyboard and mouse input.

Uses pygame for input only - no display window created.
Provides non-blocking input, key repeat control, and modifier detection.
"""

import pygame
from pygame.locals import *
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable


class Action(Enum):
    """Editor actions that can be triggered by input."""
    # Navigation
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()

    # Fast navigation
    MOVE_UP_FAST = auto()
    MOVE_DOWN_FAST = auto()
    MOVE_LEFT_FAST = auto()
    MOVE_RIGHT_FAST = auto()

    # Viewport
    PAN_UP = auto()
    PAN_DOWN = auto()
    PAN_LEFT = auto()
    PAN_RIGHT = auto()
    CENTER_CURSOR = auto()
    CENTER_ORIGIN = auto()

    # Modes
    ENTER_EDIT_MODE = auto()
    ENTER_PAN_MODE = auto()
    ENTER_COMMAND_MODE = auto()
    ENTER_DRAW_MODE = auto()
    EXIT_MODE = auto()
    TOGGLE_PAN_MODE = auto()

    # Grid
    TOGGLE_GRID_MAJOR = auto()
    TOGGLE_GRID_MINOR = auto()
    TOGGLE_GRID_ORIGIN = auto()

    # Editing
    DELETE_CHAR = auto()
    BACKSPACE = auto()
    NEWLINE = auto()

    # History
    UNDO = auto()
    REDO = auto()

    # File operations
    SAVE = auto()
    SAVE_AS = auto()
    OPEN = auto()
    NEW = auto()

    # Application
    QUIT = auto()
    HELP = auto()

    # Special
    NONE = auto()


@dataclass
class KeyBinding:
    """A single key binding."""
    key: int                    # pygame key constant
    mods: int = 0               # Modifier flags (KMOD_CTRL, etc.)
    action: Action = Action.NONE

    def matches(self, key: int, mods: int) -> bool:
        """Check if this binding matches the given key and modifiers."""
        if self.key != key:
            return False

        # Check required modifiers
        if self.mods:
            # Mask out irrelevant modifiers (caps lock, num lock, etc.)
            relevant_mods = mods & (KMOD_CTRL | KMOD_SHIFT | KMOD_ALT | KMOD_META)
            required = self.mods & (KMOD_CTRL | KMOD_SHIFT | KMOD_ALT | KMOD_META)
            return (relevant_mods & required) == required

        return True


@dataclass
class InputEvent:
    """Processed input event."""
    action: Action = Action.NONE
    char: str | None = None     # Character typed (for edit mode)
    mouse_pos: tuple[int, int] | None = None
    mouse_button: int | None = None
    raw_key: int | None = None
    mods: int = 0


@dataclass
class InputHandler:
    """
    Pygame-based input handler.

    Handles keyboard and mouse input with configurable key bindings.
    Runs in "headless" mode - pygame handles input but not display.
    """
    bindings: list[KeyBinding] = field(default_factory=list)
    _initialized: bool = field(default=False, repr=False)

    # Key repeat settings
    repeat_delay: int = 300     # ms before repeat starts
    repeat_interval: int = 30   # ms between repeats

    def __post_init__(self):
        if not self.bindings:
            self.bindings = self._default_bindings()

    def init(self) -> None:
        """Initialize pygame for input handling."""
        if self._initialized:
            return

        # Initialize only the modules we need
        pygame.display.init()
        pygame.key.set_repeat(self.repeat_delay, self.repeat_interval)

        # Create a tiny hidden window (required for input)
        # This window will be hidden/minimized
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

        self._initialized = True

    def quit(self) -> None:
        """Cleanup pygame."""
        if self._initialized:
            pygame.quit()
            self._initialized = False

    def poll(self) -> list[InputEvent]:
        """
        Poll for input events (non-blocking).

        Returns list of InputEvents that occurred since last poll.
        """
        if not self._initialized:
            self.init()

        events = []

        for event in pygame.event.get():
            if event.type == QUIT:
                events.append(InputEvent(action=Action.QUIT))

            elif event.type == KEYDOWN:
                input_event = self._process_key(event)
                if input_event:
                    events.append(input_event)

            elif event.type == MOUSEBUTTONDOWN:
                events.append(InputEvent(
                    mouse_pos=event.pos,
                    mouse_button=event.button
                ))

            elif event.type == MOUSEMOTION:
                # Could track mouse position if needed
                pass

        return events

    def wait(self, timeout_ms: int = 0) -> list[InputEvent]:
        """
        Wait for input events.

        Args:
            timeout_ms: Max time to wait (0 = forever)

        Returns:
            List of InputEvents
        """
        if not self._initialized:
            self.init()

        if timeout_ms > 0:
            pygame.time.wait(timeout_ms)

        return self.poll()

    def _process_key(self, event: pygame.event.Event) -> InputEvent | None:
        """Process a KEYDOWN event into an InputEvent."""
        key = event.key
        mods = event.mod

        # Check for bound actions
        for binding in self.bindings:
            if binding.matches(key, mods):
                return InputEvent(
                    action=binding.action,
                    raw_key=key,
                    mods=mods
                )

        # Handle printable characters for edit mode
        if event.unicode and len(event.unicode) == 1:
            char = event.unicode
            if char.isprintable():
                return InputEvent(
                    char=char,
                    raw_key=key,
                    mods=mods
                )

        # Return raw key event
        return InputEvent(raw_key=key, mods=mods)

    def _default_bindings(self) -> list[KeyBinding]:
        """Create default key bindings."""
        return [
            # Navigation - WASD
            KeyBinding(K_w, 0, Action.MOVE_UP),
            KeyBinding(K_s, 0, Action.MOVE_DOWN),
            KeyBinding(K_a, 0, Action.MOVE_LEFT),
            KeyBinding(K_d, 0, Action.MOVE_RIGHT),

            # Navigation - Arrows
            KeyBinding(K_UP, 0, Action.MOVE_UP),
            KeyBinding(K_DOWN, 0, Action.MOVE_DOWN),
            KeyBinding(K_LEFT, 0, Action.MOVE_LEFT),
            KeyBinding(K_RIGHT, 0, Action.MOVE_RIGHT),

            # Fast navigation - Shift + WASD
            KeyBinding(K_w, KMOD_SHIFT, Action.MOVE_UP_FAST),
            KeyBinding(K_s, KMOD_SHIFT, Action.MOVE_DOWN_FAST),
            KeyBinding(K_a, KMOD_SHIFT, Action.MOVE_LEFT_FAST),
            KeyBinding(K_d, KMOD_SHIFT, Action.MOVE_RIGHT_FAST),

            # Fast navigation - Shift + Arrows
            KeyBinding(K_UP, KMOD_SHIFT, Action.MOVE_UP_FAST),
            KeyBinding(K_DOWN, KMOD_SHIFT, Action.MOVE_DOWN_FAST),
            KeyBinding(K_LEFT, KMOD_SHIFT, Action.MOVE_LEFT_FAST),
            KeyBinding(K_RIGHT, KMOD_SHIFT, Action.MOVE_RIGHT_FAST),

            # Viewport panning - Ctrl + Arrows
            KeyBinding(K_UP, KMOD_CTRL, Action.PAN_UP),
            KeyBinding(K_DOWN, KMOD_CTRL, Action.PAN_DOWN),
            KeyBinding(K_LEFT, KMOD_CTRL, Action.PAN_LEFT),
            KeyBinding(K_RIGHT, KMOD_CTRL, Action.PAN_RIGHT),

            # Centering
            KeyBinding(K_c, KMOD_CTRL, Action.CENTER_CURSOR),
            KeyBinding(K_o, KMOD_CTRL, Action.CENTER_ORIGIN),

            # Mode switching
            KeyBinding(K_i, 0, Action.ENTER_EDIT_MODE),
            KeyBinding(K_ESCAPE, 0, Action.EXIT_MODE),
            KeyBinding(K_p, 0, Action.TOGGLE_PAN_MODE),
            KeyBinding(K_SEMICOLON, KMOD_SHIFT, Action.ENTER_COMMAND_MODE),  # :
            KeyBinding(K_SLASH, 0, Action.ENTER_COMMAND_MODE),

            # Grid toggles
            KeyBinding(K_g, 0, Action.TOGGLE_GRID_MAJOR),
            KeyBinding(K_g, KMOD_SHIFT, Action.TOGGLE_GRID_MINOR),
            KeyBinding(K_0, 0, Action.TOGGLE_GRID_ORIGIN),

            # Editing
            KeyBinding(K_DELETE, 0, Action.DELETE_CHAR),
            KeyBinding(K_BACKSPACE, 0, Action.BACKSPACE),
            KeyBinding(K_RETURN, 0, Action.NEWLINE),
            KeyBinding(K_KP_ENTER, 0, Action.NEWLINE),

            # History (undo/redo)
            KeyBinding(K_z, KMOD_CTRL, Action.UNDO),
            KeyBinding(K_r, KMOD_CTRL, Action.REDO),

            # File operations
            KeyBinding(K_s, KMOD_CTRL, Action.SAVE),
            KeyBinding(K_s, KMOD_CTRL | KMOD_SHIFT, Action.SAVE_AS),
            KeyBinding(K_o, 0, Action.OPEN),
            KeyBinding(K_n, KMOD_CTRL, Action.NEW),

            # Application
            KeyBinding(K_q, 0, Action.QUIT),
            KeyBinding(K_q, KMOD_CTRL, Action.QUIT),
            KeyBinding(K_F1, 0, Action.HELP),
            KeyBinding(K_h, KMOD_CTRL, Action.HELP),
        ]

    def add_binding(self, key: int, mods: int, action: Action) -> None:
        """Add a new key binding."""
        self.bindings.insert(0, KeyBinding(key, mods, action))

    def remove_binding(self, action: Action) -> None:
        """Remove all bindings for an action."""
        self.bindings = [b for b in self.bindings if b.action != action]

    def get_bindings_for_action(self, action: Action) -> list[KeyBinding]:
        """Get all bindings for an action."""
        return [b for b in self.bindings if b.action == action]

    def set_repeat(self, delay: int, interval: int) -> None:
        """Configure key repeat timing."""
        self.repeat_delay = delay
        self.repeat_interval = interval
        if self._initialized:
            pygame.key.set_repeat(delay, interval)

    def disable_repeat(self) -> None:
        """Disable key repeat."""
        if self._initialized:
            pygame.key.set_repeat(0, 0)

    def enable_repeat(self) -> None:
        """Re-enable key repeat with current settings."""
        if self._initialized:
            pygame.key.set_repeat(self.repeat_delay, self.repeat_interval)


def key_name(key: int) -> str:
    """Get human-readable name for a pygame key constant."""
    return pygame.key.name(key)


def format_binding(binding: KeyBinding) -> str:
    """Format a key binding as human-readable string."""
    parts = []

    if binding.mods & KMOD_CTRL:
        parts.append("Ctrl")
    if binding.mods & KMOD_ALT:
        parts.append("Alt")
    if binding.mods & KMOD_SHIFT:
        parts.append("Shift")
    if binding.mods & KMOD_META:
        parts.append("Meta")

    # Get key name
    key_str = pygame.key.name(binding.key)
    parts.append(key_str.capitalize())

    return "+".join(parts)
