#!/usr/bin/env python3
"""
Auto-demo module for my-grid - creates architecture diagram showcase.

VHS-compatible: Single while loop, time-based transitions, 20 FPS.
Demonstrates my-grid as a productivity canvas tool for creating
system diagrams, similar to Miro or Lucidchart but in the terminal.
"""

import time
import curses

from canvas import Canvas
from viewport import Viewport
from renderer import Renderer
from modes import ModeStateMachine, ModeConfig
from project import Project


class MyGridDemo:
    """Automated demo showing my-grid creating a system architecture diagram."""

    def __init__(self, stdscr: "curses.window"):
        self.stdscr = stdscr
        self.canvas = Canvas()
        self.viewport = Viewport()
        self.renderer = Renderer(stdscr)
        self.mode_config = ModeConfig()
        self.state_machine = ModeStateMachine(
            self.canvas, self.viewport, self.mode_config
        )
        self.project = Project()

        # Initialize viewport size
        height, width = self.renderer.get_terminal_size()
        self.viewport.resize(width, height - 1)

        # Demo state
        self.demo_time = 0
        self.running = True

    def draw_box(self, x: int, y: int, width: int, height: int, label: str):
        """Draw a box with a centered label."""
        # Draw box outline
        self.canvas.draw_rect(x, y, width, height)

        # Center the label
        label_x = x + (width - len(label)) // 2
        label_y = y + height // 2
        self.canvas.write_text(label_x, label_y, label)

    def draw_arrow(self, x1: int, y1: int, x2: int, y2: int):
        """Draw a simple horizontal arrow between two points."""
        # Draw line
        self.canvas.draw_line(x1, y1, x2, y2, "-")
        # Add arrowhead
        if x2 > x1:
            self.canvas.set(x2 - 1, y2, ">")
        else:
            self.canvas.set(x2 + 1, y2, "<")

    def run_demo(self, duration: int = 60):
        """
        Run automated demo showing my-grid as a productivity canvas.

        VHS-compatible: Single while loop with time-based transitions.
        Includes: Architecture diagrams, brainstorming, TODOs, and easter eggs!
        """
        # Demo segments with cumulative time boundaries (faster pacing!)
        # Each segment: (start_time, description, actions)
        segments = [
            (0, "Title"),
            (2, "Draw Architecture Section"),
            (5, "Connect Architecture"),
            (8, "Add Labels"),
            (9, "Show Grid Overlay"),  # Turn on grid early - looks cool!
            (11, "Pan to Brainstorming"),
            (13, "Draw Post-It Notes"),
            (18, "Pan to TODO Section"),
            (20, "Draw TODO List"),
            (24, "Add Don't Panic Easter Egg"),
            (27, "Set Architecture Bookmark"),
            (29, "Set Brainstorm Bookmark"),
            (31, "Set TODO Bookmark"),
            (33, "Jump to Brainstorm (centered)"),
            (36, "Jump to TODO (centered)"),
            (39, "Jump to Architecture (centered)"),
            (42, "Pan to Answer: 42"),
            (46, "Pan Final Overview"),
            (52, "End"),
        ]

        try:
            # Curses setup
            curses.curs_set(0)  # Hide cursor
            self.stdscr.nodelay(1)  # Non-blocking input
            self.stdscr.clear()

            start_time = time.time()
            last_time = start_time
            current_segment_idx = 0

            # Single continuous loop - VHS compatible
            while time.time() - start_time < duration and self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                elapsed = current_time - start_time

                # Find current segment
                new_segment_idx = current_segment_idx
                for i, (boundary, _) in enumerate(segments):
                    if elapsed >= boundary:
                        new_segment_idx = i

                # Execute segment actions when transitioning
                if new_segment_idx != current_segment_idx:
                    current_segment_idx = new_segment_idx
                    _, desc = segments[current_segment_idx]
                    self._execute_segment(desc)

                # Render current state
                status = self._get_status_for_segment(current_segment_idx, elapsed)
                self.renderer.render(self.canvas, self.viewport, status)

                # Check for early exit (Ctrl+C)
                try:
                    key = self.stdscr.getch()
                    if key == ord("q") or key == 3:  # q or Ctrl+C
                        self.running = False
                except curses.error:
                    pass

                # 20 FPS for VHS compatibility
                time.sleep(0.05)

        finally:
            curses.curs_set(1)  # Restore cursor
            self.stdscr.nodelay(0)

    def _center_on_position(self, x: int, y: int):
        """Center viewport on a position."""
        # Get viewport dimensions
        vp_width = self.viewport.width
        vp_height = self.viewport.height

        # Calculate center offset
        center_x = x - vp_width // 2
        center_y = y - vp_height // 2

        # Pan to center the position
        self.viewport.pan_to(center_x, center_y)
        self.viewport.cursor.set(x, y)

    def _execute_segment(self, description: str):
        """Execute actions for a demo segment."""
        if description == "Title":
            # Start at origin
            self.viewport.cursor.set(10, 5)
            self.canvas.write_text(8, 5, "my-grid: Productivity Canvas Demo")

        # SECTION 1: Architecture (left side, ~x=0-100)
        elif description == "Draw Architecture Section":
            # Draw all three boxes quickly
            self.draw_box(10, 10, 18, 5, "Frontend")
            self.draw_box(40, 10, 18, 5, "API")
            self.draw_box(70, 10, 18, 5, "Database")
            self.viewport.cursor.set(50, 12)

        elif description == "Connect Architecture":
            # Connect the boxes
            self.draw_arrow(28, 12, 40, 12)
            self.draw_arrow(58, 12, 70, 12)

        elif description == "Add Labels":
            self.canvas.write_text(32, 10, "HTTP")
            self.canvas.write_text(62, 10, "SQL")

        # SECTION 2: Brainstorming (middle, ~x=120-200, diagonal layout)
        elif description == "Pan to Brainstorming":
            self._center_on_position(150, 14)

        elif description == "Draw Post-It Notes":
            # Post-it style brainstorming notes - spread out diagonally
            self.draw_box(130, 4, 22, 5, "Feature Ideas")
            self.canvas.write_text(132, 6, "- Dark mode")
            self.canvas.write_text(132, 7, "- Export SVG")
            self.canvas.write_text(132, 8, "- Plugins")

            self.draw_box(158, 9, 22, 5, "User Stories")
            self.canvas.write_text(160, 11, "- Quick nav")
            self.canvas.write_text(160, 12, "- Templates")
            self.canvas.write_text(160, 13, "- Shortcuts")

            self.draw_box(128, 14, 22, 5, "Tech Debt")
            self.canvas.write_text(130, 16, "- Refactor")
            self.canvas.write_text(130, 17, "- Add tests")
            self.canvas.write_text(130, 18, "- Fix #123")

            self.draw_box(156, 19, 22, 5, "Wins! 🎉")
            self.canvas.write_text(158, 21, "- v1.0 shipped")
            self.canvas.write_text(158, 22, "- 42 users!")
            self.canvas.write_text(158, 23, "- Featured!")

        # SECTION 3: TODO List (right side, ~x=220-280)
        elif description == "Pan to TODO Section":
            self._center_on_position(240, 10)

        elif description == "Draw TODO List":
            self.canvas.write_text(225, 5, "Sprint TODO")
            self.canvas.write_text(225, 6, "============")
            self.canvas.write_text(225, 8, "[ ] Fix bug #123")
            self.canvas.write_text(225, 9, "[x] Review PR #456")
            self.canvas.write_text(225, 10, "[ ] Write docs")
            self.canvas.write_text(225, 11, "[x] Ship feature")
            self.canvas.write_text(225, 12, "[ ] Celebrate!")

        elif description == "Add Don't Panic Easter Egg":
            # Hitchhiker's Guide easter egg!
            self.draw_box(223, 15, 18, 5, "")
            self.canvas.write_text(226, 17, "DON'T PANIC")
            self.canvas.write_text(227, 18, "- Guide")

        # BOOKMARKS
        elif description == "Set Architecture Bookmark":
            self.state_machine.bookmarks.set("a", 50, 12, "Architecture")

        elif description == "Set Brainstorm Bookmark":
            self.state_machine.bookmarks.set("b", 150, 14, "Brainstorm")

        elif description == "Set TODO Bookmark":
            self.state_machine.bookmarks.set("t", 240, 10, "TODO")

        # NAVIGATION (centered!)
        elif description == "Jump to Brainstorm (centered)":
            bookmark = self.state_machine.bookmarks.get("b")
            if bookmark:
                self._center_on_position(bookmark.x, bookmark.y)

        elif description == "Jump to TODO (centered)":
            bookmark = self.state_machine.bookmarks.get("t")
            if bookmark:
                self._center_on_position(bookmark.x, bookmark.y)

        elif description == "Jump to Architecture (centered)":
            bookmark = self.state_machine.bookmarks.get("a")
            if bookmark:
                self._center_on_position(bookmark.x, bookmark.y)

        # THE ANSWER TO EVERYTHING
        elif description == "Pan to Answer: 42":
            # Secret section with "42"
            self._center_on_position(42, 42)
            self.draw_box(35, 38, 16, 8, "")
            self.canvas.write_text(38, 40, "The Answer")
            self.canvas.write_text(38, 41, "to Life,")
            self.canvas.write_text(38, 42, "Universe,")
            self.canvas.write_text(38, 43, "& Everything:")
            self.canvas.write_text(42, 44, "42")

        elif description == "Show Grid Overlay":
            self.renderer.grid.show_major_lines = True
            self.renderer.grid.show_origin = True

        elif description == "Pan Final Overview":
            # Wide view showing multiple sections
            self._center_on_position(140, 15)

        elif description == "End":
            pass

    def _get_status_for_segment(self, segment_idx: int, elapsed: float) -> str:
        """Generate status line based on current segment."""
        descriptions = [
            "Productivity Canvas Demo",
            "Architecture: 3-tier system",
            "Connecting services",
            "Adding protocol labels",
            "→ Brainstorming section",
            "Post-it style ideation",
            "→ TODO section",
            "Sprint planning board",
            "Easter egg: DON'T PANIC!",
            "Bookmark: Architecture (m+a)",
            "Bookmark: Brainstorm (m+b)",
            "Bookmark: TODO (m+t)",
            "Jump: Brainstorm (' + b)",
            "Jump: TODO (' + t)",
            "Jump: Architecture (' + a)",
            "Secret: The Answer (42,42)",
            "Grid overlay (g)",
            "Overview: Infinite canvas!",
            "my-grid - terminal productivity",
        ]

        desc = (
            descriptions[segment_idx]
            if segment_idx < len(descriptions)
            else "Exploring canvas..."
        )
        cursor = self.viewport.cursor

        return f" DEMO │ X:{cursor.x:>5} Y:{cursor.y:>5} │ {desc} │ {int(elapsed)}s"


def run_demo(duration: int = 75):
    """Entry point for VHS tape recording."""

    def demo_main(stdscr):
        demo = MyGridDemo(stdscr)
        demo.run_demo(duration)

    curses.wrapper(demo_main)


if __name__ == "__main__":
    import sys

    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 75
    run_demo(duration)
