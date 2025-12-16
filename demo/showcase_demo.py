#!/usr/bin/env python3
"""
my-grid Showcase Demo - Feature-Rich Training Video (v2)

A comprehensive demonstration of my-grid capabilities including:
- Figlet banners (standard font - readable)
- Real boxes tool integration for proper borders
- Live system data (pwd, ls, tree, top)
- Actual typing in edit mode demonstration
- Command mode demonstration
- Navigation showcase

Duration: ~240 seconds (4 minutes)

Usage:
    python demo/showcase_demo.py [duration]

    # For VHS recording:
    vhs demo/showcase-demo.tape
"""

import sys
import time
import subprocess
import curses
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import Application
from renderer import GridLineMode
from modes import Mode


def run_command(cmd):
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"(error: {e})"


def get_figlet(text, font="standard"):
    """Generate figlet banner using standard (readable) font."""
    return run_command(f"figlet -f {font} '{text}'")


def get_boxes(text, style="stone"):
    """Wrap text in boxes style - uses actual boxes command."""
    # Escape single quotes in text
    safe_text = text.replace("'", "'\\''")
    return run_command(f"echo '{safe_text}' | boxes -d {style}")


def get_boxes_multiline(lines, style="stone"):
    """Wrap multiple lines in boxes style."""
    text = '\n'.join(lines)
    safe_text = text.replace("'", "'\\''")
    return run_command(f"echo '{safe_text}' | boxes -d {style}")


class ShowcaseDemo(Application):
    """
    Feature-rich showcase demo with figlet, boxes, live data, and typing demos.
    """

    def __init__(self, stdscr):
        super().__init__(stdscr, server_config=None)

        self.demo_time = 0.0
        self.demo_segments = self._define_segments()
        self.current_segment_idx = 0

        # Smooth panning state
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_target_x = 0
        self.pan_target_y = 0
        self.pan_progress = 1.0
        self.pan_duration = 1.5

        # For typing animation
        self.typing_text = ""
        self.typing_index = 0
        self.typing_x = 0
        self.typing_y = 0
        self.typing_delay = 0.1
        self.typing_last_time = 0

    def _define_segments(self):
        """Define showcase segments - 240 seconds total."""
        segments = [
            # Opening (0-20s)
            (0, 20, self._segment_title_banner, "Grand opening with figlet"),

            # What is my-grid (20-40s)
            (20, 20, self._segment_what_is_mygrid, "What is my-grid?"),

            # Live typing demo (40-70s)
            (40, 30, self._segment_typing_demo, "Live typing demonstration"),

            # Command mode demo (70-95s)
            (70, 25, self._segment_command_demo, "Command mode demonstration"),

            # Live system data with top (95-130s)
            (95, 35, self._segment_live_data, "Live system data with top"),

            # Grid configuration (130-160s)
            (130, 30, self._segment_grid_config, "Grid configuration"),

            # Zones overview (160-200s)
            (160, 40, self._segment_zones_overview, "Zone types overview"),

            # Navigation showcase (200-230s)
            (200, 30, self._segment_navigation_showcase, "Navigation showcase"),

            # Finale (230-240s)
            (230, 10, self._segment_finale, "Grand finale"),
        ]
        return segments

    def _smooth_interpolate(self, t):
        """Smoothstep ease-in-out."""
        return t * t * (3 - 2 * t)

    def _pan_to(self, target_x, target_y, duration=1.5):
        """Initiate smooth pan to target coordinates."""
        self.pan_start_x = self.viewport.x
        self.pan_start_y = self.viewport.y
        self.pan_target_x = target_x
        self.pan_target_y = target_y
        self.pan_progress = 0.0
        self.pan_duration = duration

    def _update_pan(self, dt):
        """Update smooth panning animation."""
        if self.pan_progress >= 1.0:
            return

        self.pan_progress += dt / self.pan_duration
        if self.pan_progress > 1.0:
            self.pan_progress = 1.0

        t = self._smooth_interpolate(self.pan_progress)
        self.viewport.x = int(self.pan_start_x + (self.pan_target_x - self.pan_start_x) * t)
        self.viewport.y = int(self.pan_start_y + (self.pan_target_y - self.pan_start_y) * t)

    def _execute_command(self, command_str):
        """Execute a my-grid command string."""
        result = self.state_machine._execute_command(command_str)
        if result.message:
            self._show_message(result.message)

    def _draw_multiline(self, x, y, text):
        """Draw multiline text at position."""
        for i, line in enumerate(text.split('\n')):
            if line:  # Draw even "empty" lines with spaces for boxes
                self._execute_command(f"goto {x} {y + i}")
                # Escape any problematic characters
                safe_line = line.replace('"', "'")
                self._execute_command(f"text {safe_line}")

    def _draw_boxed_content(self, x, y, lines, style="stone"):
        """Draw content with real boxes borders."""
        boxed = get_boxes_multiline(lines, style)
        self._draw_multiline(x, y, boxed)

    def _simulate_typing(self, x, y, text, current_time):
        """Simulate typing one character at a time. Returns True when done."""
        if current_time - self.typing_last_time >= self.typing_delay:
            if self.typing_index < len(text):
                char = text[self.typing_index]
                # Actually draw the character on canvas
                self.canvas.set_cell(x + self.typing_index, y, char)
                self.typing_index += 1
                self.typing_last_time = current_time
                return False
        return self.typing_index >= len(text)

    # ========== SEGMENT ACTIONS ==========

    def _segment_title_banner(self, segment_time, dt):
        """Grand opening with readable figlet banner."""
        if segment_time < 0.5:
            self._pan_to(0, 0, duration=0.5)

            # Big figlet title - using standard font (readable!)
            banner = get_figlet("my-grid", "standard")
            self._draw_multiline(5, 2, banner)

        if 2.0 < segment_time < 2.5:
            # Use real boxes for the tagline
            tagline_box = get_boxes("Spatial Workspace  *  ASCII Canvas  *  Vim Navigation", "ansi-rounded")
            self._draw_multiline(5, 10, tagline_box)

        if 5.0 < segment_time < 5.5:
            # Feature list with real boxes
            features = [
                "THIS DEMO WILL SHOW YOU:",
                "",
                "  * Vim-style modes (NAV, EDIT, PAN, COMMAND)",
                "  * Live typing and drawing on the canvas",
                "  * Real-time system data (top, ls, pwd)",
                "  * Grid customization options",
                "  * Named zones for organization",
            ]
            boxed = get_boxes_multiline(features, "stone")
            self._draw_multiline(5, 15, boxed)

        if 10.0 < segment_time < 10.5:
            self.renderer.grid.show_major_lines = True
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            self._show_message("Welcome to my-grid! Let's explore...")

        # Pan to show canvas space
        if 14.0 < segment_time < 14.5:
            self._pan_to(30, 0, duration=2.0)

        if 17.0 < segment_time < 17.5:
            self._pan_to(0, 0, duration=1.5)

    def _segment_what_is_mygrid(self, segment_time, dt):
        """Explain what my-grid is with real boxes."""
        if segment_time < 0.5:
            self._pan_to(0, 35, duration=1.0)

            # Section header
            header = get_figlet("ABOUT", "standard")
            self._draw_multiline(5, 38, header)

        if 3.0 < segment_time < 3.5:
            about_text = [
                "my-grid is a terminal-based ASCII canvas editor",
                "",
                "Think of it as:",
                "  - Miro/Lucidchart for the terminal",
                "  - Infinite whiteboard in your shell",
                "  - Spatial memory workspace",
            ]
            boxed = get_boxes_multiline(about_text, "ansi-double")
            self._draw_multiline(5, 47, boxed)

        if 8.0 < segment_time < 8.5:
            use_cases = [
                "USE CASES:",
                "",
                "  -> System architecture diagrams",
                "  -> Sprint planning boards",
                "  -> Mind maps and brainstorming",
                "  -> Live dashboards",
            ]
            boxed = get_boxes_multiline(use_cases, "stone")
            self._draw_multiline(5, 60, boxed)

        if 14.0 < segment_time < 14.5:
            self._execute_command("goto 5 75")
            self._execute_command("text TIP: Projects save as JSON - perfect for git!")

    def _segment_typing_demo(self, segment_time, dt):
        """Demonstrate actual typing in edit mode."""
        if segment_time < 0.5:
            self._pan_to(0, 85, duration=1.0)

            header = get_figlet("EDIT", "standard")
            self._draw_multiline(5, 88, header)

        if 2.0 < segment_time < 2.5:
            explain = [
                "EDIT MODE - Press 'i' to enter",
                "",
                "Type directly onto the canvas!",
                "Watch as we type in real-time...",
            ]
            boxed = get_boxes_multiline(explain, "stone")
            self._draw_multiline(5, 96, boxed)

        # Switch to edit mode and show it
        if 5.0 < segment_time < 5.5:
            self.state_machine.mode = Mode.EDIT
            self._show_message("EDIT MODE - Now typing on canvas...")
            self.typing_index = 0
            self.typing_last_time = time.time()

        # Simulate typing "Hello, World!"
        if 6.0 < segment_time < 12.0:
            text = "Hello, World! This is my-grid!"
            self.viewport.cursor.x = 10
            self.viewport.cursor.y = 108
            current_time = time.time()
            if self.typing_index < len(text):
                if current_time - self.typing_last_time >= 0.15:
                    char = text[self.typing_index]
                    self.canvas.set_cell(10 + self.typing_index, 108, char)
                    self.viewport.cursor.x = 10 + self.typing_index + 1
                    self.typing_index += 1
                    self.typing_last_time = current_time

        # Draw a box manually character by character
        if 14.0 < segment_time < 14.5:
            self._execute_command("goto 10 112")
            self._execute_command("text Now let's draw a box...")
            self.typing_index = 0

        if 16.0 < segment_time < 22.0:
            # Draw box outline step by step
            box_chars = "+---------+"
            if segment_time < 17.5 and self.typing_index < len(box_chars):
                current_time = time.time()
                if current_time - self.typing_last_time >= 0.12:
                    self.canvas.set_cell(10 + self.typing_index, 114, box_chars[self.typing_index])
                    self.typing_index += 1
                    self.typing_last_time = current_time
            elif 17.5 < segment_time < 18.5:
                # Draw sides
                self.canvas.set_cell(10, 115, '|')
                self.canvas.set_cell(20, 115, '|')
                self.canvas.set_cell(10, 116, '|')
                self.canvas.set_cell(20, 116, '|')
            elif 18.5 < segment_time < 20.0:
                # Draw bottom
                for i, c in enumerate("+---------+"):
                    self.canvas.set_cell(10 + i, 117, c)
            elif 20.0 < segment_time < 22.0:
                # Fill with text
                for i, c in enumerate("  MY BOX  "):
                    self.canvas.set_cell(10 + i, 115, c)

        if 24.0 < segment_time < 24.5:
            self.state_machine.mode = Mode.NAV
            self._show_message("Press ESC to return to NAV mode")

        if 27.0 < segment_time < 27.5:
            self._execute_command("goto 10 120")
            self._execute_command("text ESC returns you to navigation mode!")

    def _segment_command_demo(self, segment_time, dt):
        """Demonstrate command mode."""
        if segment_time < 0.5:
            self._pan_to(0, 130, duration=1.0)

            header = get_figlet("COMMANDS", "standard")
            self._draw_multiline(5, 133, header)

        if 2.0 < segment_time < 2.5:
            explain = [
                "COMMAND MODE - Press ':' to enter",
                "",
                "Type commands like vim!",
            ]
            boxed = get_boxes_multiline(explain, "stone")
            self._draw_multiline(5, 142, boxed)

        # Show command examples
        if 5.0 < segment_time < 5.5:
            self._show_message("Typing :rect 25 5 ...")

        if 6.0 < segment_time < 6.5:
            self._execute_command("goto 50 145")
            self._execute_command("rect 25 5")
            self._show_message("Drew a 25x5 rectangle!")

        if 9.0 < segment_time < 9.5:
            self._show_message("Typing :text Hello ...")

        if 10.0 < segment_time < 10.5:
            self._execute_command("goto 55 147")
            self._execute_command("text Hello!")
            self._show_message("Wrote text inside the box!")

        if 13.0 < segment_time < 13.5:
            self._show_message("Typing :goto 100 150 ...")

        if 14.0 < segment_time < 14.5:
            self._execute_command("goto 100 150")
            self._show_message("Jumped to coordinates (100, 150)!")

        if 16.0 < segment_time < 16.5:
            self._execute_command("rect 30 7")

        if 17.0 < segment_time < 17.5:
            self._execute_command("goto 105 152")
            self._execute_command("text Command Mode")
            self._execute_command("goto 105 154")
            self._execute_command("text :w  = save")
            self._execute_command("goto 105 155")
            self._execute_command("text :q  = quit")

        if 20.0 < segment_time < 20.5:
            cmd_list = [
                "COMMON COMMANDS:",
                "",
                ":rect W H   - Draw rectangle",
                ":text MSG   - Write text",
                ":goto X Y   - Jump to coords",
                ":line X Y   - Draw line",
                ":w          - Save project",
                ":q          - Quit",
            ]
            boxed = get_boxes_multiline(cmd_list, "ansi-rounded")
            self._draw_multiline(5, 160, boxed)

    def _segment_live_data(self, segment_time, dt):
        """Show live system data including top."""
        if segment_time < 0.5:
            self._pan_to(0, 185, duration=1.0)

            header = get_figlet("LIVE DATA", "standard")
            self._draw_multiline(5, 188, header)

        if 2.0 < segment_time < 2.5:
            explain = [
                "Zones can show LIVE system data!",
                "PIPE zones: one-shot output",
                "WATCH zones: auto-refresh",
            ]
            boxed = get_boxes_multiline(explain, "stone")
            self._draw_multiline(5, 198, boxed)

        # Show pwd
        if 5.0 < segment_time < 5.5:
            pwd = run_command("pwd")
            pwd_box = get_boxes(f"PWD: {pwd}", "ansi-rounded")
            self._draw_multiline(5, 210, pwd_box)

        # Show hostname/user
        if 8.0 < segment_time < 8.5:
            user = run_command("whoami")
            host = run_command("hostname")
            info_box = get_boxes(f"User: {user}  |  Host: {host}", "stone")
            self._draw_multiline(5, 216, info_box)

        # Show date/uptime
        if 11.0 < segment_time < 11.5:
            date_str = run_command("date '+%Y-%m-%d %H:%M:%S'")
            uptime = run_command("uptime -p 2>/dev/null || uptime | cut -d, -f1")[:50]
            time_box = get_boxes(f"Date: {date_str}\nUptime: {uptime}", "ansi-double")
            self._draw_multiline(5, 222, time_box)

        # Show TOP output - this is the key addition!
        if 15.0 < segment_time < 15.5:
            self._execute_command("goto 5 232")
            self._execute_command("text === LIVE TOP OUTPUT ===")

        if 16.0 < segment_time < 16.5:
            # Get top output (batch mode, 1 iteration)
            top_output = run_command("top -b -n 1 | head -12")
            lines = top_output.split('\n')

            self._execute_command("goto 5 234")
            self._execute_command("text +--[ top -b -n 1 ]----------------------------------------+")

            for i, line in enumerate(lines[:10]):
                safe_line = line[:55].replace('"', "'").replace('`', "'")
                self._execute_command(f"goto 5 {235 + i}")
                self._execute_command(f"text | {safe_line:<55}|")

            self._execute_command(f"goto 5 {235 + 10}")
            self._execute_command("text +----------------------------------------------------------+")

        # Refresh top (simulate watch zone)
        if 22.0 < segment_time < 22.5:
            self._show_message("WATCH zones auto-refresh this data!")
            # Get fresh top output
            top_output = run_command("top -b -n 1 | head -12")
            lines = top_output.split('\n')

            for i, line in enumerate(lines[:10]):
                safe_line = line[:55].replace('"', "'").replace('`', "'")
                self._execute_command(f"goto 5 {235 + i}")
                self._execute_command(f"text | {safe_line:<55}|")

        # Another refresh
        if 28.0 < segment_time < 28.5:
            top_output = run_command("top -b -n 1 | head -12")
            lines = top_output.split('\n')

            for i, line in enumerate(lines[:10]):
                safe_line = line[:55].replace('"', "'").replace('`', "'")
                self._execute_command(f"goto 5 {235 + i}")
                self._execute_command(f"text | {safe_line:<55}|")

            self._show_message("Data updates in real-time!")

    def _segment_grid_config(self, segment_time, dt):
        """Show grid configuration options."""
        if segment_time < 0.5:
            self._pan_to(0, 260, duration=1.0)

            header = get_figlet("GRID", "standard")
            self._draw_multiline(5, 263, header)

        if 2.0 < segment_time < 2.5:
            explain = [
                "The grid helps alignment!",
                "Three modes available:",
            ]
            boxed = get_boxes_multiline(explain, "stone")
            self._draw_multiline(5, 272, boxed)

        # LINES mode
        if 5.0 < segment_time < 5.5:
            self.renderer.grid.line_mode = GridLineMode.LINES
            self.renderer.grid.show_minor_lines = True
            self._show_message("LINES mode - Professional box-drawing")

        if 6.0 < segment_time < 6.5:
            lines_box = get_boxes("LINES: Full grid lines\n:grid lines", "ansi-double")
            self._draw_multiline(5, 282, lines_box)

        # DOTS mode
        if 10.0 < segment_time < 10.5:
            self.renderer.grid.line_mode = GridLineMode.DOTS
            self._show_message("DOTS mode - Subtle dotted pattern")

        if 11.0 < segment_time < 11.5:
            dots_box = get_boxes("DOTS: Subtle markers\n:grid dots", "stone")
            self._draw_multiline(5, 290, dots_box)

        # MARKERS mode
        if 15.0 < segment_time < 15.5:
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            self._show_message("MARKERS mode - Just intersections")

        if 16.0 < segment_time < 16.5:
            markers_box = get_boxes("MARKERS: Intersections only\n:grid markers  or press 'g'", "ansi-rounded")
            self._draw_multiline(5, 298, markers_box)

        # Grid spacing
        if 20.0 < segment_time < 20.5:
            self.renderer.grid.major_interval = 20
            self.renderer.grid.minor_interval = 5
            self._show_message("Grid spacing: 20 (major) / 5 (minor)")

        if 22.0 < segment_time < 22.5:
            spacing_box = get_boxes(":grid interval 20 5\nWider spacing for big diagrams!", "stone")
            self._draw_multiline(5, 308, spacing_box)

        if 26.0 < segment_time < 26.5:
            self.renderer.grid.major_interval = 10
            self.renderer.grid.minor_interval = 5
            self.renderer.grid.line_mode = GridLineMode.LINES
            self.renderer.grid.show_minor_lines = False

    def _segment_zones_overview(self, segment_time, dt):
        """Overview of zone types."""
        if segment_time < 0.5:
            self._pan_to(0, 330, duration=1.0)

            header = get_figlet("ZONES", "standard")
            self._draw_multiline(5, 333, header)

        if 2.0 < segment_time < 2.5:
            intro = ["Zones are named regions!", "Jump instantly between them."]
            boxed = get_boxes_multiline(intro, "stone")
            self._draw_multiline(5, 342, boxed)

        # STATIC
        if 5.0 < segment_time < 5.5:
            static_info = [
                "STATIC Zone",
                "",
                "Basic named region",
                ":zone create NOTES 0 0 60 20",
            ]
            boxed = get_boxes_multiline(static_info, "ansi-rounded")
            self._draw_multiline(5, 352, boxed)

        # PIPE
        if 10.0 < segment_time < 10.5:
            pipe_info = [
                "PIPE Zone",
                "",
                "One-shot command output",
                ":zone pipe INFO 60 15 'uname -a'",
            ]
            boxed = get_boxes_multiline(pipe_info, "stone")
            self._draw_multiline(5, 364, pipe_info)

        # WATCH
        if 15.0 < segment_time < 15.5:
            watch_info = [
                "WATCH Zone",
                "",
                "Auto-refresh at intervals",
                ":zone watch TIME 30 5 1s 'date'",
            ]
            boxed = get_boxes_multiline(watch_info, "ansi-double")
            self._draw_multiline(5, 376, boxed)

        # PTY
        if 20.0 < segment_time < 20.5:
            pty_info = [
                "PTY Zone (Unix)",
                "",
                "Live embedded terminal!",
                ":zone pty SHELL 80 24",
                "Enter to focus, Esc to unfocus",
            ]
            boxed = get_boxes_multiline(pty_info, "ansi-rounded")
            self._draw_multiline(5, 388, boxed)

        # FIFO/Socket
        if 28.0 < segment_time < 28.5:
            external_info = [
                "FIFO & Socket Zones",
                "",
                "External tool integration!",
                ":zone fifo EXT 60 20 /tmp/pipe",
                ":zone socket API 60 20 9999",
            ]
            boxed = get_boxes_multiline(external_info, "stone")
            self._draw_multiline(5, 402, boxed)

        if 35.0 < segment_time < 35.5:
            self._execute_command("goto 5 418")
            self._execute_command("text Link zones to bookmarks: :zone link NOTES n")

    def _segment_navigation_showcase(self, segment_time, dt):
        """Show off navigation with actual movement."""
        if segment_time < 0.5:
            self._pan_to(0, 0, duration=2.0)
            self._show_message("Let's navigate the canvas we've created!")

        # Jump around the canvas
        if 4.0 < segment_time < 4.5:
            self._show_message("Jumping to title area...")
            self._pan_to(0, 0, duration=1.5)

        if 7.0 < segment_time < 7.5:
            self._show_message("Jumping to typing demo...")
            self._pan_to(0, 85, duration=1.5)

        if 10.0 < segment_time < 10.5:
            self._show_message("Jumping to live data...")
            self._pan_to(0, 185, duration=1.5)

        if 13.0 < segment_time < 13.5:
            self._show_message("Jumping to zones...")
            self._pan_to(0, 330, duration=1.5)

        if 16.0 < segment_time < 16.5:
            self._show_message("Back to grid config...")
            self._pan_to(0, 260, duration=1.5)

        if 19.0 < segment_time < 19.5:
            self._show_message("This is SPATIAL NAVIGATION!")
            self._pan_to(0, 0, duration=2.0)

        # Show bookmark setting
        if 23.0 < segment_time < 23.5:
            self._execute_command("goto 80 5")
            self._execute_command("text Press 'm' then 'a' to set bookmark 'a'")
            self._execute_command("goto 80 7")
            self._execute_command("text Press apostrophe then 'a' to jump back!")

        if 27.0 < segment_time < 27.5:
            nav_box = get_boxes("Spatial memory > hierarchical navigation!\nRemember WHERE things are, not HOW to find them.", "ansi-double")
            self._draw_multiline(80, 10, nav_box)

    def _segment_finale(self, segment_time, dt):
        """Grand finale."""
        if segment_time < 0.5:
            self._pan_to(0, 430, duration=1.0)

            header = get_figlet("THE END", "standard")
            self._draw_multiline(20, 433, header)

        if 2.0 < segment_time < 2.5:
            final_box = get_boxes_multiline([
                "github.com/jcaldwell-labs/my-grid",
                "",
                "Inspired by Jef Raskin's",
                "'The Humane Interface'",
                "",
                "Thanks for watching!",
            ], "ansi-double")
            self._draw_multiline(15, 445, final_box)

        if 6.0 < segment_time < 6.5:
            self._show_message("Try my-grid today! Press F1 for help.")

    # ========== MAIN DEMO LOOP ==========

    def run_demo(self, total_duration=240):
        """
        Run showcase demo with visual curses UI.

        VHS records this - single while loop for freeze prevention.
        """
        FRAME_DELAY = 0.05  # 20 FPS

        start_time = time.time()
        last_time = start_time
        current_segment_idx = 0
        segment_start_time = start_time

        try:
            while True:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                elapsed = current_time - start_time

                if elapsed >= total_duration:
                    break

                # Find current segment
                new_segment_idx = 0
                for i, (boundary, duration, action_fn, desc) in enumerate(self.demo_segments):
                    if elapsed >= boundary:
                        new_segment_idx = i

                # Switch segment if changed
                if new_segment_idx != current_segment_idx:
                    current_segment_idx = new_segment_idx
                    segment_start_time = current_time

                # Execute segment action
                _, duration, action_fn, desc = self.demo_segments[current_segment_idx]
                segment_time = current_time - segment_start_time
                action_fn(segment_time, dt)

                # Update smooth panning
                self._update_pan(dt)

                # Render frame
                status = self._get_status_line()
                self.renderer.render(self.canvas, self.viewport, status)

                time.sleep(FRAME_DELAY)

        finally:
            self._show_message("Demo complete!")
            status = self._get_status_line()
            self.renderer.render(self.canvas, self.viewport, status)
            time.sleep(3)


def run_demo(duration=240):
    """Entry point for demo mode."""
    def _curses_main(stdscr):
        demo = ShowcaseDemo(stdscr)
        demo.run_demo(duration)

    curses.wrapper(_curses_main)


if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    print(f"Running showcase demo for {duration} seconds (4 minutes)...")
    print("")
    print("This demo includes:")
    print("  - Readable figlet banners (standard font)")
    print("  - Real boxes tool borders")
    print("  - Live typing demonstration")
    print("  - Command mode demo")
    print("  - Live system data with TOP output")
    print("  - Grid configuration")
    print("  - Zone types overview")
    print("  - Navigation showcase")
    print("")
    run_demo(duration)
