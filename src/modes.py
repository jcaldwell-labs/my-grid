"""
Mode state machine for the ASCII canvas editor.

Handles different editor modes and their behaviors:
- Nav: Cursor movement around the canvas
- Pan: Viewport panning (cursor stays centered)
- Edit: Typing/drawing characters
- Command: Command palette input
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from canvas import Canvas
    from viewport import Viewport
    from input import Action, InputEvent
    from undo import UndoManager


class Mode(Enum):
    """Editor modes."""

    NAV = auto()
    PAN = auto()
    EDIT = auto()
    COMMAND = auto()
    MARK_SET = auto()  # Waiting for bookmark key (m + key)
    MARK_JUMP = auto()  # Waiting for bookmark key (' + key)
    VISUAL = auto()  # Visual selection mode
    DRAW = auto()  # Line drawing mode


@dataclass
class Bookmark:
    """A saved position on the canvas."""

    x: int
    y: int
    name: str = ""


class BookmarkManager:
    """
    Manages named bookmarks for quick navigation.

    Bookmarks are stored by single-character keys (a-z, 0-9).
    """

    def __init__(self):
        self._bookmarks: dict[str, Bookmark] = {}

    def set(self, key: str, x: int, y: int, name: str = "") -> None:
        """Set a bookmark at the given position."""
        key = key.lower()
        if len(key) == 1 and (key.isalnum()):
            self._bookmarks[key] = Bookmark(x=x, y=y, name=name)

    def get(self, key: str) -> Bookmark | None:
        """Get a bookmark by key."""
        return self._bookmarks.get(key.lower())

    def delete(self, key: str) -> bool:
        """Delete a bookmark. Returns True if deleted."""
        key = key.lower()
        if key in self._bookmarks:
            del self._bookmarks[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all bookmarks."""
        self._bookmarks.clear()

    def list_all(self) -> list[tuple[str, Bookmark]]:
        """Get all bookmarks as (key, bookmark) pairs, sorted by key."""
        return sorted(self._bookmarks.items())

    def to_dict(self) -> dict:
        """Serialize bookmarks for JSON export."""
        return {
            key: {"x": bm.x, "y": bm.y, "name": bm.name}
            for key, bm in self._bookmarks.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BookmarkManager":
        """Deserialize bookmarks from dictionary."""
        manager = cls()
        for key, bm_data in data.items():
            manager.set(
                key, bm_data.get("x", 0), bm_data.get("y", 0), bm_data.get("name", "")
            )
        return manager


@dataclass
class Selection:
    """
    Represents a rectangular selection on the canvas.

    The selection is defined by an anchor point and the current cursor position.
    The actual rectangle spans from min(anchor, cursor) to max(anchor, cursor).
    """

    anchor_x: int = 0
    anchor_y: int = 0
    cursor_x: int = 0
    cursor_y: int = 0

    @property
    def x1(self) -> int:
        """Left edge of selection."""
        return min(self.anchor_x, self.cursor_x)

    @property
    def y1(self) -> int:
        """Top edge of selection."""
        return min(self.anchor_y, self.cursor_y)

    @property
    def x2(self) -> int:
        """Right edge of selection (inclusive)."""
        return max(self.anchor_x, self.cursor_x)

    @property
    def y2(self) -> int:
        """Bottom edge of selection (inclusive)."""
        return max(self.anchor_y, self.cursor_y)

    @property
    def width(self) -> int:
        """Width of selection."""
        return self.x2 - self.x1 + 1

    @property
    def height(self) -> int:
        """Height of selection."""
        return self.y2 - self.y1 + 1

    def contains(self, x: int, y: int) -> bool:
        """Check if a point is within the selection."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def update_cursor(self, x: int, y: int) -> None:
        """Update the cursor position (extends/shrinks selection)."""
        self.cursor_x = x
        self.cursor_y = y


@dataclass
class ModeConfig:
    """Configuration for mode behaviors."""

    # Movement distances
    move_step: int = 1
    move_fast_step: int = 10
    pan_step: int = 5

    # Edit mode settings
    auto_advance: bool = True  # Move cursor after typing
    advance_direction: tuple[int, int] = (1, 0)  # (dx, dy) after typing

    # Scroll margin for cursor visibility
    scroll_margin: int = 3


@dataclass
class CommandBuffer:
    """Buffer for command mode input."""

    text: str = ""
    cursor_pos: int = 0
    history: list[str] = field(default_factory=list)
    history_index: int = -1

    def insert(self, char: str) -> None:
        """Insert character at cursor."""
        self.text = self.text[: self.cursor_pos] + char + self.text[self.cursor_pos :]
        self.cursor_pos += 1

    def backspace(self) -> None:
        """Delete character before cursor."""
        if self.cursor_pos > 0:
            self.text = self.text[: self.cursor_pos - 1] + self.text[self.cursor_pos :]
            self.cursor_pos -= 1

    def delete(self) -> None:
        """Delete character at cursor."""
        if self.cursor_pos < len(self.text):
            self.text = self.text[: self.cursor_pos] + self.text[self.cursor_pos + 1 :]

    def move_left(self) -> None:
        """Move cursor left."""
        self.cursor_pos = max(0, self.cursor_pos - 1)

    def move_right(self) -> None:
        """Move cursor right."""
        self.cursor_pos = min(len(self.text), self.cursor_pos + 1)

    def move_start(self) -> None:
        """Move cursor to start."""
        self.cursor_pos = 0

    def move_end(self) -> None:
        """Move cursor to end."""
        self.cursor_pos = len(self.text)

    def clear(self) -> None:
        """Clear the buffer."""
        self.text = ""
        self.cursor_pos = 0
        self.history_index = -1

    def submit(self) -> str:
        """Submit and clear buffer, add to history."""
        result = self.text
        if result and (not self.history or self.history[-1] != result):
            self.history.append(result)
        self.clear()
        return result

    def history_prev(self) -> None:
        """Navigate to previous history entry."""
        if not self.history:
            return
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.text = self.history[-(self.history_index + 1)]
            self.cursor_pos = len(self.text)

    def history_next(self) -> None:
        """Navigate to next history entry."""
        if self.history_index > 0:
            self.history_index -= 1
            self.text = self.history[-(self.history_index + 1)]
            self.cursor_pos = len(self.text)
        elif self.history_index == 0:
            self.history_index = -1
            self.text = ""
            self.cursor_pos = 0


@dataclass
class ModeResult:
    """Result of processing input in a mode."""

    handled: bool = True
    mode_changed: bool = False
    new_mode: Mode | None = None
    command: str | None = None  # For command mode submission
    message: str | None = None  # Status message to display
    message_frames: int = 2  # How long to show message (default 2 frames)
    quit: bool = False


class ModeStateMachine:
    """
    State machine managing editor modes.

    Processes input events based on current mode and manages transitions.
    """

    def __init__(
        self,
        canvas: "Canvas",
        viewport: "Viewport",
        config: ModeConfig | None = None,
        undo_manager: "UndoManager | None" = None,
    ):
        self.canvas = canvas
        self.viewport = viewport
        self.config = config or ModeConfig()
        self.undo_manager = undo_manager

        self._mode = Mode.NAV
        self._previous_mode = Mode.NAV
        self.command_buffer = CommandBuffer()
        self.bookmarks = BookmarkManager()
        self.selection: Selection | None = None  # Active selection for VISUAL mode

        # Drawing colors
        self.draw_fg: int = -1  # Foreground color (-1 = default)
        self.draw_bg: int = -1  # Background color (-1 = default)

        # Track edit mode starting column for Enter key behavior
        self._edit_start_x: int | None = None

        # Track last movement direction for DRAW mode
        self._draw_last_dir: tuple[int, int] | None = None
        # Pen state for DRAW mode (True = drawing, False = moving without drawing)
        self._draw_pen_down: bool = True
        # Frame guard to prevent double-toggle (when joystick A also sends spacebar)
        self._pen_toggled_this_frame: bool = False

        # Command handlers: command_name -> callable
        self._command_handlers: dict[str, Callable[[list[str]], ModeResult]] = {}
        self._register_default_commands()

    @property
    def mode(self) -> Mode:
        """Current mode."""
        return self._mode

    @property
    def mode_name(self) -> str:
        """Current mode name for display."""
        return self._mode.name

    def set_mode(self, mode: Mode) -> None:
        """Set the current mode."""
        self._previous_mode = self._mode
        self._mode = mode

        # Capture starting X position when entering edit mode
        if mode == Mode.EDIT:
            self._edit_start_x = self.viewport.cursor.x

        # Clear command buffer when leaving command mode
        if self._previous_mode == Mode.COMMAND and mode != Mode.COMMAND:
            self.command_buffer.clear()

    def toggle_pan_mode(self) -> None:
        """Toggle between NAV and PAN modes."""
        if self._mode == Mode.PAN:
            self.set_mode(Mode.NAV)
        elif self._mode == Mode.NAV:
            self.set_mode(Mode.PAN)

    def process(self, event: "InputEvent") -> ModeResult:
        """
        Process an input event based on current mode.

        Returns ModeResult indicating what happened.
        """
        from input import Action

        # Handle universal actions first
        if event.action == Action.QUIT:
            return ModeResult(quit=True)

        if event.action == Action.EXIT_MODE:
            return self._handle_exit_mode()

        # Delegate to mode-specific handler
        if self._mode == Mode.NAV:
            return self._process_nav(event)
        elif self._mode == Mode.PAN:
            return self._process_pan(event)
        elif self._mode == Mode.EDIT:
            return self._process_edit(event)
        elif self._mode == Mode.COMMAND:
            return self._process_command(event)
        elif self._mode == Mode.MARK_SET:
            return self._process_mark_set(event)
        elif self._mode == Mode.MARK_JUMP:
            return self._process_mark_jump(event)
        elif self._mode == Mode.VISUAL:
            return self._process_visual(event)
        elif self._mode == Mode.DRAW:
            return self._process_draw(event)

        return ModeResult(handled=False)

    def _handle_exit_mode(self) -> ModeResult:
        """Handle ESC key - exit current mode."""
        if self._mode == Mode.EDIT:
            self.set_mode(Mode.NAV)
            return ModeResult(mode_changed=True, new_mode=Mode.NAV)
        elif self._mode == Mode.PAN:
            self.set_mode(Mode.NAV)
            return ModeResult(mode_changed=True, new_mode=Mode.NAV)
        elif self._mode == Mode.COMMAND:
            self.command_buffer.clear()
            self.set_mode(Mode.NAV)
            return ModeResult(mode_changed=True, new_mode=Mode.NAV)
        elif self._mode in (Mode.MARK_SET, Mode.MARK_JUMP):
            self.set_mode(Mode.NAV)
            return ModeResult(mode_changed=True, new_mode=Mode.NAV, message="Cancelled")
        elif self._mode == Mode.VISUAL:
            self.selection = None
            self.set_mode(Mode.NAV)
            return ModeResult(
                mode_changed=True, new_mode=Mode.NAV, message="Selection cancelled"
            )
        elif self._mode == Mode.DRAW:
            self._draw_last_dir = None
            self.set_mode(Mode.NAV)
            return ModeResult(mode_changed=True, new_mode=Mode.NAV)
        return ModeResult()

    def _process_nav(self, event: "InputEvent") -> ModeResult:
        """Process input in NAV mode."""
        from input import Action

        action = event.action
        cfg = self.config

        # Mode transitions
        if action == Action.ENTER_EDIT_MODE:
            self.set_mode(Mode.EDIT)
            return ModeResult(mode_changed=True, new_mode=Mode.EDIT)

        if action == Action.TOGGLE_PAN_MODE:
            self.toggle_pan_mode()
            return ModeResult(mode_changed=True, new_mode=self._mode)

        if action == Action.ENTER_COMMAND_MODE:
            self.set_mode(Mode.COMMAND)
            return ModeResult(mode_changed=True, new_mode=Mode.COMMAND)

        if action == Action.ENTER_DRAW_MODE:
            self._draw_last_dir = None
            self._draw_pen_down = True  # Start with pen down
            self.set_mode(Mode.DRAW)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.DRAW,
                message="-- DRAW -- pen DOWN (wasd to draw, space to lift)",
            )

        # Cursor movement
        moved = self._handle_movement(action, cfg.move_step, cfg.move_fast_step)
        if moved:
            self.viewport.ensure_cursor_visible(margin=cfg.scroll_margin)
            return ModeResult()

        # Viewport centering
        if action == Action.CENTER_CURSOR:
            self.viewport.center_on_cursor()
            return ModeResult()

        if action == Action.CENTER_ORIGIN:
            self.viewport.center_on_origin()
            return ModeResult()

        # Viewport panning
        if action == Action.PAN_UP:
            self.viewport.pan(0, -cfg.pan_step)
            return ModeResult()
        if action == Action.PAN_DOWN:
            self.viewport.pan(0, cfg.pan_step)
            return ModeResult()
        if action == Action.PAN_LEFT:
            self.viewport.pan(-cfg.pan_step, 0)
            return ModeResult()
        if action == Action.PAN_RIGHT:
            self.viewport.pan(cfg.pan_step, 0)
            return ModeResult()

        # Bookmark triggers (handled by char, not action)
        if event.char == "m":
            self.set_mode(Mode.MARK_SET)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.MARK_SET,
                message="Set mark: press a-z or 0-9",
            )
        if event.char == "'":
            self.set_mode(Mode.MARK_JUMP)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.MARK_JUMP,
                message="Jump to mark: press a-z or 0-9",
            )

        # Visual selection mode
        if event.char == "v":
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            self.selection = Selection(
                anchor_x=cx, anchor_y=cy, cursor_x=cx, cursor_y=cy
            )
            self.set_mode(Mode.VISUAL)
            return ModeResult(
                mode_changed=True, new_mode=Mode.VISUAL, message="-- VISUAL -- (1x1)"
            )

        # Draw mode (line drawing)
        if event.char == "D":
            self._draw_last_dir = None
            self._draw_pen_down = True  # Start with pen down
            self.set_mode(Mode.DRAW)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.DRAW,
                message="-- DRAW -- pen DOWN (wasd to draw, space to lift)",
            )

        # Undo (vim-style)
        if event.char == "u":
            return ModeResult(command="undo")

        return ModeResult(handled=False)

    def _process_pan(self, event: "InputEvent") -> ModeResult:
        """Process input in PAN mode - movement pans viewport, cursor follows."""
        from input import Action

        action = event.action
        cfg = self.config

        # Mode transitions
        if action == Action.TOGGLE_PAN_MODE:
            self.toggle_pan_mode()
            return ModeResult(mode_changed=True, new_mode=self._mode)

        if action == Action.ENTER_EDIT_MODE:
            self.set_mode(Mode.EDIT)
            return ModeResult(mode_changed=True, new_mode=Mode.EDIT)

        if action == Action.ENTER_COMMAND_MODE:
            self.set_mode(Mode.COMMAND)
            return ModeResult(mode_changed=True, new_mode=Mode.COMMAND)

        # In pan mode, movement keys pan the viewport
        # Cursor moves with viewport to maintain screen position (locked pointer)
        pan_map = {
            Action.MOVE_UP: (0, -cfg.move_step),
            Action.MOVE_DOWN: (0, cfg.move_step),
            Action.MOVE_LEFT: (-cfg.move_step, 0),
            Action.MOVE_RIGHT: (cfg.move_step, 0),
            Action.MOVE_UP_FAST: (0, -cfg.move_fast_step),
            Action.MOVE_DOWN_FAST: (0, cfg.move_fast_step),
            Action.MOVE_LEFT_FAST: (-cfg.move_fast_step, 0),
            Action.MOVE_RIGHT_FAST: (cfg.move_fast_step, 0),
        }

        if action in pan_map:
            dx, dy = pan_map[action]
            # Move both viewport and cursor together
            self.viewport.pan(dx, dy)
            self.viewport.move_cursor(dx, dy)
            return ModeResult()

        # Centering still works
        if action == Action.CENTER_CURSOR:
            self.viewport.center_on_cursor()
            return ModeResult()

        if action == Action.CENTER_ORIGIN:
            self.viewport.center_on_origin()
            return ModeResult()

        return ModeResult(handled=False)

    def _process_edit(self, event: "InputEvent") -> ModeResult:
        """Process input in EDIT mode - typing draws on canvas."""
        from input import Action

        action = event.action
        cfg = self.config

        # Handle typed characters
        if event.char:
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            # Record undo state
            if self.undo_manager:
                self.undo_manager.begin_operation("Type")
                self.undo_manager.record_cell_before(self.canvas, cx, cy)
            self.canvas.set(cx, cy, event.char, fg=self.draw_fg, bg=self.draw_bg)
            if self.undo_manager:
                self.undo_manager.record_cell_after(self.canvas, cx, cy)
                self.undo_manager.end_operation()

            if cfg.auto_advance:
                dx, dy = cfg.advance_direction
                self.viewport.move_cursor(dx, dy)
                self.viewport.ensure_cursor_visible(margin=cfg.scroll_margin)

            return ModeResult()

        # Cursor movement still works in edit mode
        moved = self._handle_movement(action, cfg.move_step, cfg.move_fast_step)
        if moved:
            self.viewport.ensure_cursor_visible(margin=cfg.scroll_margin)
            return ModeResult()

        # Backspace - delete behind cursor and move back
        if action == Action.BACKSPACE:
            dx, dy = cfg.advance_direction
            self.viewport.move_cursor(-dx, -dy)
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            # Record undo state
            if self.undo_manager:
                self.undo_manager.begin_operation("Delete")
                self.undo_manager.record_cell_before(self.canvas, cx, cy)
            self.canvas.clear(cx, cy)
            if self.undo_manager:
                self.undo_manager.record_cell_after(self.canvas, cx, cy)
                self.undo_manager.end_operation()
            self.viewport.ensure_cursor_visible(margin=cfg.scroll_margin)
            return ModeResult()

        # Delete - clear current cell
        if action == Action.DELETE_CHAR:
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            # Record undo state
            if self.undo_manager:
                self.undo_manager.begin_operation("Delete")
                self.undo_manager.record_cell_before(self.canvas, cx, cy)
            self.canvas.clear(cx, cy)
            if self.undo_manager:
                self.undo_manager.record_cell_after(self.canvas, cx, cy)
                self.undo_manager.end_operation()
            return ModeResult()

        # Newline - move to next line, reset X to where edit started
        if action == Action.NEWLINE:
            self.viewport.cursor.y += 1
            # Reset X to where we entered edit mode (column-aligned editing)
            if self._edit_start_x is not None:
                self.viewport.cursor.x = self._edit_start_x
            else:
                # Fallback to origin X if edit_start_x not set
                self.viewport.cursor.x = self.viewport.origin.x
            self.viewport.ensure_cursor_visible(margin=cfg.scroll_margin)
            return ModeResult()

        return ModeResult(handled=False)

    def _process_command(self, event: "InputEvent") -> ModeResult:
        """Process input in COMMAND mode."""
        from input import Action

        action = event.action
        buf = self.command_buffer

        # Handle typed characters
        if event.char:
            buf.insert(event.char)
            return ModeResult()

        # Buffer navigation
        if action == Action.BACKSPACE:
            buf.backspace()
            return ModeResult()

        if action == Action.DELETE_CHAR:
            buf.delete()
            return ModeResult()

        if action == Action.MOVE_LEFT:
            buf.move_left()
            return ModeResult()

        if action == Action.MOVE_RIGHT:
            buf.move_right()
            return ModeResult()

        if action == Action.MOVE_UP:
            buf.history_prev()
            return ModeResult()

        if action == Action.MOVE_DOWN:
            buf.history_next()
            return ModeResult()

        # Submit command
        if action == Action.NEWLINE:
            command = buf.submit()
            result = self._execute_command(command)
            self.set_mode(Mode.NAV)
            result.mode_changed = True
            result.new_mode = Mode.NAV
            return result

        return ModeResult(handled=False)

    def _extract_bookmark_char(self, event: "InputEvent") -> str | None:
        """
        Extract a bookmark character (a-z, 0-9) from an input event.

        Works even if the key has a binding that prevents char from being set.
        """
        # Try event.char first (for unbound keys)
        if event.char and len(event.char) == 1 and event.char.isalnum():
            return event.char.lower()

        # Fall back to raw_key for bound keys (like 'a' and '0')
        if event.raw_key:
            from pygame.locals import (
                K_a,
                K_b,
                K_c,
                K_d,
                K_e,
                K_f,
                K_g,
                K_h,
                K_i,
                K_j,
                K_k,
                K_l,
                K_m,
                K_n,
                K_o,
                K_p,
                K_q,
                K_r,
                K_s,
                K_t,
                K_u,
                K_v,
                K_w,
                K_x,
                K_y,
                K_z,
                K_0,
                K_1,
                K_2,
                K_3,
                K_4,
                K_5,
                K_6,
                K_7,
                K_8,
                K_9,
            )

            # Map key codes to characters
            key_map = {
                K_a: "a",
                K_b: "b",
                K_c: "c",
                K_d: "d",
                K_e: "e",
                K_f: "f",
                K_g: "g",
                K_h: "h",
                K_i: "i",
                K_j: "j",
                K_k: "k",
                K_l: "l",
                K_m: "m",
                K_n: "n",
                K_o: "o",
                K_p: "p",
                K_q: "q",
                K_r: "r",
                K_s: "s",
                K_t: "t",
                K_u: "u",
                K_v: "v",
                K_w: "w",
                K_x: "x",
                K_y: "y",
                K_z: "z",
                K_0: "0",
                K_1: "1",
                K_2: "2",
                K_3: "3",
                K_4: "4",
                K_5: "5",
                K_6: "6",
                K_7: "7",
                K_8: "8",
                K_9: "9",
            }

            return key_map.get(event.raw_key)

        return None

    def _process_mark_set(self, event: "InputEvent") -> ModeResult:
        """Process input in MARK_SET mode - waiting for bookmark key."""
        # Extract character from event.char or raw_key
        key_char = self._extract_bookmark_char(event)

        if key_char:
            x, y = self.viewport.cursor.x, self.viewport.cursor.y
            self.bookmarks.set(key_char, x, y)
            self.set_mode(Mode.NAV)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.NAV,
                message=f"Mark '{key_char}' set at ({x}, {y})",
            )

        # Any other key cancels
        self.set_mode(Mode.NAV)
        return ModeResult(
            mode_changed=True, new_mode=Mode.NAV, message="Mark cancelled"
        )

    def _process_mark_jump(self, event: "InputEvent") -> ModeResult:
        """Process input in MARK_JUMP mode - waiting for bookmark key."""
        # Extract character from event.char or raw_key
        key_char = self._extract_bookmark_char(event)

        if key_char:
            bookmark = self.bookmarks.get(key_char)
            if bookmark:
                self.viewport.cursor.set(bookmark.x, bookmark.y)
                self.viewport.ensure_cursor_visible(margin=self.config.scroll_margin)
                self.set_mode(Mode.NAV)
                return ModeResult(
                    mode_changed=True,
                    new_mode=Mode.NAV,
                    message=f"Jumped to mark '{key_char}' ({bookmark.x}, {bookmark.y})",
                )
            else:
                self.set_mode(Mode.NAV)
                return ModeResult(
                    mode_changed=True,
                    new_mode=Mode.NAV,
                    message=f"Mark '{key_char}' not set",
                )

        # Any other key cancels
        self.set_mode(Mode.NAV)
        return ModeResult(
            mode_changed=True, new_mode=Mode.NAV, message="Jump cancelled"
        )

    def _handle_movement(self, action: "Action", step: int, fast_step: int) -> bool:
        """Handle cursor movement actions. Returns True if moved."""
        from input import Action

        move_map = {
            Action.MOVE_UP: (0, -step),
            Action.MOVE_DOWN: (0, step),
            Action.MOVE_LEFT: (-step, 0),
            Action.MOVE_RIGHT: (step, 0),
            Action.MOVE_UP_FAST: (0, -fast_step),
            Action.MOVE_DOWN_FAST: (0, fast_step),
            Action.MOVE_LEFT_FAST: (-fast_step, 0),
            Action.MOVE_RIGHT_FAST: (fast_step, 0),
        }

        if action in move_map:
            dx, dy = move_map[action]
            self.viewport.move_cursor(dx, dy)
            return True

        return False

    def _register_default_commands(self) -> None:
        """Register built-in commands."""
        self.register_command("q", self._cmd_quit)
        self.register_command("quit", self._cmd_quit)
        self.register_command("w", self._cmd_save)
        self.register_command("write", self._cmd_save)
        self.register_command("wq", self._cmd_save_quit)
        self.register_command("goto", self._cmd_goto)
        self.register_command("g", self._cmd_goto)
        self.register_command("origin", self._cmd_origin)
        self.register_command("clear", self._cmd_clear)
        self.register_command("help", self._cmd_help)
        self.register_command("?", self._cmd_help)
        self.register_command("h", self._cmd_help)
        # Bookmark commands
        self.register_command("marks", self._cmd_marks)
        self.register_command("mark", self._cmd_mark)
        self.register_command("delmark", self._cmd_delmark)
        self.register_command("delmarks", self._cmd_delmarks)

    def register_command(
        self, name: str, handler: Callable[[list[str]], ModeResult]
    ) -> None:
        """Register a command handler."""
        self._command_handlers[name.lower()] = handler

    def _execute_command(self, command_str: str) -> ModeResult:
        """Parse and execute a command."""
        if not command_str.strip():
            return ModeResult()

        parts = command_str.strip().split()
        cmd_name = parts[0].lower()
        args = parts[1:]

        if cmd_name in self._command_handlers:
            return self._command_handlers[cmd_name](args)

        return ModeResult(message=f"Unknown command: {cmd_name}")

    # Built-in command handlers
    def _cmd_quit(self, args: list[str]) -> ModeResult:
        return ModeResult(quit=True)

    def _cmd_save(self, args: list[str]) -> ModeResult:
        # Actual save logic will be in project.py
        return ModeResult(command="save", message="Save requested")

    def _cmd_save_quit(self, args: list[str]) -> ModeResult:
        return ModeResult(command="save", quit=True, message="Save and quit")

    def _cmd_goto(self, args: list[str]) -> ModeResult:
        """Go to coordinates: goto X Y"""
        if len(args) >= 2:
            try:
                x, y = int(args[0]), int(args[1])
                self.viewport.cursor.set(x, y)
                self.viewport.ensure_cursor_visible(margin=self.config.scroll_margin)
                return ModeResult(message=f"Moved to ({x}, {y})")
            except ValueError:
                return ModeResult(message="Usage: goto X Y")
        return ModeResult(message="Usage: goto X Y")

    def _cmd_origin(self, args: list[str]) -> ModeResult:
        """Set origin: origin [X Y] or origin here"""
        if not args or args[0] == "here":
            x, y = self.viewport.cursor.x, self.viewport.cursor.y
            self.viewport.origin.set(x, y)
            return ModeResult(message=f"Origin set to ({x}, {y})")
        elif len(args) >= 2:
            try:
                x, y = int(args[0]), int(args[1])
                self.viewport.origin.set(x, y)
                return ModeResult(message=f"Origin set to ({x}, {y})")
            except ValueError:
                return ModeResult(message="Usage: origin [X Y | here]")
        return ModeResult(message="Usage: origin [X Y | here]")

    def _cmd_clear(self, args: list[str]) -> ModeResult:
        """Clear canvas."""
        self.canvas.clear_all()
        return ModeResult(message="Canvas cleared")

    def _cmd_help(self, args: list[str]) -> ModeResult:
        """Show help."""
        return ModeResult(command="help")

    def _cmd_marks(self, args: list[str]) -> ModeResult:
        """List all bookmarks."""
        marks = self.bookmarks.list_all()
        if not marks:
            return ModeResult(message="No marks set")
        # Format: a:(10,20) b:(30,40) ...
        mark_strs = [f"{k}:({b.x},{b.y})" for k, b in marks]
        return ModeResult(message="Marks: " + " ".join(mark_strs))

    def _cmd_mark(self, args: list[str]) -> ModeResult:
        """Set a bookmark: mark KEY [X Y]"""
        if not args:
            return ModeResult(message="Usage: mark KEY [X Y]")
        key = args[0]
        if len(key) != 1 or not key.isalnum():
            return ModeResult(message="Mark key must be a-z or 0-9")
        if len(args) >= 3:
            try:
                x, y = int(args[1]), int(args[2])
            except ValueError:
                return ModeResult(message="Invalid coordinates")
        else:
            x, y = self.viewport.cursor.x, self.viewport.cursor.y
        self.bookmarks.set(key, x, y)
        return ModeResult(message=f"Mark '{key}' set at ({x}, {y})")

    def _cmd_delmark(self, args: list[str]) -> ModeResult:
        """Delete a bookmark: delmark KEY"""
        if not args:
            return ModeResult(message="Usage: delmark KEY")
        key = args[0]
        if self.bookmarks.delete(key):
            return ModeResult(message=f"Mark '{key}' deleted")
        return ModeResult(message=f"Mark '{key}' not found")

    def _cmd_delmarks(self, args: list[str]) -> ModeResult:
        """Delete all bookmarks."""
        self.bookmarks.clear()
        return ModeResult(message="All marks deleted")

    def _process_visual(self, event: "InputEvent") -> ModeResult:
        """Process input in VISUAL mode - selection operations."""
        from input import Action

        action = event.action
        cfg = self.config

        if self.selection is None:
            # Shouldn't happen, but recover gracefully
            self.set_mode(Mode.NAV)
            return ModeResult(mode_changed=True, new_mode=Mode.NAV)

        # Movement extends/shrinks selection
        move_map = {
            Action.MOVE_UP: (0, -cfg.move_step),
            Action.MOVE_DOWN: (0, cfg.move_step),
            Action.MOVE_LEFT: (-cfg.move_step, 0),
            Action.MOVE_RIGHT: (cfg.move_step, 0),
            Action.MOVE_UP_FAST: (0, -cfg.move_fast_step),
            Action.MOVE_DOWN_FAST: (0, cfg.move_fast_step),
            Action.MOVE_LEFT_FAST: (-cfg.move_fast_step, 0),
            Action.MOVE_RIGHT_FAST: (cfg.move_fast_step, 0),
        }

        if action in move_map:
            dx, dy = move_map[action]
            # Move both cursor and selection cursor
            self.viewport.move_cursor(dx, dy)
            self.selection.update_cursor(self.viewport.cursor.x, self.viewport.cursor.y)
            self.viewport.ensure_cursor_visible(margin=cfg.scroll_margin)
            # Update status with selection size
            w, h = self.selection.width, self.selection.height
            return ModeResult(message=f"-- VISUAL -- ({w}x{h})")

        # Yank selection
        if event.char == "y":
            # Signal to yank selection, handled by main.py
            sel = self.selection
            self.selection = None
            self.set_mode(Mode.NAV)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.NAV,
                command=f"yank_selection {sel.x1} {sel.y1} {sel.width} {sel.height}",
            )

        # Delete selection
        if event.char == "d":
            # Signal to delete selection, handled by main.py
            sel = self.selection
            self.selection = None
            self.set_mode(Mode.NAV)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.NAV,
                command=f"delete_selection {sel.x1} {sel.y1} {sel.width} {sel.height}",
            )

        # Fill selection (trigger command mode with fill)
        if event.char == "f":
            sel = self.selection
            self.selection = None
            self.set_mode(Mode.COMMAND)
            # Pre-fill command buffer with fill command template
            self.command_buffer.text = (
                f"fill {sel.x1} {sel.y1} {sel.width} {sel.height} "
            )
            self.command_buffer.cursor_pos = len(self.command_buffer.text)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.COMMAND,
                message="Fill selection with character:",
            )

        return ModeResult(handled=False)

    def _process_draw(self, event: "InputEvent") -> ModeResult:
        """Process input in DRAW mode - movement draws lines."""
        from input import Action
        from zones import get_border_chars
        import logging

        _draw_log = logging.getLogger("joystick_debug")

        action = event.action
        cfg = self.config

        # Direction mapping for movement actions
        dir_map = {
            Action.MOVE_UP: (0, -1),
            Action.MOVE_DOWN: (0, 1),
            Action.MOVE_LEFT: (-1, 0),
            Action.MOVE_RIGHT: (1, 0),
        }

        if action in dir_map:
            dx, dy = dir_map[action]
            x, y = self.viewport.cursor.x, self.viewport.cursor.y

            _draw_log.debug(
                f"DRAW move: pen_down={self._draw_pen_down}, action={action.name}"
            )

            # Only draw if pen is down
            if self._draw_pen_down:
                # Get the line character for current position
                char = self._get_draw_char(x, y, self._draw_last_dir, (dx, dy))
                # Record undo state
                if self.undo_manager:
                    self.undo_manager.begin_operation("Draw")
                    self.undo_manager.record_cell_before(self.canvas, x, y)
                self.canvas.set(x, y, char, fg=self.draw_fg, bg=self.draw_bg)
                if self.undo_manager:
                    self.undo_manager.record_cell_after(self.canvas, x, y)
                    self.undo_manager.end_operation()
                # Update last direction only when drawing
                self._draw_last_dir = (dx, dy)
            else:
                # Pen up - clear last direction so next pen-down starts fresh
                self._draw_last_dir = None

            # Move cursor
            self.viewport.move_cursor(dx, dy)
            self.viewport.ensure_cursor_visible(margin=cfg.scroll_margin)

            return ModeResult()

        # Space bar toggles pen up/down (with frame guard to prevent double-toggle)
        if event.char == " ":
            if self._pen_toggled_this_frame:
                _draw_log.debug(f"SPACEBAR: BLOCKED by frame guard (already toggled)")
                return ModeResult()  # Already toggled this frame, ignore
            _draw_log.debug(f"SPACEBAR: pen_before={self._draw_pen_down}")
            pen_down = self.toggle_draw_pen()
            _draw_log.debug(f"SPACEBAR: pen_after={pen_down}")
            state = "DOWN (drawing)" if pen_down else "UP (moving)"
            return ModeResult(message=f"-- DRAW -- pen {state}")

        return ModeResult(handled=False)

    def toggle_draw_pen(self) -> bool:
        """Toggle pen up/down state in DRAW mode. Returns new state (True=down)."""
        import logging

        _draw_log = logging.getLogger("joystick_debug")
        _draw_log.debug(f"toggle_draw_pen() called: before={self._draw_pen_down}")
        self._draw_pen_down = not self._draw_pen_down
        self._pen_toggled_this_frame = True  # Set frame guard
        _draw_log.debug(f"toggle_draw_pen() done: after={self._draw_pen_down}")
        if not self._draw_pen_down:
            # Reset direction when lifting pen
            self._draw_last_dir = None
        return self._draw_pen_down

    def reset_pen_toggle_guard(self) -> None:
        """Reset the frame guard. Call this once per frame."""
        self._pen_toggled_this_frame = False

    def _get_draw_char(
        self, x: int, y: int, from_dir: tuple[int, int] | None, to_dir: tuple[int, int]
    ) -> str:
        """
        Determine the appropriate line character based on directions.

        Uses direction bits: UP=1, DOWN=2, LEFT=4, RIGHT=8
        Each line character represents a combination of connected directions.
        """
        from zones import get_border_chars

        chars = get_border_chars()

        # Direction bit flags
        UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8

        # Map directions to bits
        dir_to_bit = {
            (0, -1): UP,
            (0, 1): DOWN,
            (-1, 0): LEFT,
            (1, 0): RIGHT,
        }

        # Map bit combinations to character keys
        bit_to_char = {
            LEFT | RIGHT: "horiz",  # ─
            UP | DOWN: "vert",  # │
            DOWN | RIGHT: "tl",  # ┌ (going down-right, corner at top-left)
            DOWN | LEFT: "tr",  # ┐
            UP | RIGHT: "bl",  # └
            UP | LEFT: "br",  # ┘
            LEFT | RIGHT | DOWN: "tee_down",  # ┬
            LEFT | RIGHT | UP: "tee_up",  # ┴
            UP | DOWN | RIGHT: "tee_right",  # ├
            UP | DOWN | LEFT: "tee_left",  # ┤
            UP | DOWN | LEFT | RIGHT: "cross",  # ┼
        }

        # Calculate current direction bits
        bits = 0

        # Add the direction we're going TO
        if to_dir in dir_to_bit:
            bits |= dir_to_bit[to_dir]

        # Add the direction we came FROM (opposite of from_dir)
        if from_dir:
            # We came FROM from_dir, so we connect in the opposite direction
            opposite = (-from_dir[0], -from_dir[1])
            if opposite in dir_to_bit:
                bits |= dir_to_bit[opposite]

        # Check existing cell for additional directions
        cell = self.canvas.get(x, y)
        if cell:
            existing_bits = self._char_to_bits(cell.char, chars)
            bits |= existing_bits

        # Look up the character for this bit combination
        char_key = bit_to_char.get(bits)
        if char_key and char_key in chars:
            return chars[char_key]

        # Fallback: if only one direction, use appropriate line
        if bits == UP or bits == DOWN:
            return chars["vert"]
        if bits == LEFT or bits == RIGHT:
            return chars["horiz"]

        # Default fallback
        return chars.get("cross", "+")

    def _char_to_bits(self, char: str, chars: dict[str, str]) -> int:
        """Convert a line character back to direction bits."""
        UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8

        # Reverse mapping from character to bits
        char_to_bits_map = {
            chars.get("horiz", "-"): LEFT | RIGHT,
            chars.get("vert", "|"): UP | DOWN,
            chars.get("tl", "+"): DOWN | RIGHT,
            chars.get("tr", "+"): DOWN | LEFT,
            chars.get("bl", "+"): UP | RIGHT,
            chars.get("br", "+"): UP | LEFT,
            chars.get("tee_down", "+"): LEFT | RIGHT | DOWN,
            chars.get("tee_up", "+"): LEFT | RIGHT | UP,
            chars.get("tee_right", "+"): UP | DOWN | RIGHT,
            chars.get("tee_left", "+"): UP | DOWN | LEFT,
            chars.get("cross", "+"): UP | DOWN | LEFT | RIGHT,
        }

        return char_to_bits_map.get(char, 0)
