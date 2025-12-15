#!/usr/bin/env python3
"""
Visual Auto-Demo for VHS Recording

This module runs the actual curses UI with programmed actions,
allowing VHS to record the visual canvas display.

Based on jcaldwell-labs-media skill patterns:
- Single fullscreen session (no transitions)
- 20 FPS for VHS compatibility (0.05s frame delay)
- Time-based segment switching in single while loop
- Smooth parametric panning animations

Usage:
    python demo/visual_auto_demo.py [duration]

    # For VHS recording:
    vhs demo/visual-auto-demo.tape
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


class VisualAutoDemo(Application):
    """
    Auto-demo that runs curses UI with programmed actions.

    VHS records the visual canvas instead of API command output.
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
        self.pan_progress = 1.0  # 1.0 = no pan in progress

    def _define_segments(self):
        """
        Define demo segments with cumulative time boundaries.

        Each segment: (start_time, duration, action_function, description)
        """
        segments = [
            (0, 8, self._segment_welcome, "Welcome banner"),
            (8, 10, self._segment_drawing, "Drawing primitives"),
            (18, 8, self._segment_navigation, "Navigation & bookmarks"),
            (26, 8, self._segment_modes, "Editor modes"),
            (34, 10, self._segment_architecture, "System diagrams"),
            (44, 8, self._segment_productivity, "Productivity features"),
            (52, 8, self._segment_api, "API control"),
            (60, 5, self._segment_easter_egg, "Easter egg"),
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
        from modes import ModeResult
        result = self.state_machine._execute_command(command_str)
        if result.message:
            self._show_message(result.message)

    # ========== SEGMENT ACTIONS ==========

    def _segment_welcome(self, segment_time, dt):
        """Welcome segment: Create giant banner and pan across it."""
        if segment_time < 0.5:
            # Create giant banner at (400, 40)
            self._execute_command("goto 400 40")
            self._execute_command("text my-grid: Infinite ASCII Canvas")
            self._execute_command("goto 400 50")
            self._execute_command("text ═════════════════════════════")
            self._execute_command("goto 400 60")
            self._execute_command("text Pan anywhere • Draw anything")
            self._pan_to(350, 20, duration=2.0)

        # Smooth pan across the banner
        if 2.0 < segment_time < 6.0:
            pan_t = (segment_time - 2.0) / 4.0
            self.viewport.x = int(350 + math.sin(pan_t * math.pi) * 100)

    def _segment_drawing(self, segment_time, dt):
        """Drawing segment: Demonstrate rectangles, lines, text."""
        if segment_time < 0.5:
            self._execute_command("goto 100 130")
            self._execute_command("text === DRAWING PRIMITIVES ===")
            self._pan_to(80, 110, duration=1.0)

        if 1.5 < segment_time < 2.0:
            self._execute_command("goto 100 145")
            self._execute_command("rect 40 10 #")

        if 3.0 < segment_time < 3.5:
            self._execute_command("goto 100 160")
            self._execute_command("line 140 180 *")

        if 5.0 < segment_time < 5.5:
            self._execute_command("goto 100 185")
            self._execute_command("text Hello from my-grid!")

    def _segment_navigation(self, segment_time, dt):
        """Navigation segment: Bookmarks and movement."""
        if segment_time < 0.5:
            self._execute_command("goto 600 130")
            self._execute_command("text === NAVIGATION ===")
            self._pan_to(580, 110, duration=1.0)

        if 1.5 < segment_time < 2.0:
            self._execute_command("mark a 600 145")
            self._execute_command("goto 600 145")
            self._execute_command("text Bookmark 'a' here")

        if 3.0 < segment_time < 3.5:
            self._execute_command("mark b 650 160")
            self._execute_command("goto 650 160")
            self._execute_command("text Bookmark 'b' here")

        if 4.5 < segment_time < 5.0:
            self._execute_command("goto 600 175")
            self._execute_command("text Jump with ' + key")

    def _segment_modes(self, segment_time, dt):
        """Modes segment: Show different modes."""
        if segment_time < 0.5:
            self._execute_command("goto 1100 130")
            self._execute_command("text === EDITOR MODES ===")
            self._pan_to(1080, 110, duration=1.0)

        if 1.5 < segment_time < 2.0:
            self._execute_command("goto 1100 145")
            self._execute_command("text NAV: wasd navigation")

        if 3.0 < segment_time < 3.5:
            self._execute_command("goto 1100 155")
            self._execute_command("text EDIT: i to draw")

        if 4.5 < segment_time < 5.0:
            self._execute_command("goto 1100 165")
            self._execute_command("text PAN: p to pan view")

        if 6.0 < segment_time < 6.5:
            self._execute_command("goto 1100 175")
            self._execute_command("text COMMAND: : for commands")

    def _segment_architecture(self, segment_time, dt):
        """Architecture segment: Draw diagram."""
        if segment_time < 0.5:
            self._execute_command("goto 100 310")
            self._execute_command("text === ARCHITECTURE ===")
            self._pan_to(80, 290, duration=1.0)

        if 1.5 < segment_time < 2.0:
            self._execute_command("goto 100 330")
            self._execute_command("rect 30 5 │")
            self._execute_command("goto 110 332")
            self._execute_command("text Canvas")

        if 3.0 < segment_time < 3.5:
            self._execute_command("goto 135 332")
            self._execute_command("text -> Viewport -> Renderer")

        if 5.0 < segment_time < 5.5:
            self._execute_command("goto 100 345")
            self._execute_command("text Sparse dict[(x,y)] storage")

    def _segment_productivity(self, segment_time, dt):
        """Productivity segment: TODO lists, notes."""
        if segment_time < 0.5:
            self._execute_command("goto 600 310")
            self._execute_command("text === PRODUCTIVITY ===")
            self._pan_to(580, 290, duration=1.0)

        if 1.5 < segment_time < 2.0:
            self._execute_command("goto 600 330")
            self._execute_command("text TODO:")

        if 2.5 < segment_time < 3.0:
            self._execute_command("goto 600 335")
            self._execute_command("text [ ] Design wireframes")

        if 3.5 < segment_time < 4.0:
            self._execute_command("goto 600 340")
            self._execute_command("text [x] Create canvas editor")

        if 5.0 < segment_time < 5.5:
            self._execute_command("goto 600 350")
            self._execute_command("text Infinite canvas = infinite ideas")

    def _segment_api(self, segment_time, dt):
        """API segment: External control."""
        if segment_time < 0.5:
            self._execute_command("goto 1100 310")
            self._execute_command("text === HEADLESS API ===")
            self._pan_to(1080, 290, duration=1.0)

        if 1.5 < segment_time < 2.0:
            self._execute_command("goto 1100 330")
            self._execute_command("text mygrid-ctl text 'Hi'")

        if 3.0 < segment_time < 3.5:
            self._execute_command("goto 1100 340")
            self._execute_command("text TCP socket + FIFO API")

        if 5.0 < segment_time < 5.5:
            self._execute_command("goto 1100 350")
            self._execute_command("text Automate anything!")

    def _segment_easter_egg(self, segment_time, dt):
        """Easter egg segment: The answer."""
        if segment_time < 0.5:
            self._pan_to(1320, 410, duration=2.0)

        if 2.5 < segment_time < 3.0:
            self._execute_command("goto 1337 420")
            self._execute_command("text 42")
            self._execute_command("goto 1320 425")
            self._execute_command("text (The Ultimate Answer)")

    # ========== MAIN DEMO LOOP ==========

    def run_demo(self, total_duration=75):
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
            self._show_message("Demo complete! github.com/jcaldwell/my-grid")
            status = self._get_status_line()
            self.renderer.render(self.canvas, self.viewport, status)
            time.sleep(2)


def run_demo(duration=75):
    """Entry point for demo mode."""
    def _curses_main(stdscr):
        demo = VisualAutoDemo(stdscr)
        demo.run_demo(duration)

    curses.wrapper(_curses_main)


if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 75
    print(f"Running my-grid visual auto-demo for {duration} seconds...")
    print("This demo runs the actual curses UI with programmed actions.")
    print("VHS will record the visual canvas display.")
    run_demo(duration)
