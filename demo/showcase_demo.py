#!/usr/bin/env python3
"""
my-grid Showcase Demo v3 - Feature-Rich Training Video

Fixed issues:
- Use 'banner' figlet font (cleanest, most readable)
- Actually call /usr/bin/boxes for all borders
- Fix mode setter (use set_mode() not direct assignment)
- Show live top output
- Demonstrate typing and commands

Duration: ~240 seconds (4 minutes)

Usage:
    python demo/showcase_demo.py [duration]
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


def run_cmd(cmd):
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        return result.stdout.rstrip('\n')
    except Exception as e:
        return f"(error: {e})"


def figlet_banner(text):
    """Generate figlet banner using banner font (cleanest)."""
    return run_cmd(f"figlet -f banner '{text}'")


def boxes_wrap(content, style="stone"):
    """Wrap content with /usr/bin/boxes - the REAL boxes command."""
    # Write to temp file to avoid shell escaping issues
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        tmpfile = f.name
    result = run_cmd(f"cat {tmpfile} | /usr/bin/boxes -d {style}")
    run_cmd(f"rm {tmpfile}")
    return result


class ShowcaseDemo(Application):
    """Feature-rich showcase demo with proper boxes and figlet."""

    def __init__(self, stdscr):
        super().__init__(stdscr, server_config=None)
        self.demo_segments = self._define_segments()
        self.current_segment_idx = 0

        # Panning
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_target_x = 0
        self.pan_target_y = 0
        self.pan_progress = 1.0
        self.pan_duration = 1.5

        # Typing animation
        self.typing_index = 0
        self.typing_last_time = 0

    def _define_segments(self):
        """240 second demo structure."""
        return [
            (0, 25, self._seg_title, "Title"),
            (25, 25, self._seg_about, "About"),
            (50, 30, self._seg_typing, "Typing demo"),
            (80, 25, self._seg_commands, "Commands"),
            (105, 35, self._seg_live_data, "Live data"),
            (140, 30, self._seg_grid, "Grid config"),
            (170, 40, self._seg_zones, "Zones"),
            (210, 20, self._seg_nav, "Navigation"),
            (230, 10, self._seg_finale, "Finale"),
        ]

    def _smooth(self, t):
        return t * t * (3 - 2 * t)

    def _pan_to(self, x, y, dur=1.5):
        self.pan_start_x = self.viewport.x
        self.pan_start_y = self.viewport.y
        self.pan_target_x = x
        self.pan_target_y = y
        self.pan_progress = 0.0
        self.pan_duration = dur

    def _update_pan(self, dt):
        if self.pan_progress >= 1.0:
            return
        self.pan_progress += dt / self.pan_duration
        if self.pan_progress > 1.0:
            self.pan_progress = 1.0
        t = self._smooth(self.pan_progress)
        self.viewport.x = int(self.pan_start_x + (self.pan_target_x - self.pan_start_x) * t)
        self.viewport.y = int(self.pan_start_y + (self.pan_target_y - self.pan_start_y) * t)

    def _cmd(self, s):
        result = self.state_machine._execute_command(s)
        if result.message:
            self._show_message(result.message)

    def _draw_text(self, x, y, text):
        """Draw multiline text."""
        for i, line in enumerate(text.split('\n')):
            if line:
                self._cmd(f"goto {x} {y + i}")
                safe = line.replace('"', "'")
                self._cmd(f"text {safe}")

    # ========== SEGMENTS ==========

    def _seg_title(self, t, dt):
        """Title with banner figlet."""
        if t < 0.5:
            self._pan_to(0, 0, 0.5)
            # Big readable banner
            banner = figlet_banner("my-grid")
            self._draw_text(5, 2, banner)

        if 3.0 < t < 3.5:
            # Use real boxes for tagline
            box = boxes_wrap("Spatial Workspace  -  ASCII Canvas  -  Vim Navigation", "ansi-rounded")
            self._draw_text(5, 12, box)

        if 6.0 < t < 6.5:
            content = """THIS DEMO SHOWS:

  * Vim-style modes (NAV, EDIT, PAN, COMMAND)
  * Live typing on the canvas
  * Real-time system data (top, ls, pwd)
  * Grid customization
  * Named zones"""
            box = boxes_wrap(content, "stone")
            self._draw_text(5, 17, box)

        if 12.0 < t < 12.5:
            self.renderer.grid.show_major_lines = True
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            self._show_message("Welcome to my-grid!")

        if 18.0 < t < 18.5:
            self._pan_to(40, 0, 2.0)

        if 22.0 < t < 22.5:
            self._pan_to(0, 0, 1.5)

    def _seg_about(self, t, dt):
        """What is my-grid."""
        if t < 0.5:
            self._pan_to(0, 40, 1.0)
            banner = figlet_banner("ABOUT")
            self._draw_text(5, 43, banner)

        if 3.0 < t < 3.5:
            content = """my-grid is a terminal-based ASCII canvas editor

Think of it as:
  - Miro/Lucidchart for the terminal
  - Infinite whiteboard in your shell
  - Spatial memory workspace"""
            box = boxes_wrap(content, "ansi-double")
            self._draw_text(5, 52, box)

        if 10.0 < t < 10.5:
            content = """USE CASES:

  -> System architecture diagrams
  -> Sprint planning boards
  -> Mind maps and brainstorming
  -> Live dashboards"""
            box = boxes_wrap(content, "stone")
            self._draw_text(5, 65, box)

        if 18.0 < t < 18.5:
            self._cmd("goto 5 80")
            self._cmd("text TIP: Projects save as JSON - perfect for git!")

    def _seg_typing(self, t, dt):
        """Live typing demonstration."""
        if t < 0.5:
            self._pan_to(0, 90, 1.0)
            banner = figlet_banner("EDIT")
            self._draw_text(5, 93, banner)

        if 2.0 < t < 2.5:
            content = """EDIT MODE - Press 'i' to enter

Type directly onto the canvas!
Watch as we type in real-time..."""
            box = boxes_wrap(content, "stone")
            self._draw_text(5, 102, box)

        # Enter edit mode using set_mode (not direct assignment!)
        if 5.0 < t < 5.5:
            self.state_machine.set_mode(Mode.EDIT)
            self._show_message("EDIT MODE - Now typing on canvas...")
            self.typing_index = 0
            self.typing_last_time = time.time()

        # Simulate typing
        if 6.0 < t < 14.0:
            text = "Hello, World! This is my-grid!"
            self.viewport.cursor.x = 10
            self.viewport.cursor.y = 115
            now = time.time()
            if self.typing_index < len(text):
                if now - self.typing_last_time >= 0.12:
                    char = text[self.typing_index]
                    self.canvas.set_cell(10 + self.typing_index, 115, char)
                    self.viewport.cursor.x = 10 + self.typing_index + 1
                    self.typing_index += 1
                    self.typing_last_time = now

        if 16.0 < t < 16.5:
            self._cmd("goto 10 118")
            self._cmd("text Now drawing a box character by character...")
            self.typing_index = 0
            self.typing_last_time = time.time()

        # Draw box character by character
        if 18.0 < t < 24.0:
            box_top = "+-----------+"
            if t < 20.0 and self.typing_index < len(box_top):
                now = time.time()
                if now - self.typing_last_time >= 0.1:
                    self.canvas.set_cell(10 + self.typing_index, 120, box_top[self.typing_index])
                    self.typing_index += 1
                    self.typing_last_time = now
            elif 20.0 < t < 21.0:
                self.canvas.set_cell(10, 121, '|')
                self.canvas.set_cell(22, 121, '|')
                self.canvas.set_cell(10, 122, '|')
                self.canvas.set_cell(22, 122, '|')
            elif 21.0 < t < 22.5:
                for i, c in enumerate("+-----------+"):
                    self.canvas.set_cell(10 + i, 123, c)
            elif 22.5 < t < 24.0:
                for i, c in enumerate("  MY BOX!   "):
                    self.canvas.set_cell(10 + i, 121, c)

        if 26.0 < t < 26.5:
            self.state_machine.set_mode(Mode.NAV)
            self._show_message("ESC returns to NAV mode")

    def _seg_commands(self, t, dt):
        """Command mode demonstration."""
        if t < 0.5:
            self._pan_to(0, 135, 1.0)
            banner = figlet_banner("COMMANDS")
            self._draw_text(5, 138, banner)

        if 2.0 < t < 2.5:
            content = """COMMAND MODE - Press ':' to enter

Type commands like vim!"""
            box = boxes_wrap(content, "stone")
            self._draw_text(5, 148, box)

        if 5.0 < t < 5.5:
            self._show_message("Typing :rect 25 5 ...")

        if 6.0 < t < 6.5:
            self._cmd("goto 50 155")
            self._cmd("rect 25 5")
            self._show_message("Drew a 25x5 rectangle!")

        if 9.0 < t < 9.5:
            self._show_message("Typing :text Hello ...")

        if 10.0 < t < 10.5:
            self._cmd("goto 55 157")
            self._cmd("text Hello!")

        if 13.0 < t < 13.5:
            self._show_message("Typing :goto 100 160 ...")

        if 14.0 < t < 14.5:
            self._cmd("goto 100 160")
            self._cmd("rect 30 7")

        if 16.0 < t < 16.5:
            self._cmd("goto 105 162")
            self._cmd("text Command Mode")
            self._cmd("goto 105 164")
            self._cmd("text :w = save  :q = quit")

        if 19.0 < t < 19.5:
            content = """COMMON COMMANDS:

:rect W H   - Draw rectangle
:text MSG   - Write text
:goto X Y   - Jump to coords
:w / :q     - Save / Quit"""
            box = boxes_wrap(content, "ansi-rounded")
            self._draw_text(5, 170, box)

    def _seg_live_data(self, t, dt):
        """Live system data with top."""
        if t < 0.5:
            self._pan_to(0, 195, 1.0)
            banner = figlet_banner("LIVE DATA")
            self._draw_text(5, 198, banner)

        if 2.0 < t < 2.5:
            content = """Zones can show LIVE system data!
PIPE zones: one-shot output
WATCH zones: auto-refresh"""
            box = boxes_wrap(content, "stone")
            self._draw_text(5, 210, box)

        # PWD
        if 5.0 < t < 5.5:
            pwd = run_cmd("pwd")
            box = boxes_wrap(f"PWD: {pwd}", "ansi-rounded")
            self._draw_text(5, 222, box)

        # User/host
        if 8.0 < t < 8.5:
            user = run_cmd("whoami")
            host = run_cmd("hostname")
            box = boxes_wrap(f"User: {user}  |  Host: {host}", "stone")
            self._draw_text(5, 228, box)

        # Date
        if 11.0 < t < 11.5:
            date = run_cmd("date '+%Y-%m-%d %H:%M:%S'")
            box = boxes_wrap(f"Date: {date}", "ansi-double")
            self._draw_text(5, 234, box)

        # TOP output
        if 15.0 < t < 15.5:
            self._cmd("goto 5 242")
            self._cmd("text === LIVE TOP OUTPUT ===")

        if 16.0 < t < 16.5:
            top = run_cmd("top -b -n 1 | head -10")
            box = boxes_wrap(top, "stone")
            self._draw_text(5, 244, box)

        # Refresh top
        if 23.0 < t < 23.5:
            self._show_message("WATCH zones auto-refresh!")
            top = run_cmd("top -b -n 1 | head -10")
            box = boxes_wrap(top, "stone")
            self._draw_text(5, 244, box)

        # Another refresh
        if 30.0 < t < 30.5:
            top = run_cmd("top -b -n 1 | head -10")
            box = boxes_wrap(top, "stone")
            self._draw_text(5, 244, box)
            self._show_message("Data updates in real-time!")

    def _seg_grid(self, t, dt):
        """Grid configuration."""
        if t < 0.5:
            self._pan_to(0, 280, 1.0)
            banner = figlet_banner("GRID")
            self._draw_text(5, 283, banner)

        if 2.0 < t < 2.5:
            content = """The grid helps alignment!
Three modes available:"""
            box = boxes_wrap(content, "stone")
            self._draw_text(5, 293, box)

        # LINES
        if 5.0 < t < 5.5:
            self.renderer.grid.line_mode = GridLineMode.LINES
            self.renderer.grid.show_minor_lines = True
            self._show_message("LINES mode - Full grid")

        if 6.0 < t < 6.5:
            box = boxes_wrap("LINES: Full grid lines\n:grid lines", "ansi-double")
            self._draw_text(5, 302, box)

        # DOTS
        if 10.0 < t < 10.5:
            self.renderer.grid.line_mode = GridLineMode.DOTS
            self._show_message("DOTS mode - Subtle")

        if 11.0 < t < 11.5:
            box = boxes_wrap("DOTS: Subtle markers\n:grid dots", "stone")
            self._draw_text(5, 310, box)

        # MARKERS
        if 15.0 < t < 15.5:
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            self._show_message("MARKERS mode - Intersections only")

        if 16.0 < t < 16.5:
            box = boxes_wrap("MARKERS: Intersections only\n:grid markers", "ansi-rounded")
            self._draw_text(5, 318, box)

        # Spacing
        if 20.0 < t < 20.5:
            self.renderer.grid.major_interval = 20
            self.renderer.grid.minor_interval = 5
            self._show_message("Grid spacing: 20 major / 5 minor")

        if 22.0 < t < 22.5:
            box = boxes_wrap(":grid interval 20 5\nWider spacing for big diagrams!", "stone")
            self._draw_text(5, 326, box)

        if 26.0 < t < 26.5:
            self.renderer.grid.major_interval = 10
            self.renderer.grid.line_mode = GridLineMode.LINES
            self.renderer.grid.show_minor_lines = False

    def _seg_zones(self, t, dt):
        """Zone types."""
        if t < 0.5:
            self._pan_to(0, 345, 1.0)
            banner = figlet_banner("ZONES")
            self._draw_text(5, 348, banner)

        if 2.0 < t < 2.5:
            box = boxes_wrap("Zones are named regions!\nJump instantly between them.", "stone")
            self._draw_text(5, 360, box)

        # STATIC
        if 6.0 < t < 6.5:
            content = """STATIC Zone

Basic named region
:zone create NOTES 0 0 60 20"""
            box = boxes_wrap(content, "ansi-rounded")
            self._draw_text(5, 370, box)

        # PIPE
        if 12.0 < t < 12.5:
            content = """PIPE Zone

One-shot command output
:zone pipe INFO 60 15 'uname -a'"""
            box = boxes_wrap(content, "stone")
            self._draw_text(5, 382, box)

        # WATCH
        if 18.0 < t < 18.5:
            content = """WATCH Zone

Auto-refresh at intervals
:zone watch TIME 30 5 1s 'date'"""
            box = boxes_wrap(content, "ansi-double")
            self._draw_text(5, 394, box)

        # PTY
        if 24.0 < t < 24.5:
            content = """PTY Zone (Unix)

Live embedded terminal!
:zone pty SHELL 80 24"""
            box = boxes_wrap(content, "ansi-rounded")
            self._draw_text(5, 406, box)

        # FIFO/Socket
        if 32.0 < t < 32.5:
            content = """FIFO & Socket Zones

External tool integration!
:zone fifo EXT 60 20 /tmp/pipe
:zone socket API 60 20 9999"""
            box = boxes_wrap(content, "stone")
            self._draw_text(5, 420, box)

    def _seg_nav(self, t, dt):
        """Navigation showcase."""
        if t < 0.5:
            self._pan_to(0, 0, 2.0)
            self._show_message("Let's navigate the canvas!")

        if 4.0 < t < 4.5:
            self._show_message("Jumping to title...")
            self._pan_to(0, 0, 1.5)

        if 7.0 < t < 7.5:
            self._show_message("Jumping to typing demo...")
            self._pan_to(0, 90, 1.5)

        if 10.0 < t < 10.5:
            self._show_message("Jumping to live data...")
            self._pan_to(0, 195, 1.5)

        if 13.0 < t < 13.5:
            self._show_message("Jumping to zones...")
            self._pan_to(0, 345, 1.5)

        if 16.0 < t < 16.5:
            self._show_message("SPATIAL NAVIGATION!")
            self._pan_to(0, 0, 2.0)

    def _seg_finale(self, t, dt):
        """Grand finale."""
        if t < 0.5:
            self._pan_to(0, 450, 1.0)
            banner = figlet_banner("THE END")
            self._draw_text(20, 453, banner)

        if 2.0 < t < 2.5:
            content = """github.com/jcaldwell-labs/my-grid

Inspired by Jef Raskin's
'The Humane Interface'

Thanks for watching!"""
            box = boxes_wrap(content, "ansi-double")
            self._draw_text(15, 465, box)

        if 6.0 < t < 6.5:
            self._show_message("Try my-grid today! Press F1 for help.")

    # ========== MAIN LOOP ==========

    def run_demo(self, duration=240):
        FRAME_DELAY = 0.05
        start = time.time()
        last = start
        seg_idx = 0
        seg_start = start

        try:
            while True:
                now = time.time()
                dt = now - last
                last = now
                elapsed = now - start

                if elapsed >= duration:
                    break

                # Find segment
                new_idx = 0
                for i, (boundary, dur, fn, desc) in enumerate(self.demo_segments):
                    if elapsed >= boundary:
                        new_idx = i

                if new_idx != seg_idx:
                    seg_idx = new_idx
                    seg_start = now

                # Execute
                _, dur, fn, desc = self.demo_segments[seg_idx]
                seg_time = now - seg_start
                fn(seg_time, dt)

                self._update_pan(dt)

                status = self._get_status_line()
                self.renderer.render(self.canvas, self.viewport, status)

                time.sleep(FRAME_DELAY)

        finally:
            self._show_message("Demo complete!")
            self.renderer.render(self.canvas, self.viewport, self._get_status_line())
            time.sleep(3)


def run_demo(duration=240):
    def main(stdscr):
        ShowcaseDemo(stdscr).run_demo(duration)
    curses.wrapper(main)


if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    print(f"Running showcase demo v3 for {duration}s...")
    print("Fixes: banner font, real boxes, mode setter")
    run_demo(duration)
