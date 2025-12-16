#!/usr/bin/env python3
"""
Spatial Workspace Demo for VHS Recording

Demonstrates Sprint 1-5 features:
- Grid line modes (MARKERS, LINES, DOTS)
- Edge rulers and coordinate labels
- Named zones with navigation
- Dynamic zones (PIPE, WATCH, PTY)
- External tool integration (boxes, figlet, pipe)
- Layouts (workspace templates)
- Clipboard (yank/paste)
- FIFO/Socket zones (external connectors)
- Claude Code integration patterns

Based on jcaldwell-labs-media skill patterns:
- Single fullscreen session (no transitions)
- 20 FPS for VHS compatibility (0.05s frame delay)
- Time-based segment switching in single while loop
- Smooth parametric panning animations

Usage:
    python demo/spatial_workspace_demo.py [duration]

    # For VHS recording:
    vhs demo/spatial-workspace-demo.tape
"""

import sys
import time
import math
import curses
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import Application
from input import InputEvent, Action
from renderer import GridLineMode


class SpatialWorkspaceDemo(Application):
    """
    Demo showcasing spatial workspace features.

    Features demonstrated (Sprint 1-5):
    - Zone creation and navigation
    - Dynamic zones (PIPE, WATCH, PTY)
    - Grid line modes (LINES, DOTS, MARKERS)
    - Rulers and coordinate labels
    - External tool integration (boxes, figlet, pipe)
    - Layouts (workspace templates)
    - Clipboard (yank/paste)
    - FIFO/Socket zones (external connectors)
    - Claude Code integration patterns
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
        """
        Define demo segments with cumulative time boundaries.

        Each segment: (start_time, duration, action_function, description)
        """
        segments = [
            (0, 10, self._segment_intro, "Introduction"),
            (10, 15, self._segment_zones, "Zone system"),
            (25, 12, self._segment_dynamic_zones, "Dynamic zones"),
            (37, 12, self._segment_grid_modes, "Grid line modes"),
            (49, 10, self._segment_rulers, "Rulers and labels"),
            (59, 12, self._segment_workspace_layout, "Workspace layout"),
            (71, 10, self._segment_layouts, "Layouts and templates"),
            (81, 12, self._segment_external_connectors, "External connectors"),
            (93, 10, self._segment_navigation, "Zone navigation"),
            (103, 12, self._segment_finale, "Finale"),
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
        """Execute a command string."""
        result = self.state_machine._execute_command(command_str)
        if result.message:
            self._show_message(result.message)

    # ========== SEGMENT ACTIONS ==========

    def _segment_intro(self, segment_time, dt):
        """Introduction: Title and overview."""
        if segment_time < 0.5:
            # Create title at origin
            self._execute_command("goto 5 5")
            self._execute_command("text SPATIAL WORKSPACE DEMO")
            self._execute_command("goto 5 7")
            self._execute_command("text ═══════════════════════")
            self._execute_command("goto 5 10")
            self._execute_command("text my-grid Sprint 1-5 Features:")
            self._execute_command("goto 5 12")
            self._execute_command("text   • Named Zones (static, dynamic)")
            self._execute_command("goto 5 13")
            self._execute_command("text   • Dynamic: PIPE, WATCH, PTY")
            self._execute_command("goto 5 14")
            self._execute_command("text   • Grid Modes & Rulers")
            self._execute_command("goto 5 15")
            self._execute_command("text   • Layouts & Clipboard")
            self._execute_command("goto 5 16")
            self._execute_command("text   • FIFO/Socket Connectors")
            self._pan_to(0, 0, duration=1.0)

        # Enable grid display
        if 4.0 < segment_time < 4.5:
            self.renderer.grid.show_major_lines = True
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            self._show_message("Grid: MARKERS mode")

    def _segment_zones(self, segment_time, dt):
        """Zone system: Create and demonstrate zones."""
        if segment_time < 0.5:
            self._execute_command("goto 0 30")
            self._execute_command("text === ZONE SYSTEM ===")
            self._pan_to(-5, 25, duration=1.0)

        # Create INBOX zone
        if 2.0 < segment_time < 2.5:
            self._execute_command("zone create INBOX 0 40 60 20 Quick capture")
            self._execute_command("zone link INBOX i")
            self._execute_command("goto 5 42")
            self._execute_command("rect 50 16")
            self._execute_command("goto 10 44")
            self._execute_command("text INBOX - Quick Capture")
            self._execute_command("goto 10 47")
            self._execute_command("text [i] Drop ideas here")

        # Create WORKSPACE zone
        if 5.0 < segment_time < 5.5:
            self._execute_command("zone create WORKSPACE 150 40 80 30 Main work area")
            self._execute_command("zone link WORKSPACE w")
            self._pan_to(140, 30, duration=1.5)

        if 7.0 < segment_time < 7.5:
            self._execute_command("goto 155 42")
            self._execute_command("rect 70 26")
            self._execute_command("goto 160 44")
            self._execute_command("text WORKSPACE - Main Area")
            self._execute_command("goto 160 47")
            self._execute_command("text [w] Primary work zone")

        # Create ARCHIVE zone
        if 10.0 < segment_time < 10.5:
            self._execute_command("zone create ARCHIVE 300 40 60 20 Completed items")
            self._execute_command("zone link ARCHIVE a")
            self._pan_to(290, 30, duration=1.5)

        if 12.0 < segment_time < 12.5:
            self._execute_command("goto 305 42")
            self._execute_command("rect 50 16")
            self._execute_command("goto 310 44")
            self._execute_command("text ARCHIVE - Completed")
            self._execute_command("goto 310 47")
            self._execute_command("text [a] Done items here")

    def _segment_dynamic_zones(self, segment_time, dt):
        """Dynamic zones: PIPE, WATCH zone types."""
        if segment_time < 0.5:
            self._pan_to(0, 200, duration=1.0)
            self._execute_command("goto 5 205")
            self._execute_command("text === DYNAMIC ZONES ===")

        # Explain dynamic zone types
        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 210")
            self._execute_command("text PIPE zones: One-shot command output")
            self._execute_command("goto 5 212")
            self._execute_command("text   :zone pipe NAME W H COMMAND")

        if 4.0 < segment_time < 4.5:
            self._execute_command("goto 5 215")
            self._execute_command("text WATCH zones: Periodic refresh")
            self._execute_command("goto 5 217")
            self._execute_command("text   :zone watch NAME W H 5s COMMAND")

        if 6.0 < segment_time < 6.5:
            self._execute_command("goto 5 220")
            self._execute_command("text PTY zones: Live terminal (Unix)")
            self._execute_command("goto 5 222")
            self._execute_command("text   :zone pty NAME W H [SHELL]")

        # Show zone type indicators
        if 8.0 < segment_time < 8.5:
            self._execute_command("goto 5 226")
            self._execute_command("text Zone borders show type: [P] [W] [T]")

        if 10.0 < segment_time < 10.5:
            self._execute_command("goto 5 229")
            self._execute_command("text Content auto-refreshes in viewport!")

    def _segment_grid_modes(self, segment_time, dt):
        """Grid modes: Demonstrate LINES, DOTS, MARKERS."""
        if segment_time < 0.5:
            self._pan_to(0, 80, duration=1.0)
            self._execute_command("goto 5 85")
            self._execute_command("text === GRID LINE MODES ===")

        # LINES mode
        if 2.0 < segment_time < 2.5:
            self.renderer.grid.line_mode = GridLineMode.LINES
            self.renderer.grid.show_minor_lines = True
            self._show_message("Grid: LINES mode - Full box-drawing characters")

        if 3.0 < segment_time < 3.5:
            self._execute_command("goto 5 90")
            self._execute_command("text LINES: ═══╬═══ Full grid lines")

        # DOTS mode
        if 5.0 < segment_time < 5.5:
            self.renderer.grid.line_mode = GridLineMode.DOTS
            self._show_message("Grid: DOTS mode - Subtle dotted lines")

        if 6.0 < segment_time < 6.5:
            self._execute_command("goto 5 93")
            self._execute_command("text DOTS: • • • Subtle markers")

        # MARKERS mode
        if 8.0 < segment_time < 8.5:
            self.renderer.grid.line_mode = GridLineMode.MARKERS
            self._show_message("Grid: MARKERS mode - Intersection only")

        if 9.0 < segment_time < 9.5:
            self._execute_command("goto 5 96")
            self._execute_command("text MARKERS: + + + Intersections only")

        # Back to LINES for visibility
        if 10.5 < segment_time < 11.0:
            self.renderer.grid.line_mode = GridLineMode.LINES

    def _segment_rulers(self, segment_time, dt):
        """Rulers and labels: Show coordinate helpers."""
        if segment_time < 0.5:
            self._pan_to(0, 110, duration=1.0)
            self._execute_command("goto 5 115")
            self._execute_command("text === RULERS & LABELS ===")

        # Enable rulers
        if 2.0 < segment_time < 2.5:
            self.renderer.grid.show_rulers = True
            self._show_message("Rulers enabled - Edge coordinate display")

        if 4.0 < segment_time < 4.5:
            self._execute_command("goto 10 120")
            self._execute_command("text Rulers show coordinates at edges")

        # Enable coordinate labels
        if 6.0 < segment_time < 6.5:
            self.renderer.grid.show_labels = True
            self.renderer.grid.label_interval = 50
            self._show_message("Coordinate labels enabled")

        if 8.0 < segment_time < 8.5:
            self._execute_command("goto 10 123")
            self._execute_command("text Labels: floating x=N, y=N markers")

        # Disable for cleaner view in next segments
        if 10.0 < segment_time < 10.5:
            self.renderer.grid.show_rulers = False
            self.renderer.grid.show_labels = False
            self.renderer.grid.show_minor_lines = False

    def _segment_workspace_layout(self, segment_time, dt):
        """Workspace layout: Show practical spatial arrangement."""
        if segment_time < 0.5:
            self._pan_to(140, 30, duration=1.5)
            self._execute_command("goto 155 50")
            self._execute_command("text Building a spatial workspace...")

        # Add content to WORKSPACE
        if 3.0 < segment_time < 3.5:
            self._execute_command("goto 160 55")
            self._execute_command("text TODO:")
            self._execute_command("goto 160 57")
            self._execute_command("text [x] Create zones")
            self._execute_command("goto 160 59")
            self._execute_command("text [x] Configure grid")
            self._execute_command("goto 160 61")
            self._execute_command("text [ ] Add content")

        # Pan to show zone connections
        if 6.0 < segment_time < 6.5:
            self._pan_to(70, 35, duration=2.0)

        # Draw connection arrows
        if 8.0 < segment_time < 8.5:
            self._execute_command("goto 62 50")
            self._execute_command("text ──────►")
            self._execute_command("goto 232 50")
            self._execute_command("text ──────►")

        # Show status bar zone indicator
        if 10.0 < segment_time < 10.5:
            self._execute_command("goto 5 70")
            self._execute_command("text Status bar shows: current zone + nearest zone")

        if 10.0 < segment_time < 10.5:
            self._execute_command("goto 5 72")
            self._execute_command("text Example: WORKSPACE | →120 [a]")

    def _segment_layouts(self, segment_time, dt):
        """Layouts: Workspace templates."""
        if segment_time < 0.5:
            self._pan_to(0, 250, duration=1.0)
            self._execute_command("goto 5 255")
            self._execute_command("text === LAYOUTS & CLIPBOARD ===")

        # Layout commands
        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 260")
            self._execute_command("text :layout save NAME - Save current zones")
            self._execute_command("goto 5 262")
            self._execute_command("text :layout load NAME - Load workspace")

        # Default layouts
        if 4.0 < segment_time < 4.5:
            self._execute_command("goto 5 266")
            self._execute_command("text Default layouts: devops, development, monitoring")

        # Clipboard
        if 6.0 < segment_time < 6.5:
            self._execute_command("goto 5 270")
            self._execute_command("text :yank W H - Yank region to clipboard")
            self._execute_command("goto 5 272")
            self._execute_command("text :paste   - Paste at cursor")

        if 8.0 < segment_time < 8.5:
            self._execute_command("goto 5 275")
            self._execute_command("text System clipboard: :yank system / :paste system")

    def _segment_external_connectors(self, segment_time, dt):
        """External connectors: FIFO and Socket zones."""
        if segment_time < 0.5:
            self._pan_to(0, 300, duration=1.0)
            self._execute_command("goto 5 305")
            self._execute_command("text === EXTERNAL CONNECTORS ===")

        # FIFO zones
        if 2.0 < segment_time < 2.5:
            self._execute_command("goto 5 310")
            self._execute_command("text FIFO zones (Unix): Named pipe listener")
            self._execute_command("goto 5 312")
            self._execute_command("text   :zone fifo NAME W H /tmp/pipe.fifo")

        # Socket zones
        if 4.0 < segment_time < 4.5:
            self._execute_command("goto 5 316")
            self._execute_command("text Socket zones: TCP port listener")
            self._execute_command("goto 5 318")
            self._execute_command("text   :zone socket NAME W H 9999")

        # Claude Code integration
        if 6.0 < segment_time < 6.5:
            self._execute_command("goto 5 322")
            self._execute_command("text Claude Code Integration:")
            self._execute_command("goto 5 324")
            self._execute_command("text   • Socket zone receives Claude output")
            self._execute_command("goto 5 326")
            self._execute_command("text   • API server for bidirectional control")

        if 9.0 < segment_time < 9.5:
            self._execute_command("goto 5 330")
            self._execute_command("text See CLAUDE.md for integration patterns")

    def _segment_navigation(self, segment_time, dt):
        """Zone navigation: Quick jumps between zones."""
        if segment_time < 0.5:
            self._execute_command("goto 155 64")
            self._execute_command("text === ZONE NAVIGATION ===")
            self._pan_to(140, 30, duration=1.0)

        # Jump to INBOX
        if 2.0 < segment_time < 2.5:
            self._execute_command("zone goto INBOX")
            self._show_message("Jumped to INBOX zone")

        if 2.5 < segment_time < 3.0:
            self._pan_to(-5, 35, duration=1.0)

        # Jump to ARCHIVE
        if 4.0 < segment_time < 4.5:
            self._execute_command("zone goto ARCHIVE")
            self._show_message("Jumped to ARCHIVE zone")

        if 4.5 < segment_time < 5.0:
            self._pan_to(290, 35, duration=1.5)

        # Jump to WORKSPACE
        if 6.0 < segment_time < 6.5:
            self._execute_command("zone goto WORKSPACE")
            self._show_message("Jumped to WORKSPACE zone")

        if 6.5 < segment_time < 7.0:
            self._pan_to(140, 35, duration=1.5)

        # Return to origin
        if 8.0 < segment_time < 8.5:
            self._execute_command("goto 0 0")
            self._show_message("Returned to origin")

        if 8.5 < segment_time < 9.0:
            self._pan_to(0, 0, duration=1.5)

    def _segment_finale(self, segment_time, dt):
        """Finale: Summary and wrap-up."""
        if segment_time < 0.5:
            # Create SUMMARY zone at far location
            self._execute_command("zone create SUMMARY 500 0 70 30 Final summary")
            self._pan_to(490, -5, duration=2.0)

        if 2.5 < segment_time < 3.0:
            self._execute_command("goto 505 2")
            self._execute_command("rect 60 26")
            self._execute_command("goto 510 4")
            self._execute_command("text SPATIAL WORKSPACE")
            self._execute_command("goto 510 5")
            self._execute_command("text ════════════════")

        if 4.0 < segment_time < 4.5:
            self._execute_command("goto 510 8")
            self._execute_command("text Sprint 1-5 Complete:")
            self._execute_command("goto 510 10")
            self._execute_command("text + Grid modes (LINES/DOTS/MARKERS)")
            self._execute_command("goto 510 11")
            self._execute_command("text + Rulers & coordinate labels")
            self._execute_command("goto 510 12")
            self._execute_command("text + Named zones with bookmarks")
            self._execute_command("goto 510 13")
            self._execute_command("text + Dynamic zones (PIPE/WATCH/PTY)")
            self._execute_command("goto 510 14")
            self._execute_command("text + Layouts & Clipboard")
            self._execute_command("goto 510 15")
            self._execute_command("text + FIFO/Socket connectors")
            self._execute_command("goto 510 16")
            self._execute_command("text + Claude Code integration")

        if 7.0 < segment_time < 7.5:
            self._execute_command("goto 510 19")
            self._execute_command("text Inspired by Jef Raskin's")
            self._execute_command("goto 510 20")
            self._execute_command("text 'The Humane Interface'")

        if 9.0 < segment_time < 9.5:
            self._execute_command("goto 510 23")
            self._execute_command("text github.com/jcaldwell-labs/my-grid")

    # ========== MAIN DEMO LOOP ==========

    def run_demo(self, total_duration=100):
        """
        Run automated demo with visual curses UI.

        VHS records this - single while loop for freeze prevention.
        """
        # VHS-compatible frame rate
        FRAME_DELAY = 0.05  # 20 FPS - proven reliable

        start_time = time.time()
        last_time = start_time
        current_segment_idx = 0
        segment_start_time = start_time

        # Single fullscreen session (VHS freeze prevention)
        try:
            while True:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                elapsed = current_time - start_time

                # Check total duration
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

                # VHS-compatible frame rate
                time.sleep(FRAME_DELAY)

        finally:
            # Clean exit message
            self._show_message("Demo complete! Spatial workspace ready.")
            status = self._get_status_line()
            self.renderer.render(self.canvas, self.viewport, status)
            time.sleep(2)


def run_demo(duration=100):
    """Entry point for demo mode."""
    def _curses_main(stdscr):
        demo = SpatialWorkspaceDemo(stdscr)
        demo.run_demo(duration)

    curses.wrapper(_curses_main)


if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    print(f"Running spatial workspace demo for {duration} seconds...")
    print("This demo showcases Sprint 1-5 features:")
    print("  - Zone system with navigation")
    print("  - Dynamic zones (PIPE, WATCH, PTY)")
    print("  - Grid line modes (LINES, DOTS, MARKERS)")
    print("  - Rulers and coordinate labels")
    print("  - Layouts and Clipboard")
    print("  - FIFO/Socket external connectors")
    print("  - Claude Code integration")
    print("")
    print("VHS will record the visual canvas display.")
    run_demo(duration)
