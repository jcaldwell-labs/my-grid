#!/usr/bin/env python3
"""
my-grid - ASCII Canvas Editor

Main entry point that wires together all components.
"""

import argparse
import curses
import json
import logging
import sys
from pathlib import Path

from canvas import Canvas
from viewport import Viewport
from renderer import Renderer, GridSettings, GridLineMode, create_status_line
from input import InputHandler, Action, InputEvent
from modes import Mode, ModeConfig, ModeStateMachine, ModeResult
from project import Project, add_recent_project, suggest_filename
from command_queue import CommandQueue, CommandResponse, send_response
from server import APIServer, ServerConfig
from zones import Zone, ZoneManager, ZoneExecutor, ZoneType, PTYHandler, PTY_AVAILABLE
from layouts import LayoutManager, install_default_layouts
from external import (
    tool_available, get_tool_status,
    draw_box, get_boxes_styles,
    draw_figlet, get_figlet_fonts,
    pipe_command, write_lines_to_canvas
)
from joystick import JoystickHandler, JoystickConfig, JoystickDirection

logger = logging.getLogger(__name__)


class Application:
    """
    Main application class.

    Coordinates all components and runs the main loop.
    """

    def __init__(self, stdscr: "curses.window", server_config: ServerConfig | None = None):
        self.stdscr = stdscr

        # Core components
        self.canvas = Canvas()
        self.viewport = Viewport()
        self.renderer = Renderer(stdscr)
        self.input_handler = InputHandler()
        self.mode_config = ModeConfig()
        self.state_machine = ModeStateMachine(
            self.canvas, self.viewport, self.mode_config
        )
        self.project = Project()
        self.zone_manager = ZoneManager()
        self.zone_executor = ZoneExecutor(self.zone_manager)
        self.pty_handler = PTYHandler(self.zone_manager)
        self.layout_manager = LayoutManager()

        # Install default layouts on first run
        install_default_layouts()

        # PTY focus tracking
        self._focused_pty: str | None = None  # Name of focused PTY zone

        # API server components
        self.command_queue = CommandQueue()
        self.api_server: APIServer | None = None
        self._server_config = server_config

        # Joystick handler
        self.joystick = JoystickHandler()
        self._joystick_enabled = False

        # Status message (temporary display)
        self._status_message: str | None = None
        self._status_message_frames: int = 0

        # Initialize viewport size
        self._update_viewport_size()

        # Register additional commands
        self._register_commands()

        # Start API server if configured
        if server_config:
            self._start_server(server_config)

        # Initialize joystick (silent - don't clutter startup)
        self._joystick_enabled = self.joystick.init(silent=True)

    def _update_viewport_size(self) -> None:
        """Update viewport to match terminal size."""
        height, width = self.renderer.get_terminal_size()
        # Reserve 1 line for status bar
        self.viewport.resize(width, height - 1)

    def _register_commands(self) -> None:
        """Register application-level commands."""
        self.state_machine.register_command("save", self._cmd_save)
        self.state_machine.register_command("saveas", self._cmd_save_as)
        self.state_machine.register_command("open", self._cmd_open)
        self.state_machine.register_command("new", self._cmd_new)
        self.state_machine.register_command("export", self._cmd_export)
        self.state_machine.register_command("import", self._cmd_import)
        self.state_machine.register_command("rect", self._cmd_rect)
        self.state_machine.register_command("line", self._cmd_line)
        self.state_machine.register_command("text", self._cmd_text)
        self.state_machine.register_command("grid", self._cmd_grid)
        self.state_machine.register_command("ydir", self._cmd_ydir)
        self.state_machine.register_command("status", self._cmd_status)
        self.state_machine.register_command("zone", self._cmd_zone)
        self.state_machine.register_command("zones", self._cmd_zones)
        self.state_machine.register_command("box", self._cmd_box)
        self.state_machine.register_command("figlet", self._cmd_figlet)
        self.state_machine.register_command("pipe", self._cmd_pipe)
        self.state_machine.register_command("tools", self._cmd_tools)
        self.state_machine.register_command("layout", self._cmd_layout)

    def _start_server(self, config: ServerConfig) -> None:
        """Start the API server."""
        self.api_server = APIServer(self.command_queue)
        self.api_server.start(config)
        logger.info(f"API server started on port {config.tcp_port}")

    def _stop_server(self) -> None:
        """Stop the API server."""
        if self.api_server:
            self.api_server.stop()
            self.api_server = None

    def load_file(self, filepath: str | Path) -> None:
        """Load a project or text file."""
        filepath = Path(filepath)

        if not filepath.exists():
            self._show_message(f"File not found: {filepath}")
            return

        try:
            if filepath.suffix.lower() == '.json':
                self.project = Project.load(
                    filepath, self.canvas, self.viewport,
                    grid_settings=self.renderer.grid,
                    bookmarks=self.state_machine.bookmarks,
                    zones=self.zone_manager
                )
                add_recent_project(filepath)
                self._show_message(f"Loaded: {filepath.name}")
            else:
                # Treat as text file
                self.project = Project.import_text(
                    filepath, self.canvas, self.viewport
                )
                self._show_message(f"Imported: {filepath.name}")
        except Exception as e:
            self._show_message(f"Error loading: {e}")

    def _show_message(self, message: str, frames: int = 60) -> None:
        """Show a temporary status message."""
        self._status_message = message
        self._status_message_frames = frames

    def _get_status_line(self) -> str:
        """Build the status line string."""
        # Show temporary message if active
        if self._status_message and self._status_message_frames > 0:
            self._status_message_frames -= 1
            return f" {self._status_message}"

        # Show PTY focus mode indicator
        if self._focused_pty:
            return f" [PTY] {self._focused_pty} - Press Esc to unfocus"

        # Show command buffer in command mode
        if self.state_machine.mode == Mode.COMMAND:
            buf = self.state_machine.command_buffer
            return f":{buf.text}_"

        # Show prompt for bookmark modes
        if self.state_machine.mode == Mode.MARK_SET:
            return " SET MARK: press a-z or 0-9 (Esc to cancel)"
        if self.state_machine.mode == Mode.MARK_JUMP:
            return " JUMP TO MARK: press a-z or 0-9 (Esc to cancel)"

        # Build status line sections
        mode = self.state_machine.mode_name
        cursor = self.viewport.cursor

        # Mode indicator with visual distinction
        mode_indicators = {
            "NAV": "NAV",
            "PAN": "PAN",
            "EDIT": "EDT",
            "COMMAND": "CMD",
        }
        mode_str = mode_indicators.get(mode, mode)

        # Cursor position - prominent display
        pos_str = f"X:{cursor.x:>5} Y:{cursor.y:>5}"

        # Cell at cursor
        cell_char = self.canvas.get_char(cursor.x, cursor.y)
        if cell_char == ' ':
            cell_str = "·"
        else:
            cell_str = f"'{cell_char}'"

        # Current zone (if cursor is in one)
        current_zone = self.zone_manager.find_at(cursor.x, cursor.y)
        zone_str = current_zone.name if current_zone else "---"

        # Nearest zone/bookmark indicator
        nearest_info = ""
        nearest = self.zone_manager.nearest(cursor.x, cursor.y)
        if nearest:
            zone, dist, direction = nearest
            # Show bookmark key if zone has one, otherwise zone name
            label = f"[{zone.bookmark}]" if zone.bookmark else zone.name[:8]
            nearest_info = f"{direction}{int(dist)} {label}"

        # File status: name with modified indicator
        if self.project.dirty:
            file_status = f"[+] {self.project.filename}"
        else:
            file_status = self.project.filename

        # Build the line with clear sections
        # Format: MODE | X:    0 Y:    0 | 'char' | ZONE | →120 [b] | filename | cells
        parts = [
            f" {mode_str}",
            f"{pos_str}",
            f"{cell_str:>3}",
            zone_str,
        ]

        # Add nearest zone indicator if available
        if nearest_info:
            parts.append(nearest_info)

        parts.append(file_status)

        # Add cell count
        if self.canvas.cell_count > 0:
            parts.append(f"{self.canvas.cell_count} cells")

        # Add joystick indicator
        if self._joystick_enabled and self.joystick.is_connected:
            parts.append("JOY")

        return " │ ".join(parts)

    def run(self) -> None:
        """Main application loop."""
        running = True

        # Enable non-blocking input if server or joystick is active
        if self._server_config or self._joystick_enabled:
            self.stdscr.timeout(50)  # 50ms timeout = ~20 FPS

        try:
            while running:
                # Process external commands from API server
                if self._server_config:
                    self._process_external_commands()

                # Process joystick input
                if self._joystick_enabled:
                    self._process_joystick_input()

                # Handle terminal resize
                self._update_viewport_size()

                # Render dynamic zones to canvas
                self.zone_manager.render_all_zones(self.canvas)

                # Render frame
                status = self._get_status_line()
                self.renderer.render(self.canvas, self.viewport, status)

                # Get input (may timeout if server/joystick mode)
                key = self.renderer.get_input()

                # Handle timeout (no input) - just continue loop for joystick polling
                if key == -1:
                    continue

                # Handle resize event
                if key == curses.KEY_RESIZE:
                    continue

                # If PTY is focused, forward input to PTY
                if self._focused_pty:
                    if key == 27:  # Escape - unfocus PTY
                        self._focused_pty = None
                        self._show_message("PTY unfocused")
                    else:
                        # Forward key to PTY
                        self._forward_key_to_pty(key)
                    continue

                # Convert curses key to action
                event = self._curses_key_to_event(key)
                if not event:
                    continue

                # Check if Enter pressed in a PTY zone - focus it
                if event.action == Action.NEWLINE:
                    current_zone = self.zone_manager.find_at(
                        self.viewport.cursor.x, self.viewport.cursor.y
                    )
                    if current_zone and current_zone.zone_type == ZoneType.PTY:
                        if self.pty_handler.is_active(current_zone.name):
                            self._focused_pty = current_zone.name
                            self._show_message(f"PTY focused: {current_zone.name}")
                            continue

                # Process through state machine
                result = self.state_machine.process(event)

                # Handle result
                if result.quit:
                    if self._confirm_quit():
                        running = False
                    continue

                if result.message:
                    self._show_message(result.message)

                if result.command:
                    self._handle_command(result.command)

                # Handle grid toggles (not mode-dependent)
                if event.action == Action.TOGGLE_GRID_MAJOR:
                    self.renderer.grid.show_major_lines = not self.renderer.grid.show_major_lines
                    self._show_message(
                        f"Major grid: {'ON' if self.renderer.grid.show_major_lines else 'OFF'}"
                    )
                elif event.action == Action.TOGGLE_GRID_MINOR:
                    self.renderer.grid.show_minor_lines = not self.renderer.grid.show_minor_lines
                    self._show_message(
                        f"Minor grid: {'ON' if self.renderer.grid.show_minor_lines else 'OFF'}"
                    )
                elif event.action == Action.TOGGLE_GRID_ORIGIN:
                    self.renderer.grid.show_origin = not self.renderer.grid.show_origin
                    self._show_message(
                        f"Origin marker: {'ON' if self.renderer.grid.show_origin else 'OFF'}"
                    )

                # Handle file operations
                if event.action == Action.SAVE:
                    self._do_save()
                elif event.action == Action.SAVE_AS:
                    self._do_save_as()
                elif event.action == Action.OPEN:
                    self._do_open()
                elif event.action == Action.NEW:
                    self._do_new()
                elif event.action == Action.HELP:
                    self._show_help()

                # Mark dirty on canvas changes in edit mode
                if self.state_machine.mode == Mode.EDIT and event.char:
                    self.project.mark_dirty()
        finally:
            # Clean up server on exit
            self._stop_server()
            # Clean up joystick
            if self._joystick_enabled:
                self.joystick.cleanup()
            # Clean up zone watchers
            self.zone_executor.stop_all()
            # Clean up PTY sessions
            self.pty_handler.stop_all()

    def _process_external_commands(self) -> None:
        """Process commands from the external API queue."""
        # Process up to 10 commands per frame to prevent flooding
        for _ in range(10):
            ext_cmd = self.command_queue.get_nowait()
            if not ext_cmd:
                break

            try:
                result = self._execute_external_command(ext_cmd.command)
                response = CommandResponse(
                    status="ok",
                    message=result.message or "OK",
                    data=result.data if hasattr(result, 'data') else None
                )
            except Exception as e:
                response = CommandResponse(status="error", message=str(e))

            # Send response back if requested
            send_response(ext_cmd, response)

    def _process_joystick_input(self) -> None:
        """Process joystick input for cursor movement."""
        # Get movement from joystick (handles repeat timing internally)
        dx, dy = self.joystick.get_movement()

        if dx != 0 or dy != 0:
            # Move cursor based on current mode
            mode = self.state_machine.mode

            if mode == Mode.NAV or mode == Mode.EDIT:
                # Move cursor and ensure it stays visible (auto-pan)
                self.viewport.move_cursor(dx, dy)
                self.viewport.ensure_cursor_visible(margin=self.mode_config.scroll_margin)
            elif mode == Mode.PAN:
                # Pan viewport (cursor follows)
                self.viewport.pan(dx, dy)

        # Check for button presses
        buttons = self.joystick.get_button_presses()
        for btn in buttons:
            if btn == 0:  # A button - confirm/select
                # In NAV mode, enter edit mode
                if self.state_machine.mode == Mode.NAV:
                    self.state_machine.set_mode(Mode.EDIT)
                    self._show_message("-- EDIT --")
            elif btn == 1:  # B button - back/escape
                # Exit current mode back to NAV
                if self.state_machine.mode != Mode.NAV:
                    self.state_machine.set_mode(Mode.NAV)
                    self._show_message("")

    def _forward_key_to_pty(self, key: int) -> None:
        """Forward a key press to the focused PTY."""
        if not self._focused_pty:
            return

        # Convert curses key codes to terminal sequences
        if key == curses.KEY_UP:
            data = '\x1b[A'
        elif key == curses.KEY_DOWN:
            data = '\x1b[B'
        elif key == curses.KEY_RIGHT:
            data = '\x1b[C'
        elif key == curses.KEY_LEFT:
            data = '\x1b[D'
        elif key == curses.KEY_BACKSPACE or key == 127:
            data = '\x7f'
        elif key == curses.KEY_DC:  # Delete
            data = '\x1b[3~'
        elif key == curses.KEY_HOME:
            data = '\x1b[H'
        elif key == curses.KEY_END:
            data = '\x1b[F'
        elif key == 10 or key == 13:  # Enter
            data = '\n'
        elif key == 9:  # Tab
            data = '\t'
        elif 1 <= key <= 26:  # Ctrl+A through Ctrl+Z
            data = chr(key)
        elif 32 <= key <= 126:  # Printable ASCII
            data = chr(key)
        else:
            return  # Unknown key, don't forward

        self.pty_handler.send_input(self._focused_pty, data)

    def _execute_external_command(self, command: str) -> ModeResult:
        """Execute a command string from external source."""
        # Strip leading : or / if present
        if command.startswith(':') or command.startswith('/'):
            command = command[1:]

        # Parse command and args
        parts = command.split()
        if not parts:
            return ModeResult(message="Empty command")

        cmd_name = parts[0].lower()
        args = parts[1:]

        # Look up command handler
        handler = self.state_machine.commands.get(cmd_name)
        if handler:
            return handler(args)

        # Try built-in commands
        if cmd_name in ("quit", "q"):
            return ModeResult(message="Quit not allowed via API")
        elif cmd_name in ("goto", "g"):
            return self.state_machine._cmd_goto(args)
        elif cmd_name == "clear":
            return self.state_machine._cmd_clear(args)
        elif cmd_name == "origin":
            return self.state_machine._cmd_origin(args)

        return ModeResult(message=f"Unknown command: {cmd_name}")

    def _curses_key_to_event(self, key: int) -> InputEvent | None:
        """Convert curses key code to InputEvent."""
        from input import Action

        # Map curses keys to actions
        key_map = {
            ord('w'): Action.MOVE_UP,
            ord('s'): Action.MOVE_DOWN,
            ord('a'): Action.MOVE_LEFT,
            ord('d'): Action.MOVE_RIGHT,
            curses.KEY_UP: Action.MOVE_UP,
            curses.KEY_DOWN: Action.MOVE_DOWN,
            curses.KEY_LEFT: Action.MOVE_LEFT,
            curses.KEY_RIGHT: Action.MOVE_RIGHT,

            ord('W'): Action.MOVE_UP_FAST,
            ord('S'): Action.MOVE_DOWN_FAST,
            ord('A'): Action.MOVE_LEFT_FAST,
            ord('D'): Action.MOVE_RIGHT_FAST,

            ord('i'): Action.ENTER_EDIT_MODE,
            ord('p'): Action.TOGGLE_PAN_MODE,
            ord(':'): Action.ENTER_COMMAND_MODE,
            ord('/'): Action.ENTER_COMMAND_MODE,
            27: Action.EXIT_MODE,  # Escape

            ord('g'): Action.TOGGLE_GRID_MAJOR,
            ord('G'): Action.TOGGLE_GRID_MINOR,
            ord('0'): Action.TOGGLE_GRID_ORIGIN,

            ord('q'): Action.QUIT,
            curses.KEY_F1: Action.HELP,

            curses.KEY_BACKSPACE: Action.BACKSPACE,
            127: Action.BACKSPACE,  # Alt backspace
            curses.KEY_DC: Action.DELETE_CHAR,
            10: Action.NEWLINE,  # Enter
            13: Action.NEWLINE,  # Carriage return
        }

        # Check for Ctrl combinations
        if key == 19:  # Ctrl+S
            return InputEvent(action=Action.SAVE)
        if key == 15:  # Ctrl+O
            return InputEvent(action=Action.OPEN)
        if key == 14:  # Ctrl+N
            return InputEvent(action=Action.NEW)

        # Check mapped actions
        if key in key_map:
            action = key_map[key]
            # In edit/command mode, letter keys type instead of triggering actions
            if self.state_machine.mode in (Mode.EDIT, Mode.COMMAND):
                # Allow arrow keys, function keys, and special keys
                if key in (curses.KEY_UP, curses.KEY_DOWN,
                          curses.KEY_LEFT, curses.KEY_RIGHT,
                          curses.KEY_BACKSPACE, curses.KEY_DC,
                          curses.KEY_F1, 27, 10, 13, 127):
                    return InputEvent(action=action)
                # Letter/number keys should type as characters
                if 32 <= key <= 126:
                    return InputEvent(char=chr(key))
            return InputEvent(action=action)

        # Printable characters
        if 32 <= key <= 126:
            return InputEvent(char=chr(key))

        return None

    def _confirm_quit(self) -> bool:
        """Confirm quit if there are unsaved changes."""
        if not self.project.dirty:
            return True

        self.renderer.render_message(
            "Unsaved changes! Press 'q' again to quit, any other key to cancel.",
            row=-1
        )
        key = self.renderer.get_input()
        return key == ord('q')

    def _handle_command(self, command: str) -> None:
        """Handle special commands from mode result."""
        if command == "save":
            self._do_save()
        elif command == "help":
            self._show_help()

    def _do_save(self) -> None:
        """Save the current project."""
        if self.project.filepath:
            try:
                self.project.save(
                    self.canvas, self.viewport,
                    grid_settings=self.renderer.grid,
                    bookmarks=self.state_machine.bookmarks,
                    zones=self.zone_manager
                )
                add_recent_project(self.project.filepath)
                self._show_message(f"Saved: {self.project.filename}")
            except Exception as e:
                self._show_message(f"Save error: {e}")
        else:
            self._do_save_as()

    def _do_save_as(self) -> None:
        """Save with a new filename."""
        suggested = suggest_filename(self.canvas)
        filename = self.renderer.get_string_input(f"Save as [{suggested}]: ")

        if not filename:
            filename = suggested

        if not filename.endswith('.json'):
            filename += '.json'

        try:
            filepath = Path(filename)
            self.project.save(
                self.canvas, self.viewport,
                grid_settings=self.renderer.grid,
                bookmarks=self.state_machine.bookmarks,
                zones=self.zone_manager,
                filepath=filepath
            )
            add_recent_project(filepath)
            self._show_message(f"Saved: {filepath.name}")
        except Exception as e:
            self._show_message(f"Save error: {e}")

    def _do_open(self) -> None:
        """Open a file."""
        filename = self.renderer.get_string_input("Open file: ")
        if filename:
            self.load_file(filename)

    def _do_new(self) -> None:
        """Create a new canvas."""
        if self.project.dirty:
            self.renderer.render_message(
                "Unsaved changes! Press 'y' to discard, any other key to cancel.",
                row=-1
            )
            if self.renderer.get_input() != ord('y'):
                return

        self.canvas.clear_all()
        self.viewport.cursor.set(0, 0)
        self.viewport.origin.set(0, 0)
        self.viewport.pan_to(0, 0)
        self.state_machine.bookmarks.clear()
        self.zone_manager.clear()
        self.project = Project()
        self._show_message("New canvas created")

    def _show_help(self) -> None:
        """Show help screen."""
        # Build joystick status line
        joy_status = ""
        if self._joystick_enabled and self.joystick.is_connected:
            info = self.joystick.get_info()
            joy_status = f"  JOYSTICK: {info['name']} (connected)\n"
            joy_status += "    D-pad/Stick   - Move cursor       Button A      - Enter EDIT mode\n"
            joy_status += "    Button B      - Exit to NAV\n"

        help_text = f"""
  my-grid - ASCII Canvas Editor

  MODES:
    NAV (default) - Navigate canvas    PAN (p)       - Pan viewport
    EDIT (i)      - Type/draw          COMMAND (:)   - Enter commands

  NAVIGATION:
    wasd / arrows - Move cursor        WASD          - Fast move (10x)

  BOOKMARKS:
    m + key       - Set mark at cursor (a-z, 0-9)
    ' + key       - Jump to mark
    :marks        - List all marks
    :delmark X    - Delete mark X

  COMMANDS:
    :q / :wq      - Quit / Save+quit   :w            - Save
    :goto X Y     - Move to position   :origin here  - Set origin
    :clear        - Clear canvas       :export       - Export as text
    :grid N       - Set grid interval  :rect W H     - Draw rectangle
    :help / :?    - This help screen

  KEYS:
    g / G         - Toggle major/minor grid
    0             - Toggle origin marker
    Ctrl+S        - Save               Esc           - Exit mode
    F1            - This help          q             - Quit

{joy_status}  Press any key to continue...
"""
        self.stdscr.clear()
        for i, line in enumerate(help_text.strip().split('\n')):
            try:
                self.stdscr.addstr(i, 0, line)
            except curses.error:
                pass
        self.stdscr.refresh()

        # Wait for actual keypress (disable timeout temporarily)
        self.stdscr.timeout(-1)  # Block until key pressed
        self.renderer.get_input()
        # Restore timeout if joystick is active
        if self._joystick_enabled or self._server_config:
            self.stdscr.timeout(50)

    # Command handlers
    def _cmd_save(self, args: list[str]) -> ModeResult:
        self._do_save()
        return ModeResult()

    def _cmd_save_as(self, args: list[str]) -> ModeResult:
        if args:
            filename = args[0]
            if not filename.endswith('.json'):
                filename += '.json'
            try:
                self.project.save(
                    self.canvas, self.viewport,
                    grid_settings=self.renderer.grid,
                    bookmarks=self.state_machine.bookmarks,
                    zones=self.zone_manager,
                    filepath=Path(filename)
                )
                self._show_message(f"Saved: {filename}")
            except Exception as e:
                return ModeResult(message=f"Save error: {e}")
        else:
            self._do_save_as()
        return ModeResult()

    def _cmd_open(self, args: list[str]) -> ModeResult:
        if args:
            self.load_file(args[0])
        else:
            self._do_open()
        return ModeResult()

    def _cmd_new(self, args: list[str]) -> ModeResult:
        self._do_new()
        return ModeResult()

    def _cmd_export(self, args: list[str]) -> ModeResult:
        filepath = args[0] if args else None
        try:
            result = self.project.export_text(self.canvas, filepath=filepath)
            return ModeResult(message=f"Exported: {result.name}")
        except Exception as e:
            return ModeResult(message=f"Export error: {e}")

    def _cmd_import(self, args: list[str]) -> ModeResult:
        if not args:
            return ModeResult(message="Usage: import <filename>")
        self.load_file(args[0])
        return ModeResult()

    def _cmd_rect(self, args: list[str]) -> ModeResult:
        """Draw rectangle: rect WIDTH HEIGHT [CHAR]"""
        if len(args) < 2:
            return ModeResult(message="Usage: rect WIDTH HEIGHT [char]")
        try:
            w, h = int(args[0]), int(args[1])
            char = args[2] if len(args) > 2 else None
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            if char:
                self.canvas.draw_rect(cx, cy, w, h, char, char, char)
            else:
                self.canvas.draw_rect(cx, cy, w, h)
            self.project.mark_dirty()
            return ModeResult(message=f"Drew {w}x{h} rectangle")
        except ValueError:
            return ModeResult(message="Invalid dimensions")

    def _cmd_line(self, args: list[str]) -> ModeResult:
        """Draw line: line X2 Y2 [CHAR]"""
        if len(args) < 2:
            return ModeResult(message="Usage: line X2 Y2 [char]")
        try:
            x2, y2 = int(args[0]), int(args[1])
            char = args[2] if len(args) > 2 else '*'
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            self.canvas.draw_line(cx, cy, x2, y2, char)
            self.project.mark_dirty()
            return ModeResult(message=f"Drew line to ({x2}, {y2})")
        except ValueError:
            return ModeResult(message="Invalid coordinates")

    def _cmd_text(self, args: list[str]) -> ModeResult:
        """Write text: text MESSAGE"""
        if not args:
            return ModeResult(message="Usage: text MESSAGE")
        text = ' '.join(args)
        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
        self.canvas.write_text(cx, cy, text)
        self.project.mark_dirty()
        return ModeResult(message=f"Wrote {len(text)} characters")

    def _cmd_grid(self, args: list[str]) -> ModeResult:
        """Configure grid: grid [major|minor|lines|markers|dots|off|rulers|labels|interval]"""
        if not args:
            mode_name = self.renderer.grid.line_mode.name.lower()
            return ModeResult(
                message=f"Grid: mode={mode_name} major={self.renderer.grid.major_interval} "
                       f"minor={self.renderer.grid.minor_interval} "
                       f"rulers={'ON' if self.renderer.grid.show_rulers else 'OFF'}"
            )

        arg = args[0].lower()

        # Toggle major/minor grid visibility
        if arg == "major":
            self.renderer.grid.show_major_lines = not self.renderer.grid.show_major_lines
            return ModeResult(message=f"Major grid: {'ON' if self.renderer.grid.show_major_lines else 'OFF'}")
        elif arg == "minor":
            self.renderer.grid.show_minor_lines = not self.renderer.grid.show_minor_lines
            return ModeResult(message=f"Minor grid: {'ON' if self.renderer.grid.show_minor_lines else 'OFF'}")

        # Grid line modes
        elif arg == "lines":
            self.renderer.grid.line_mode = GridLineMode.LINES
            return ModeResult(message="Grid mode: LINES (full grid lines)")
        elif arg == "markers":
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            return ModeResult(message="Grid mode: MARKERS (intersection only)")
        elif arg == "dots":
            self.renderer.grid.line_mode = GridLineMode.DOTS
            return ModeResult(message="Grid mode: DOTS (dotted lines)")
        elif arg == "off":
            self.renderer.grid.line_mode = GridLineMode.OFF
            return ModeResult(message="Grid mode: OFF")

        # Ruler and label toggles
        elif arg == "rulers":
            self.renderer.grid.show_rulers = not self.renderer.grid.show_rulers
            return ModeResult(message=f"Rulers: {'ON' if self.renderer.grid.show_rulers else 'OFF'}")
        elif arg == "labels":
            self.renderer.grid.show_labels = not self.renderer.grid.show_labels
            return ModeResult(message=f"Coordinate labels: {'ON' if self.renderer.grid.show_labels else 'OFF'}")

        # Interval configuration
        elif arg == "interval":
            if len(args) < 2:
                return ModeResult(message=f"Interval: major={self.renderer.grid.major_interval} minor={self.renderer.grid.minor_interval}")
            try:
                major = int(args[1])
                minor = int(args[2]) if len(args) > 2 else major // 2
                self.renderer.grid.major_interval = major
                self.renderer.grid.minor_interval = minor
                return ModeResult(message=f"Grid interval: major={major} minor={minor}")
            except ValueError:
                return ModeResult(message="Usage: grid interval MAJOR [MINOR]")

        # Try as a number (legacy: set major interval)
        else:
            try:
                interval = int(arg)
                self.renderer.grid.major_interval = interval
                return ModeResult(message=f"Major interval: {interval}")
            except ValueError:
                return ModeResult(
                    message="Usage: grid [major|minor|lines|markers|dots|off|rulers|labels|interval N]"
                )

    def _cmd_ydir(self, args: list[str]) -> ModeResult:
        """Set Y direction: ydir up|down"""
        from viewport import YAxisDirection
        if not args:
            current = self.viewport.y_direction.name
            return ModeResult(message=f"Y direction: {current}")
        arg = args[0].lower()
        if arg == "up":
            self.viewport.y_direction = YAxisDirection.UP
            return ModeResult(message="Y direction: UP (mathematical)")
        elif arg == "down":
            self.viewport.y_direction = YAxisDirection.DOWN
            return ModeResult(message="Y direction: DOWN (screen)")
        else:
            return ModeResult(message="Usage: ydir up|down")

    def _cmd_status(self, args: list[str]) -> ModeResult:
        """Return current state as JSON."""
        state = {
            "cursor": {"x": self.viewport.cursor.x, "y": self.viewport.cursor.y},
            "viewport": {
                "x": self.viewport.x,
                "y": self.viewport.y,
                "width": self.viewport.width,
                "height": self.viewport.height
            },
            "mode": self.state_machine.mode_name,
            "cells": self.canvas.cell_count,
            "dirty": self.project.dirty,
            "file": self.project.filename,
            "server": self.api_server.status.tcp_port if self.api_server else None
        }
        return ModeResult(message=json.dumps(state))

    def _cmd_zone(self, args: list[str]) -> ModeResult:
        """
        Zone management command.

        Usage:
            :zone create NAME X Y W H [desc]  - Create zone at coordinates
            :zone create NAME here W H [desc] - Create zone at cursor
            :zone delete NAME                 - Delete zone
            :zone goto NAME                   - Jump to zone center
            :zone info [NAME]                 - Show zone info
            :zone rename OLD NEW              - Rename zone
            :zone resize NAME W H             - Resize zone
            :zone move NAME X Y               - Move zone
            :zone link NAME BOOKMARK          - Associate bookmark
            :zone border NAME [style]         - Draw border (uses boxes)
            :zone pipe NAME W H CMD           - Create pipe zone
            :zone watch NAME W H INTERVAL CMD - Create watch zone
            :zone refresh NAME                - Refresh pipe/watch zone
            :zone pause NAME                  - Pause watch zone
            :zone resume NAME                 - Resume watch zone
        """
        if not args:
            return ModeResult(
                message="Usage: zone create|delete|goto|pipe|watch|refresh|..."
            )

        subcmd = args[0].lower()

        # :zone create NAME X Y W H [desc]
        # :zone create NAME here W H [desc]
        if subcmd == "create":
            if len(args) < 5:
                return ModeResult(message="Usage: zone create NAME X Y W H [desc]")
            name = args[1]
            if args[2].lower() == "here":
                x = self.viewport.cursor.x
                y = self.viewport.cursor.y
                try:
                    w = int(args[3])
                    h = int(args[4])
                    desc = " ".join(args[5:]) if len(args) > 5 else ""
                except (ValueError, IndexError):
                    return ModeResult(message="Usage: zone create NAME here W H [desc]")
            else:
                try:
                    x = int(args[2])
                    y = int(args[3])
                    w = int(args[4])
                    h = int(args[5])
                    desc = " ".join(args[6:]) if len(args) > 6 else ""
                except (ValueError, IndexError):
                    return ModeResult(message="Usage: zone create NAME X Y W H [desc]")

            try:
                self.zone_manager.create(name, x, y, w, h, description=desc)
                self.project.mark_dirty()
                return ModeResult(message=f"Created zone '{name}' at ({x},{y}) {w}x{h}")
            except ValueError as e:
                return ModeResult(message=str(e))

        # :zone delete NAME
        elif subcmd == "delete":
            if len(args) < 2:
                return ModeResult(message="Usage: zone delete NAME")
            name = args[1]
            if self.zone_manager.delete(name):
                self.project.mark_dirty()
                return ModeResult(message=f"Deleted zone '{name}'")
            return ModeResult(message=f"Zone '{name}' not found")

        # :zone goto NAME
        elif subcmd == "goto":
            if len(args) < 2:
                return ModeResult(message="Usage: zone goto NAME")
            name = args[1]
            zone = self.zone_manager.get(name)
            if zone is None:
                return ModeResult(message=f"Zone '{name}' not found")
            cx, cy = zone.center()
            self.viewport.cursor.set(cx, cy)
            self.viewport.center_on_cursor()
            return ModeResult(message=f"Jumped to zone '{zone.name}'")

        # :zone info [NAME]
        elif subcmd == "info":
            if len(args) < 2:
                # Show current zone info
                zone = self.zone_manager.find_at(
                    self.viewport.cursor.x, self.viewport.cursor.y
                )
                if zone is None:
                    return ModeResult(message="Not in any zone")
            else:
                zone = self.zone_manager.get(args[1])
                if zone is None:
                    return ModeResult(message=f"Zone '{args[1]}' not found")

            info = f"'{zone.name}' ({zone.x},{zone.y}) {zone.width}x{zone.height}"
            if zone.bookmark:
                info += f" [bookmark:{zone.bookmark}]"
            if zone.description:
                info += f" - {zone.description}"
            return ModeResult(message=info)

        # :zone rename OLD NEW
        elif subcmd == "rename":
            if len(args) < 3:
                return ModeResult(message="Usage: zone rename OLD NEW")
            if self.zone_manager.rename(args[1], args[2]):
                self.project.mark_dirty()
                return ModeResult(message=f"Renamed '{args[1]}' to '{args[2]}'")
            return ModeResult(message=f"Failed to rename (zone not found or name conflict)")

        # :zone resize NAME W H
        elif subcmd == "resize":
            if len(args) < 4:
                return ModeResult(message="Usage: zone resize NAME W H")
            try:
                w, h = int(args[2]), int(args[3])
                if self.zone_manager.resize(args[1], w, h):
                    self.project.mark_dirty()
                    return ModeResult(message=f"Resized '{args[1]}' to {w}x{h}")
                return ModeResult(message=f"Zone '{args[1]}' not found")
            except ValueError:
                return ModeResult(message="Invalid dimensions")

        # :zone move NAME X Y
        elif subcmd == "move":
            if len(args) < 4:
                return ModeResult(message="Usage: zone move NAME X Y")
            try:
                x, y = int(args[2]), int(args[3])
                if self.zone_manager.move(args[1], x, y):
                    self.project.mark_dirty()
                    return ModeResult(message=f"Moved '{args[1]}' to ({x},{y})")
                return ModeResult(message=f"Zone '{args[1]}' not found")
            except ValueError:
                return ModeResult(message="Invalid coordinates")

        # :zone link NAME BOOKMARK
        elif subcmd == "link":
            if len(args) < 3:
                return ModeResult(message="Usage: zone link NAME BOOKMARK")
            bookmark = args[2] if args[2] != "none" else None
            if self.zone_manager.set_bookmark(args[1], bookmark):
                self.project.mark_dirty()
                if bookmark:
                    return ModeResult(message=f"Linked '{args[1]}' to bookmark '{bookmark}'")
                return ModeResult(message=f"Unlinked bookmark from '{args[1]}'")
            return ModeResult(message=f"Zone '{args[1]}' not found")

        # :zone border NAME [style]
        elif subcmd == "border":
            if len(args) < 2:
                return ModeResult(message="Usage: zone border NAME [style]")
            zone = self.zone_manager.get(args[1])
            if zone is None:
                return ModeResult(message=f"Zone '{args[1]}' not found")

            # Draw a simple border around the zone
            style = args[2] if len(args) > 2 else None
            zone.border_style = style

            # Draw border using canvas rect
            self.canvas.draw_rect(zone.x, zone.y, zone.width, zone.height)
            self.project.mark_dirty()
            return ModeResult(message=f"Drew border for zone '{zone.name}'")

        # :zone pipe NAME W H CMD
        elif subcmd == "pipe":
            if len(args) < 5:
                return ModeResult(message="Usage: zone pipe NAME W H COMMAND")
            name = args[1]
            try:
                w, h = int(args[2]), int(args[3])
                cmd = " ".join(args[4:])
            except (ValueError, IndexError):
                return ModeResult(message="Invalid width/height")

            x = self.viewport.cursor.x
            y = self.viewport.cursor.y

            try:
                zone = self.zone_manager.create_pipe(name, x, y, w, h, cmd)
                # Execute immediately
                self.zone_executor.execute_pipe(zone)
                self.project.mark_dirty()
                return ModeResult(message=f"Created pipe zone '{name}' - {len(zone.content_lines)} lines")
            except ValueError as e:
                return ModeResult(message=str(e))

        # :zone watch NAME W H INTERVAL CMD
        elif subcmd == "watch":
            if len(args) < 6:
                return ModeResult(message="Usage: zone watch NAME W H INTERVAL COMMAND")
            name = args[1]
            try:
                w, h = int(args[2]), int(args[3])
                # Parse interval (e.g., "5s", "10", "1m")
                interval_str = args[4]
                if interval_str.endswith("s"):
                    interval = float(interval_str[:-1])
                elif interval_str.endswith("m"):
                    interval = float(interval_str[:-1]) * 60
                else:
                    interval = float(interval_str)
                cmd = " ".join(args[5:])
            except (ValueError, IndexError):
                return ModeResult(message="Invalid width/height/interval")

            x = self.viewport.cursor.x
            y = self.viewport.cursor.y

            try:
                zone = self.zone_manager.create_watch(name, x, y, w, h, cmd, interval)
                # Start background refresh
                self.zone_executor.start_watch(zone)
                self.project.mark_dirty()
                return ModeResult(message=f"Created watch zone '{name}' (refresh: {interval}s)")
            except ValueError as e:
                return ModeResult(message=str(e))

        # :zone refresh NAME
        elif subcmd == "refresh":
            if len(args) < 2:
                return ModeResult(message="Usage: zone refresh NAME")
            if self.zone_executor.refresh_zone(args[1]):
                zone = self.zone_manager.get(args[1])
                return ModeResult(message=f"Refreshed '{args[1]}' - {len(zone.content_lines)} lines")
            return ModeResult(message=f"Zone '{args[1]}' not found or not refreshable")

        # :zone pause NAME
        elif subcmd == "pause":
            if len(args) < 2:
                return ModeResult(message="Usage: zone pause NAME")
            if self.zone_executor.pause_zone(args[1]):
                return ModeResult(message=f"Paused zone '{args[1]}'")
            return ModeResult(message=f"Zone '{args[1]}' not found or not a watch zone")

        # :zone resume NAME
        elif subcmd == "resume":
            if len(args) < 2:
                return ModeResult(message="Usage: zone resume NAME")
            if self.zone_executor.resume_zone(args[1]):
                return ModeResult(message=f"Resumed zone '{args[1]}'")
            return ModeResult(message=f"Zone '{args[1]}' not found or not a watch zone")

        # :zone pty NAME W H [SHELL]
        elif subcmd == "pty":
            if not PTY_AVAILABLE:
                return ModeResult(message="PTY not available on this platform (requires Unix)")

            if len(args) < 4:
                return ModeResult(message="Usage: zone pty NAME W H [SHELL]")
            name = args[1]
            try:
                w, h = int(args[2]), int(args[3])
                shell = args[4] if len(args) > 4 else "/bin/bash"
            except (ValueError, IndexError):
                return ModeResult(message="Invalid width/height")

            x = self.viewport.cursor.x
            y = self.viewport.cursor.y

            try:
                zone = self.zone_manager.create_pty(name, x, y, w, h, shell=shell)
                # Start PTY session
                if self.pty_handler.create_pty(zone):
                    self.project.mark_dirty()
                    return ModeResult(message=f"Created PTY zone '{name}' - press Enter to focus")
                else:
                    self.zone_manager.delete(name)
                    return ModeResult(message=f"Failed to create PTY for zone '{name}'")
            except ValueError as e:
                return ModeResult(message=str(e))

        # :zone send NAME TEXT
        elif subcmd == "send":
            if len(args) < 3:
                return ModeResult(message="Usage: zone send NAME TEXT")
            name = args[1]
            text = " ".join(args[2:])
            # Handle escape sequences
            text = text.replace("\\n", "\n").replace("\\t", "\t")

            if self.pty_handler.send_input(name, text):
                return ModeResult(message=f"Sent to '{name}'")
            return ModeResult(message=f"Zone '{name}' not found or not an active PTY")

        # :zone focus NAME
        elif subcmd == "focus":
            if len(args) < 2:
                return ModeResult(message="Usage: zone focus NAME")
            name = args[1]
            zone = self.zone_manager.get(name)
            if not zone:
                return ModeResult(message=f"Zone '{name}' not found")
            if zone.zone_type != ZoneType.PTY:
                return ModeResult(message=f"Zone '{name}' is not a PTY zone")
            if not self.pty_handler.is_active(name):
                return ModeResult(message=f"PTY for zone '{name}' is not active")
            self._focused_pty = name
            return ModeResult(message=f"PTY focused: {name}")

        else:
            return ModeResult(
                message="Usage: zone create|delete|goto|pipe|watch|pty|send|focus|..."
            )

    def _cmd_zones(self, args: list[str]) -> ModeResult:
        """List all zones."""
        zones = self.zone_manager.list_all()
        if not zones:
            return ModeResult(message="No zones defined")

        # Build zone list
        lines = []
        for z in zones:
            info = f"  {z.name}: ({z.x},{z.y}) {z.width}x{z.height}"
            if z.bookmark:
                info += f" [{z.bookmark}]"
            lines.append(info)

        return ModeResult(message=f"{len(zones)} zones: " + ", ".join(z.name for z in zones))

    def _cmd_box(self, args: list[str]) -> ModeResult:
        """
        Draw a box using the external 'boxes' tool.

        Usage:
            :box list              - List available box styles
            :box STYLE TEXT...     - Draw box with style around text
            :box TEXT...           - Draw box with default style (ansi)
        """
        if not args:
            return ModeResult(message="Usage: box [list | STYLE] TEXT...")

        # Check if boxes is available
        if not tool_available("boxes"):
            return ModeResult(message="Error: 'boxes' command not found")

        # List styles
        if args[0].lower() == "list":
            styles = get_boxes_styles()
            if not styles:
                return ModeResult(message="No box styles found")
            # Show first 20 styles
            preview = styles[:20]
            more = f" (+{len(styles) - 20} more)" if len(styles) > 20 else ""
            return ModeResult(message=f"Styles: {', '.join(preview)}{more}")

        # Determine style and content
        styles = get_boxes_styles()
        if args[0].lower() in [s.lower() for s in styles]:
            style = args[0]
            content = " ".join(args[1:]) if len(args) > 1 else ""
        else:
            style = "ansi"
            content = " ".join(args)

        if not content:
            return ModeResult(message="Usage: box [STYLE] TEXT...")

        # Generate box
        result = draw_box(content, style)
        if not result.success:
            return ModeResult(message=f"Box error: {result.error}")

        # Write to canvas at cursor position
        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
        width, height = write_lines_to_canvas(self.canvas, result.lines, cx, cy)
        self.project.mark_dirty()

        return ModeResult(message=f"Drew {width}x{height} box ({style})")

    def _cmd_figlet(self, args: list[str]) -> ModeResult:
        """
        Generate ASCII art text using figlet.

        Usage:
            :figlet list           - List available fonts
            :figlet TEXT           - Draw with default font (standard)
            :figlet -f FONT TEXT   - Draw with specific font
        """
        if not args:
            return ModeResult(message="Usage: figlet [-f FONT] TEXT...")

        # Check if figlet is available
        if not tool_available("figlet"):
            return ModeResult(message="Error: 'figlet' command not found")

        # List fonts
        if args[0].lower() == "list":
            fonts = get_figlet_fonts()
            if not fonts:
                return ModeResult(message="No figlet fonts found")
            return ModeResult(message=f"Fonts: {', '.join(fonts)}")

        # Parse font option
        font = "standard"
        text_start = 0
        if args[0] == "-f" and len(args) > 2:
            font = args[1]
            text_start = 2

        text = " ".join(args[text_start:])
        if not text:
            return ModeResult(message="Usage: figlet [-f FONT] TEXT...")

        # Generate figlet
        result = draw_figlet(text, font)
        if not result.success:
            return ModeResult(message=f"Figlet error: {result.error}")

        # Write to canvas at cursor position
        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
        width, height = write_lines_to_canvas(self.canvas, result.lines, cx, cy)
        self.project.mark_dirty()

        return ModeResult(message=f"Drew {width}x{height} figlet ({font})")

    def _cmd_pipe(self, args: list[str]) -> ModeResult:
        """
        Execute a shell command and write output to canvas.

        Usage:
            :pipe COMMAND          - Execute command, write stdout at cursor
        """
        if not args:
            return ModeResult(message="Usage: pipe COMMAND...")

        command = " ".join(args)

        # Execute command
        result = pipe_command(command, timeout=10)

        if not result.lines:
            if result.error:
                return ModeResult(message=f"Pipe error: {result.error}")
            return ModeResult(message="Command produced no output")

        # Write to canvas at cursor position
        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
        width, height = write_lines_to_canvas(self.canvas, result.lines, cx, cy)
        self.project.mark_dirty()

        status = "OK" if result.success else f"Exit: {result.error}"
        return ModeResult(message=f"Piped {height} lines ({status})")

    def _cmd_tools(self, args: list[str]) -> ModeResult:
        """Show status of external tools."""
        status = get_tool_status()
        parts = [f"{name}: {'OK' if available else 'NOT FOUND'}"
                 for name, available in status.items()]
        return ModeResult(message="Tools: " + ", ".join(parts))

    def _cmd_layout(self, args: list[str]) -> ModeResult:
        """
        Layout management command.

        Usage:
            :layout list              - List available layouts
            :layout load NAME         - Load a layout
            :layout save NAME [DESC]  - Save current zones as layout
            :layout delete NAME       - Delete a layout
            :layout info NAME         - Show layout details
        """
        if not args:
            return ModeResult(message="Usage: layout list|load|save|delete|info ...")

        subcmd = args[0].lower()

        # :layout list
        if subcmd == "list":
            layouts = self.layout_manager.list_layouts()
            if not layouts:
                return ModeResult(message="No layouts found. Use ':layout save NAME' to create one.")
            # Show names with descriptions
            parts = []
            for name, desc in layouts:
                if desc:
                    parts.append(f"{name} ({desc[:20]})")
                else:
                    parts.append(name)
            return ModeResult(message=f"Layouts: {', '.join(parts)}")

        # :layout load NAME [--clear]
        elif subcmd == "load":
            if len(args) < 2:
                return ModeResult(message="Usage: layout load NAME [--clear]")
            name = args[1]
            clear_existing = "--clear" in args

            layout = self.layout_manager.load(name)
            if not layout:
                return ModeResult(message=f"Layout '{name}' not found")

            created, errors = self.layout_manager.apply_layout(
                layout,
                self.zone_manager,
                self.zone_executor,
                pty_handler=self.pty_handler,
                clear_existing=clear_existing,
            )

            # Apply cursor/viewport if specified
            if layout.cursor_x is not None:
                self.viewport.cursor.set(layout.cursor_x, layout.cursor_y or 0)
            if layout.viewport_x is not None:
                self.viewport.pan_to(layout.viewport_x, layout.viewport_y or 0)

            self.project.mark_dirty()

            msg = f"Loaded layout '{name}': {created} zones created"
            if errors:
                msg += f" ({len(errors)} errors)"
            return ModeResult(message=msg)

        # :layout save NAME [DESCRIPTION]
        elif subcmd == "save":
            if len(args) < 2:
                return ModeResult(message="Usage: layout save NAME [DESCRIPTION]")
            name = args[1]
            description = " ".join(args[2:]) if len(args) > 2 else ""

            if len(self.zone_manager) == 0:
                return ModeResult(message="No zones to save. Create zones first.")

            cursor = (self.viewport.cursor.x, self.viewport.cursor.y)
            viewport = (self.viewport.x, self.viewport.y)

            path = self.layout_manager.save_from_zones(
                name, description, self.zone_manager,
                cursor=cursor, viewport=viewport
            )
            return ModeResult(message=f"Saved layout '{name}' ({len(self.zone_manager)} zones)")

        # :layout delete NAME
        elif subcmd == "delete":
            if len(args) < 2:
                return ModeResult(message="Usage: layout delete NAME")
            name = args[1]
            if self.layout_manager.delete(name):
                return ModeResult(message=f"Deleted layout '{name}'")
            return ModeResult(message=f"Layout '{name}' not found")

        # :layout info NAME
        elif subcmd == "info":
            if len(args) < 2:
                return ModeResult(message="Usage: layout info NAME")
            name = args[1]
            layout = self.layout_manager.load(name)
            if not layout:
                return ModeResult(message=f"Layout '{name}' not found")

            zone_types = {}
            for z in layout.zones:
                zone_types[z.zone_type] = zone_types.get(z.zone_type, 0) + 1

            type_info = ", ".join(f"{k}:{v}" for k, v in zone_types.items())
            return ModeResult(
                message=f"Layout '{name}': {len(layout.zones)} zones ({type_info}) - {layout.description}"
            )

        else:
            return ModeResult(message="Usage: layout list|load|save|delete|info ...")


def main(stdscr: "curses.window", args: argparse.Namespace) -> None:
    """Main entry point called by curses wrapper."""
    # Build server config if enabled
    server_config = None
    if args.server:
        server_config = ServerConfig(
            tcp_enabled=not args.no_tcp,
            tcp_port=args.port,
            fifo_enabled=not args.no_fifo,
            fifo_path=args.fifo or "/tmp/mygrid.fifo"
        )

    app = Application(stdscr, server_config=server_config)

    # Load file if specified
    if args.file:
        app.load_file(args.file)

    app.run()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="my-grid - ASCII Canvas Editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    Start with empty canvas
  %(prog)s project.json       Open existing project
  %(prog)s drawing.txt        Import text file
  %(prog)s --server           Start with API server enabled
  %(prog)s --server --port 9000  Use custom port

Keys:
  wasd/arrows  Move cursor      i  Enter edit mode
  p            Toggle pan mode  :  Enter command mode
  g/G          Toggle grid      q  Quit
  Ctrl+S       Save             F1 Help

API Server:
  When --server is enabled, external processes can send commands
  via TCP (default port 8765) or FIFO (/tmp/mygrid.fifo on Unix).
  Use mygrid-ctl to send commands from another terminal.
"""
    )
    parser.add_argument(
        'file',
        nargs='?',
        help='Project file (.json) or text file to open'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.2.0'
    )

    # Server options
    server_group = parser.add_argument_group('API Server')
    server_group.add_argument(
        '--server',
        action='store_true',
        help='Enable API server for external commands'
    )
    server_group.add_argument(
        '--port',
        type=int,
        default=8765,
        help='TCP port for API server (default: 8765)'
    )
    server_group.add_argument(
        '--no-tcp',
        action='store_true',
        help='Disable TCP listener'
    )
    server_group.add_argument(
        '--fifo',
        metavar='PATH',
        help='FIFO path for Unix (default: /tmp/mygrid.fifo)'
    )
    server_group.add_argument(
        '--no-fifo',
        action='store_true',
        help='Disable FIFO listener'
    )
    server_group.add_argument(
        '--headless',
        action='store_true',
        help='Run API server without curses UI (for background/daemon use)'
    )

    return parser.parse_args()


def main_headless(args: argparse.Namespace) -> None:
    """Run headless API server (no curses UI)."""
    import signal
    import time

    # Build server config
    server_config = ServerConfig(
        tcp_enabled=not args.no_tcp,
        tcp_port=args.port,
        fifo_enabled=not args.no_fifo,
        fifo_path=args.fifo or "/tmp/mygrid.fifo"
    )

    # Create minimal components for headless operation
    canvas = Canvas()
    viewport = Viewport()
    viewport.resize(80, 24)  # Default size for headless

    command_queue = CommandQueue()
    api_server = APIServer(command_queue)
    api_server.start(server_config)

    print(f"my-grid headless server running on port {server_config.tcp_port}")
    print("Press Ctrl+C to stop...")

    # Handle shutdown signals
    running = True
    def signal_handler(sig, frame):
        nonlocal running
        running = False
        print("\nShutting down...")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Main loop - process commands
    mode_config = ModeConfig()
    state_machine = ModeStateMachine(canvas, viewport, mode_config)

    from command_queue import CommandResponse

    while running:
        # Process queued commands (get_nowait returns None if empty)
        cmd = command_queue.get_nowait()
        while cmd is not None:
            result = state_machine._execute_command(cmd.command)
            # Log command results in headless mode
            if result.message:
                logger.info(f"Command result: {result.message}")
            # Send response if requested (must be CommandResponse object)
            if cmd.response_queue:
                response = CommandResponse(
                    status="ok" if not result.message or "error" not in result.message.lower() else "error",
                    message=result.message or "OK"
                )
                cmd.response_queue.put(response)
            cmd = command_queue.get_nowait()

        time.sleep(0.01)  # Small sleep to prevent CPU spin

    # Cleanup
    api_server.stop()
    print("Server stopped.")


if __name__ == "__main__":
    args = parse_args()
    if args.headless:
        if not args.server:
            print("Error: --headless requires --server")
            sys.exit(1)
        main_headless(args)
    else:
        curses.wrapper(lambda stdscr: main(stdscr, args))
