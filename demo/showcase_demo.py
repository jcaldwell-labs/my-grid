#!/usr/bin/env python3
"""
my-grid Showcase Demo - Feature-Rich Training Video

A comprehensive demonstration of my-grid capabilities including:
- Figlet banners and boxes styling
- Live system data (pwd, ls, tree, top)
- Real FIFO/external tool integration
- Grid configuration options
- Explanatory text for viewers

Duration: ~180 seconds (3 minutes)

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


def run_command(cmd):
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"(error: {e})"


def get_figlet(text, font="slant"):
    """Generate figlet banner."""
    return run_command(f"figlet -f {font} '{text}'")


def get_boxes(text, style="ansi-rounded"):
    """Wrap text in boxes style."""
    return run_command(f"echo '{text}' | boxes -d {style}")


class ShowcaseDemo(Application):
    """
    Feature-rich showcase demo with figlet, boxes, and live data.
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

    def _define_segments(self):
        """Define showcase segments - 180 seconds total."""
        segments = [
            # Opening (0-25s)
            (0, 25, self._segment_title_banner, "Grand opening with figlet"),

            # Core Features (25-70s)
            (25, 20, self._segment_what_is_mygrid, "What is my-grid?"),
            (45, 25, self._segment_modes_explained, "Mode system explained"),

            # Live Data Showcase (70-110s)
            (70, 20, self._segment_live_system_info, "Live system info"),
            (90, 20, self._segment_live_directory, "Live directory listing"),

            # Grid Configuration (110-140s)
            (110, 15, self._segment_grid_deep_dive, "Grid configuration"),
            (125, 15, self._segment_grid_spacing, "Grid spacing options"),

            # Zones & External Tools (140-165s)
            (140, 25, self._segment_zones_showcase, "Zone types showcase"),

            # Finale (165-180s)
            (165, 15, self._segment_grand_finale, "Grand finale"),
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
            if line.strip():
                self._execute_command(f"goto {x} {y + i}")
                # Escape any problematic characters
                safe_line = line.replace('"', "'")
                self._execute_command(f"text {safe_line}")

    def _draw_box_with_style(self, x, y, content, style="ansi-rounded"):
        """Draw content wrapped in boxes style."""
        boxed = get_boxes(content, style)
        self._draw_multiline(x, y, boxed)

    # ========== SEGMENT ACTIONS ==========

    def _segment_title_banner(self, segment_time, dt):
        """Grand opening with figlet banner."""
        if segment_time < 0.5:
            self._pan_to(0, 0, duration=0.5)

            # Big figlet title
            banner = get_figlet("my-grid", "slant")
            self._draw_multiline(10, 3, banner)

            # Tagline in a box
            self._execute_command("goto 10 12")
            self._execute_command("text ╭─────────────────────────────────────────────────────╮")
            self._execute_command("goto 10 13")
            self._execute_command("text │  Spatial Workspace • ASCII Canvas • Vim Navigation  │")
            self._execute_command("goto 10 14")
            self._execute_command("text ╰─────────────────────────────────────────────────────╯")

        if 3.0 < segment_time < 3.5:
            self._execute_command("goto 10 18")
            self._execute_command("text ┌─────────────────────────────────────────────────────┐")
            self._execute_command("goto 10 19")
            self._execute_command("text │  THIS DEMO WILL SHOW YOU:                           │")
            self._execute_command("goto 10 20")
            self._execute_command("text │                                                     │")
            self._execute_command("goto 10 21")
            self._execute_command("text │  • Vim-style modes (NAV, EDIT, PAN, COMMAND)        │")
            self._execute_command("goto 10 22")
            self._execute_command("text │  • Infinite canvas with sparse storage              │")
            self._execute_command("goto 10 23")
            self._execute_command("text │  • Named zones for spatial organization             │")
            self._execute_command("goto 10 24")
            self._execute_command("text │  • Live data integration (pwd, ls, top)             │")
            self._execute_command("goto 10 25")
            self._execute_command("text │  • Grid customization & rulers                      │")
            self._execute_command("goto 10 26")
            self._execute_command("text │  • External tool integration (figlet, boxes)        │")
            self._execute_command("goto 10 27")
            self._execute_command("text └─────────────────────────────────────────────────────┘")

        if 8.0 < segment_time < 8.5:
            self.renderer.grid.show_major_lines = True
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            self._show_message("Let's explore the infinite canvas...")

        # Slowly pan right to show infinite space
        if 12.0 < segment_time < 12.5:
            self._pan_to(50, 0, duration=3.0)

        if 18.0 < segment_time < 18.5:
            self._pan_to(0, 0, duration=2.0)

    def _segment_what_is_mygrid(self, segment_time, dt):
        """Explain what my-grid is."""
        if segment_time < 0.5:
            self._pan_to(0, 45, duration=1.0)

            # Section banner
            banner = get_figlet("WHAT?", "small")
            self._draw_multiline(5, 48, banner)

        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 56")
            self._execute_command("text ╔═══════════════════════════════════════════════════════════╗")
            self._execute_command("goto 5 57")
            self._execute_command("text ║  my-grid is a terminal-based ASCII canvas editor         ║")
            self._execute_command("goto 5 58")
            self._execute_command("text ║                                                           ║")
            self._execute_command("goto 5 59")
            self._execute_command("text ║  Think of it as:                                          ║")
            self._execute_command("goto 5 60")
            self._execute_command("text ║    • Miro/Lucidchart for the terminal                     ║")
            self._execute_command("goto 5 61")
            self._execute_command("text ║    • Infinite whiteboard that lives in your shell         ║")
            self._execute_command("goto 5 62")
            self._execute_command("text ║    • Spatial memory workspace (Jef Raskin style)          ║")
            self._execute_command("goto 5 63")
            self._execute_command("text ╚═══════════════════════════════════════════════════════════╝")

        if 6.0 < segment_time < 6.5:
            self._execute_command("goto 5 67")
            self._execute_command("text USE CASES:")
            self._execute_command("goto 5 69")
            self._execute_command("text   → System architecture diagrams")
            self._execute_command("goto 5 70")
            self._execute_command("text   → Sprint planning boards (Kanban)")
            self._execute_command("goto 5 71")
            self._execute_command("text   → Mind maps and brainstorming")
            self._execute_command("goto 5 72")
            self._execute_command("text   → Live dashboards with system data")
            self._execute_command("goto 5 73")
            self._execute_command("text   → Documentation and notes")

        if 12.0 < segment_time < 12.5:
            self._execute_command("goto 5 77")
            self._execute_command("text TIP: Everything saves to JSON - version control friendly!")

    def _segment_modes_explained(self, segment_time, dt):
        """Explain the mode system."""
        if segment_time < 0.5:
            self._pan_to(0, 90, duration=1.0)

            banner = get_figlet("MODES", "small")
            self._draw_multiline(5, 93, banner)

        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 101")
            self._execute_command("text ┌────────────────────────────────────────────────────────────┐")
            self._execute_command("goto 5 102")
            self._execute_command("text │  NAV MODE (default)                                        │")
            self._execute_command("goto 5 103")
            self._execute_command("text │    wasd/arrows = move cursor                               │")
            self._execute_command("goto 5 104")
            self._execute_command("text │    WASD = fast move (10x)                                  │")
            self._execute_command("goto 5 105")
            self._execute_command("text │    The cursor is your presence on the infinite canvas      │")
            self._execute_command("goto 5 106")
            self._execute_command("text └────────────────────────────────────────────────────────────┘")

        if 5.0 < segment_time < 5.5:
            self._execute_command("goto 5 109")
            self._execute_command("text ┌────────────────────────────────────────────────────────────┐")
            self._execute_command("goto 5 110")
            self._execute_command("text │  EDIT MODE (press 'i')                                     │")
            self._execute_command("goto 5 111")
            self._execute_command("text │    Type characters directly onto canvas                    │")
            self._execute_command("goto 5 112")
            self._execute_command("text │    Arrow keys still move cursor                            │")
            self._execute_command("goto 5 113")
            self._execute_command("text │    ESC = back to NAV mode                                  │")
            self._execute_command("goto 5 114")
            self._execute_command("text └────────────────────────────────────────────────────────────┘")

        if 8.0 < segment_time < 8.5:
            self._execute_command("goto 5 117")
            self._execute_command("text ┌────────────────────────────────────────────────────────────┐")
            self._execute_command("goto 5 118")
            self._execute_command("text │  PAN MODE (press 'p')                                      │")
            self._execute_command("goto 5 119")
            self._execute_command("text │    wasd moves viewport, cursor stays centered              │")
            self._execute_command("goto 5 120")
            self._execute_command("text │    Great for exploring large canvases                      │")
            self._execute_command("goto 5 121")
            self._execute_command("text └────────────────────────────────────────────────────────────┘")

        if 11.0 < segment_time < 11.5:
            self._execute_command("goto 5 124")
            self._execute_command("text ┌────────────────────────────────────────────────────────────┐")
            self._execute_command("goto 5 125")
            self._execute_command("text │  COMMAND MODE (press ':')                                  │")
            self._execute_command("goto 5 126")
            self._execute_command("text │    :rect 20 10     = draw rectangle                        │")
            self._execute_command("goto 5 127")
            self._execute_command("text │    :text Hello     = write text                            │")
            self._execute_command("goto 5 128")
            self._execute_command("text │    :goto 100 50    = jump to coordinates                   │")
            self._execute_command("goto 5 129")
            self._execute_command("text │    :w / :q         = save / quit (vim style!)              │")
            self._execute_command("goto 5 130")
            self._execute_command("text └────────────────────────────────────────────────────────────┘")

        if 15.0 < segment_time < 15.5:
            self._execute_command("goto 5 133")
            self._execute_command("text ┌────────────────────────────────────────────────────────────┐")
            self._execute_command("goto 5 134")
            self._execute_command("text │  BOOKMARK MODE (press 'm' then a-z)                        │")
            self._execute_command("goto 5 135")
            self._execute_command("text │    Set named positions you can jump back to                │")
            self._execute_command("goto 5 136")
            self._execute_command("text │    Press ' then letter to return                           │")
            self._execute_command("goto 5 137")
            self._execute_command("text │    SPATIAL MEMORY - remember WHERE things are!             │")
            self._execute_command("goto 5 138")
            self._execute_command("text └────────────────────────────────────────────────────────────┘")

        if 19.0 < segment_time < 19.5:
            self._show_message("Press F1 anytime for full help!")

    def _segment_live_system_info(self, segment_time, dt):
        """Show live system information."""
        if segment_time < 0.5:
            self._pan_to(0, 150, duration=1.0)

            banner = get_figlet("LIVE", "small")
            self._draw_multiline(5, 153, banner)

            self._execute_command("goto 30 153")
            self._execute_command("text DATA")

        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 161")
            self._execute_command("text Zones can display LIVE system data!")
            self._execute_command("goto 5 163")
            self._execute_command("text PIPE zones: one-shot command output")
            self._execute_command("goto 5 164")
            self._execute_command("text WATCH zones: periodic refresh")

        # Show current working directory
        if 5.0 < segment_time < 5.5:
            pwd = run_command("pwd")
            self._execute_command("goto 5 168")
            self._execute_command("text ╭─[ Current Directory ]─────────────────────────────────────╮")
            self._execute_command(f"goto 5 169")
            self._execute_command(f"text │  {pwd[:55]:<55} │")
            self._execute_command("goto 5 170")
            self._execute_command("text ╰────────────────────────────────────────────────────────────╯")

        # Show hostname and user
        if 8.0 < segment_time < 8.5:
            hostname = run_command("hostname")
            user = run_command("whoami")
            self._execute_command("goto 5 173")
            self._execute_command("text ╭─[ System ]────────────────────────────────────────────────╮")
            self._execute_command(f"goto 5 174")
            self._execute_command(f"text │  User: {user:<20} Host: {hostname:<22} │")
            self._execute_command("goto 5 175")
            self._execute_command("text ╰────────────────────────────────────────────────────────────╯")

        # Show date/time
        if 11.0 < segment_time < 11.5:
            date_str = run_command("date '+%Y-%m-%d %H:%M:%S'")
            uptime = run_command("uptime -p 2>/dev/null || echo 'uptime unavailable'")[:40]
            self._execute_command("goto 5 178")
            self._execute_command("text ╭─[ Time ]──────────────────────────────────────────────────╮")
            self._execute_command(f"goto 5 179")
            self._execute_command(f"text │  {date_str:<56} │")
            self._execute_command(f"goto 5 180")
            self._execute_command(f"text │  {uptime:<56} │")
            self._execute_command("goto 5 181")
            self._execute_command("text ╰────────────────────────────────────────────────────────────╯")

        if 15.0 < segment_time < 15.5:
            self._execute_command("goto 5 185")
            self._execute_command("text TIP: Use :zone watch NAME W H 5s 'date' for auto-refresh!")

    def _segment_live_directory(self, segment_time, dt):
        """Show live directory listing."""
        if segment_time < 0.5:
            self._pan_to(0, 195, duration=1.0)

            self._execute_command("goto 5 198")
            self._execute_command("text ╔════════════════════════════════════════════════════════════╗")
            self._execute_command("goto 5 199")
            self._execute_command("text ║  LIVE DIRECTORY LISTING                                    ║")
            self._execute_command("goto 5 200")
            self._execute_command("text ╚════════════════════════════════════════════════════════════╝")

        if 3.0 < segment_time < 3.5:
            # Get directory listing
            ls_output = run_command("ls -la ~/projects/active/my-grid | head -12")
            lines = ls_output.split('\n')

            self._execute_command("goto 5 203")
            self._execute_command("text ┌─[ ls -la ~/projects/active/my-grid ]─────────────────────┐")

            for i, line in enumerate(lines[:10]):
                safe_line = line[:58].replace('"', "'")
                self._execute_command(f"goto 5 {204 + i}")
                self._execute_command(f"text │ {safe_line:<58}│")

            self._execute_command(f"goto 5 {204 + min(len(lines), 10)}")
            self._execute_command("text └────────────────────────────────────────────────────────────┘")

        if 10.0 < segment_time < 10.5:
            # Show tree output
            tree_output = run_command("tree -L 2 ~/projects/active/my-grid/src 2>/dev/null | head -15")
            if "command not found" in tree_output or not tree_output:
                tree_output = run_command("ls -R ~/projects/active/my-grid/src | head -15")

            lines = tree_output.split('\n')

            self._execute_command("goto 70 203")
            self._execute_command("text ┌─[ src/ structure ]──────────────────┐")

            for i, line in enumerate(lines[:12]):
                safe_line = line[:36].replace('"', "'")
                self._execute_command(f"goto 70 {204 + i}")
                self._execute_command(f"text │ {safe_line:<36}│")

            self._execute_command(f"goto 70 {204 + min(len(lines), 12)}")
            self._execute_command("text └──────────────────────────────────────┘")

    def _segment_grid_deep_dive(self, segment_time, dt):
        """Deep dive into grid configuration."""
        if segment_time < 0.5:
            self._pan_to(0, 240, duration=1.0)

            banner = get_figlet("GRID", "small")
            self._draw_multiline(5, 243, banner)

        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 251")
            self._execute_command("text The grid helps you align content and navigate:")

            # Show LINES mode
            self.renderer.grid.line_mode = GridLineMode.LINES
            self.renderer.grid.show_minor_lines = True
            self._show_message("Grid Mode: LINES - Full box-drawing characters")

        if 4.0 < segment_time < 4.5:
            self._execute_command("goto 5 254")
            self._execute_command("text ┌─────────────────────────────────────────────────┐")
            self._execute_command("goto 5 255")
            self._execute_command("text │  LINES mode: ═══╬═══ Professional appearance    │")
            self._execute_command("goto 5 256")
            self._execute_command("text │  Toggle with: :grid lines                       │")
            self._execute_command("goto 5 257")
            self._execute_command("text └─────────────────────────────────────────────────┘")

        if 6.0 < segment_time < 6.5:
            self.renderer.grid.line_mode = GridLineMode.DOTS
            self._show_message("Grid Mode: DOTS - Subtle dotted pattern")

        if 7.0 < segment_time < 7.5:
            self._execute_command("goto 5 260")
            self._execute_command("text ┌─────────────────────────────────────────────────┐")
            self._execute_command("goto 5 261")
            self._execute_command("text │  DOTS mode: · · · · Subtle and clean            │")
            self._execute_command("goto 5 262")
            self._execute_command("text │  Toggle with: :grid dots                        │")
            self._execute_command("goto 5 263")
            self._execute_command("text └─────────────────────────────────────────────────┘")

        if 9.0 < segment_time < 9.5:
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            self._show_message("Grid Mode: MARKERS - Intersections only")

        if 10.0 < segment_time < 10.5:
            self._execute_command("goto 5 266")
            self._execute_command("text ┌─────────────────────────────────────────────────┐")
            self._execute_command("goto 5 267")
            self._execute_command("text │  MARKERS mode: + + + Minimal, just intersections│")
            self._execute_command("goto 5 268")
            self._execute_command("text │  Toggle with: :grid markers (or press 'g')      │")
            self._execute_command("goto 5 269")
            self._execute_command("text └─────────────────────────────────────────────────┘")

        if 12.0 < segment_time < 12.5:
            self.renderer.grid.show_minor_lines = False
            self.renderer.grid.line_mode = GridLineMode.LINES

    def _segment_grid_spacing(self, segment_time, dt):
        """Show grid spacing options."""
        if segment_time < 0.5:
            self._pan_to(0, 280, duration=1.0)

            self._execute_command("goto 5 283")
            self._execute_command("text ╔════════════════════════════════════════════════════════════╗")
            self._execute_command("goto 5 284")
            self._execute_command("text ║  GRID SPACING & RULERS                                     ║")
            self._execute_command("goto 5 285")
            self._execute_command("text ╚════════════════════════════════════════════════════════════╝")

        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 288")
            self._execute_command("text Customize grid intervals for your workflow:")
            self._execute_command("goto 5 290")
            self._execute_command("text   :grid interval 20     = Major lines every 20 cells")
            self._execute_command("goto 5 291")
            self._execute_command("text   :grid interval 50 10  = Major every 50, minor every 10")

        if 4.0 < segment_time < 4.5:
            # Change grid interval
            self.renderer.grid.major_interval = 20
            self.renderer.grid.minor_interval = 5
            self._show_message("Grid interval: 20 (major) / 5 (minor)")

        if 6.0 < segment_time < 6.5:
            self._execute_command("goto 5 295")
            self._execute_command("text Enable rulers to see coordinates:")
            self._execute_command("goto 5 297")
            self._execute_command("text   :grid rulers on   = Show edge coordinates")
            self._execute_command("goto 5 298")
            self._execute_command("text   :grid labels on   = Show floating labels")

        if 8.0 < segment_time < 8.5:
            self.renderer.grid.show_rulers = True
            self._show_message("Rulers enabled - coordinates at edges")

        if 10.0 < segment_time < 10.5:
            self.renderer.grid.show_labels = True
            self.renderer.grid.label_interval = 20
            self._show_message("Labels enabled - floating coordinate markers")

        if 12.0 < segment_time < 12.5:
            # Reset for cleaner view
            self.renderer.grid.show_rulers = False
            self.renderer.grid.show_labels = False
            self.renderer.grid.major_interval = 10
            self.renderer.grid.minor_interval = 5

    def _segment_zones_showcase(self, segment_time, dt):
        """Showcase zone types with boxes styling."""
        if segment_time < 0.5:
            self._pan_to(0, 320, duration=1.0)

            banner = get_figlet("ZONES", "small")
            self._draw_multiline(5, 323, banner)

        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 331")
            self._execute_command("text Zones are named regions on your canvas:")

        # STATIC zone
        if 4.0 < segment_time < 4.5:
            self._execute_command("goto 5 335")
            self._execute_command("text ╭─[ STATIC Zone ]───────────────────────────────────────────╮")
            self._execute_command("goto 5 336")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 337")
            self._execute_command("text │  Basic named region - draw anything here                  │")
            self._execute_command("goto 5 338")
            self._execute_command("text │  :zone create NOTES 0 0 60 20                             │")
            self._execute_command("goto 5 339")
            self._execute_command("text │  Jump with: :zone goto NOTES                              │")
            self._execute_command("goto 5 340")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 341")
            self._execute_command("text ╰───────────────────────────────────────────────────────────╯")

        # PIPE zone
        if 7.0 < segment_time < 7.5:
            self._execute_command("goto 5 344")
            self._execute_command("text ╭─[ PIPE Zone ]─────────────────────────────────────────────╮")
            self._execute_command("goto 5 345")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 346")
            self._execute_command("text │  One-shot command output - runs once when created         │")
            self._execute_command("goto 5 347")
            self._execute_command("text │  :zone pipe SYSINFO 60 15 'uname -a'                      │")
            self._execute_command("goto 5 348")
            self._execute_command("text │  Refresh with: :zone refresh SYSINFO                      │")
            self._execute_command("goto 5 349")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 350")
            self._execute_command("text ╰───────────────────────────────────────────────────────────╯")

        # WATCH zone
        if 10.0 < segment_time < 10.5:
            self._execute_command("goto 5 353")
            self._execute_command("text ╭─[ WATCH Zone ]────────────────────────────────────────────╮")
            self._execute_command("goto 5 354")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 355")
            self._execute_command("text │  Auto-refresh at intervals - like 'watch' command         │")
            self._execute_command("goto 5 356")
            self._execute_command("text │  :zone watch CLOCK 30 5 1s 'date'                         │")
            self._execute_command("goto 5 357")
            self._execute_command("text │  Great for: logs, metrics, status                         │")
            self._execute_command("goto 5 358")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 359")
            self._execute_command("text ╰───────────────────────────────────────────────────────────╯")

        # PTY zone
        if 13.0 < segment_time < 13.5:
            self._execute_command("goto 5 362")
            self._execute_command("text ╭─[ PTY Zone ]──────────────────────────────────────────────╮")
            self._execute_command("goto 5 363")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 364")
            self._execute_command("text │  Live terminal embedded in your canvas! (Unix only)       │")
            self._execute_command("goto 5 365")
            self._execute_command("text │  :zone pty SHELL 80 24                                    │")
            self._execute_command("goto 5 366")
            self._execute_command("text │  Enter to focus, type commands, Esc to unfocus            │")
            self._execute_command("goto 5 367")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 368")
            self._execute_command("text ╰───────────────────────────────────────────────────────────╯")

        # FIFO/Socket
        if 17.0 < segment_time < 17.5:
            self._execute_command("goto 5 371")
            self._execute_command("text ╭─[ FIFO & Socket Zones ]──────────────────────────────────╮")
            self._execute_command("goto 5 372")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 373")
            self._execute_command("text │  External integration - receive data from other tools     │")
            self._execute_command("goto 5 374")
            self._execute_command("text │  :zone fifo EXTERNAL 60 20 /tmp/mygrid.fifo               │")
            self._execute_command("goto 5 375")
            self._execute_command("text │  :zone socket CLAUDE 60 20 9999                           │")
            self._execute_command("goto 5 376")
            self._execute_command("text │  Perfect for: Claude Code output, log streams             │")
            self._execute_command("goto 5 377")
            self._execute_command("text │                                                           │")
            self._execute_command("goto 5 378")
            self._execute_command("text ╰───────────────────────────────────────────────────────────╯")

        if 21.0 < segment_time < 21.5:
            self._execute_command("goto 5 382")
            self._execute_command("text TIP: Link zones to bookmarks with :zone link NAME KEY")

    def _segment_grand_finale(self, segment_time, dt):
        """Grand finale with summary."""
        if segment_time < 0.5:
            self._pan_to(0, 400, duration=1.5)

            # Big finale banner
            banner = get_figlet("FIN", "slant")
            self._draw_multiline(20, 403, banner)

        if 3.0 < segment_time < 3.5:
            self._execute_command("goto 5 415")
            self._execute_command("text ╔════════════════════════════════════════════════════════════════╗")
            self._execute_command("goto 5 416")
            self._execute_command("text ║                         QUICK REFERENCE                        ║")
            self._execute_command("goto 5 417")
            self._execute_command("text ╠════════════════════════════════════════════════════════════════╣")
            self._execute_command("goto 5 418")
            self._execute_command("text ║  wasd      Move cursor          :rect W H    Draw box          ║")
            self._execute_command("goto 5 419")
            self._execute_command("text ║  i         Edit mode            :text MSG    Write text        ║")
            self._execute_command("goto 5 420")
            self._execute_command("text ║  p         Pan mode             :goto X Y    Jump to coords    ║")
            self._execute_command("goto 5 421")
            self._execute_command("text ║  :         Command mode         :zone ...    Zone commands     ║")
            self._execute_command("goto 5 422")
            self._execute_command("text ║  m + key   Set bookmark         :w / :q      Save / Quit       ║")
            self._execute_command("goto 5 423")
            self._execute_command("text ║  ' + key   Jump to bookmark     F1           Help screen       ║")
            self._execute_command("goto 5 424")
            self._execute_command("text ╚════════════════════════════════════════════════════════════════╝")

        if 7.0 < segment_time < 7.5:
            self._execute_command("goto 5 428")
            self._execute_command("text ┌────────────────────────────────────────────────────────────────┐")
            self._execute_command("goto 5 429")
            self._execute_command("text │  github.com/jcaldwell-labs/my-grid                             │")
            self._execute_command("goto 5 430")
            self._execute_command("text │                                                                │")
            self._execute_command("goto 5 431")
            self._execute_command("text │  Inspired by Jef Raskin's 'The Humane Interface'               │")
            self._execute_command("goto 5 432")
            self._execute_command("text │  Spatial memory > hierarchical navigation                      │")
            self._execute_command("goto 5 433")
            self._execute_command("text └────────────────────────────────────────────────────────────────┘")

        if 10.0 < segment_time < 10.5:
            self._show_message("Thanks for watching! Try my-grid today!")

    # ========== MAIN DEMO LOOP ==========

    def run_demo(self, total_duration=180):
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
            self._show_message("Demo complete! Explore my-grid at github.com/jcaldwell-labs/my-grid")
            status = self._get_status_line()
            self.renderer.render(self.canvas, self.viewport, status)
            time.sleep(3)


def run_demo(duration=180):
    """Entry point for demo mode."""
    def _curses_main(stdscr):
        demo = ShowcaseDemo(stdscr)
        demo.run_demo(duration)

    curses.wrapper(_curses_main)


if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    print(f"Running showcase demo for {duration} seconds...")
    print("")
    print("This demo includes:")
    print("  - Figlet banners")
    print("  - Live system data (pwd, ls, tree, hostname)")
    print("  - Grid configuration walkthrough")
    print("  - Zone types explained")
    print("  - External tool integration")
    print("")
    run_demo(duration)
