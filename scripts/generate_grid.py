#!/usr/bin/env python3
"""
Generate coordinate grid on my-grid canvas.

Usage:
    python generate_grid.py [width] [height] [spacing]

Examples:
    python generate_grid.py              # Default 100x100, spacing 10
    python generate_grid.py 200 100      # Custom size
    python generate_grid.py 100 100 20   # Custom spacing
"""

import sys
from pathlib import Path

try:
    from mygrid_client import MyGridClient, MyGridError
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from mygrid_client import MyGridClient, MyGridError


def generate_grid(width=100, height=100, spacing=10):
    """Generate coordinate grid on canvas."""
    client = MyGridClient()

    print(f"Generating {width}x{height} grid with spacing {spacing}...")

    # Draw intersection points
    for x in range(0, width + 1, spacing):
        for y in range(0, height + 1, spacing):
            client.goto(x, y)
            client.text("+")

    # Draw horizontal lines
    for y in range(0, height + 1, spacing):
        for x in range(0, width + 1):
            if x % spacing != 0:  # Skip intersection points
                client.goto(x, y)
                client.text("-")

    # Draw vertical lines
    for x in range(0, width + 1, spacing):
        for y in range(0, height + 1):
            if y % spacing != 0:  # Skip intersection points
                client.goto(x, y)
                client.text("|")

    # Add coordinate labels
    for x in range(0, width + 1, spacing):
        client.goto(x, -1)
        client.text(str(x))

    for y in range(spacing, height + 1, spacing):
        client.goto(-3, y)
        client.text(str(y).rjust(2))

    print(f"Grid generated: {width}x{height}")


def main():
    width = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    height = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    spacing = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    try:
        generate_grid(width, height, spacing)
    except MyGridError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
