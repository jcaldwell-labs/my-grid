"""
Minimal Textual app for my-grid prototype with mode support.

Demonstrates the CanvasWidget with:
- NAV mode: Basic navigation keybindings
- EDIT mode: Typing characters on canvas
- COMMAND mode: Execute commands like :goto, :clear, :rect
- VISUAL mode: Selection and yank/delete operations
"""

import sys
from enum import Enum, auto
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from textual.app import App, ComposeResult
from textual.widgets import Static, Input
from textual.binding import Binding
from textual.reactive import reactive
from textual.containers import Vertical
from textual import events

from canvas import Canvas
from viewport import Viewport
from .canvas_widget import CanvasWidget
from .zones import ZoneType, ZoneManager


class Mode(Enum):
    """Editor modes."""

    NAV = auto()
    EDIT = auto()
    COMMAND = auto()
    VISUAL = auto()
    PTY_FOCUS = auto()  # PTY zone has keyboard focus


class StatusBar(Static):
    """Status bar showing cursor position and mode."""

    cursor_x: reactive[int] = reactive(0)
    cursor_y: reactive[int] = reactive(0)
    mode: reactive[str] = reactive("NAV")
    message: reactive[str] = reactive("")
    grid_status: reactive[str] = reactive("")

    def render(self) -> str:
        grid_info = f" | Grid: {self.grid_status}" if self.grid_status else ""
        msg_info = f" | {self.message}" if self.message else ""
        return (
            f" [{self.mode}] "
            f"Cursor: ({self.cursor_x}, {self.cursor_y})"
            f"{grid_info}"
            f"{msg_info}"
            f" | Press ? for help"
        )


class CommandInput(Input):
    """Command line input that appears at the bottom."""

    DEFAULT_CSS = """
    CommandInput {
        height: 1;
        background: $surface;
        border: none;
        padding: 0 1;
    }
    """


class MyGridApp(App):
    """
    Minimal my-grid Textual app with multiple modes.

    A proof-of-concept showing:
    - NAV mode: wasd/arrows to move cursor
    - EDIT mode: 'i' to enter, type characters, Esc to exit
    - COMMAND mode: ':' to enter, type commands, Enter to execute
    - VISUAL mode: 'v' to enter, move to select, y/d to yank/delete
    """

    CSS = """
    Screen {
        layout: vertical;
    }

    CanvasWidget {
        height: 1fr;
    }

    #status {
        height: 1;
        background: $primary;
        color: $text;
    }

    #command-container {
        height: auto;
        display: none;
    }

    #command-container.visible {
        display: block;
    }

    CommandInput {
        height: 1;
        background: $surface;
    }
    """

    # Only bind keys for NAV mode - other modes handle keys via on_key
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("w", "move_up", "Up", show=False),
        Binding("s", "move_down", "Down", show=False),
        Binding("a", "move_left", "Left", show=False),
        Binding("d", "move_right", "Right", show=False),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("left", "move_left", "Left", show=False),
        Binding("right", "move_right", "Right", show=False),
        Binding("W", "fast_up", "Fast Up", show=False),
        Binding("S", "fast_down", "Fast Down", show=False),
        Binding("A", "fast_left", "Fast Left", show=False),
        Binding("D", "fast_right", "Fast Right", show=False),
        Binding("g", "toggle_major_grid", "Toggle Major Grid"),
        Binding("G", "toggle_minor_grid", "Toggle Minor Grid", show=False),
        Binding("0", "toggle_origin", "Toggle Origin", show=False),
        Binding("c", "center_on_origin", "Center on Origin", show=False),
        Binding("question_mark", "show_help", "Help"),
        Binding("i", "enter_edit_mode", "Edit Mode", show=False),
        Binding("colon", "enter_command_mode", "Command Mode", show=False),
        Binding("v", "enter_visual_mode", "Visual Mode", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.canvas = Canvas()
        self.viewport = Viewport()

        # Mode state
        self._mode = Mode.NAV

        # Visual mode state
        self._visual_anchor: tuple[int, int] | None = None

        # Clipboard for yank/paste
        self._clipboard: list[list[str]] | None = None

        # Track WATCH zone refresh timers (zone_name -> timer)
        self._watch_timers: dict[str, object] = {}

        # PTY focus tracking
        self._focused_pty_zone: str | None = None  # Name of focused PTY zone
        self._pty_refresh_timer = None  # Timer for refreshing PTY display

        # Add some demo content
        self._add_demo_content()

    def _add_demo_content(self) -> None:
        """Add demo content to show the canvas working."""
        # Draw a simple box
        self.canvas.draw_rect(5, 3, 20, 8, h_char="-", v_char="|", corner_char="+")

        # Add some text
        self.canvas.write_text(8, 5, "my-grid")
        self.canvas.write_text(7, 6, "Textual Demo")

        # Add some colored cells
        self.canvas.set(30, 5, "R", fg=1)  # Red
        self.canvas.set(31, 5, "G", fg=2)  # Green
        self.canvas.set(32, 5, "B", fg=4)  # Blue
        self.canvas.set(33, 5, "Y", fg=3)  # Yellow

        # Add a cell with background color
        self.canvas.set(30, 7, " ", bg=1)  # Red bg
        self.canvas.set(31, 7, " ", bg=2)  # Green bg
        self.canvas.set(32, 7, " ", bg=4)  # Blue bg
        self.canvas.set(33, 7, " ", bg=3)  # Yellow bg

    def compose(self) -> ComposeResult:
        yield CanvasWidget(self.canvas, self.viewport, id="canvas")
        with Vertical(id="command-container"):
            yield CommandInput(placeholder=":", id="command-input")
        yield StatusBar(id="status")

    def on_mount(self) -> None:
        """Set up after mounting."""
        self._update_status()

    @property
    def mode(self) -> Mode:
        """Current mode."""
        return self._mode

    def _set_mode(self, mode: Mode) -> None:
        """Change the current mode."""
        old_mode = self._mode
        self._mode = mode

        # Handle mode transitions
        if old_mode == Mode.COMMAND:
            # Hide command input
            container = self.query_one("#command-container")
            container.remove_class("visible")

        if mode == Mode.COMMAND:
            # Show and focus command input
            container = self.query_one("#command-container")
            container.add_class("visible")
            cmd_input = self.query_one("#command-input", CommandInput)
            cmd_input.value = ""
            cmd_input.focus()

        if old_mode == Mode.VISUAL:
            # Clear selection
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            canvas_widget.clear_selection()
            self._visual_anchor = None

        if mode == Mode.VISUAL:
            # Start selection at cursor
            cx = self.viewport.cursor.x
            cy = self.viewport.cursor.y
            self._visual_anchor = (cx, cy)
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            canvas_widget.set_selection(cx, cy, cx, cy)

        self._update_status()

    def _update_status(self, message: str = "") -> None:
        """Update the status bar."""
        status = self.query_one("#status", StatusBar)
        status.cursor_x = self.viewport.cursor.x
        status.cursor_y = self.viewport.cursor.y
        status.mode = self._mode.name
        status.message = message

        canvas_widget = self.query_one("#canvas", CanvasWidget)
        grid_parts = []
        if canvas_widget.show_major_grid:
            grid_parts.append("Major")
        if canvas_widget.show_minor_grid:
            grid_parts.append("Minor")
        status.grid_status = "+".join(grid_parts) if grid_parts else "Off"

    def _move_cursor(self, dx: int, dy: int) -> None:
        """Move cursor and refresh."""
        canvas_widget = self.query_one("#canvas", CanvasWidget)
        canvas_widget.move_cursor(dx, dy)

        # Update selection if in visual mode
        if self._mode == Mode.VISUAL and self._visual_anchor is not None:
            ax, ay = self._visual_anchor
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            canvas_widget.set_selection(ax, ay, cx, cy)
            sel = canvas_widget.get_selection_bounds()
            if sel:
                w = sel[2] - sel[0] + 1
                h = sel[3] - sel[1] + 1
                self._update_status(f"{w}x{h}")
            return

        self._update_status()

    # Override key handling for mode-specific behavior
    def on_key(self, event: events.Key) -> None:
        """Handle key events based on current mode."""

        if self._mode == Mode.EDIT:
            self._handle_edit_key(event)
        elif self._mode == Mode.VISUAL:
            self._handle_visual_key(event)
        elif self._mode == Mode.PTY_FOCUS:
            self._handle_pty_key(event)
        elif self._mode == Mode.NAV:
            # Handle Enter to focus PTY zone under cursor
            if event.key == "enter":
                self._try_focus_pty_under_cursor(event)
        # NAV and COMMAND modes use bindings / Input widget

    def _handle_edit_key(self, event: events.Key) -> None:
        """Handle keys in EDIT mode."""
        canvas_widget = self.query_one("#canvas", CanvasWidget)

        if event.key == "escape":
            self._set_mode(Mode.NAV)
            event.stop()
            return

        # Movement keys still work in edit mode
        if event.key in ("up", "w"):
            self._move_cursor(0, -1)
            event.stop()
            return
        if event.key in ("down", "s"):
            self._move_cursor(0, 1)
            event.stop()
            return
        if event.key in ("left", "a"):
            self._move_cursor(-1, 0)
            event.stop()
            return
        if event.key in ("right", "d"):
            self._move_cursor(1, 0)
            event.stop()
            return

        # Backspace - delete and move left
        if event.key == "backspace":
            self._move_cursor(-1, 0)
            canvas_widget.delete_char()
            event.stop()
            return

        # Printable character - write to canvas and advance
        if (
            event.character
            and len(event.character) == 1
            and event.character.isprintable()
        ):
            canvas_widget.set_char(event.character)
            self._move_cursor(1, 0)  # Advance cursor right
            event.stop()
            return

    def _handle_visual_key(self, event: events.Key) -> None:
        """Handle keys in VISUAL mode."""
        canvas_widget = self.query_one("#canvas", CanvasWidget)

        if event.key == "escape":
            self._set_mode(Mode.NAV)
            self._update_status("Selection cancelled")
            event.stop()
            return

        # Movement extends selection (use hjkl or arrows in VISUAL mode)
        # We avoid w/a/s/d conflicts with yank(y)/delete(d)
        if event.key in ("up", "k"):
            self._move_cursor(0, -1)
            event.stop()
            return
        if event.key in ("down", "j"):
            self._move_cursor(0, 1)
            event.stop()
            return
        if event.key in ("left", "h"):
            self._move_cursor(-1, 0)
            event.stop()
            return
        if event.key in ("right", "l"):
            self._move_cursor(1, 0)
            event.stop()
            return

        # Fast movement (capital HJKL or shift+arrows)
        if event.key == "K":
            self._move_cursor(0, -10)
            event.stop()
            return
        if event.key == "J":
            self._move_cursor(0, 10)
            event.stop()
            return
        if event.key == "H":
            self._move_cursor(-10, 0)
            event.stop()
            return
        if event.key == "L":
            self._move_cursor(10, 0)
            event.stop()
            return

        # Yank selection
        if event.key == "y":
            sel = canvas_widget.get_selection_bounds()
            if sel:
                self._clipboard = canvas_widget.yank_region(*sel)
                w = sel[2] - sel[0] + 1
                h = sel[3] - sel[1] + 1
                self._set_mode(Mode.NAV)
                self._update_status(f"Yanked {w}x{h} region")
            event.stop()
            return

        # Delete selection
        if event.key == "d":
            sel = canvas_widget.get_selection_bounds()
            if sel:
                canvas_widget.delete_region(*sel)
                w = sel[2] - sel[0] + 1
                h = sel[3] - sel[1] + 1
                self._set_mode(Mode.NAV)
                self._update_status(f"Deleted {w}x{h} region")
            event.stop()
            return

    def _handle_pty_key(self, event: events.Key) -> None:
        """Handle keys in PTY_FOCUS mode - forward to PTY."""
        # Escape unfocuses
        if event.key == "escape":
            self._unfocus_pty_zone()
            event.stop()
            return

        # Get the focused PTY zone
        if not self._focused_pty_zone:
            self._unfocus_pty_zone()
            return

        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.get(self._focused_pty_zone)

        if not zone or not zone.is_pty_active():
            self._unfocus_pty_zone()
            return

        # Map key to terminal sequence
        key_to_send = self._map_key_to_terminal(event)
        if key_to_send:
            zone.write_to_pty(key_to_send)

        event.stop()

    def _map_key_to_terminal(self, event: events.Key) -> str | None:
        """Map a Textual key event to terminal escape sequence."""
        key = event.key

        # Special keys mapping
        special_keys = {
            "enter": "\r",
            "tab": "\t",
            "backspace": "\x7f",  # DEL character
            "delete": "\x1b[3~",
            "up": "\x1b[A",
            "down": "\x1b[B",
            "right": "\x1b[C",
            "left": "\x1b[D",
            "home": "\x1b[H",
            "end": "\x1b[F",
            "pageup": "\x1b[5~",
            "pagedown": "\x1b[6~",
            "insert": "\x1b[2~",
            "f1": "\x1bOP",
            "f2": "\x1bOQ",
            "f3": "\x1bOR",
            "f4": "\x1bOS",
            "f5": "\x1b[15~",
            "f6": "\x1b[17~",
            "f7": "\x1b[18~",
            "f8": "\x1b[19~",
            "f9": "\x1b[20~",
            "f10": "\x1b[21~",
            "f11": "\x1b[23~",
            "f12": "\x1b[24~",
        }

        if key in special_keys:
            return special_keys[key]

        # Ctrl+key combinations
        if key.startswith("ctrl+"):
            ctrl_char = key[5:]
            if len(ctrl_char) == 1 and ctrl_char.isalpha():
                # Ctrl+A = 0x01, Ctrl+B = 0x02, etc.
                return chr(ord(ctrl_char.lower()) - ord("a") + 1)
            if ctrl_char == "c":
                return "\x03"  # Ctrl+C (interrupt)
            if ctrl_char == "d":
                return "\x04"  # Ctrl+D (EOF)
            if ctrl_char == "z":
                return "\x1a"  # Ctrl+Z (suspend)

        # Regular printable character
        if event.character and len(event.character) == 1:
            return event.character

        return None

    def _try_focus_pty_under_cursor(self, event: events.Key) -> None:
        """Try to focus a PTY zone under the cursor."""
        canvas_widget = self.query_one("#canvas", CanvasWidget)
        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
        zone = canvas_widget.zone_manager.get_zone_at(cx, cy)

        if zone and zone.zone_type == ZoneType.PTY and zone.is_pty_active():
            self._focus_pty_zone(zone)
            event.stop()

    # Command input handlers
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        if event.input.id == "command-input":
            command = event.value.strip()
            self._execute_command(command)
            self._set_mode(Mode.NAV)
            # Refocus canvas
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            canvas_widget.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Detect Escape in command input to cancel."""
        pass  # Handled by key binding

    def _execute_command(self, command: str) -> None:
        """Execute a command string."""
        if not command:
            return

        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]

        canvas_widget = self.query_one("#canvas", CanvasWidget)

        if cmd in ("quit", "q"):
            self.exit()
        elif cmd in ("goto", "g"):
            if len(args) >= 2:
                try:
                    x, y = int(args[0]), int(args[1])
                    self.viewport.cursor.set(x, y)
                    self.viewport.ensure_cursor_visible(margin=2)
                    canvas_widget.refresh()
                    self._update_status(f"Moved to ({x}, {y})")
                except ValueError:
                    self._update_status("Usage: goto X Y")
            else:
                self._update_status("Usage: goto X Y")
        elif cmd == "clear":
            self.canvas.clear_all()
            canvas_widget.refresh()
            self._update_status("Canvas cleared")
        elif cmd == "rect":
            if len(args) >= 2:
                try:
                    w, h = int(args[0]), int(args[1])
                    char = args[2] if len(args) > 2 else "#"
                    cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
                    self.canvas.draw_rect(
                        cx, cy, w, h, h_char=char, v_char=char, corner_char=char
                    )
                    canvas_widget.refresh()
                    self._update_status(f"Drew {w}x{h} rectangle")
                except ValueError:
                    self._update_status("Usage: rect W H [char]")
            else:
                self._update_status("Usage: rect W H [char]")
        elif cmd == "paste" or cmd == "p":
            if self._clipboard:
                cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
                canvas_widget.paste_region(self._clipboard, cx, cy)
                h = len(self._clipboard)
                w = len(self._clipboard[0]) if h > 0 else 0
                self._update_status(f"Pasted {w}x{h} region")
            else:
                self._update_status("Clipboard empty")
        elif cmd == "zone":
            self._handle_zone_command(args)
        elif cmd == "zones":
            self._handle_zones_list()
        else:
            self._update_status(f"Unknown command: {cmd}")

    # Action handlers for keybindings (NAV mode)
    def action_move_up(self) -> None:
        if self._mode == Mode.NAV:
            self._move_cursor(0, -1)

    def action_move_down(self) -> None:
        if self._mode == Mode.NAV:
            self._move_cursor(0, 1)

    def action_move_left(self) -> None:
        if self._mode == Mode.NAV:
            self._move_cursor(-1, 0)

    def action_move_right(self) -> None:
        if self._mode == Mode.NAV:
            self._move_cursor(1, 0)

    def action_fast_up(self) -> None:
        if self._mode == Mode.NAV:
            self._move_cursor(0, -10)

    def action_fast_down(self) -> None:
        if self._mode == Mode.NAV:
            self._move_cursor(0, 10)

    def action_fast_left(self) -> None:
        if self._mode == Mode.NAV:
            self._move_cursor(-10, 0)

    def action_fast_right(self) -> None:
        if self._mode == Mode.NAV:
            self._move_cursor(10, 0)

    def action_toggle_major_grid(self) -> None:
        if self._mode == Mode.NAV:
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            canvas_widget.toggle_major_grid()
            self._update_status()

    def action_toggle_minor_grid(self) -> None:
        if self._mode == Mode.NAV:
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            canvas_widget.toggle_minor_grid()
            self._update_status()

    def action_toggle_origin(self) -> None:
        if self._mode == Mode.NAV:
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            canvas_widget.toggle_origin()

    def action_center_on_origin(self) -> None:
        if self._mode == Mode.NAV:
            self.viewport.center_on_origin()
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            canvas_widget.refresh()
            self._update_status()

    def action_show_help(self) -> None:
        """Show help message."""
        if self._mode == Mode.NAV:
            help_text = "NAV: wasd/arrows | WASD fast | g grid | i edit | : cmd | v visual | q quit"
        elif self._mode == Mode.EDIT:
            help_text = "EDIT: type chars | arrows move | backspace delete | Esc exit"
        elif self._mode == Mode.VISUAL:
            help_text = "VISUAL: hjkl/arrows select | y yank | d delete | Esc cancel"
        else:
            help_text = "COMMAND: type cmd | Enter execute | Esc cancel"
        self.notify(help_text, title="Controls", timeout=5)

    def action_enter_edit_mode(self) -> None:
        """Enter edit mode."""
        if self._mode == Mode.NAV:
            self._set_mode(Mode.EDIT)
            self._update_status("-- INSERT --")

    def action_enter_command_mode(self) -> None:
        """Enter command mode."""
        if self._mode == Mode.NAV:
            self._set_mode(Mode.COMMAND)

    def action_enter_visual_mode(self) -> None:
        """Enter visual selection mode."""
        if self._mode == Mode.NAV:
            self._set_mode(Mode.VISUAL)
            self._update_status("1x1")

    def action_quit(self) -> None:
        """Quit the app, but check mode first."""
        if self._mode == Mode.NAV:
            self.exit()
        elif self._mode == Mode.EDIT:
            # In edit mode, 'q' should just type 'q'
            pass
        elif self._mode == Mode.COMMAND:
            # In command mode, let it go to input
            pass

    # Handle escape in command mode
    def key_escape(self) -> None:
        """Handle escape key."""
        if self._mode == Mode.COMMAND:
            self._set_mode(Mode.NAV)
            # Refocus canvas
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            canvas_widget.focus()
            self._update_status("Command cancelled")

    # Zone command handlers
    def _handle_zone_command(self, args: list[str]) -> None:
        """Handle :zone subcommands."""
        if not args:
            self._update_status(
                "Usage: zone create|pipe|watch|delete|goto|info NAME ..."
            )
            return

        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "create":
            self._zone_create(subargs)
        elif subcmd == "pipe":
            self._zone_pipe(subargs)
        elif subcmd == "watch":
            self._zone_watch(subargs)
        elif subcmd == "pty":
            self._zone_pty(subargs)
        elif subcmd == "delete":
            self._zone_delete(subargs)
        elif subcmd == "goto":
            self._zone_goto(subargs)
        elif subcmd == "info":
            self._zone_info(subargs)
        elif subcmd == "refresh":
            self._zone_refresh(subargs)
        elif subcmd == "send":
            self._zone_send(subargs)
        elif subcmd == "focus":
            self._zone_focus(subargs)
        else:
            self._update_status(f"Unknown zone subcommand: {subcmd}")

    def _zone_create(self, args: list[str]) -> None:
        """Handle :zone create NAME X Y W H"""
        if len(args) < 5:
            self._update_status("Usage: zone create NAME X Y W H")
            return

        name = args[0]
        try:
            # Support 'here' keyword for X Y
            if args[1].lower() == "here":
                x = self.viewport.cursor.x
                y = self.viewport.cursor.y
                w = int(args[2])
                h = int(args[3])
            else:
                x, y = int(args[1]), int(args[2])
                w, h = int(args[3]), int(args[4])
        except (ValueError, IndexError):
            self._update_status("Usage: zone create NAME X Y W H")
            return

        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.create(
            name=name,
            x=x,
            y=y,
            width=w,
            height=h,
            zone_type=ZoneType.STATIC,
        )
        canvas_widget.refresh()
        self._update_status(f"Created zone {zone.name} at ({x},{y}) {w}x{h}")

    def _zone_pipe(self, args: list[str]) -> None:
        """Handle :zone pipe NAME W H CMD"""
        if len(args) < 4:
            self._update_status("Usage: zone pipe NAME W H CMD...")
            return

        name = args[0]
        try:
            w, h = int(args[1]), int(args[2])
        except ValueError:
            self._update_status("Usage: zone pipe NAME W H CMD...")
            return

        # Command is everything after W H
        command = " ".join(args[3:])

        # Create at cursor position
        x = self.viewport.cursor.x
        y = self.viewport.cursor.y

        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.create(
            name=name,
            x=x,
            y=y,
            width=w,
            height=h,
            zone_type=ZoneType.PIPE,
            command=command,
        )
        canvas_widget.refresh()
        self._update_status(f"Created pipe zone {zone.name}")

    def _zone_watch(self, args: list[str]) -> None:
        """Handle :zone watch NAME W H INTERVAL CMD"""
        if len(args) < 5:
            self._update_status("Usage: zone watch NAME W H INTERVAL CMD...")
            return

        name = args[0]
        try:
            w, h = int(args[1]), int(args[2])
        except ValueError:
            self._update_status("Usage: zone watch NAME W H INTERVAL CMD...")
            return

        # Parse interval (e.g., "5s", "10s", "1m")
        interval_str = args[3].lower()
        try:
            if interval_str.endswith("s"):
                interval = float(interval_str[:-1])
            elif interval_str.endswith("m"):
                interval = float(interval_str[:-1]) * 60
            else:
                interval = float(interval_str)
        except ValueError:
            self._update_status(f"Invalid interval: {interval_str}")
            return

        # Command is everything after interval
        command = " ".join(args[4:])

        # Create at cursor position
        x = self.viewport.cursor.x
        y = self.viewport.cursor.y

        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.create(
            name=name,
            x=x,
            y=y,
            width=w,
            height=h,
            zone_type=ZoneType.WATCH,
            command=command,
            interval=interval,
        )

        # Set up periodic refresh using Textual's set_interval
        self._start_watch_timer(zone)

        canvas_widget.refresh()
        self._update_status(f"Created watch zone {zone.name} (refresh: {interval}s)")

    def _start_watch_timer(self, zone) -> None:
        """Start a periodic timer to refresh a WATCH zone."""
        # Cancel any existing timer for this zone
        if zone.name in self._watch_timers:
            timer = self._watch_timers[zone.name]
            timer.stop()

        def refresh_zone():
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            z = canvas_widget.zone_manager.get(zone.name)
            if z and z.zone_type == ZoneType.WATCH:
                z.refresh()
                canvas_widget.refresh()

        # Create new timer
        timer = self.set_interval(zone.interval, refresh_zone)
        self._watch_timers[zone.name] = timer

    def _zone_delete(self, args: list[str]) -> None:
        """Handle :zone delete NAME"""
        if not args:
            self._update_status("Usage: zone delete NAME")
            return

        name = args[0].upper()

        # Cancel any watch timer
        if name in self._watch_timers:
            self._watch_timers[name].stop()
            del self._watch_timers[name]

        canvas_widget = self.query_one("#canvas", CanvasWidget)
        if canvas_widget.zone_manager.delete(name):
            canvas_widget.refresh()
            self._update_status(f"Deleted zone {name}")
        else:
            self._update_status(f"Zone not found: {name}")

    def _zone_goto(self, args: list[str]) -> None:
        """Handle :zone goto NAME - jump cursor to zone center"""
        if not args:
            self._update_status("Usage: zone goto NAME")
            return

        name = args[0]
        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.get(name)

        if not zone:
            self._update_status(f"Zone not found: {name}")
            return

        # Move cursor to zone center
        cx = zone.x + zone.width // 2
        cy = zone.y + zone.height // 2
        self.viewport.cursor.set(cx, cy)
        self.viewport.ensure_cursor_visible(margin=2)
        canvas_widget.refresh()
        self._update_status(f"Jumped to zone {zone.name}")

    def _zone_info(self, args: list[str]) -> None:
        """Handle :zone info NAME - show zone details"""
        if not args:
            self._update_status("Usage: zone info NAME")
            return

        name = args[0]
        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.get(name)

        if not zone:
            self._update_status(f"Zone not found: {name}")
            return

        info = f"{zone.name}: [{zone.type_indicator}] ({zone.x},{zone.y}) {zone.width}x{zone.height}"
        if zone.command:
            info += f" cmd='{zone.command}'"
        self._update_status(info)

    def _zone_refresh(self, args: list[str]) -> None:
        """Handle :zone refresh NAME - manually refresh a zone"""
        if not args:
            self._update_status("Usage: zone refresh NAME")
            return

        name = args[0]
        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.get(name)

        if not zone:
            self._update_status(f"Zone not found: {name}")
            return

        if zone.zone_type not in (ZoneType.PIPE, ZoneType.WATCH):
            self._update_status(f"Cannot refresh static zone {name}")
            return

        zone.refresh()
        canvas_widget.refresh()
        self._update_status(f"Refreshed zone {zone.name}")

    def _handle_zones_list(self) -> None:
        """Handle :zones - list all zones"""
        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zones = canvas_widget.zone_manager.list_zones()

        if not zones:
            self._update_status("No zones defined")
            return

        zone_list = ", ".join(f"{z.name}[{z.type_indicator}]" for z in zones)
        self._update_status(f"Zones: {zone_list}")

    # PTY zone commands
    def _zone_pty(self, args: list[str]) -> None:
        """Handle :zone pty NAME W H [SHELL]"""
        if len(args) < 3:
            self._update_status("Usage: zone pty NAME W H [SHELL]")
            return

        name = args[0]
        try:
            w, h = int(args[1]), int(args[2])
        except ValueError:
            self._update_status("Usage: zone pty NAME W H [SHELL]")
            return

        shell = args[3] if len(args) > 3 else "/bin/bash"

        # Create at cursor position
        x = self.viewport.cursor.x
        y = self.viewport.cursor.y

        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.create(
            name=name,
            x=x,
            y=y,
            width=w,
            height=h,
            zone_type=ZoneType.PTY,
        )

        # Start the PTY session
        if zone.start_pty(shell):
            # Set up periodic refresh for PTY display
            self._start_pty_refresh_timer()
            canvas_widget.refresh()
            self._update_status(f"Created PTY zone {zone.name} - Enter to focus")
        else:
            canvas_widget.zone_manager.delete(name)
            self._update_status("Failed to start PTY")

    def _start_pty_refresh_timer(self) -> None:
        """Start/ensure timer for refreshing PTY zone displays."""
        if self._pty_refresh_timer is None:

            def refresh_pty_zones():
                canvas_widget = self.query_one("#canvas", CanvasWidget)
                # Just refresh the widget to pick up PTY content changes
                canvas_widget.refresh()

            self._pty_refresh_timer = self.set_interval(0.1, refresh_pty_zones)

    def _zone_send(self, args: list[str]) -> None:
        """Handle :zone send NAME TEXT - send text to PTY"""
        if len(args) < 2:
            self._update_status("Usage: zone send NAME TEXT")
            return

        name = args[0]
        # Join remaining args as the text to send
        text = " ".join(args[1:])
        # Handle escape sequences
        text = text.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")

        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.get(name)

        if not zone:
            self._update_status(f"Zone not found: {name}")
            return

        if zone.zone_type != ZoneType.PTY:
            self._update_status(f"Not a PTY zone: {name}")
            return

        if not zone.is_pty_active():
            self._update_status(f"PTY not active: {name}")
            return

        if zone.write_to_pty(text):
            self._update_status(f"Sent to {zone.name}")
        else:
            self._update_status(f"Failed to send to {zone.name}")

    def _zone_focus(self, args: list[str]) -> None:
        """Handle :zone focus NAME - focus PTY for keyboard input"""
        if not args:
            self._update_status("Usage: zone focus NAME")
            return

        name = args[0].upper()
        canvas_widget = self.query_one("#canvas", CanvasWidget)
        zone = canvas_widget.zone_manager.get(name)

        if not zone:
            self._update_status(f"Zone not found: {name}")
            return

        if zone.zone_type != ZoneType.PTY:
            self._update_status(f"Not a PTY zone: {name}")
            return

        if not zone.is_pty_active():
            self._update_status(f"PTY not active: {name}")
            return

        # Focus the zone
        self._focus_pty_zone(zone)

    def _focus_pty_zone(self, zone) -> None:
        """Focus a PTY zone for keyboard input."""
        # Unfocus any previously focused zone
        if self._focused_pty_zone:
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            old_zone = canvas_widget.zone_manager.get(self._focused_pty_zone)
            if old_zone:
                old_zone.focused = False

        # Focus the new zone
        zone.focused = True
        self._focused_pty_zone = zone.name
        self._set_mode(Mode.PTY_FOCUS)
        self._update_status(f"[PTY] {zone.name} - Esc to unfocus")

    def _unfocus_pty_zone(self) -> None:
        """Unfocus the current PTY zone."""
        if self._focused_pty_zone:
            canvas_widget = self.query_one("#canvas", CanvasWidget)
            zone = canvas_widget.zone_manager.get(self._focused_pty_zone)
            if zone:
                zone.focused = False
            self._focused_pty_zone = None

        self._set_mode(Mode.NAV)
        self._update_status("PTY unfocused")


def main():
    """Run the app."""
    app = MyGridApp()
    app.run()


if __name__ == "__main__":
    main()
