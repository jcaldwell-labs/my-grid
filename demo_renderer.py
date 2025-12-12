#!/usr/bin/env python3
"""
Demo script to test the renderer with canvas and viewport.

Run: python demo_renderer.py

Controls:
    wasd / arrows: Move cursor
    WASD: Pan viewport
    g: Toggle major grid
    G: Toggle minor grid
    o: Center on origin
    c: Center on cursor
    r: Draw a test rectangle
    t: Write test text
    x: Clear cell at cursor
    q: Quit
"""

import curses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from canvas import Canvas
from viewport import Viewport
from renderer import Renderer, create_status_line


def main(stdscr):
    # Initialize components
    canvas = Canvas()
    viewport = Viewport()
    renderer = Renderer(stdscr)

    # Set viewport size to terminal size
    height, width = renderer.get_terminal_size()
    viewport.resize(width, height - 1)  # Reserve 1 line for status

    # Draw some initial content
    canvas.write_text(0, 0, "Hello, ASCII Canvas!")
    canvas.draw_rect(5, 3, 20, 8)
    canvas.write_text(7, 5, "Use wasd to move")
    canvas.write_text(7, 6, "Press 'q' to quit")

    mode = "NAV"

    while True:
        # Render frame
        status = create_status_line(viewport, mode)
        renderer.render(canvas, viewport, status)

        # Handle input
        key = renderer.get_input()

        # Handle resize
        if key == curses.KEY_RESIZE:
            height, width = renderer.get_terminal_size()
            viewport.resize(width, height - 1)
            continue

        # Quit
        if key == ord('q'):
            break

        # Cursor movement (wasd / arrows)
        if key in (ord('w'), curses.KEY_UP):
            viewport.move_cursor(0, -1)
            viewport.ensure_cursor_visible(margin=3)
        elif key in (ord('s'), curses.KEY_DOWN):
            viewport.move_cursor(0, 1)
            viewport.ensure_cursor_visible(margin=3)
        elif key in (ord('a'), curses.KEY_LEFT):
            viewport.move_cursor(-1, 0)
            viewport.ensure_cursor_visible(margin=3)
        elif key in (ord('d'), curses.KEY_RIGHT):
            viewport.move_cursor(1, 0)
            viewport.ensure_cursor_visible(margin=3)

        # Viewport panning (WASD)
        elif key == ord('W'):
            viewport.pan(0, -5)
        elif key == ord('S'):
            viewport.pan(0, 5)
        elif key == ord('A'):
            viewport.pan(-5, 0)
        elif key == ord('D'):
            viewport.pan(5, 0)

        # Grid toggles
        elif key == ord('g'):
            renderer.grid.show_major_lines = not renderer.grid.show_major_lines
        elif key == ord('G'):
            renderer.grid.show_minor_lines = not renderer.grid.show_minor_lines

        # Centering
        elif key == ord('o'):
            viewport.center_on_origin()
        elif key == ord('c'):
            viewport.center_on_cursor()

        # Drawing
        elif key == ord('r'):
            cx, cy = viewport.cursor.x, viewport.cursor.y
            canvas.draw_rect(cx, cy, 10, 5)
        elif key == ord('t'):
            cx, cy = viewport.cursor.x, viewport.cursor.y
            canvas.write_text(cx, cy, "Test!")

        # Clear cell
        elif key == ord('x'):
            canvas.clear(viewport.cursor.x, viewport.cursor.y)

        # Type character at cursor
        elif 32 <= key <= 126:  # Printable ASCII
            canvas.set(viewport.cursor.x, viewport.cursor.y, chr(key))
            viewport.move_cursor(1, 0)
            viewport.ensure_cursor_visible(margin=3)


if __name__ == "__main__":
    curses.wrapper(main)
