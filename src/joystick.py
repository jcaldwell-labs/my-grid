"""
Joystick input handler for my-grid.

Provides cross-platform joystick support using pygame.
Works on Windows native and WSL via USB passthrough (usbipd).
"""

import time
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable

# pygame import is deferred to avoid loading if not needed
_pygame_available: Optional[bool] = None
_pygame = None


def _check_pygame() -> bool:
    """Check if pygame is available and can be imported."""
    global _pygame_available, _pygame
    if _pygame_available is None:
        try:
            import pygame
            _pygame = pygame
            _pygame_available = True
        except ImportError:
            _pygame_available = False
    return _pygame_available


class JoystickDirection(Enum):
    """Digital direction from joystick axes."""
    NONE = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    UP_LEFT = auto()
    UP_RIGHT = auto()
    DOWN_LEFT = auto()
    DOWN_RIGHT = auto()


@dataclass
class JoystickState:
    """Current state of joystick inputs."""
    # Analog axis values (-1.0 to 1.0)
    x_axis: float = 0.0
    y_axis: float = 0.0

    # Digital direction (derived from axes)
    direction: JoystickDirection = JoystickDirection.NONE

    # Button states (dict of button_id -> pressed)
    buttons: dict = field(default_factory=dict)

    # Connection status
    connected: bool = False
    name: str = ""


@dataclass
class JoystickConfig:
    """Joystick configuration settings."""
    # Deadzone for analog sticks (0.0 to 1.0)
    deadzone: float = 0.15

    # Threshold for converting analog to digital direction
    digital_threshold: float = 0.5

    # Movement repeat rate when holding direction (moves per second)
    repeat_rate: float = 10.0

    # Initial delay before repeat starts (seconds)
    repeat_delay: float = 0.3

    # Button mappings (button_id -> action name)
    button_map: dict = field(default_factory=lambda: {
        0: "select",   # Usually A/Cross
        1: "back",     # Usually B/Circle
        2: "action1",  # X/Square
        3: "action2",  # Y/Triangle
    })


class JoystickHandler:
    """
    Handles joystick input with auto-detection and reconnection.

    Designed to work alongside curses keyboard input, providing
    continuous directional input when the stick is held.
    """

    def __init__(self, config: JoystickConfig | None = None):
        self.config = config or JoystickConfig()
        self._joystick = None
        self._initialized = False
        self._healthy = True
        self._last_health_check = 0.0

        # Direction repeat tracking
        self._last_direction = JoystickDirection.NONE
        self._direction_start_time = 0.0
        self._last_repeat_time = 0.0
        self._repeat_triggered = False

        # Button state tracking (for edge detection)
        self._prev_buttons: dict = {}

        # Reconnection tracking
        self._reconnect_interval = 1.0  # seconds
        self._last_reconnect_attempt = 0.0

        # Thread safety
        self._lock = threading.Lock()

    def init(self, silent: bool = False) -> bool:
        """
        Initialize joystick subsystem and detect joystick.

        Args:
            silent: If True, suppress status messages

        Returns:
            True if joystick was found and initialized
        """
        if not _check_pygame():
            if not silent:
                print("pygame not available - joystick disabled")
            return False

        try:
            _pygame.init()
            _pygame.joystick.init()

            if _pygame.joystick.get_count() > 0:
                self._joystick = _pygame.joystick.Joystick(0)
                self._joystick.init()
                self._initialized = True
                self._healthy = True

                # Initialize button tracking
                _pygame.event.pump()
                time.sleep(0.05)  # Let state settle
                for i in range(self._joystick.get_numbuttons()):
                    self._prev_buttons[i] = self._joystick.get_button(i)

                if not silent:
                    print(f"Joystick: {self._joystick.get_name()}")
                return True
            else:
                if not silent:
                    print("No joystick detected")
                return False

        except Exception as e:
            if not silent:
                print(f"Joystick init failed: {e}")
            self._initialized = False
            return False

    def cleanup(self) -> None:
        """Clean up joystick resources."""
        with self._lock:
            if self._joystick:
                try:
                    self._joystick.quit()
                except Exception:
                    pass
                self._joystick = None

            if _pygame_available and _pygame:
                try:
                    _pygame.joystick.quit()
                except Exception:
                    pass

            self._initialized = False
            self._healthy = False

    def _check_health(self) -> bool:
        """Check if joystick is still responsive."""
        if not self._initialized or not self._joystick:
            return False

        now = time.time()
        if now - self._last_health_check < 1.0:
            return self._healthy

        self._last_health_check = now

        try:
            _ = self._joystick.get_numaxes()
            self._healthy = True
            return True
        except Exception:
            self._healthy = False
            self._initialized = False
            if self._joystick:
                try:
                    self._joystick.quit()
                except Exception:
                    pass
                self._joystick = None
            return False

    def _attempt_reconnect(self) -> bool:
        """Try to reconnect if joystick was disconnected."""
        if self._initialized:
            return True

        now = time.time()
        if now - self._last_reconnect_attempt < self._reconnect_interval:
            return False

        self._last_reconnect_attempt = now

        try:
            if self._joystick:
                try:
                    self._joystick.quit()
                except Exception:
                    pass
                self._joystick = None

            _pygame.joystick.quit()
            _pygame.joystick.init()

            if _pygame.joystick.get_count() > 0:
                self._joystick = _pygame.joystick.Joystick(0)
                self._joystick.init()
                self._initialized = True
                self._healthy = True

                _pygame.event.pump()
                self._prev_buttons = {}
                for i in range(self._joystick.get_numbuttons()):
                    self._prev_buttons[i] = self._joystick.get_button(i)

                return True
        except Exception:
            pass

        return False

    def poll(self) -> JoystickState:
        """
        Poll current joystick state.

        Returns:
            Current JoystickState
        """
        state = JoystickState()

        # Try reconnect if needed
        if not self._initialized:
            self._attempt_reconnect()

        if not self._check_health():
            return state

        try:
            _pygame.event.pump()

            state.connected = True
            state.name = self._joystick.get_name()

            # Read axes
            if self._joystick.get_numaxes() >= 2:
                raw_x = self._joystick.get_axis(0)
                raw_y = self._joystick.get_axis(1)

                # Apply deadzone
                state.x_axis = raw_x if abs(raw_x) > self.config.deadzone else 0.0
                state.y_axis = raw_y if abs(raw_y) > self.config.deadzone else 0.0

            # Determine digital direction
            state.direction = self._axes_to_direction(state.x_axis, state.y_axis)

            # Read buttons
            for i in range(self._joystick.get_numbuttons()):
                state.buttons[i] = self._joystick.get_button(i)

        except Exception:
            self._healthy = False
            self._initialized = False
            state.connected = False

        return state

    def _axes_to_direction(self, x: float, y: float) -> JoystickDirection:
        """Convert analog axes to digital direction."""
        threshold = self.config.digital_threshold

        up = y < -threshold
        down = y > threshold
        left = x < -threshold
        right = x > threshold

        if up and left:
            return JoystickDirection.UP_LEFT
        elif up and right:
            return JoystickDirection.UP_RIGHT
        elif down and left:
            return JoystickDirection.DOWN_LEFT
        elif down and right:
            return JoystickDirection.DOWN_RIGHT
        elif up:
            return JoystickDirection.UP
        elif down:
            return JoystickDirection.DOWN
        elif left:
            return JoystickDirection.LEFT
        elif right:
            return JoystickDirection.RIGHT
        else:
            return JoystickDirection.NONE

    def get_movement(self) -> tuple[int, int]:
        """
        Get movement delta based on joystick direction with repeat.

        Implements press-and-hold repeat behavior:
        - First press: immediate movement
        - Hold: wait for repeat_delay, then repeat at repeat_rate

        Returns:
            (dx, dy) movement delta
        """
        state = self.poll()
        direction = state.direction
        now = time.time()

        # Direction changed
        if direction != self._last_direction:
            self._last_direction = direction
            self._direction_start_time = now
            self._last_repeat_time = now
            self._repeat_triggered = False

            # Immediate movement on new direction
            return self._direction_to_delta(direction)

        # Same direction held
        if direction != JoystickDirection.NONE:
            held_time = now - self._direction_start_time

            # Check if we should repeat
            if held_time >= self.config.repeat_delay:
                repeat_interval = 1.0 / self.config.repeat_rate
                if now - self._last_repeat_time >= repeat_interval:
                    self._last_repeat_time = now
                    self._repeat_triggered = True
                    return self._direction_to_delta(direction)

        return (0, 0)

    def _direction_to_delta(self, direction: JoystickDirection) -> tuple[int, int]:
        """Convert direction to (dx, dy) delta."""
        deltas = {
            JoystickDirection.NONE: (0, 0),
            JoystickDirection.UP: (0, -1),
            JoystickDirection.DOWN: (0, 1),
            JoystickDirection.LEFT: (-1, 0),
            JoystickDirection.RIGHT: (1, 0),
            JoystickDirection.UP_LEFT: (-1, -1),
            JoystickDirection.UP_RIGHT: (1, -1),
            JoystickDirection.DOWN_LEFT: (-1, 1),
            JoystickDirection.DOWN_RIGHT: (1, 1),
        }
        return deltas.get(direction, (0, 0))

    def get_button_presses(self) -> list[int]:
        """
        Get list of buttons that were just pressed (edge detection).

        Returns:
            List of button IDs that transitioned from released to pressed
        """
        state = self.poll()
        pressed = []

        for btn_id, is_pressed in state.buttons.items():
            was_pressed = self._prev_buttons.get(btn_id, False)
            if is_pressed and not was_pressed:
                pressed.append(btn_id)

        self._prev_buttons = state.buttons.copy()
        return pressed

    def get_info(self) -> dict:
        """Get joystick information for status display."""
        if not self._initialized or not self._joystick:
            return {
                "connected": False,
                "name": None,
                "axes": 0,
                "buttons": 0,
            }

        try:
            return {
                "connected": True,
                "name": self._joystick.get_name(),
                "axes": self._joystick.get_numaxes(),
                "buttons": self._joystick.get_numbuttons(),
            }
        except Exception:
            return {
                "connected": False,
                "name": None,
                "axes": 0,
                "buttons": 0,
            }

    @property
    def is_connected(self) -> bool:
        """Check if joystick is currently connected."""
        return self._initialized and self._healthy
