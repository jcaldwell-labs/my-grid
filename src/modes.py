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


class Mode(Enum):
    """Editor modes."""
    NAV = auto()
    PAN = auto()
    EDIT = auto()
    COMMAND = auto()
    MARK_SET = auto()      # Waiting for bookmark key (m + key)
    MARK_JUMP = auto()     # Waiting for bookmark key (' + key)


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
                key,
                bm_data.get("x", 0),
                bm_data.get("y", 0),
                bm_data.get("name", "")
            )
        return manager


@dataclass
class ModeConfig:
    """Configuration for mode behaviors."""
    # Movement distances
    move_step: int = 1
    move_fast_step: int = 10
    pan_step: int = 5

    # Edit mode settings
    auto_advance: bool = True       # Move cursor after typing
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
        self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
        self.cursor_pos += 1

    def backspace(self) -> None:
        """Delete character before cursor."""
        if self.cursor_pos > 0:
            self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
            self.cursor_pos -= 1

    def delete(self) -> None:
        """Delete character at cursor."""
        if self.cursor_pos < len(self.text):
            self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]

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
    command: str | None = None      # For command mode submission
    message: str | None = None      # Status message to display
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
        config: ModeConfig | None = None
    ):
        self.canvas = canvas
        self.viewport = viewport
        self.config = config or ModeConfig()

        self._mode = Mode.NAV
        self._previous_mode = Mode.NAV
        self.command_buffer = CommandBuffer()
        self.bookmarks = BookmarkManager()

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
        if event.char == 'm':
            self.set_mode(Mode.MARK_SET)
            return ModeResult(mode_changed=True, new_mode=Mode.MARK_SET,
                            message="Set mark: press a-z or 0-9")
        if event.char == "'":
            self.set_mode(Mode.MARK_JUMP)
            return ModeResult(mode_changed=True, new_mode=Mode.MARK_JUMP,
                            message="Jump to mark: press a-z or 0-9")

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
            self.canvas.set(cx, cy, event.char)

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
            self.canvas.clear(self.viewport.cursor.x, self.viewport.cursor.y)
            self.viewport.ensure_cursor_visible(margin=cfg.scroll_margin)
            return ModeResult()

        # Delete - clear current cell
        if action == Action.DELETE_CHAR:
            self.canvas.clear(self.viewport.cursor.x, self.viewport.cursor.y)
            return ModeResult()

        # Newline - move to next line, reset X to origin or 0
        if action == Action.NEWLINE:
            self.viewport.cursor.y += 1
            # Reset X to origin X (start of line behavior)
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

    def _process_mark_set(self, event: "InputEvent") -> ModeResult:
        """Process input in MARK_SET mode - waiting for bookmark key."""
        # Any alphanumeric character sets a bookmark
        if event.char and len(event.char) == 1 and event.char.isalnum():
            key = event.char.lower()
            x, y = self.viewport.cursor.x, self.viewport.cursor.y
            self.bookmarks.set(key, x, y)
            self.set_mode(Mode.NAV)
            return ModeResult(
                mode_changed=True,
                new_mode=Mode.NAV,
                message=f"Mark '{key}' set at ({x}, {y})"
            )

        # Any other key cancels
        self.set_mode(Mode.NAV)
        return ModeResult(mode_changed=True, new_mode=Mode.NAV, message="Mark cancelled")

    def _process_mark_jump(self, event: "InputEvent") -> ModeResult:
        """Process input in MARK_JUMP mode - waiting for bookmark key."""
        # Any alphanumeric character jumps to bookmark
        if event.char and len(event.char) == 1 and event.char.isalnum():
            key = event.char.lower()
            bookmark = self.bookmarks.get(key)
            if bookmark:
                self.viewport.cursor.set(bookmark.x, bookmark.y)
                self.viewport.ensure_cursor_visible(margin=self.config.scroll_margin)
                self.set_mode(Mode.NAV)
                return ModeResult(
                    mode_changed=True,
                    new_mode=Mode.NAV,
                    message=f"Jumped to mark '{key}' ({bookmark.x}, {bookmark.y})"
                )
            else:
                self.set_mode(Mode.NAV)
                return ModeResult(
                    mode_changed=True,
                    new_mode=Mode.NAV,
                    message=f"Mark '{key}' not set"
                )

        # Any other key cancels
        self.set_mode(Mode.NAV)
        return ModeResult(mode_changed=True, new_mode=Mode.NAV, message="Jump cancelled")

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
        self,
        name: str,
        handler: Callable[[list[str]], ModeResult]
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
        return ModeResult(command="help", message="Help requested")

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
