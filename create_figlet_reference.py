#!/usr/bin/env python3
"""
Create a figlet font reference canvas.

Demonstrates all available figlet fonts with sample text.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from canvas import Canvas
from viewport import Viewport
from project import Project, ProjectMetadata
from external import draw_figlet, get_figlet_fonts, tool_available

def create_figlet_reference():
    """Create a canvas with figlet font examples."""

    if not tool_available("figlet"):
        print("Error: figlet command not found")
        print("Install with: sudo apt-get install figlet")
        return 1

    # Get available fonts
    fonts = get_figlet_fonts()

    if not fonts:
        print("No figlet fonts found")
        return 1

    print(f"Found {len(fonts)} figlet fonts")

    # Create canvas and viewport
    canvas = Canvas()
    viewport = Viewport(width=120, height=50)

    # Starting position
    y = 0
    x_col1 = 0
    x_col2 = 80

    # Sample text for demonstration
    sample_text = "ABCabc"

    # Create two columns of fonts
    col1_fonts = fonts[:len(fonts)//2]
    col2_fonts = fonts[len(fonts)//2:]

    # Column 1
    for font in col1_fonts:
        # Write font name as label
        label = f"--- {font} ---"
        for i, char in enumerate(label):
            canvas.set(x_col1 + i, y, char)
        y += 1

        # Generate figlet
        result = draw_figlet(sample_text, font)
        if result.success:
            for line in result.lines:
                for i, char in enumerate(line):
                    if char != ' ':
                        canvas.set(x_col1 + i, y, char)
                y += 1
        else:
            error_msg = f"Error: {result.error}"
            for i, char in enumerate(error_msg):
                canvas.set(x_col1 + i, y, char)
            y += 1

        y += 1  # Spacing between fonts

    # Column 2
    y_col2 = 0
    for font in col2_fonts:
        # Write font name as label
        label = f"--- {font} ---"
        for i, char in enumerate(label):
            canvas.set(x_col2 + i, y_col2, char)
        y_col2 += 1

        # Generate figlet
        result = draw_figlet(sample_text, font)
        if result.success:
            for line in result.lines:
                for i, char in enumerate(line):
                    if char != ' ':
                        canvas.set(x_col2 + i, y_col2, char)
                y_col2 += 1
        else:
            error_msg = f"Error: {result.error}"
            for i, char in enumerate(error_msg):
                canvas.set(x_col2 + i, y_col2, char)
            y_col2 += 1

        y_col2 += 1  # Spacing between fonts

    # Add title at the top
    title = "FIGLET FONT REFERENCE"
    title_result = draw_figlet(title, "banner")
    if title_result.success:
        title_y = -15  # Place above the fonts
        for line in title_result.lines:
            for i, char in enumerate(line):
                if char != ' ':
                    canvas.set(i, title_y, char)
            title_y += 1

    # Save to file
    output_file = "figlet-reference.json"
    metadata = ProjectMetadata(
        name="Figlet Font Reference",
        description=f"Examples of all {len(fonts)} available figlet fonts"
    )

    # Create project and save
    project = Project(metadata=metadata)
    viewport.y = -15  # Start viewport at title
    project.save(canvas, viewport, filepath=output_file)

    print(f"Created {output_file}")
    print(f"Open with: python3 mygrid.py {output_file}")
    print(f"\nFonts included: {', '.join(fonts)}")

    return 0

if __name__ == "__main__":
    sys.exit(create_figlet_reference())
