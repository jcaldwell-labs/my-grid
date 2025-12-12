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
from renderer import Renderer, GridSettings, create_status_line
from input import InputHandler, Action, InputEvent
from modes import Mode, ModeConfig, ModeStateMachine, ModeResult
from project import Project, add_recent_project, suggest_filename
from command_queue import CommandQueue, CommandResponse, send_response
from server import APIServer, ServerConfig

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

        # API server components
        self.command_queue = CommandQueue()
        self.api_server: APIServer | None = None
        self._server_config = server_config

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
                    bookmarks=self.state_machine.bookmarks
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
        origin = self.viewport.origin

        # Mode indicator with visual distinction
        mode_indicators = {
            "NAV": "NAV",
            "PAN": "PAN",
            "EDIT": "EDT",
            "COMMAND": "CMD",
        }
        mode_str = mode_indicators.get(mode, mode)

        # File status: name with modified indicator
        file_status = self.project.display_name
        if self.project.dirty:
            file_status = f"[+] {self.project.filename}"
        else:
            file_status = f"    {self.project.filename}"

        # Cursor position - prominent display
        pos_str = f"X:{cursor.x:>5} Y:{cursor.y:>5}"

        # Cell at cursor
        cell_char = self.canvas.get_char(cursor.x, cursor.y)
        if cell_char == ' ':
            cell_str = "·"
        else:
            cell_str = f"'{cell_char}'"

        # Build the line with clear sections
        # Format: MODE | X:    0 Y:    0 | 'char' | [+] filename | cells
        parts = [
            f" {mode_str}",
            f"{pos_str}",
            f"{cell_str:>3}",
            file_status,
        ]

        # Add cell count
        if self.canvas.cell_count > 0:
            parts.append(f"{self.canvas.cell_count} cells")

        return " │ ".join(parts)

    def run(self) -> None:
        """Main application loop."""
        running = True

        # Enable non-blocking input if server is running
        if self._server_config:
            self.stdscr.timeout(50)  # 50ms timeout = ~20 FPS

        try:
            while running:
                # Process external commands from API server
                if self._server_config:
                    self._process_external_commands()

                # Handle terminal resize
                self._update_viewport_size()

                # Render frame
                status = self._get_status_line()
                self.renderer.render(self.canvas, self.viewport, status)

                # Get input (may timeout if server mode)
                key = self.renderer.get_input()

                # Handle timeout (no input) - just continue loop
                if key == -1:
                    continue

                # Handle resize event
                if key == curses.KEY_RESIZE:
                    continue

                # Convert curses key to action
                event = self._curses_key_to_event(key)
                if not event:
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
            # In edit/command mode, some keys type instead of action
            if self.state_machine.mode in (Mode.EDIT, Mode.COMMAND):
                if action in (Action.MOVE_UP, Action.MOVE_DOWN,
                             Action.MOVE_LEFT, Action.MOVE_RIGHT):
                    # Arrow keys still navigate
                    if key in (curses.KEY_UP, curses.KEY_DOWN,
                              curses.KEY_LEFT, curses.KEY_RIGHT):
                        return InputEvent(action=action)
                    # WASD types in edit mode
                    if self.state_machine.mode == Mode.EDIT:
                        return InputEvent(char=chr(key))
                    # WASD navigates command buffer
                    return InputEvent(action=action)
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
                    bookmarks=self.state_machine.bookmarks
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
        self.project = Project()
        self._show_message("New canvas created")

    def _show_help(self) -> None:
        """Show help screen."""
        help_text = """
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

  KEYS:
    g / G         - Toggle major/minor grid
    0             - Toggle origin marker
    Ctrl+S        - Save               Esc           - Exit mode
    F1            - This help          q             - Quit

  Press any key to continue...
"""
        self.stdscr.clear()
        for i, line in enumerate(help_text.strip().split('\n')):
            try:
                self.stdscr.addstr(i, 0, line)
            except curses.error:
                pass
        self.stdscr.refresh()
        self.renderer.get_input()

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
        """Configure grid: grid major|minor|N"""
        if not args:
            return ModeResult(
                message=f"Grid: major={self.renderer.grid.major_interval} "
                       f"minor={self.renderer.grid.minor_interval}"
            )
        arg = args[0].lower()
        if arg == "major":
            self.renderer.grid.show_major_lines = not self.renderer.grid.show_major_lines
            return ModeResult(message=f"Major grid: {'ON' if self.renderer.grid.show_major_lines else 'OFF'}")
        elif arg == "minor":
            self.renderer.grid.show_minor_lines = not self.renderer.grid.show_minor_lines
            return ModeResult(message=f"Minor grid: {'ON' if self.renderer.grid.show_minor_lines else 'OFF'}")
        else:
            try:
                interval = int(arg)
                self.renderer.grid.major_interval = interval
                return ModeResult(message=f"Major interval: {interval}")
            except ValueError:
                return ModeResult(message="Usage: grid major|minor|N")

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

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    curses.wrapper(lambda stdscr: main(stdscr, args))
