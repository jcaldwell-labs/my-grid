#!/usr/bin/env python3
"""
my-grid - ASCII Canvas Editor

Main entry point that wires together all components.
"""

import argparse
import curses
import json
import logging
import os
import sys
from pathlib import Path

from canvas import Canvas, parse_color, COLOR_NUMBERS
from viewport import Viewport
from undo import UndoManager
from renderer import Renderer, GridLineMode
from input import InputHandler, Action, InputEvent
from modes import Mode, ModeConfig, ModeStateMachine, ModeResult
from project import Project, add_recent_project, suggest_filename, SessionManager
from command_queue import CommandQueue, CommandResponse, send_response
from server import APIServer, ServerConfig
from zones import (
    ZoneManager,
    ZoneExecutor,
    ZoneType,
    ZoneConfig,
    PTYHandler,
    PTY_AVAILABLE,
    Clipboard,
    FIFOHandler,
    SocketHandler,
    get_border_style,
    set_border_style,
    list_border_styles,
    load_pager_content,
    get_available_renderers,
    strip_ansi,
)
from layouts import LayoutManager, install_default_layouts
from external import (
    tool_available,
    get_tool_status,
    draw_box,
    get_boxes_styles,
    draw_figlet,
    get_figlet_fonts,
    pipe_command,
    write_lines_to_canvas,
)
from joystick import JoystickHandler

logger = logging.getLogger(__name__)


class Application:
    """
    Main application class.

    Coordinates all components and runs the main loop.
    """

    def __init__(
        self, stdscr: "curses.window", server_config: ServerConfig | None = None
    ):
        self.stdscr = stdscr

        # Core components
        self.canvas = Canvas()
        self.viewport = Viewport()
        self.renderer = Renderer(stdscr)
        self.input_handler = InputHandler()
        self.mode_config = ModeConfig()
        self.undo_manager = UndoManager(max_history=100)
        self.state_machine = ModeStateMachine(
            self.canvas, self.viewport, self.mode_config, undo_manager=self.undo_manager
        )
        self.project = Project()
        self.zone_manager = ZoneManager()
        self.zone_executor = ZoneExecutor(self.zone_manager)
        self.pty_handler = PTYHandler(self.zone_manager)
        self.layout_manager = LayoutManager()
        self.clipboard = Clipboard()
        self.fifo_handler = FIFOHandler(self.zone_manager)
        self.socket_handler = SocketHandler(self.zone_manager)
        self.session_manager = SessionManager()

        # Install default layouts on first run
        install_default_layouts()

        # PTY focus tracking
        self._focused_pty: str | None = None  # Name of focused PTY zone

        # Pager focus tracking
        self._focused_pager: str | None = None  # Name of focused PAGER zone

        # Mouse drag tracking for visual selection
        self._mouse_drag_start: tuple[int, int] | None = None  # (canvas_x, canvas_y)

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
        self.state_machine.register_command(
            "w", self._cmd_write
        )  # vim-style :w [filename]
        self.state_machine.register_command("write", self._cmd_write)
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
        self.state_machine.register_command("yank", self._cmd_yank)
        self.state_machine.register_command("y", self._cmd_yank)
        self.state_machine.register_command("paste", self._cmd_paste)
        self.state_machine.register_command("p", self._cmd_paste)
        self.state_machine.register_command("clipboard", self._cmd_clipboard)
        self.state_machine.register_command("border", self._cmd_border)
        self.state_machine.register_command("borders", self._cmd_border)
        self.state_machine.register_command("session", self._cmd_session)
        self.state_machine.register_command("fill", self._cmd_fill)
        self.state_machine.register_command("color", self._cmd_color)
        self.state_machine.register_command("palette", self._cmd_palette)
        self.state_machine.register_command("draw", self._cmd_draw)
        self.state_machine.register_command("shader", self._cmd_shader)
        self.state_machine.register_command("undo", self._cmd_undo)
        self.state_machine.register_command("redo", self._cmd_redo)
        self.state_machine.register_command("history", self._cmd_history)
        self.state_machine.register_command("search", self._cmd_search)

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
            if filepath.suffix.lower() == ".json":
                self.project = Project.load(
                    filepath,
                    self.canvas,
                    self.viewport,
                    grid_settings=self.renderer.grid,
                    bookmarks=self.state_machine.bookmarks,
                    zones=self.zone_manager,
                )
                add_recent_project(filepath)
                # Initialize PAGER zones with content
                self._init_pager_zones()
                self._show_message(f"Loaded: {filepath.name}")
            else:
                # Treat as text file
                self.project = Project.import_text(filepath, self.canvas, self.viewport)
                self._show_message(f"Imported: {filepath.name}")
        except Exception as e:
            self._show_message(f"Error loading: {e}")

    def load_layout_by_name(self, name: str) -> None:
        """Load a layout by name on startup."""
        layout = self.layout_manager.load(name)
        if not layout:
            self._show_message(f"Layout '{name}' not found")
            return

        created, errors = self.layout_manager.apply_layout(
            layout,
            self.zone_manager,
            self.zone_executor,
            pty_handler=self.pty_handler,
            fifo_handler=self.fifo_handler,
            socket_handler=self.socket_handler,
            clear_existing=False,
        )

        # Register zone bookmarks
        self._register_zone_bookmarks()

        # Apply cursor/viewport if specified
        if layout.cursor_x is not None:
            self.viewport.cursor.set(layout.cursor_x, layout.cursor_y or 0)
        if layout.viewport_x is not None:
            self.viewport.pan_to(layout.viewport_x, layout.viewport_y or 0)

        msg = f"Loaded layout '{name}': {created} zones"
        if errors:
            msg += f" ({len(errors)} errors)"
        self._show_message(msg, frames=60)  # Show longer on startup

    def _register_zone_bookmarks(self) -> None:
        """Register bookmarks for all zones that have them."""
        for zone in self.zone_manager.list_all():
            if zone.bookmark:
                # Calculate zone center point
                center_x = zone.x + (zone.width // 2)
                center_y = zone.y + (zone.height // 2)
                self.state_machine.bookmarks.set(
                    zone.bookmark, center_x, center_y, zone.name
                )

    def _init_pager_zones(self) -> None:
        """Initialize PAGER zones by loading their content."""
        for zone in self.zone_manager.list_all():
            if zone.zone_type == ZoneType.PAGER and zone.config.file_path:
                load_pager_content(zone, use_wsl=False)

    def _show_message(self, message: str, frames: int = 2) -> None:
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
            zone = self.zone_manager.get(self._focused_pty)
            if zone and zone.zone_type == ZoneType.PTY:
                if zone.config.pty_auto_scroll:
                    return f" [PTY] {self._focused_pty} - Shift+PgUp:scroll Esc:unfocus"
                else:
                    # In scroll mode
                    total = len(zone._content_lines)
                    line = zone.config.pty_scroll_offset + 1
                    return f" [PTY SCROLL] {self._focused_pty} - {line}/{total} - Shift+End:auto Esc:unfocus"
            return f" [PTY] {self._focused_pty} - Esc:unfocus"

        # Show PAGER focus mode indicator
        if self._focused_pager:
            zone = self.zone_manager.get(self._focused_pager)
            if zone and zone.zone_type == ZoneType.PAGER:
                line = zone.config.scroll_offset + 1
                total = zone.pager_line_count
                pct = (
                    int(
                        100
                        * zone.config.scroll_offset
                        / max(1, total - zone.pager_visible_lines)
                    )
                    if total > zone.pager_visible_lines
                    else 100
                )
                search_info = ""
                if zone.config.search_term and zone.config.search_matches:
                    idx = zone.config.search_index + 1
                    cnt = len(zone.config.search_matches)
                    search_info = f' "{zone.config.search_term}" {idx}/{cnt}'
                return f" [PAGER] {self._focused_pager} - Line {line}/{total} ({pct}%){search_info} - j/k:scroll g/G:top/bottom n/N:match q:exit"

        # Show command buffer in command mode
        if self.state_machine.mode == Mode.COMMAND:
            buf = self.state_machine.command_buffer
            return f":{buf.text}_"

        # Show search buffer in search mode
        if self.state_machine.mode == Mode.SEARCH:
            buf = self.state_machine.command_buffer
            return f"/{buf.text}_"

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
            "VISUAL": "VIS",
            "DRAW": "DRW",
            "SEARCH": "SRH",
        }
        mode_str = mode_indicators.get(mode, mode)

        # In DRAW mode, show pen state
        if mode == "DRAW":
            pen_state = "v" if self.state_machine._draw_pen_down else "^"
            mode_str = f"DRW{pen_state}"

        # Cursor position - prominent display
        pos_str = f"X:{cursor.x:>5} Y:{cursor.y:>5}"

        # Cell at cursor
        cell_char = self.canvas.get_char(cursor.x, cursor.y)
        if cell_char == " ":
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
                # Reset frame guards
                self.state_machine.reset_pen_toggle_guard()

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

                # Auto-save session if interval elapsed
                if self.project.dirty:
                    self.session_manager.auto_save(
                        self.canvas,
                        self.viewport,
                        grid_settings=self.renderer.grid,
                        bookmarks=self.state_machine.bookmarks,
                        zones=self.zone_manager,
                    )

                # Render frame
                status = self._get_status_line()
                self.renderer.render(
                    self.canvas,
                    self.viewport,
                    status,
                    selection=self.state_machine.selection,
                    search_state=self.state_machine.search_state,
                )

                # Get input (may timeout if server/joystick mode)
                key = self.renderer.get_input()

                # Handle timeout (no input) - just continue loop for joystick polling
                if key == -1:
                    continue

                # Handle resize event
                if key == curses.KEY_RESIZE:
                    continue

                # Handle mouse events
                if key == curses.KEY_MOUSE:
                    self._handle_mouse_event()
                    continue

                # If PTY is focused, forward input to PTY
                if self._focused_pty:
                    # DEBUG: Show key code for Enter debugging
                    if key == 10 or key == 13 or key == curses.KEY_ENTER:
                        self._show_message(
                            f"DEBUG: Enter key={key} (10=\\n, 13=\\r, {curses.KEY_ENTER}=KEY_ENTER)",
                            frames=180,
                        )

                    if key == 27:  # Escape - unfocus PTY
                        self._focused_pty = None
                        self._show_message("PTY unfocused")
                    elif self._handle_pty_scroll_keys(key):
                        # Scroll key handled (PgUp/PgDn)
                        continue
                    else:
                        # Forward key to PTY
                        self._forward_key_to_pty(key)
                    continue

                # If PAGER is focused, handle pager navigation
                if self._focused_pager:
                    if self._handle_pager_key(key):
                        continue

                # Convert curses key to action
                event = self._curses_key_to_event(key)
                if not event:
                    continue

                # Check if Enter pressed in a PTY or PAGER zone - focus it
                if event.action == Action.NEWLINE:
                    current_zone = self.zone_manager.find_at(
                        self.viewport.cursor.x, self.viewport.cursor.y
                    )
                    if current_zone and current_zone.zone_type == ZoneType.PTY:
                        if self.pty_handler.is_active(current_zone.name):
                            self._focused_pty = current_zone.name
                            self._show_message(f"PTY focused: {current_zone.name}")
                            continue
                    elif current_zone and current_zone.zone_type == ZoneType.PAGER:
                        self._focused_pager = current_zone.name
                        zone = self.zone_manager.get(current_zone.name)
                        line = zone.config.scroll_offset + 1
                        total = zone.pager_line_count
                        self._show_message(
                            f"PAGER focused: {current_zone.name} - Line {line}/{total}"
                        )
                        continue

                # Process through state machine
                result = self.state_machine.process(event)

                # Handle result
                if result.quit:
                    if self._confirm_quit():
                        running = False
                    continue

                if result.message:
                    self._show_message(result.message, frames=result.message_frames)

                if result.command:
                    self._handle_command(result.command)

                # Handle grid toggles (not mode-dependent)
                if event.action == Action.TOGGLE_GRID_MAJOR:
                    self.renderer.grid.show_major_lines = (
                        not self.renderer.grid.show_major_lines
                    )
                    self._show_message(
                        f"Major grid: {'ON' if self.renderer.grid.show_major_lines else 'OFF'}"
                    )
                elif event.action == Action.TOGGLE_GRID_MINOR:
                    self.renderer.grid.show_minor_lines = (
                        not self.renderer.grid.show_minor_lines
                    )
                    self._show_message(
                        f"Minor grid: {'ON' if self.renderer.grid.show_minor_lines else 'OFF'}"
                    )
                elif event.action == Action.TOGGLE_GRID_ORIGIN:
                    self.renderer.grid.show_origin = not self.renderer.grid.show_origin
                    self._show_message(
                        f"Origin marker: {'ON' if self.renderer.grid.show_origin else 'OFF'}"
                    )

                # Handle undo/redo
                if event.action == Action.UNDO:
                    self._do_undo()
                elif event.action == Action.REDO:
                    self._do_redo()

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
            # Clean up FIFO listeners
            self.fifo_handler.stop_all()
            # Clean up socket listeners
            self.socket_handler.stop_all()
            # Clear session file on clean exit (not crash)
            if not self.project.dirty:
                self.session_manager.clear_current_session()

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
                    data=result.data if hasattr(result, "data") else None,
                )
            except Exception as e:
                response = CommandResponse(status="error", message=str(e))

            # Send response back if requested
            send_response(ext_cmd, response)

    def _process_joystick_input(self) -> None:
        """Process joystick input for cursor movement."""
        from input import Action, InputEvent

        # Debug logging
        import logging

        _joy_log = logging.getLogger("joystick_debug")
        if not _joy_log.handlers:
            _joy_log.setLevel(logging.DEBUG)
            fh = logging.FileHandler("joystick_debug.log")
            fh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
            _joy_log.addHandler(fh)

        # Get movement from joystick (handles repeat timing internally)
        dx, dy = self.joystick.get_movement()

        if dx != 0 or dy != 0:
            # Move cursor based on current mode
            mode = self.state_machine.mode

            if mode == Mode.NAV or mode == Mode.EDIT:
                # Move cursor and ensure it stays visible (auto-pan)
                self.viewport.move_cursor(dx, dy)
                self.viewport.ensure_cursor_visible(
                    margin=self.mode_config.scroll_margin
                )
            elif mode == Mode.PAN:
                # Pan viewport (cursor follows)
                self.viewport.pan(dx, dy)
            elif mode == Mode.DRAW:
                # In DRAW mode, create movement event to trigger line drawing
                if dx > 0:
                    action = Action.MOVE_RIGHT
                elif dx < 0:
                    action = Action.MOVE_LEFT
                elif dy > 0:
                    action = Action.MOVE_DOWN
                else:
                    action = Action.MOVE_UP
                # Process through state machine to draw lines
                self.state_machine.process(InputEvent(action=action))

        # Check for button presses
        buttons = self.joystick.get_button_presses()
        mode = self.state_machine.mode

        # Debug: log button presses and pen state
        if buttons:
            _joy_log.debug(
                f"Buttons pressed: {buttons}, mode={mode.name}, pen_down_before={self.state_machine._draw_pen_down}"
            )

        for btn in buttons:
            if btn == 0:  # A button - confirm/select
                if mode == Mode.NAV:
                    # In NAV mode, enter edit mode
                    self.state_machine.set_mode(Mode.EDIT)
                    self._show_message("-- EDIT --", frames=30)
                elif mode == Mode.DRAW:
                    # In DRAW mode, toggle pen up/down (with frame guard)
                    if self.state_machine._pen_toggled_this_frame:
                        _joy_log.debug(
                            "BTN0 in DRAW: BLOCKED by frame guard (already toggled)"
                        )
                        continue  # Skip this button, already toggled this frame
                    before = self.state_machine._draw_pen_down
                    _joy_log.debug(f"BTN0 in DRAW: pen_before={before}")
                    pen_down = self.state_machine.toggle_draw_pen()
                    after = self.state_machine._draw_pen_down
                    _joy_log.debug(
                        f"BTN0 in DRAW: pen_after={pen_down}, actual_state={after}"
                    )
                    # Verify the toggle actually happened
                    if before == after:
                        _joy_log.error(f"TOGGLE FAILED! before={before}, after={after}")
                    state = "DOWN (drawing)" if pen_down else "UP (moving)"
                    self._show_message(f"-- DRAW -- pen {state}", frames=60)
            elif btn == 1:  # B button - back/escape
                # Exit current mode back to NAV
                if mode != Mode.NAV:
                    self.state_machine.set_mode(Mode.NAV)
                    self._show_message("")
            elif btn == 2:  # X button - cycle border styles
                from zones import list_border_styles, get_border_style, set_border_style

                styles = list_border_styles()
                current = get_border_style()
                try:
                    idx = styles.index(current)
                    next_idx = (idx + 1) % len(styles)
                except ValueError:
                    next_idx = 0
                new_style = styles[next_idx]
                set_border_style(new_style)
                self._show_message(f"Border: {new_style}", frames=60)

    def _forward_key_to_pty(self, key: int) -> None:
        """Forward a key press to the focused PTY."""
        if not self._focused_pty:
            return

        # Convert curses key codes to terminal sequences
        if key == curses.KEY_UP:
            data = "\x1b[A"
        elif key == curses.KEY_DOWN:
            data = "\x1b[B"
        elif key == curses.KEY_RIGHT:
            data = "\x1b[C"
        elif key == curses.KEY_LEFT:
            data = "\x1b[D"
        elif key == curses.KEY_BACKSPACE or key == 127:
            data = "\x7f"
        elif key == curses.KEY_DC:  # Delete
            data = "\x1b[3~"
        elif key == curses.KEY_HOME:
            data = "\x1b[H"
        elif key == curses.KEY_END:
            data = "\x1b[F"
        elif key == curses.KEY_PPAGE:  # Page Up
            data = "\x1b[5~"
        elif key == curses.KEY_NPAGE:  # Page Down
            data = "\x1b[6~"
        elif key == 10 or key == 13:  # Enter
            data = "\r"  # Use carriage return instead of newline for PTY
            self._show_message("DEBUG: Sending Enter (\\r) to PTY", frames=120)
        elif key == 9:  # Tab
            data = "\t"
        elif 1 <= key <= 26:  # Ctrl+A through Ctrl+Z
            data = chr(key)
        elif 32 <= key <= 126:  # Printable ASCII
            data = chr(key)
        else:
            return  # Unknown key, don't forward

        success = self.pty_handler.send_input(self._focused_pty, data)
        if key == 10 or key == 13:  # Debug Enter specifically
            self._show_message(f"DEBUG: send_input returned {success}", frames=120)

    def _handle_mouse_event(self) -> None:
        """
        Handle mouse events (clicks, drags, scroll wheel).

        Converts screen coordinates to canvas coordinates and performs
        the appropriate action:
        - Left click: Move cursor to position
        - Left drag: Enter visual selection mode
        - Scroll up/down: Pan viewport
        """
        from modes import Selection

        mouse = self.renderer.get_mouse()
        if not mouse:
            return

        _id, screen_x, screen_y, _z, bstate = mouse

        # Get terminal size to check if click is in canvas area
        height, width = self.renderer.get_terminal_size()

        # Status line is at the bottom - don't handle clicks there
        if screen_y >= height - 1:
            return

        # Convert screen coordinates to canvas coordinates
        canvas_x = self.viewport.x + screen_x
        canvas_y = self.viewport.y + screen_y

        # Handle scroll wheel (panning)
        if bstate & curses.BUTTON4_PRESSED:  # Scroll up
            self.viewport.pan(0, -3)  # Pan up 3 cells
            return
        if bstate & getattr(curses, "BUTTON5_PRESSED", 0x200000):  # Scroll down
            self.viewport.pan(0, 3)  # Pan down 3 cells
            return

        # Handle left button release - end drag
        if bstate & curses.BUTTON1_RELEASED:
            if self._mouse_drag_start:
                self._mouse_drag_start = None
                # Selection stays active in VISUAL mode
            return

        # Handle left click/press
        if bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
            # Check if clicking inside a PTY zone - focus it
            zone = self.zone_manager.find_at(canvas_x, canvas_y)
            if zone and zone.zone_type == ZoneType.PTY:
                if self.pty_handler.is_active(zone.name):
                    self._focused_pty = zone.name
                    self._show_message(f"PTY focused: {zone.name}")
                    return

            # Start drag tracking for potential visual selection
            if bstate & curses.BUTTON1_PRESSED:
                self._mouse_drag_start = (canvas_x, canvas_y)

            # Move cursor to clicked position
            self.viewport.cursor.x = canvas_x
            self.viewport.cursor.y = canvas_y

            # If already in visual mode, update selection endpoint
            if self.state_machine.mode == Mode.VISUAL and self.state_machine.selection:
                self.state_machine.selection.update_cursor(canvas_x, canvas_y)
            return

        # Handle mouse motion (drag) - reported if REPORT_MOUSE_POSITION is enabled
        # Check for motion during a drag
        if self._mouse_drag_start:
            start_x, start_y = self._mouse_drag_start

            # Only enter visual mode if we've moved from the start position
            if (canvas_x, canvas_y) != (start_x, start_y):
                # Enter visual mode if not already
                if self.state_machine.mode != Mode.VISUAL:
                    # Create selection anchored at drag start
                    self.state_machine.selection = Selection(
                        anchor_x=start_x,
                        anchor_y=start_y,
                        cursor_x=canvas_x,
                        cursor_y=canvas_y,
                    )
                    self.state_machine.set_mode(Mode.VISUAL)
                    self._show_message("-- VISUAL (drag) --")
                else:
                    # Update selection endpoint
                    self.state_machine.selection.update_cursor(canvas_x, canvas_y)

                # Move cursor to current drag position
                self.viewport.cursor.x = canvas_x
                self.viewport.cursor.y = canvas_y

    def _handle_pty_scroll_keys(self, key: int) -> bool:
        """
        Handle scroll keys when a PTY zone is focused.

        Uses Shift+PgUp/PgDn for scrollback so raw PgUp/PgDn can be
        forwarded to the PTY application.

        Keys:
            Shift+PgUp: Scroll up half page (enters scroll mode)
            Shift+PgDn: Scroll down half page
            Shift+Home: Go to top of history
            Shift+End: Go to bottom (re-enables auto-scroll)

        Returns:
            True if key was a scroll key, False to forward to PTY
        """
        if not self._focused_pty:
            return False

        zone = self.zone_manager.get(self._focused_pty)
        if not zone or zone.zone_type != ZoneType.PTY:
            return False

        # Use Shift+PgUp/PgDn for scrollback (raw PgUp/PgDn go to PTY)
        # KEY_SPREVIOUS = Shift+PgUp, KEY_SNEXT = Shift+PgDn
        # KEY_SHOME = Shift+Home, KEY_SEND = Shift+End
        if key not in (
            curses.KEY_SPREVIOUS,  # Shift+PgUp
            curses.KEY_SNEXT,  # Shift+PgDn
            curses.KEY_SHOME,  # Shift+Home
            curses.KEY_SEND,  # Shift+End
        ):
            return False

        total_lines = len(zone._content_lines)
        content_h = zone.height - 2
        max_offset = max(0, total_lines - content_h)
        half_page = content_h // 2

        # Shift+PgUp: Scroll up half page (enters scroll mode)
        if key == curses.KEY_SPREVIOUS:
            zone.config.pty_auto_scroll = False
            zone.config.pty_scroll_offset = max(
                0, zone.config.pty_scroll_offset - half_page
            )
            line = zone.config.pty_scroll_offset + 1
            self._show_message(
                f"PTY scroll: line {line}/{total_lines} | Shift+End:auto"
            )
            return True

        # Shift+PgDn: Scroll down half page
        elif key == curses.KEY_SNEXT:
            zone.config.pty_auto_scroll = False
            zone.config.pty_scroll_offset = min(
                max_offset, zone.config.pty_scroll_offset + half_page
            )
            line = zone.config.pty_scroll_offset + 1
            self._show_message(
                f"PTY scroll: line {line}/{total_lines} | Shift+End:auto"
            )
            return True

        # Shift+Home: Go to top
        elif key == curses.KEY_SHOME:
            zone.config.pty_auto_scroll = False
            zone.config.pty_scroll_offset = 0
            self._show_message("PTY scroll: top | Shift+End:auto")
            return True

        # Shift+End: Go to bottom (re-enable auto-scroll)
        elif key == curses.KEY_SEND:
            zone.config.pty_auto_scroll = True
            zone.config.pty_scroll_offset = 0
            self._show_message("PTY auto-scroll ON | Shift+PgUp:scroll")
            return True

        return False

    def _handle_pager_key(self, key: int) -> bool:
        """
        Handle key press when a PAGER zone is focused.

        Keys:
            j / DOWN: Scroll down one line
            k / UP: Scroll up one line
            d / PGDN: Scroll down half page
            u / PGUP: Scroll up half page
            g: Go to top
            G: Go to bottom
            n: Next search match
            N: Previous search match
            q / Esc: Unfocus

        Returns:
            True if key was handled, False otherwise
        """
        if not self._focused_pager:
            return False

        zone = self.zone_manager.get(self._focused_pager)
        if not zone or zone.zone_type != ZoneType.PAGER:
            self._focused_pager = None
            return False

        max_offset = max(0, zone.pager_line_count - zone.pager_visible_lines)
        half_page = zone.pager_visible_lines // 2

        handled = True

        # Escape or q: unfocus
        if key == 27 or key == ord("q"):
            self._focused_pager = None
            self._show_message("PAGER unfocused")

        # j or DOWN: scroll down one line
        elif key == ord("j") or key == curses.KEY_DOWN:
            if zone.config.scroll_offset < max_offset:
                zone.config.scroll_offset += 1

        # k or UP: scroll up one line
        elif key == ord("k") or key == curses.KEY_UP:
            if zone.config.scroll_offset > 0:
                zone.config.scroll_offset -= 1

        # d or PGDN: scroll down half page
        elif key == ord("d") or key == curses.KEY_NPAGE:
            zone.config.scroll_offset = min(
                max_offset, zone.config.scroll_offset + half_page
            )

        # u or PGUP: scroll up half page
        elif key == ord("u") or key == curses.KEY_PPAGE:
            zone.config.scroll_offset = max(0, zone.config.scroll_offset - half_page)

        # g: go to top
        elif key == ord("g"):
            zone.config.scroll_offset = 0

        # G: go to bottom
        elif key == ord("G"):
            zone.config.scroll_offset = max_offset

        # n: next search match
        elif key == ord("n"):
            if zone.config.search_matches:
                zone.config.search_index = (zone.config.search_index + 1) % len(
                    zone.config.search_matches
                )
                zone.config.scroll_offset = zone.config.search_matches[
                    zone.config.search_index
                ]
                self._show_message(
                    f"Match {zone.config.search_index + 1}/{len(zone.config.search_matches)}"
                )
            else:
                self._show_message("No search - use :zone search NAME TERM")

        # N: previous search match
        elif key == ord("N"):
            if zone.config.search_matches:
                zone.config.search_index = (zone.config.search_index - 1) % len(
                    zone.config.search_matches
                )
                zone.config.scroll_offset = zone.config.search_matches[
                    zone.config.search_index
                ]
                self._show_message(
                    f"Match {zone.config.search_index + 1}/{len(zone.config.search_matches)}"
                )
            else:
                self._show_message("No search - use :zone search NAME TERM")

        # /: unfocus and go to command mode for search
        elif key == ord("/"):
            self._focused_pager = None
            # Pre-fill command with search command
            self.state_machine._enter_command_mode()
            self.state_machine._command_buffer = f"zone search {zone.name} "
            self._show_message("Enter search term...")

        else:
            handled = False

        return handled

    def _execute_external_command(self, command: str) -> ModeResult:
        """Execute a command string from external source."""
        # Strip leading : or / if present
        if command.startswith(":") or command.startswith("/"):
            command = command[1:]

        # Parse command and args
        parts = command.split()
        if not parts:
            return ModeResult(message="Empty command")

        cmd_name = parts[0].lower()
        args = parts[1:]

        # Look up command handler
        handler = self.state_machine._command_handlers.get(cmd_name)
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
            ord("w"): Action.MOVE_UP,
            ord("s"): Action.MOVE_DOWN,
            ord("a"): Action.MOVE_LEFT,
            ord("d"): Action.MOVE_RIGHT,
            curses.KEY_UP: Action.MOVE_UP,
            curses.KEY_DOWN: Action.MOVE_DOWN,
            curses.KEY_LEFT: Action.MOVE_LEFT,
            curses.KEY_RIGHT: Action.MOVE_RIGHT,
            ord("W"): Action.MOVE_UP_FAST,
            ord("S"): Action.MOVE_DOWN_FAST,
            ord("A"): Action.MOVE_LEFT_FAST,
            ord("D"): Action.MOVE_RIGHT_FAST,
            ord("i"): Action.ENTER_EDIT_MODE,
            ord("p"): Action.TOGGLE_PAN_MODE,
            ord(":"): Action.ENTER_COMMAND_MODE,
            # Note: / handled as character in modes.py to enter SEARCH mode
            27: Action.EXIT_MODE,  # Escape
            ord("g"): Action.TOGGLE_GRID_MAJOR,
            ord("G"): Action.TOGGLE_GRID_MINOR,
            ord("0"): Action.TOGGLE_GRID_ORIGIN,
            ord("q"): Action.QUIT,
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

        # Special case: 'D' in NAV mode enters DRAW mode (not fast move)
        if key == ord("D") and self.state_machine.mode == Mode.NAV:
            return InputEvent(action=Action.ENTER_DRAW_MODE)

        # Check mapped actions
        if key in key_map:
            action = key_map[key]
            # In edit/command/search mode, letter keys type instead of triggering actions
            if self.state_machine.mode in (Mode.EDIT, Mode.COMMAND, Mode.SEARCH):
                # Allow arrow keys, function keys, and special keys
                if key in (
                    curses.KEY_UP,
                    curses.KEY_DOWN,
                    curses.KEY_LEFT,
                    curses.KEY_RIGHT,
                    curses.KEY_BACKSPACE,
                    curses.KEY_DC,
                    curses.KEY_F1,
                    27,
                    10,
                    13,
                    127,
                ):
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
            "Unsaved changes! Press 'q' again to quit, any other key to cancel.", row=-1
        )
        key = self.renderer.get_input()
        return key == ord("q")

    def _handle_command(self, command: str) -> None:
        """Handle special commands from mode result."""
        if command == "save":
            self._do_save()
        elif command == "help":
            self._show_help()
        elif command.startswith("yank_selection"):
            # yank_selection X Y W H
            parts = command.split()
            if len(parts) == 5:
                x, y, w, h = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                lines = self.clipboard.yank_region(
                    self.canvas, x, y, x + w - 1, y + h - 1
                )
                self._show_message(f"Yanked {w}x{h} region ({lines} lines)")
        elif command.startswith("delete_selection"):
            # delete_selection X Y W H
            parts = command.split()
            if len(parts) == 5:
                x, y, w, h = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                # Record undo state for all affected cells
                self.undo_manager.begin_operation("Delete Region")
                for cy in range(y, y + h):
                    for cx in range(x, x + w):
                        self.undo_manager.record_cell_before(self.canvas, cx, cy)
                # Clear the rectangular region
                for cy in range(y, y + h):
                    for cx in range(x, x + w):
                        self.canvas.clear(cx, cy)
                for cy in range(y, y + h):
                    for cx in range(x, x + w):
                        self.undo_manager.record_cell_after(self.canvas, cx, cy)
                self.undo_manager.end_operation()
                self.project.mark_dirty()
                self._show_message(f"Deleted {w}x{h} region")
        elif command == "undo":
            self._do_undo()
        elif command == "redo":
            self._do_redo()
        elif command.startswith("search "):
            # search PATTERN
            pattern = command[7:]  # Remove "search " prefix
            self._do_search(pattern)

    def _do_save(self) -> None:
        """Save the current project."""
        if self.project.filepath:
            try:
                self.project.save(
                    self.canvas,
                    self.viewport,
                    grid_settings=self.renderer.grid,
                    bookmarks=self.state_machine.bookmarks,
                    zones=self.zone_manager,
                )
                add_recent_project(self.project.filepath)
                self._show_message(f"Saved: {self.project.filename}")
            except Exception as e:
                self._show_message(f"Save error: {e}")
        else:
            # Don't use blocking prompt - especially problematic in server mode
            suggested = suggest_filename(self.canvas)
            self._show_message(
                f"Use :w {suggested} or :w <filename> to save", frames=180
            )

    def _do_save_as(self) -> None:
        """Save with a new filename."""
        suggested = suggest_filename(self.canvas)
        filename = self.renderer.get_string_input(f"Save as [{suggested}]: ")

        if not filename:
            filename = suggested

        if not filename.endswith(".json"):
            filename += ".json"

        try:
            filepath = Path(filename)
            self.project.save(
                self.canvas,
                self.viewport,
                grid_settings=self.renderer.grid,
                bookmarks=self.state_machine.bookmarks,
                zones=self.zone_manager,
                filepath=filepath,
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
                row=-1,
            )
            if self.renderer.get_input() != ord("y"):
                return

        self.canvas.clear_all()
        self.viewport.cursor.set(0, 0)
        self.viewport.origin.set(0, 0)
        self.viewport.pan_to(0, 0)
        self.state_machine.bookmarks.clear()
        self.zone_manager.clear()
        self.project = Project()
        self.undo_manager.clear()  # Clear undo history for new canvas
        self._show_message("New canvas created")

    def _do_undo(self) -> None:
        """Undo the last canvas operation."""
        desc = self.undo_manager.undo(self.canvas)
        if desc:
            self._show_message(f"Undo: {desc}")
            self.project.mark_dirty()
        else:
            self._show_message("Nothing to undo")

    def _do_redo(self) -> None:
        """Redo the last undone operation."""
        desc = self.undo_manager.redo(self.canvas)
        if desc:
            self._show_message(f"Redo: {desc}")
            self.project.mark_dirty()
        else:
            self._show_message("Nothing to redo")

    def _cmd_search(self, args: list[str]) -> ModeResult:
        """Search for text: search PATTERN"""
        if not args:
            return ModeResult(message="Usage: search PATTERN")
        pattern = " ".join(args)
        self._do_search(pattern)
        return ModeResult()

    def _do_search(self, pattern: str) -> None:
        """Search for text pattern in the canvas."""
        search_state = self.state_machine.search_state

        # Search the canvas
        matches = self.canvas.search_text(pattern, case_sensitive=False)

        # Update search state
        search_state.term = pattern
        search_state.matches = matches
        search_state.current_index = 0
        search_state.active = len(matches) > 0

        if matches:
            # Jump to first match
            x, y, _ = matches[0]
            self.viewport.cursor.set(x, y)
            self.viewport.ensure_cursor_visible(
                margin=self.state_machine.config.scroll_margin
            )
            self._show_message(f"[/{pattern}] 1/{len(matches)} - n:next N:prev")
        else:
            search_state.active = False
            self._show_message(f"Pattern not found: {pattern}")

    def _show_help(self) -> None:
        """Show help screen with multiple pages."""
        # Build joystick status line
        joy_status = ""
        if self._joystick_enabled and self.joystick.is_connected:
            info = self.joystick.get_info()
            joy_status = f"  JOYSTICK: {info['name']} (connected)\n"
            joy_status += "    D-pad/Stick   - Move cursor       Button A      - EDIT/toggle pen\n"
            joy_status += "    Button B      - Exit to NAV       Button X      - Cycle border style\n\n"

        # Page 1: Basic navigation and modes
        page1 = f"""
  my-grid - ASCII Canvas Editor                                    [Page 1/3]

  MODES:
    NAV (default) - Navigate canvas    PAN (p)       - Pan viewport
    EDIT (i)      - Type/draw          COMMAND (:)   - Enter commands
    VISUAL (v)    - Visual selection   DRAW (D)      - Line drawing
    Esc           - Exit current mode

  NAVIGATION:
    wasd / arrows - Move cursor        WASD          - Fast move (10x)

  VISUAL SELECTION (press 'v' in NAV mode):
    wasd/arrows   - Extend selection   y             - Yank selection
    d             - Delete selection   f             - Fill selection
    Esc           - Cancel selection

  BOOKMARKS:
    m + key       - Set mark (a-z, 0-9)    ' + key   - Jump to mark
    :marks        - List all marks         :delmark X - Delete mark X

  UNDO/REDO:
    u / Ctrl+Z    - Undo last operation    Ctrl+R    - Redo
    :undo         - Undo via command       :redo     - Redo via command
    :history      - Show operation history

  DRAWING:
    D / :draw     - Enter line draw mode   :border STYLE - Set line style
    :rect W H [c] - Draw rectangle         :line X Y  - Draw line to X,Y
    :text MSG     - Write text             :box STYLE TEXT - ASCII box
    :figlet TEXT  - ASCII art text         :fill [X Y] W H C - Fill region

{joy_status}  [n/Space] Next page | [p] Prev | [q/Esc] Close"""

        # Page 2: Zones and dynamic content
        page2 = """
  ZONES - Named regions for organization                           [Page 2/3]

  STATIC ZONES:
    :zone create NAME X Y W H   - Create zone at coordinates
    :zone create NAME here W H  - Create zone at cursor
    :zone delete NAME           - Delete zone
    :zone goto NAME             - Jump to zone center
    :zones                      - List all zones

  DYNAMIC ZONES:
    :zone pipe NAME W H CMD     - Create pipe zone (command output)
    :zone watch NAME W H INT CMD - Create watch zone (auto-refresh)
    :zone refresh NAME          - Manually refresh pipe/watch
    :zone pause/resume NAME     - Control watch zones
    :zone buffer NAME           - View full buffer (scrollable)

  PTY ZONES (Unix):
    :zone pty NAME W H [SHELL]  - Create live terminal zone
    :zone send NAME TEXT        - Send text to PTY
    :zone focus NAME            - Focus PTY (Enter in zone also focuses)
    Esc                         - Unfocus PTY

  EXTERNAL CONNECTORS:
    :zone fifo NAME W H PATH    - Create FIFO zone (Unix)
    :zone socket NAME W H PORT  - Create socket zone (TCP listener)

  [n/Space] Next page | [p] Prev | [q/Esc] Close"""

        # Page 3: Layouts, clipboard, file operations
        page3 = """
  LAYOUTS & CLIPBOARD                                              [Page 3/3]

  LAYOUTS:
    :layout list              - List saved layouts
    :layout save NAME [DESC]  - Save current zones as layout
    :layout load NAME         - Load a layout (adds to existing)
    :layout reload NAME       - Reload layout (clears existing)
    :layout delete NAME       - Delete a layout

  CLIPBOARD:
    :yank W H                 - Yank region at cursor
    :yank zone NAME           - Yank zone content
    :paste                    - Paste at cursor
    :clipboard                - Show clipboard info
    :clipboard zone [NAME]    - Create clipboard zone

  FILE OPERATIONS:
    :w / :write     - Save         :saveas FILE  - Save as
    :q / :quit      - Quit         :wq           - Save and quit
    :export [FILE]  - Export text  :import FILE  - Import text
    Ctrl+S          - Save         Ctrl+O        - Open
    Ctrl+N          - New          F1            - This help

  COLORS:
    :color FG [BG]    - Set drawing color (fg/bg)
    :color off        - Reset to default colors
    :color apply W H  - Apply current color to region
    :palette          - Show available colors

  EXTERNAL TOOLS:
    :tools          - Show tool availability (boxes, figlet)
    :box list       - List box styles
    :figlet list    - List figlet fonts

  [n/Space] Next page | [p] Prev | [q/Esc] Close"""

        pages = [page1, page2, page3]
        current_page = 0

        # Disable timeout for blocking input
        self.stdscr.timeout(-1)

        while True:
            self.stdscr.clear()
            for i, line in enumerate(pages[current_page].strip().split("\n")):
                try:
                    self.stdscr.addstr(i, 0, line)
                except curses.error:
                    pass
            self.stdscr.refresh()

            key = self.renderer.get_input()

            # Navigation
            if key in (ord("n"), ord(" "), curses.KEY_RIGHT, curses.KEY_DOWN):
                current_page = (current_page + 1) % len(pages)
            elif key in (ord("p"), curses.KEY_LEFT, curses.KEY_UP):
                current_page = (current_page - 1) % len(pages)
            elif key in (ord("q"), 27, ord("Q")):  # q, Esc, Q
                break

        # Restore timeout if joystick/server is active
        if self._joystick_enabled or self._server_config:
            self.stdscr.timeout(50)

    def _show_buffer_viewer(self, zone_name: str, lines: list[str]) -> None:
        """Show scrollable buffer viewer for zone content."""
        scroll_offset = 0
        search_term = ""
        search_matches: list[int] = []  # Line numbers with matches
        current_match = 0

        # Disable timeout for blocking input
        self.stdscr.timeout(-1)

        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()

            # Header
            header = f" Zone Buffer: {zone_name} ({len(lines)} lines)"
            if search_term:
                header += f" | Search: '{search_term}' ({len(search_matches)} matches)"
            header = header[: width - 1]
            try:
                self.stdscr.attron(curses.A_REVERSE)
                self.stdscr.addstr(0, 0, header.ljust(width - 1))
                self.stdscr.attroff(curses.A_REVERSE)
            except curses.error:
                pass

            # Content area (leave room for header and footer)
            content_height = height - 3
            visible_lines = lines[scroll_offset : scroll_offset + content_height]

            for row, line in enumerate(visible_lines):
                line_num = scroll_offset + row
                # Truncate line to fit
                display_line = line[: width - 8] if len(line) > width - 8 else line
                prefix = f"{line_num+1:5} "
                try:
                    # Highlight search matches
                    if search_term and line_num in search_matches:
                        self.stdscr.attron(curses.A_BOLD)
                        self.stdscr.addstr(row + 1, 0, prefix + display_line)
                        self.stdscr.attroff(curses.A_BOLD)
                    else:
                        self.stdscr.addstr(row + 1, 0, prefix + display_line)
                except curses.error:
                    pass

            # Footer with controls
            footer = (
                " [j/↓]Down [k/↑]Up [g]Top [G]End [/]Search [n]Next [N]Prev [q]Quit"
            )
            scroll_info = f" Line {scroll_offset+1}-{min(scroll_offset+content_height, len(lines))}/{len(lines)}"
            footer_text = (footer + scroll_info)[: width - 1]
            try:
                self.stdscr.attron(curses.A_REVERSE)
                self.stdscr.addstr(height - 1, 0, footer_text.ljust(width - 1))
                self.stdscr.attroff(curses.A_REVERSE)
            except curses.error:
                pass

            self.stdscr.refresh()

            key = self.renderer.get_input()

            # Navigation
            if key in (ord("j"), curses.KEY_DOWN):
                if scroll_offset < len(lines) - content_height:
                    scroll_offset += 1
            elif key in (ord("k"), curses.KEY_UP):
                if scroll_offset > 0:
                    scroll_offset -= 1
            elif key in (ord("d"), curses.KEY_NPAGE):  # Page down
                scroll_offset = min(
                    scroll_offset + content_height, max(0, len(lines) - content_height)
                )
            elif key in (ord("u"), curses.KEY_PPAGE):  # Page up
                scroll_offset = max(0, scroll_offset - content_height)
            elif key == ord("g"):  # Top
                scroll_offset = 0
            elif key == ord("G"):  # Bottom
                scroll_offset = max(0, len(lines) - content_height)
            elif key == ord("/"):  # Search
                # Simple search input
                curses.echo()
                self.stdscr.addstr(height - 1, 0, "/".ljust(width - 1))
                self.stdscr.move(height - 1, 1)
                try:
                    search_bytes = self.stdscr.getstr(height - 1, 1, 40)
                    search_term = search_bytes.decode("utf-8", errors="replace")
                except (curses.error, UnicodeDecodeError, OSError):
                    search_term = ""
                curses.noecho()
                # Find matches
                search_matches = []
                if search_term:
                    for i, line in enumerate(lines):
                        if search_term.lower() in line.lower():
                            search_matches.append(i)
                    current_match = 0
                    # Jump to first match
                    if search_matches:
                        scroll_offset = max(0, search_matches[0] - content_height // 2)
            elif key == ord("n") and search_matches:  # Next match
                current_match = (current_match + 1) % len(search_matches)
                scroll_offset = max(
                    0, search_matches[current_match] - content_height // 2
                )
            elif key == ord("N") and search_matches:  # Prev match
                current_match = (current_match - 1) % len(search_matches)
                scroll_offset = max(
                    0, search_matches[current_match] - content_height // 2
                )
            elif key in (ord("q"), 27):  # q or Esc
                break

        # Restore timeout if joystick/server is active
        if self._joystick_enabled or self._server_config:
            self.stdscr.timeout(50)

    # Command handlers
    def _cmd_save(self, args: list[str]) -> ModeResult:
        self._do_save()
        return ModeResult()

    def _cmd_write(self, args: list[str]) -> ModeResult:
        """Handle :w [filename] - vim-style write command."""
        if args:
            # :w filename - save to specified file
            filename = args[0]
            if not filename.endswith(".json"):
                filename += ".json"
            try:
                self.project.save(
                    self.canvas,
                    self.viewport,
                    grid_settings=self.renderer.grid,
                    bookmarks=self.state_machine.bookmarks,
                    zones=self.zone_manager,
                    filepath=Path(filename),
                )
                add_recent_project(Path(filename))
                self._show_message(f"Saved: {filename}")
            except Exception as e:
                return ModeResult(message=f"Save error: {e}")
        else:
            # :w - save to current file or prompt
            self._do_save()
        return ModeResult()

    def _cmd_save_as(self, args: list[str]) -> ModeResult:
        if args:
            filename = args[0]
            if not filename.endswith(".json"):
                filename += ".json"
            try:
                self.project.save(
                    self.canvas,
                    self.viewport,
                    grid_settings=self.renderer.grid,
                    bookmarks=self.state_machine.bookmarks,
                    zones=self.zone_manager,
                    filepath=Path(filename),
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
        from zones import get_border_chars

        if len(args) < 2:
            return ModeResult(message="Usage: rect WIDTH HEIGHT [char]")
        try:
            w, h = int(args[0]), int(args[1])
            char = args[2] if len(args) > 2 else None
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            if char:
                # User specified custom char - use it for all
                self.canvas.draw_rect(cx, cy, w, h, char, char, corner_char=char)
            else:
                # Use current border style
                chars = get_border_chars()
                self.canvas.draw_rect(
                    cx,
                    cy,
                    w,
                    h,
                    h_char=chars["horiz"],
                    v_char=chars["vert"],
                    tl=chars["tl"],
                    tr=chars["tr"],
                    bl=chars["bl"],
                    br=chars["br"],
                )
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
            char = args[2] if len(args) > 2 else "*"
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y

            # Compute line cells using Bresenham's algorithm for undo recording
            line_cells = []
            dx, dy = abs(x2 - cx), abs(y2 - cy)
            sx, sy = (1 if cx < x2 else -1), (1 if cy < y2 else -1)
            err, x, y = dx - dy, cx, cy
            while True:
                line_cells.append((x, y))
                if x == x2 and y == y2:
                    break
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x += sx
                if e2 < dx:
                    err += dx
                    y += sy

            # Record undo state
            self.undo_manager.begin_operation("Line")
            for lx, ly in line_cells:
                self.undo_manager.record_cell_before(self.canvas, lx, ly)
            self.canvas.draw_line(cx, cy, x2, y2, char)
            for lx, ly in line_cells:
                self.undo_manager.record_cell_after(self.canvas, lx, ly)
            self.undo_manager.end_operation()

            self.project.mark_dirty()
            return ModeResult(message=f"Drew line to ({x2}, {y2})")
        except ValueError:
            return ModeResult(message="Invalid coordinates")

    def _cmd_text(self, args: list[str]) -> ModeResult:
        """Write text: text MESSAGE"""
        if not args:
            return ModeResult(message="Usage: text MESSAGE")
        text = " ".join(args)
        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y

        # Record undo state for each character position
        self.undo_manager.begin_operation("Text")
        for i in range(len(text)):
            self.undo_manager.record_cell_before(self.canvas, cx + i, cy)
        self.canvas.write_text(cx, cy, text)
        for i in range(len(text)):
            self.undo_manager.record_cell_after(self.canvas, cx + i, cy)
        self.undo_manager.end_operation()

        self.project.mark_dirty()
        return ModeResult(message=f"Wrote {len(text)} characters")

    def _cmd_fill(self, args: list[str]) -> ModeResult:
        """Fill a rectangular region with a character.

        Usage:
            :fill X Y W H CHAR   - Fill region at (X,Y) with dimensions WxH
            :fill W H CHAR       - Fill region at cursor with dimensions WxH
        """
        if len(args) < 3:
            return ModeResult(message="Usage: fill [X Y] W H CHAR")

        try:
            # Check if first two args are coordinates or dimensions
            if len(args) >= 5:
                # fill X Y W H CHAR
                x, y = int(args[0]), int(args[1])
                w, h = int(args[2]), int(args[3])
                char = args[4] if len(args) > 4 else " "
            else:
                # fill W H CHAR (use cursor position)
                x, y = self.viewport.cursor.x, self.viewport.cursor.y
                w, h = int(args[0]), int(args[1])
                char = args[2] if len(args) > 2 else " "

            # Use only the first character
            char = char[0] if char else " "

            # Record undo state for all affected cells
            self.undo_manager.begin_operation("Fill")
            for fy in range(y, y + h):
                for fx in range(x, x + w):
                    self.undo_manager.record_cell_before(self.canvas, fx, fy)

            # Fill the region with current drawing colors
            fg = self.state_machine.draw_fg
            bg = self.state_machine.draw_bg
            for fy in range(y, y + h):
                for fx in range(x, x + w):
                    self.canvas.set(fx, fy, char, fg=fg, bg=bg)

            for fy in range(y, y + h):
                for fx in range(x, x + w):
                    self.undo_manager.record_cell_after(self.canvas, fx, fy)
            self.undo_manager.end_operation()

            self.project.mark_dirty()
            return ModeResult(message=f"Filled {w}x{h} region with '{char}'")

        except ValueError:
            return ModeResult(message="Usage: fill [X Y] W H CHAR")

    def _cmd_color(self, args: list[str]) -> ModeResult:
        """
        Set drawing color for text/drawing operations.

        Usage:
            :color                  - Show current color
            :color FG               - Set foreground color
            :color FG BG            - Set foreground and background
            :color off              - Reset to default colors
            :color apply W H        - Apply current color to region at cursor

        Colors: black, red, green, yellow, blue, magenta, cyan, white, default
        Or use numbers 0-7 (or 0-255 on supported terminals)
        """
        if not args:
            # Show current drawing color
            fg = self.state_machine.draw_fg
            bg = self.state_machine.draw_bg
            fg_name = COLOR_NUMBERS.get(fg, str(fg))
            bg_name = COLOR_NUMBERS.get(bg, str(bg))
            return ModeResult(message=f"Color: fg={fg_name} bg={bg_name}")

        subcmd = args[0].lower()

        # Reset colors
        if subcmd in ("off", "reset", "default"):
            self.state_machine.draw_fg = -1
            self.state_machine.draw_bg = -1
            return ModeResult(message="Color reset to default")

        # Apply color to region
        if subcmd == "apply":
            if len(args) < 3:
                return ModeResult(message="Usage: color apply W H")
            try:
                w, h = int(args[1]), int(args[2])
                fg = self.state_machine.draw_fg
                bg = self.state_machine.draw_bg
                cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
                for y in range(cy, cy + h):
                    for x in range(cx, cx + w):
                        self.canvas.set_color(x, y, fg, bg)
                self.project.mark_dirty()
                return ModeResult(message=f"Applied color to {w}x{h} region")
            except ValueError:
                return ModeResult(message="Usage: color apply W H")

        # Set foreground (and optionally background)
        fg = parse_color(args[0])
        if fg == -1 and args[0].lower() not in ("default", "-1"):
            return ModeResult(
                message=f"Unknown color: {args[0]}. Use: black,red,green,yellow,blue,magenta,cyan,white"
            )

        bg = -1
        if len(args) > 1:
            bg = parse_color(args[1])
            if bg == -1 and args[1].lower() not in ("default", "-1"):
                return ModeResult(message=f"Unknown color: {args[1]}")

        self.state_machine.draw_fg = fg
        self.state_machine.draw_bg = bg

        fg_name = COLOR_NUMBERS.get(fg, str(fg))
        bg_name = COLOR_NUMBERS.get(bg, str(bg))
        return ModeResult(message=f"Color set: fg={fg_name} bg={bg_name}")

    def _cmd_palette(self, args: list[str]) -> ModeResult:
        """Show available colors."""
        colors = (
            "black(0) red(1) green(2) yellow(3) blue(4) magenta(5) cyan(6) white(7)"
        )
        return ModeResult(message=f"Colors: {colors}", message_frames=60)

    def _cmd_draw(self, args: list[str]) -> ModeResult:
        """Enter draw mode for line drawing."""
        from modes import Mode

        self.state_machine._draw_last_dir = None
        self.state_machine._draw_pen_down = True  # Start with pen down
        self.state_machine.set_mode(Mode.DRAW)
        return ModeResult(
            mode_changed=True,
            new_mode=Mode.DRAW,
            message="-- DRAW -- pen DOWN (wasd to draw, space to lift)",
        )

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
            self.renderer.grid.show_major_lines = (
                not self.renderer.grid.show_major_lines
            )
            return ModeResult(
                message=f"Major grid: {'ON' if self.renderer.grid.show_major_lines else 'OFF'}"
            )
        elif arg == "minor":
            self.renderer.grid.show_minor_lines = (
                not self.renderer.grid.show_minor_lines
            )
            return ModeResult(
                message=f"Minor grid: {'ON' if self.renderer.grid.show_minor_lines else 'OFF'}"
            )

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
            return ModeResult(
                message=f"Rulers: {'ON' if self.renderer.grid.show_rulers else 'OFF'}"
            )
        elif arg == "labels":
            self.renderer.grid.show_labels = not self.renderer.grid.show_labels
            return ModeResult(
                message=f"Coordinate labels: {'ON' if self.renderer.grid.show_labels else 'OFF'}"
            )

        # Interval configuration
        elif arg == "interval":
            if len(args) < 2:
                return ModeResult(
                    message=f"Interval: major={self.renderer.grid.major_interval} minor={self.renderer.grid.minor_interval}"
                )
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
                "height": self.viewport.height,
            },
            "mode": self.state_machine.mode_name,
            "cells": self.canvas.cell_count,
            "dirty": self.project.dirty,
            "file": self.project.filename,
            "server": self.api_server.status.tcp_port if self.api_server else None,
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
            :zone buffer NAME                 - View full zone buffer (scrollable)
            :zone export NAME [FILE]          - Export zone buffer to file
            :zone pty NAME W H [SHELL]        - Create PTY zone (Unix only)
            :zone send NAME TEXT              - Send text to PTY zone
            :zone focus NAME                  - Focus PTY/pager zone
            :zone fifo NAME W H PATH          - Create FIFO zone (Unix only)
            :zone socket NAME W H PORT        - Create socket zone
            :zone pager NAME W H FILE [opts]  - Create pager zone for file viewing
            :zone scroll NAME +/-N|top|bottom - Scroll pager zone
            :zone search NAME TERM            - Search in pager zone
            :zone reload NAME                 - Reload pager content
            :zone renderers [--wsl]           - List available renderers
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

            # Get zone before deleting to clear its canvas region
            zone = self.zone_manager.get(name)
            if zone is None:
                return ModeResult(message=f"Zone '{name}' not found")

            # Clear canvas cells in zone's region
            for y in range(zone.y, zone.y + zone.height):
                for x in range(zone.x, zone.x + zone.width):
                    self.canvas.clear(x, y)

            # Now delete the zone
            self.zone_manager.delete(name)
            self.project.mark_dirty()
            return ModeResult(message=f"Deleted zone '{name}'")

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

            info = f"'{zone.name}' ({zone.x},{zone.y}) {zone.width}x{zone.height} [{zone.type_indicator()}]"
            if zone.bookmark:
                info += f" [bookmark:{zone.bookmark}]"
            if zone.zone_type == ZoneType.PAGER:
                info += f" | styled_lines={len(zone._styled_content)}"
                info += f" | file={zone.config.file_path}"
            elif zone.description:
                info += f" - {zone.description}"
            return ModeResult(message=info)

        # :zone rename OLD NEW
        elif subcmd == "rename":
            if len(args) < 3:
                return ModeResult(message="Usage: zone rename OLD NEW")
            if self.zone_manager.rename(args[1], args[2]):
                self.project.mark_dirty()
                return ModeResult(message=f"Renamed '{args[1]}' to '{args[2]}'")
            return ModeResult(
                message="Failed to rename (zone not found or name conflict)"
            )

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
                    return ModeResult(
                        message=f"Linked '{args[1]}' to bookmark '{bookmark}'"
                    )
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
                return ModeResult(
                    message=f"Created pipe zone '{name}' - {len(zone.content_lines)} lines"
                )
            except ValueError as e:
                return ModeResult(message=str(e))

        # :zone watch NAME W H (INTERVAL|watch:PATH) CMD
        elif subcmd == "watch":
            if len(args) < 6:
                return ModeResult(
                    message="Usage: zone watch NAME W H (INTERVAL|watch:PATH) COMMAND"
                )
            name = args[1]
            try:
                w, h = int(args[2]), int(args[3])
                watch_spec = args[4]
                cmd = " ".join(args[5:])

                # Detect file-watch vs interval mode
                if watch_spec.startswith("watch:"):
                    # File-watching mode
                    watch_path = watch_spec[6:]  # Remove "watch:" prefix
                    if not watch_path:
                        return ModeResult(message="Missing file path after 'watch:'")

                    # Expand ~ and resolve relative paths
                    watch_path = os.path.expanduser(watch_path)
                    if not os.path.isabs(watch_path):
                        watch_path = os.path.abspath(watch_path)

                    x = self.viewport.cursor.x
                    y = self.viewport.cursor.y

                    zone = self.zone_manager.create_watch_file(
                        name, x, y, w, h, cmd, watch_path
                    )
                    self.zone_executor.start_watch(zone)
                    self.project.mark_dirty()
                    return ModeResult(
                        message=f"Created watch zone '{name}' (watching: {watch_path})"
                    )
                else:
                    # Interval-based mode (existing behavior)
                    if watch_spec.endswith("s"):
                        interval = float(watch_spec[:-1])
                    elif watch_spec.endswith("m"):
                        interval = float(watch_spec[:-1]) * 60
                    else:
                        interval = float(watch_spec)

                    x = self.viewport.cursor.x
                    y = self.viewport.cursor.y

                    zone = self.zone_manager.create_watch(
                        name, x, y, w, h, cmd, interval
                    )
                    self.zone_executor.start_watch(zone)
                    self.project.mark_dirty()
                    return ModeResult(
                        message=f"Created watch zone '{name}' (refresh: {interval}s)"
                    )
            except (ValueError, IndexError) as e:
                return ModeResult(message=f"Invalid arguments: {e}")

        # :zone http NAME W H URL [INTERVAL]
        elif subcmd == "http":
            if len(args) < 5:
                return ModeResult(message="Usage: zone http NAME W H URL [interval]")
            name = args[1]
            try:
                w, h = int(args[2]), int(args[3])
                url = args[4]
                interval = None

                # Parse optional interval
                if len(args) > 5:
                    interval_spec = args[5]
                    if interval_spec.endswith("s"):
                        interval = float(interval_spec[:-1])
                    elif interval_spec.endswith("m"):
                        interval = float(interval_spec[:-1]) * 60
                    else:
                        interval = float(interval_spec)

                x = self.viewport.cursor.x
                y = self.viewport.cursor.y

                zone = self.zone_manager.create_http(name, x, y, w, h, url, interval)
                # Execute immediately
                self.zone_executor.execute_http(zone)
                # Start background refresh if interval specified
                if interval:
                    self.zone_executor.start_http_watch(zone)
                self.project.mark_dirty()

                msg = f"Created HTTP zone '{name}' - {len(zone.content_lines)} lines"
                if interval:
                    msg += f" (refresh: {interval}s)"
                return ModeResult(message=msg)
            except (ValueError, IndexError) as e:
                return ModeResult(message=f"Invalid arguments: {e}")

        # :zone refresh NAME
        elif subcmd == "refresh":
            if len(args) < 2:
                return ModeResult(message="Usage: zone refresh NAME")
            if self.zone_executor.refresh_zone(args[1]):
                zone = self.zone_manager.get(args[1])
                return ModeResult(
                    message=f"Refreshed '{args[1]}' - {len(zone.content_lines)} lines"
                )
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

        # :zone buffer NAME
        elif subcmd == "buffer":
            if len(args) < 2:
                return ModeResult(message="Usage: zone buffer NAME")
            zone = self.zone_manager.get(args[1])
            if zone is None:
                return ModeResult(message=f"Zone '{args[1]}' not found")
            lines = zone.content_lines
            if not lines:
                return ModeResult(message=f"Zone '{args[1]}' buffer is empty")
            self._show_buffer_viewer(zone.name, lines)
            return ModeResult()

        # :zone export NAME [FILE]
        elif subcmd == "export":
            if len(args) < 2:
                return ModeResult(message="Usage: zone export NAME [FILE]")
            zone = self.zone_manager.get(args[1])
            if zone is None:
                return ModeResult(message=f"Zone '{args[1]}' not found")
            lines = zone.content_lines
            if not lines:
                return ModeResult(message=f"Zone '{args[1]}' buffer is empty")

            # Generate default filename if not provided
            if len(args) >= 3:
                filename = args[2]
            else:
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{zone.name.lower()}_{timestamp}.txt"

            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                    f.write("\n")  # Trailing newline
                return ModeResult(message=f"Exported {len(lines)} lines to {filename}")
            except Exception as e:
                return ModeResult(message=f"Export error: {e}")

        # :zone pty NAME W H [SHELL]
        elif subcmd == "pty":
            if not PTY_AVAILABLE:
                return ModeResult(
                    message="PTY not available on this platform (requires Unix)"
                )

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
                    return ModeResult(
                        message=f"Created PTY zone '{name}' - press Enter to focus"
                    )
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
            if zone.zone_type == ZoneType.PTY:
                if not self.pty_handler.is_active(name):
                    return ModeResult(message=f"PTY for zone '{name}' is not active")
                self._focused_pty = name
                return ModeResult(message=f"PTY focused: {name}")
            elif zone.zone_type == ZoneType.PAGER:
                self._focused_pager = name
                line = zone.config.scroll_offset + 1
                total = zone.pager_line_count
                return ModeResult(
                    message=f"PAGER focused: {name} - Line {line}/{total}"
                )
            else:
                return ModeResult(message=f"Zone '{name}' is not a PTY or PAGER zone")

        # :zone fifo NAME W H PATH
        elif subcmd == "fifo":
            if os.name == "nt":
                return ModeResult(
                    message="FIFO not available on Windows (requires Unix)"
                )

            if len(args) < 5:
                return ModeResult(message="Usage: zone fifo NAME W H PATH")
            name = args[1]
            try:
                w, h = int(args[2]), int(args[3])
                path = args[4]
            except (ValueError, IndexError):
                return ModeResult(message="Invalid width/height")

            x = self.viewport.cursor.x
            y = self.viewport.cursor.y

            try:
                # Create zone with FIFO config
                config = ZoneConfig(zone_type=ZoneType.FIFO, path=path)
                zone = self.zone_manager.create(
                    name, x, y, w, h, config=config, description=f"FIFO: {path}"
                )
                # Start FIFO listener
                if self.fifo_handler.create_fifo(zone):
                    self.project.mark_dirty()
                    return ModeResult(
                        message=f"Created FIFO zone '{name}' listening on {path}"
                    )
                else:
                    self.zone_manager.delete(name)
                    return ModeResult(
                        message=f"Failed to create FIFO for zone '{name}'"
                    )
            except ValueError as e:
                return ModeResult(message=str(e))

        # :zone socket NAME W H PORT
        elif subcmd == "socket":
            if len(args) < 5:
                return ModeResult(message="Usage: zone socket NAME W H PORT")
            name = args[1]
            try:
                w, h = int(args[2]), int(args[3])
                port = int(args[4])
            except (ValueError, IndexError):
                return ModeResult(message="Invalid width/height/port")

            x = self.viewport.cursor.x
            y = self.viewport.cursor.y

            try:
                # Create zone with socket config
                config = ZoneConfig(zone_type=ZoneType.SOCKET, port=port)
                zone = self.zone_manager.create(
                    name, x, y, w, h, config=config, description=f"Socket: port {port}"
                )
                # Start socket listener
                if self.socket_handler.create_socket(zone):
                    self.project.mark_dirty()
                    return ModeResult(
                        message=f"Created socket zone '{name}' listening on port {port}"
                    )
                else:
                    self.zone_manager.delete(name)
                    return ModeResult(
                        message=f"Failed to create socket for zone '{name}'"
                    )
            except ValueError as e:
                return ModeResult(message=str(e))

        # :zone pager NAME W H FILE [--renderer RENDERER] [--wsl]
        elif subcmd == "pager":
            if len(args) < 5:
                return ModeResult(
                    message="Usage: zone pager NAME W H FILE [--renderer glow|bat|plain] [--wsl]"
                )
            name = args[1]
            try:
                w, h = int(args[2]), int(args[3])
                file_path = args[4]
            except (ValueError, IndexError):
                return ModeResult(message="Invalid width/height")

            # Parse optional flags
            renderer = "auto"
            use_wsl = False
            i = 5
            while i < len(args):
                if args[i] == "--renderer" and i + 1 < len(args):
                    renderer = args[i + 1]
                    i += 2
                elif args[i] == "--wsl":
                    use_wsl = True
                    i += 1
                else:
                    i += 1

            x = self.viewport.cursor.x
            y = self.viewport.cursor.y

            # Resolve relative paths
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)

            try:
                # Create zone with PAGER config
                config = ZoneConfig(
                    zone_type=ZoneType.PAGER,
                    file_path=file_path,
                    renderer=renderer,
                )
                zone = self.zone_manager.create(
                    name,
                    x,
                    y,
                    w,
                    h,
                    config=config,
                    description=f"Pager: {os.path.basename(file_path)}",
                )

                # Load and render content
                if load_pager_content(zone, use_wsl):
                    self.project.mark_dirty()
                    line_count = zone.pager_line_count
                    return ModeResult(
                        message=f"Created pager zone '{name}' - {line_count} lines - press Enter to focus"
                    )
                else:
                    self.zone_manager.delete(name)
                    return ModeResult(
                        message=f"Failed to load content for pager zone '{name}'"
                    )
            except ValueError as e:
                return ModeResult(message=str(e))

        # :zone scroll NAME +/-N|top|bottom
        elif subcmd == "scroll":
            if len(args) < 3:
                return ModeResult(message="Usage: zone scroll NAME +/-N|top|bottom")
            name = args[1]
            zone = self.zone_manager.get(name)
            if zone is None:
                return ModeResult(message=f"Zone '{name}' not found")
            if zone.zone_type != ZoneType.PAGER:
                return ModeResult(message=f"Zone '{name}' is not a pager zone")

            scroll_arg = args[2].lower()
            max_offset = max(0, zone.pager_line_count - zone.pager_visible_lines)

            if scroll_arg == "top":
                zone.config.scroll_offset = 0
            elif scroll_arg == "bottom":
                zone.config.scroll_offset = max_offset
            else:
                try:
                    if scroll_arg.startswith("+"):
                        delta = int(scroll_arg[1:])
                        zone.config.scroll_offset = min(
                            max_offset, zone.config.scroll_offset + delta
                        )
                    elif scroll_arg.startswith("-"):
                        delta = int(scroll_arg[1:])
                        zone.config.scroll_offset = max(
                            0, zone.config.scroll_offset - delta
                        )
                    else:
                        # Absolute position
                        zone.config.scroll_offset = max(
                            0, min(max_offset, int(scroll_arg))
                        )
                except ValueError:
                    return ModeResult(message=f"Invalid scroll value: {scroll_arg}")

            line = zone.config.scroll_offset + 1
            total = zone.pager_line_count
            return ModeResult(message=f"Scrolled to line {line}/{total}")

        # :zone search NAME TERM
        elif subcmd == "search":
            if len(args) < 3:
                return ModeResult(message="Usage: zone search NAME TERM")
            name = args[1]
            zone = self.zone_manager.get(name)
            if zone is None:
                return ModeResult(message=f"Zone '{name}' not found")
            if zone.zone_type != ZoneType.PAGER:
                return ModeResult(message=f"Zone '{name}' is not a pager zone")

            term = " ".join(args[2:])
            zone.config.search_term = term
            zone.config.search_matches = []
            zone.config.search_index = 0

            # Search through plain content lines
            for i, line in enumerate(zone._content_lines):
                if term.lower() in strip_ansi(line).lower():
                    zone.config.search_matches.append(i)

            if zone.config.search_matches:
                # Jump to first match
                zone.config.scroll_offset = zone.config.search_matches[0]
                return ModeResult(
                    message=f"Found {len(zone.config.search_matches)} matches - use n/N to navigate"
                )
            else:
                zone.config.search_term = None
                return ModeResult(message=f"No matches for '{term}'")

        # :zone reload NAME
        elif subcmd == "reload":
            if len(args) < 2:
                return ModeResult(message="Usage: zone reload NAME")
            name = args[1]
            zone = self.zone_manager.get(name)
            if zone is None:
                return ModeResult(message=f"Zone '{name}' not found")
            if zone.zone_type != ZoneType.PAGER:
                return ModeResult(message=f"Zone '{name}' is not a pager zone")

            if load_pager_content(zone, use_wsl=False):
                return ModeResult(
                    message=f"Reloaded pager zone '{name}' - {zone.pager_line_count} lines"
                )
            else:
                return ModeResult(message=f"Failed to reload content for '{name}'")

        # :zone renderers
        elif subcmd == "renderers":
            use_wsl = "--wsl" in args
            renderers = get_available_renderers(use_wsl)
            lines = []
            for name, desc, available in renderers:
                status = "✓" if available else "✗"
                lines.append(f"  {status} {name}: {desc}")
            env = "WSL" if use_wsl else "native"
            return ModeResult(message=f"Renderers ({env}):\n" + "\n".join(lines))

        else:
            return ModeResult(
                message="Usage: zone create|delete|goto|pipe|watch|pager|pty|fifo|socket|..."
            )

    def _cmd_shader(self, args: list[str]) -> ModeResult:
        """Control shader parameters in zone mode animations via control socket.

        Usage:
            :shader ZONE_NAME param PARAM VALUE  - Set parameter value
            :shader ZONE_NAME port PORT          - Set control port for zone
            :shader ZONE_NAME info               - Show zone control info

        Examples:
            :shader LISSAJOUS param freq_x 5.0
            :shader PLASMA param freq_y 0.15
            :shader LISSAJOUS param phase 1.57
            :shader LISSAJOUS port 9998          - Set control port

        Note: Shaders must be started with --control-port flag
        """
        if len(args) < 2:
            return ModeResult(message="Usage: shader ZONE_NAME param PARAM VALUE")

        zone_name = args[0]
        zone = self.zone_manager.get(zone_name)

        if not zone:
            return ModeResult(message=f"Zone '{zone_name}' not found")

        subcmd = args[1].lower()

        # Port assignment for shader zones (stored in zone metadata)
        if not hasattr(zone, "_control_port"):
            # Default ports for known shaders
            default_ports = {
                "LISSAJOUS": 9998,
                "PLASMA": 9997,
                "SPIRAL": 9996,
                "WAVES": 9995,
            }
            zone._control_port = default_ports.get(zone_name.upper())

        if subcmd == "port":
            if len(args) < 3:
                return ModeResult(message="Usage: shader ZONE port PORT")
            try:
                zone._control_port = int(args[2])
                return ModeResult(
                    message=f"Set control port {zone._control_port} for {zone_name}"
                )
            except ValueError:
                return ModeResult(message=f"Invalid port: {args[2]}")

        elif subcmd == "param":
            if len(args) < 4:
                return ModeResult(message="Usage: shader ZONE param PARAM VALUE")

            if not zone._control_port:
                return ModeResult(
                    message=f"No control port set for {zone_name}. Use :shader {zone_name} port PORT"
                )

            param_name = args[2]
            try:
                param_value = float(args[3])
            except ValueError:
                return ModeResult(message=f"Invalid parameter value: {args[3]}")

            # Send JSON command to control socket
            import json
            import socket

            cmd = json.dumps(
                {"command": "set_param", "param": param_name, "value": param_value}
            )

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                s.connect(("localhost", zone._control_port))
                s.sendall(cmd.encode("utf-8") + b"\n")
                # Read response (discard - just need to wait for acknowledgment)
                s.recv(1024)
                s.close()
                return ModeResult(message=f"✓ {param_name}={param_value}")
            except ConnectionRefusedError:
                return ModeResult(
                    message=f"Control port {zone._control_port} not listening. Shader running with --control-port?"
                )
            except Exception as e:
                return ModeResult(message=f"Error: {e}")

        elif subcmd == "info":
            port_info = (
                f" (port {zone._control_port})"
                if zone._control_port
                else " (no control port)"
            )
            return ModeResult(message=f"Zone: {zone_name}{port_info}")

        else:
            return ModeResult(message="Usage: shader ZONE param PARAM VALUE")

    def _cmd_undo(self, args: list[str]) -> ModeResult:
        """Undo the last canvas operation.

        Usage:
            :undo           - Undo last operation
        """
        desc = self.undo_manager.undo(self.canvas)
        if desc:
            self.project.mark_dirty()
            return ModeResult(message=f"Undo: {desc}")
        return ModeResult(message="Nothing to undo")

    def _cmd_redo(self, args: list[str]) -> ModeResult:
        """Redo the last undone operation.

        Usage:
            :redo           - Redo last undone operation
        """
        desc = self.undo_manager.redo(self.canvas)
        if desc:
            self.project.mark_dirty()
            return ModeResult(message=f"Redo: {desc}")
        return ModeResult(message="Nothing to redo")

    def _cmd_history(self, args: list[str]) -> ModeResult:
        """Show undo/redo history.

        Usage:
            :history        - Show recent operation history
            :history N      - Show N most recent operations
        """
        limit = 10
        if args:
            try:
                limit = int(args[0])
            except ValueError:
                return ModeResult(message=f"Invalid limit: {args[0]} (expected number)")

        history = self.undo_manager.get_history(limit)
        if not history:
            return ModeResult(message="No history")

        undo_count = self.undo_manager.undo_count
        redo_count = self.undo_manager.redo_count
        lines = [f"History ({undo_count} undo, {redo_count} redo):"]
        for idx, desc in history:
            marker = ">" if idx == 0 else " "
            lines.append(f"  {marker} {idx}: {desc}")

        return ModeResult(message="\n".join(lines), message_frames=180)

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

        return ModeResult(
            message=f"{len(zones)} zones: " + ", ".join(z.name for z in zones)
        )

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
        parts = [
            f"{name}: {'OK' if available else 'NOT FOUND'}"
            for name, available in status.items()
        ]
        return ModeResult(message="Tools: " + ", ".join(parts))

    def _cmd_border(self, args: list[str]) -> ModeResult:
        """
        Set zone border style.

        Usage:
            :border              - Show current style
            :border list         - List available styles
            :border STYLE        - Set border style (ascii, unicode, rounded, double, heavy)
        """
        if not args:
            current = get_border_style()
            return ModeResult(message=f"Border style: {current}")

        subcmd = args[0].lower()

        if subcmd == "list":
            styles = list_border_styles()
            current = get_border_style()
            parts = [f"*{s}*" if s == current else s for s in styles]
            return ModeResult(message=f"Border styles: {', '.join(parts)}")

        # Try to set the style
        if set_border_style(subcmd):
            # Force redraw of all zones
            self.zone_manager.render_all_zones(self.canvas)
            return ModeResult(message=f"Border style set to: {subcmd}")
        else:
            styles = list_border_styles()
            return ModeResult(message=f"Unknown style. Available: {', '.join(styles)}")

    def _cmd_session(self, args: list[str]) -> ModeResult:
        """
        Session management command.

        Usage:
            :session              - Show session info
            :session list         - List available sessions
            :session restore [N]  - Restore session (latest or by index)
            :session save         - Force save current session
            :session on           - Enable auto-save
            :session off          - Disable auto-save
            :session clear        - Clear all saved sessions
        """
        if not args:
            # Show session info
            status = "enabled" if self.session_manager.enabled else "disabled"
            interval = self.session_manager.interval_seconds
            sessions = self.session_manager.list_sessions()
            return ModeResult(
                message=f"Auto-save: {status} ({interval}s interval), {len(sessions)} sessions saved"
            )

        subcmd = args[0].lower()

        # :session list
        if subcmd == "list":
            sessions = self.session_manager.list_sessions()
            if not sessions:
                return ModeResult(message="No sessions found", message_frames=60)

            # Show up to 10 sessions
            parts = []
            for i, sess in enumerate(sessions[:10]):
                ts = (
                    sess["timestamp"][:16]
                    if sess["timestamp"] != "Unknown"
                    else "Unknown"
                )
                parts.append(f"{i}: {ts}")
            return ModeResult(
                message=f"Sessions: {', '.join(parts)}", message_frames=120
            )

        # :session restore [N]
        elif subcmd == "restore":
            sessions = self.session_manager.list_sessions()
            if not sessions:
                return ModeResult(message="No sessions to restore")

            # Get session index (default to 0 = latest)
            index = 0
            if len(args) > 1:
                try:
                    index = int(args[1])
                except ValueError:
                    return ModeResult(
                        message="Usage: session restore [N] (N = session index)"
                    )

            if index < 0 or index >= len(sessions):
                return ModeResult(
                    message=f"Invalid session index. Range: 0-{len(sessions)-1}"
                )

            session_path = sessions[index]["path"]
            success = self.session_manager.restore_session(
                session_path,
                self.canvas,
                self.viewport,
                grid_settings=self.renderer.grid,
                bookmarks=self.state_machine.bookmarks,
                zones=self.zone_manager,
            )

            if success:
                self.project.mark_dirty()  # Mark as dirty since restored
                return ModeResult(
                    message=f"Restored session from {sessions[index]['timestamp'][:16]}"
                )
            else:
                return ModeResult(message="Failed to restore session")

        # :session save
        elif subcmd == "save":

            self.session_manager._last_save_time = 0  # Force save
            result = self.session_manager.auto_save(
                self.canvas,
                self.viewport,
                grid_settings=self.renderer.grid,
                bookmarks=self.state_machine.bookmarks,
                zones=self.zone_manager,
            )
            if result:
                return ModeResult(message=f"Session saved to {result.name}")
            else:
                return ModeResult(message="Failed to save session")

        # :session on
        elif subcmd == "on":
            self.session_manager.enabled = True
            return ModeResult(message="Auto-save enabled")

        # :session off
        elif subcmd == "off":
            self.session_manager.enabled = False
            return ModeResult(message="Auto-save disabled")

        # :session clear
        elif subcmd == "clear":
            sessions = self.session_manager.list_sessions()
            for sess in sessions:
                try:
                    sess["path"].unlink()
                except Exception:
                    pass
            return ModeResult(message=f"Cleared {len(sessions)} sessions")

        else:
            return ModeResult(
                message="Usage: session list|restore|save|on|off|clear",
                message_frames=60,
            )

    def _cmd_layout(self, args: list[str]) -> ModeResult:
        """
        Layout management command.

        Usage:
            :layout list              - List available layouts
            :layout load NAME         - Load a layout (adds to existing)
            :layout load NAME --clear - Load layout, clearing existing zones
            :layout reload NAME       - Reload layout (stops handlers, clears zones)
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
                return ModeResult(
                    message="No layouts found. Use ':layout save NAME' to create one."
                )
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

            # Stop all existing handlers and clear zones before loading
            if clear_existing:
                self.zone_executor.stop_all()
                self.pty_handler.stop_all()
                self.fifo_handler.stop_all()
                self.socket_handler.stop_all()
                # Clear zones AND their canvas regions
                self.zone_manager.clear_with_canvas(self.canvas)

            created, errors = self.layout_manager.apply_layout(
                layout,
                self.zone_manager,
                self.zone_executor,
                pty_handler=self.pty_handler,
                fifo_handler=self.fifo_handler,
                socket_handler=self.socket_handler,
                clear_existing=False,  # Already cleared above
            )

            # Register zone bookmarks
            self._register_zone_bookmarks()

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

        # :layout reload NAME - Shortcut for load --clear
        elif subcmd == "reload":
            if len(args) < 2:
                return ModeResult(message="Usage: layout reload NAME")
            # Re-invoke with --clear flag
            return self._cmd_layout(["load", args[1], "--clear"])

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
                name, description, self.zone_manager, cursor=cursor, viewport=viewport
            )
            return ModeResult(
                message=f"Saved layout '{name}' ({len(self.zone_manager)} zones)"
            )

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

    def _cmd_yank(self, args: list[str]) -> ModeResult:
        """
        Yank (copy) content to clipboard.

        Usage:
            :yank W H           - Yank WxH region at cursor
            :yank zone NAME     - Yank zone content
            :yank system        - Yank from system clipboard
        """
        if not args:
            # Default: yank 1x1 at cursor (single character)
            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            char = self.canvas.get_char(cx, cy)
            self.clipboard.set_content([char], f"char at ({cx},{cy})")
            return ModeResult(message=f"Yanked: '{char}'")

        subcmd = args[0].lower()

        # :yank zone NAME
        if subcmd == "zone":
            if len(args) < 2:
                return ModeResult(message="Usage: yank zone NAME")
            name = args[1]
            zone = self.zone_manager.get(name)
            if not zone:
                return ModeResult(message=f"Zone '{name}' not found")
            lines = self.clipboard.yank_zone(zone)
            return ModeResult(message=f"Yanked {lines} lines from zone '{name}'")

        # :yank system - read from system clipboard
        elif subcmd == "system":
            if self.clipboard.from_system_clipboard():
                lines = len(self.clipboard.content)
                return ModeResult(message=f"Yanked {lines} lines from system clipboard")
            return ModeResult(message="Could not read system clipboard")

        # :yank W H - yank region at cursor
        else:
            try:
                w = int(args[0])
                h = int(args[1]) if len(args) > 1 else 1
            except ValueError:
                return ModeResult(
                    message="Usage: yank W H | yank zone NAME | yank system"
                )

            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            lines = self.clipboard.yank_region(
                self.canvas, cx, cy, cx + w - 1, cy + h - 1
            )
            return ModeResult(message=f"Yanked {w}x{h} region ({lines} lines)")

    def _cmd_paste(self, args: list[str]) -> ModeResult:
        """
        Paste clipboard content at cursor.

        Usage:
            :paste              - Paste at cursor
            :paste system       - Copy to system clipboard
            :paste skip         - Paste, skipping spaces
        """
        if self.clipboard.is_empty:
            return ModeResult(message="Clipboard is empty")

        # :paste system - copy to system clipboard
        if args and args[0].lower() == "system":
            if self.clipboard.to_system_clipboard():
                return ModeResult(message="Copied to system clipboard")
            return ModeResult(message="Could not access system clipboard")

        # :paste [skip]
        skip_spaces = args and args[0].lower() == "skip"

        cx, cy = self.viewport.cursor.x, self.viewport.cursor.y

        # Calculate paste dimensions for undo recording
        content = self.clipboard.content
        paste_h = len(content)
        paste_w = max((len(line) for line in content), default=0)

        # Record undo state for affected region
        self.undo_manager.begin_operation("Paste")
        for py in range(paste_h):
            for px in range(paste_w):
                self.undo_manager.record_cell_before(self.canvas, cx + px, cy + py)

        w, h = self.clipboard.paste_to_canvas(
            self.canvas, cx, cy, skip_spaces=skip_spaces
        )

        for py in range(paste_h):
            for px in range(paste_w):
                self.undo_manager.record_cell_after(self.canvas, cx + px, cy + py)
        self.undo_manager.end_operation()

        if w > 0:
            self.project.mark_dirty()
            return ModeResult(message=f"Pasted {w}x{h} from {self.clipboard.source}")
        return ModeResult(message="Nothing to paste")

    def _cmd_clipboard(self, args: list[str]) -> ModeResult:
        """
        Clipboard management.

        Usage:
            :clipboard          - Show clipboard info
            :clipboard clear    - Clear clipboard
            :clipboard zone     - Create clipboard zone at cursor
        """
        if not args:
            # Show clipboard info
            if self.clipboard.is_empty:
                return ModeResult(message="Clipboard is empty")
            lines = len(self.clipboard.content)
            width = (
                max(len(line) for line in self.clipboard.content)
                if self.clipboard.content
                else 0
            )
            return ModeResult(
                message=f"Clipboard: {lines} lines, max width {width} (from: {self.clipboard.source})"
            )

        subcmd = args[0].lower()

        if subcmd == "clear":
            self.clipboard.clear()
            return ModeResult(message="Clipboard cleared")

        elif subcmd == "zone":
            # Create a clipboard zone at cursor
            name = args[1] if len(args) > 1 else "CLIPBOARD"
            w = int(args[2]) if len(args) > 2 else 40
            h = int(args[3]) if len(args) > 3 else 10

            cx, cy = self.viewport.cursor.x, self.viewport.cursor.y
            try:
                zone = self.zone_manager.create_clipboard(name, cx, cy, w, h)
                # Update with current clipboard content
                self.clipboard.update_clipboard_zone(zone)
                self.project.mark_dirty()
                return ModeResult(message=f"Created clipboard zone '{name}'")
            except ValueError as e:
                return ModeResult(message=str(e))

        return ModeResult(
            message="Usage: clipboard | clipboard clear | clipboard zone [NAME W H]"
        )


def main(stdscr: "curses.window", args: argparse.Namespace) -> None:
    """Main entry point called by curses wrapper."""
    # Build server config if enabled
    server_config = None
    if args.server:
        server_config = ServerConfig(
            tcp_enabled=not args.no_tcp,
            tcp_port=args.port,
            fifo_enabled=not args.no_fifo,
            fifo_path=args.fifo or "/tmp/mygrid.fifo",
        )

    app = Application(stdscr, server_config=server_config)

    # Load file if specified
    if args.file:
        app.load_file(args.file)

    # Load layout if specified
    if args.layout:
        app.load_layout_by_name(args.layout)

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
  %(prog)s --layout dashboard   Load layout on startup
  %(prog)s --layout live-dashboard --server  Layout with API server

Keys:
  wasd/arrows  Move cursor      i  Enter edit mode
  p            Toggle pan mode  :  Enter command mode
  g/G          Toggle grid      q  Quit
  Ctrl+S       Save             F1 Help

API Server:
  When --server is enabled, external processes can send commands
  via TCP (default port 8765) or FIFO (/tmp/mygrid.fifo on Unix).
  Use mygrid-ctl to send commands from another terminal.
""",
    )
    parser.add_argument(
        "file", nargs="?", help="Project file (.json) or text file to open"
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.0")

    # Server options
    server_group = parser.add_argument_group("API Server")
    server_group.add_argument(
        "--server", action="store_true", help="Enable API server for external commands"
    )
    server_group.add_argument(
        "--port", type=int, default=8765, help="TCP port for API server (default: 8765)"
    )
    server_group.add_argument(
        "--no-tcp", action="store_true", help="Disable TCP listener"
    )
    server_group.add_argument(
        "--fifo", metavar="PATH", help="FIFO path for Unix (default: /tmp/mygrid.fifo)"
    )
    server_group.add_argument(
        "--no-fifo", action="store_true", help="Disable FIFO listener"
    )
    server_group.add_argument(
        "--headless",
        action="store_true",
        help="Run API server without curses UI (for background/daemon use)",
    )

    # Layout options
    layout_group = parser.add_argument_group("Layout")
    layout_group.add_argument(
        "--layout",
        metavar="NAME",
        help="Load a layout on startup (e.g., --layout live-dashboard)",
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
        fifo_path=args.fifo or "/tmp/mygrid.fifo",
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
                    status=(
                        "ok"
                        if not result.message or "error" not in result.message.lower()
                        else "error"
                    ),
                    message=result.message or "OK",
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
