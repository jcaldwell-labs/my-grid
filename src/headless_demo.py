#!/usr/bin/env python3
"""
Headless demo generator for my-grid.

Generates tutorial content without requiring a terminal/curses.
Perfect for CI/CD, documentation generation, and automated examples.

Includes a few easter eggs from The Hitchhiker's Guide to the Galaxy.
Because 42 is the answer, even if we don't know the question.
"""

from canvas import Canvas
from viewport import Viewport
from renderer import GridSettings
from project import Project
from pathlib import Path
import textwrap


class HeadlessDemo:
    """
    Generate my-grid tutorial content without a terminal.

    DON'T PANIC - this is completely automated.
    """

    def __init__(self):
        self.canvas = Canvas()
        self.viewport = Viewport()
        self.grid = GridSettings()
        self.bookmarks = {}

    def draw_box(self, x: int, y: int, width: int, height: int, label: str = ""):
        """Draw a box with optional centered label."""
        self.canvas.draw_rect(x, y, width, height)
        if label:
            label_x = x + (width - len(label)) // 2
            label_y = y + height // 2
            self.canvas.write_text(label_x, label_y, label)

    def draw_arrow(self, x1: int, y1: int, x2: int, y2: int, char: str = '-'):
        """Draw an arrow between two points."""
        self.canvas.draw_line(x1, y1, x2, y2, char)
        # Add arrowhead
        if x2 > x1:
            self.canvas.set(x2 - 1, y2, '>')
        elif x2 < x1:
            self.canvas.set(x2 + 1, y2, '<')
        elif y2 > y1:
            self.canvas.set(x2, y2 - 1, 'v')
        elif y2 < y1:
            self.canvas.set(x2, y2 + 1, '^')

    def export_to_text(self, bounds: tuple[int, int, int, int] = None) -> str:
        """
        Export canvas to text representation.

        Args:
            bounds: (min_x, min_y, max_x, max_y) to export, or None for all content
        """
        if self.canvas.cell_count == 0:
            return ""

        if bounds:
            min_x, min_y, max_x, max_y = bounds
        else:
            # Calculate bounds from canvas content
            bbox = self.canvas.bounding_box()
            if not bbox:
                return ""
            min_x, min_y, max_x, max_y = bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y

        lines = []
        for y in range(min_y, max_y + 1):
            line = []
            for x in range(min_x, max_x + 1):
                char = self.canvas.get_char(x, y)
                line.append(char if char != ' ' else ' ')
            lines.append(''.join(line).rstrip())

        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        return '\n'.join(lines)

    def clear(self):
        """Clear the canvas. Mostly harmless."""
        self.canvas.clear_all()
        self.bookmarks.clear()


class TutorialGenerator:
    """
    Generate comprehensive my-grid tutorial with examples.

    "This must be Thursday. I never could get the hang of Thursdays."
    - Arthur Dent (probably learning my-grid)
    """

    def __init__(self):
        self.demo = HeadlessDemo()
        self.sections = []

    def add_section(self, title: str, description: str, example_code: str = None,
                    canvas_output: str = None, notes: str = None):
        """Add a tutorial section."""
        section = {
            'title': title,
            'description': description,
            'example_code': example_code,
            'canvas_output': canvas_output,
            'notes': notes
        }
        self.sections.append(section)

    def generate_basics_tutorial(self):
        """Generate basic usage tutorial."""

        # Section 1: Starting my-grid
        self.add_section(
            "Getting Started - Don't Panic!",
            textwrap.dedent("""
            Welcome to my-grid, the ASCII canvas editor for developers who prefer
            to keep their hands on the keyboard and their minds in the terminal.

            Starting my-grid is as easy as knowing where your towel is:
            """),
            example_code="""
            # Start with empty canvas
            python mygrid.py

            # Open existing project
            python mygrid.py architecture.json

            # Import text file
            python mygrid.py diagram.txt
            """,
            notes="Tip: Always know where your .json project files are."
        )

        # Section 2: Modes
        self.add_section(
            "The Five Modes (and how not to get lost in them)",
            textwrap.dedent("""
            my-grid has 5 modes. Think of them as different floors in the
            Hitchhiker's Guide offices - each serves a purpose.

            Mode Indicator: Look at the status bar (top left)
            """),
            example_code="""
            NAV  - Navigation mode (default) - Move around with WASD or arrows
            EDIT - Edit mode (press 'i')     - Type characters on canvas
            PAN  - Pan mode (press 'p')      - Move the viewport around
            COMMAND - Command mode (press ':') - Execute commands
            MARK - Bookmark mode (press 'm' or '\'') - Set/jump to marks

            Press ESC to exit any mode (your panic button)
            """,
            notes="ESC is your towel - always brings you back to safety (NAV mode)."
        )

        # Section 3: Drawing boxes
        self.demo.clear()
        self.demo.draw_box(5, 2, 20, 5, "Hello, World!")

        self.add_section(
            "Drawing Your First Box",
            textwrap.dedent("""
            Boxes are the answer to life, the universe, and architectural diagrams.
            Well, part of the answer. The number is still 42.
            """),
            example_code="""
            # In NAV mode, move cursor to starting position
            # Then enter COMMAND mode
            Press: :

            # Draw a 20x5 box at cursor position
            Type: rect 20 5
            Press: Enter

            # Draw a box with custom border character
            Type: rect 20 5 #
            Press: Enter
            """,
            canvas_output=self.demo.export_to_text((0, 0, 30, 8)),
            notes="The box appears where your cursor is. Much like the Restaurant at the End of the Universe, location matters."
        )

        # Section 4: System Architecture Example
        self.demo.clear()

        # Draw a proper system architecture
        self.demo.draw_box(0, 0, 18, 5, "Frontend")
        self.demo.draw_box(30, 0, 18, 5, "API Gateway")
        self.demo.draw_box(60, 0, 18, 5, "Database")

        # Connections
        self.demo.draw_arrow(18, 2, 30, 2)
        self.demo.draw_arrow(48, 2, 60, 2)

        # Labels
        self.demo.canvas.write_text(21, 1, "HTTP")
        self.demo.canvas.write_text(51, 1, "SQL")

        # Add some fun details
        self.demo.canvas.write_text(3, 2, "React")
        self.demo.canvas.write_text(32, 2, "Node.js")
        self.demo.canvas.write_text(63, 2, "Postgres")

        self.add_section(
            "Example: System Architecture Diagram",
            textwrap.dedent("""
            Let's create a complete system architecture. This is what the
            Heart of Gold's planning computer would draw, if it weren't busy
            calculating improbability drives.
            """),
            example_code="""
            # Draw three service boxes
            :goto 0 0
            :rect 18 5
            :text Frontend

            :goto 30 0
            :rect 18 5
            :text API Gateway

            :goto 60 0
            :rect 18 5
            :text Database

            # Connect them with arrows
            :line 30 2 -    # Line from Frontend to API
            :line 60 2 -    # Line from API to Database

            # Add protocol labels
            :goto 21 1
            :text HTTP

            :goto 51 1
            :text SQL
            """,
            canvas_output=self.demo.export_to_text((0, 0, 80, 6)),
            notes="Professional diagrams in 42 seconds or less!"
        )

        # Section 5: Bookmarks
        self.demo.clear()
        self.demo.draw_box(10, 5, 15, 4, "Component A")
        self.demo.draw_box(50, 20, 15, 4, "Component B")
        self.demo.canvas.write_text(15, 9, "Mark: 'a'")
        self.demo.canvas.write_text(55, 24, "Mark: 'b'")
        self.demo.draw_arrow(25, 7, 50, 22, '.')

        self.add_section(
            "Bookmarks - Your Infinite Improbability Navigator",
            textwrap.dedent("""
            With an infinite canvas, you need a way to jump around.
            Bookmarks are like the Infinite Improbability Drive, but more predictable.
            You can set up to 36 bookmarks (a-z, 0-9).
            """),
            example_code="""
            # Set bookmark 'a' at current cursor position
            Press: m
            Press: a

            # Jump to bookmark 'a'
            Press: '
            Press: a

            # Via commands
            :mark a           # Set bookmark 'a' at cursor
            :mark b 50 20     # Set bookmark 'b' at (50, 20)
            :marks            # List all bookmarks
            :delmark a        # Delete bookmark 'a'
            :delmarks         # Delete all bookmarks (use carefully!)
            """,
            canvas_output=self.demo.export_to_text((5, 3, 70, 26)),
            notes="Pro tip: Mark important components before your infinite canvas becomes infinitely confusing."
        )

        # Section 6: Grid and Navigation
        self.add_section(
            "Grid Overlay - Because Space is Big",
            textwrap.dedent("""
            "Space is big. You just won't believe how vastly, hugely, mind-bogglingly
            big it is." - Douglas Adams

            The grid helps you navigate this vastness.
            """),
            example_code="""
            # Toggle major grid (every 10 units)
            Press: g

            # Toggle minor grid (every 1 unit)
            Press: G

            # Toggle origin marker
            Press: 0

            # Set custom grid interval
            :grid 5    # Major grid every 5 units
            :grid 20   # Major grid every 20 units

            # Configure via commands
            :grid major   # Toggle major grid
            :grid minor   # Toggle minor grid
            """,
            notes="The grid overlay doesn't affect your canvas content. It's just a guide, like the Guide itself."
        )

        # Section 7: Fast Navigation
        self.add_section(
            "Fast Navigation - Ludicrous Speed!",
            textwrap.dedent("""
            Moving one cell at a time is like traveling at regular speed.
            Sometimes you need to go plaid.
            """),
            example_code="""
            # Normal movement (1 cell)
            w/s/a/d           # Up/Down/Left/Right
            Arrow keys        # Also work

            # Fast movement (10 cells - LUDICROUS SPEED!)
            W/S/A/D           # Shift + movement

            # Jump to coordinates
            :goto 100 50      # Jump to x=100, y=50
            :g 100 50         # Short form

            # Pan mode (move viewport, not cursor)
            p                 # Toggle pan mode
            w/s/a/d           # Move viewport while in pan mode
            p or ESC          # Exit pan mode
            """,
            notes="Remember: 'W' is 10x faster than 'w'. Like a Vogon constructor fleet, but less destructive."
        )

        # Section 8: Saving and Loading
        self.add_section(
            "Saving Your Work - Don't Lose Your Towel",
            textwrap.dedent("""
            The universe may not care about your diagrams, but git does.
            my-grid saves in JSON format, perfect for version control.
            """),
            example_code="""
            # Save current project
            Press: Ctrl+S
            # Or via command:
            :w
            :write

            # Save with new name
            :saveas my-architecture.json

            # Save and quit
            :wq

            # Quit without saving
            :q

            # If you have unsaved changes, you'll get a warning
            # Press 'q' again to confirm, or any other key to cancel
            """,
            notes="Pro tip: Commit your .json files to git. Your future self will thank you."
        )

        # Section 9: Export and Import
        self.add_section(
            "Export to Text - Share Your Wisdom",
            textwrap.dedent("""
            Sometimes you need plain ASCII art for documentation, comments,
            or impressing Vogons with your poetry (though that's unlikely to work).
            """),
            example_code="""
            # Export current canvas to text
            :export diagram.txt

            # Export without filename (auto-generates name)
            :export

            # Import text file (converts to my-grid canvas)
            :import existing-diagram.txt

            # Or load text file on startup
            python mygrid.py diagram.txt
            """,
            notes="Exported text files are pure ASCII. Include them in code comments, README files, or messages to alien civilizations."
        )

        # Section 10: Easter Egg Section
        self.demo.clear()
        self.demo.canvas.write_text(10, 5, "  ___   ___  ")
        self.demo.canvas.write_text(10, 6, " /   \\ /   \\ ")
        self.demo.canvas.write_text(10, 7, " \\___/ \\___/ ")
        self.demo.canvas.write_text(10, 8, "             ")
        self.demo.canvas.write_text(10, 9, "    DON'T    ")
        self.demo.canvas.write_text(10, 10, "    PANIC    ")

        self.demo.draw_box(8, 4, 16, 8)

        self.add_section(
            "Advanced Tips - The Ultimate Answer",
            textwrap.dedent("""
            You've made it this far. You're clearly a hoopy frood who knows
            where their towel is. Here are some advanced tips:
            """),
            example_code="""
            # Set coordinate system direction
            :ydir up      # Y increases upward (mathematical)
            :ydir down    # Y increases downward (screen coordinates)

            # Set custom origin point
            :origin here          # Set origin at current cursor
            :origin 0 0           # Set origin at (0, 0)

            # Draw lines with custom characters
            :line 50 10 =         # Line with '=' character
            :line 50 10 *         # Line with '*' character

            # Chain commands (create workflow scripts)
            # Put commands in a text file and execute them
            # (Feature idea for future: :source commands.txt)

            # The Answer to Everything
            :goto 42 42           # The ultimate coordinates
            :text The Answer
            """,
            canvas_output=self.demo.export_to_text((5, 3, 30, 13)),
            notes=textwrap.dedent("""
            "The Answer to the Great Question... Of Life, the Universe and Everything... Is...
            Forty-two." - Deep Thought

            And now you know where to find it on your canvas.
            """)
        )

        # Section 11: Help
        self.add_section(
            "Getting Help - The Guide Is Your Friend",
            textwrap.dedent("""
            When in doubt, consult the Guide. It's less snarky than the original,
            but just as helpful.
            """),
            example_code="""
            # Show help screen
            Press: F1

            # Or quit and use --help
            python mygrid.py --help

            # Check version
            python mygrid.py --version
            """,
            notes="Remember: DON'T PANIC. The help system has all the answers (well, most of them)."
        )

    def generate_markdown(self) -> str:
        """Generate markdown tutorial document."""
        output = []

        # Header
        output.append("# my-grid Tutorial")
        output.append("")
        output.append("*An ASCII Canvas Editor for the Aspiring Hitchhiker*")
        output.append("")
        output.append("---")
        output.append("")

        # Introduction
        output.append(textwrap.dedent("""
        ## Introduction

        > "Don't Panic." - The Hitchhiker's Guide to the Galaxy

        Welcome to my-grid, a terminal-based ASCII canvas editor with vim-style navigation.
        Whether you're creating system architecture diagrams, flow charts, mind maps, or
        planning the destruction of Earth for a hyperspace bypass, my-grid has you covered.

        This tutorial will guide you through the basics and beyond. Look for easter eggs
        from The Hitchhiker's Guide to the Galaxy along the way. After all, life's too
        short to be entirely serious about ASCII art.

        ---
        """))

        # Generate sections
        for i, section in enumerate(self.sections, 1):
            output.append(f"## {i}. {section['title']}")
            output.append("")
            output.append(section['description'])
            output.append("")

            if section['example_code']:
                output.append("**Commands:**")
                output.append("```")
                output.append(section['example_code'].strip())
                output.append("```")
                output.append("")

            if section['canvas_output']:
                output.append("**Canvas Output:**")
                output.append("```")
                output.append(section['canvas_output'])
                output.append("```")
                output.append("")

            if section['notes']:
                output.append(f"*{section['notes']}*")
                output.append("")

            output.append("---")
            output.append("")

        # Footer
        output.append(textwrap.dedent("""
        ## Conclusion

        You've completed the my-grid tutorial! You now know:

        - ✅ How to navigate the infinite canvas
        - ✅ How to draw boxes and lines
        - ✅ How to use bookmarks for quick navigation
        - ✅ How to save and export your work
        - ✅ Where to find the number 42 on your canvas

        ### Next Steps

        1. **Create something** - Open my-grid and try the examples
        2. **Experiment** - The canvas is infinite, go wild
        3. **Share** - Export your diagrams and include them in documentation
        4. **Contribute** - Found a bug? Have an idea? Open an issue!

        ### Quick Reference

        | Action | Key/Command |
        |--------|-------------|
        | Move cursor | `wasd` or arrows |
        | Fast move | `WASD` |
        | Edit mode | `i` |
        | Command mode | `:` |
        | Exit mode | `Esc` |
        | Set bookmark | `m` + key |
        | Jump to bookmark | `'` + key |
        | Save | `Ctrl+S` or `:w` |
        | Quit | `:q` |
        | Help | `F1` |

        ### Resources

        - **GitHub**: github.com/yourusername/my-grid
        - **Documentation**: See `CLAUDE.md` in the repository
        - **Examples**: Check the `demo/` directory

        ### Final Words

        > "So long, and thanks for all the fish!" - Douglas Adams

        Or in our case: "So long, and thanks for all the ASCII art!"

        Now go forth and create amazing diagrams. And remember: DON'T PANIC.

        ---

        *Generated with love (and a headless demo generator) on*
        *a small planet in the unfashionable end of the Western Spiral Arm of the Galaxy.*

        **Answer to everything**: Try `:goto 42 42` and `:text The Answer`
        """))

        return '\n'.join(output)

    def generate_plain_text(self) -> str:
        """Generate plain text tutorial document."""
        output = []

        # Header
        output.append("=" * 78)
        output.append("MY-GRID TUTORIAL")
        output.append("An ASCII Canvas Editor for the Aspiring Hitchhiker")
        output.append("=" * 78)
        output.append("")

        # Introduction
        output.append('"Don\'t Panic." - The Hitchhiker\'s Guide to the Galaxy')
        output.append("")
        output.append("Welcome to my-grid! This tutorial will guide you through everything")
        output.append("you need to know. Look for Hitchhiker's Guide easter eggs along the way.")
        output.append("")
        output.append("-" * 78)
        output.append("")

        # Sections
        for i, section in enumerate(self.sections, 1):
            output.append(f"{i}. {section['title'].upper()}")
            output.append("")
            # Wrap description
            for line in section['description'].split('\n'):
                if line.strip():
                    wrapped = textwrap.fill(line.strip(), width=76)
                    output.append(wrapped)
                    output.append("")

            if section['example_code']:
                output.append("Commands:")
                output.append("")
                for line in section['example_code'].strip().split('\n'):
                    output.append(f"    {line}")
                output.append("")

            if section['canvas_output']:
                output.append("Canvas Output:")
                output.append("")
                for line in section['canvas_output'].split('\n'):
                    output.append(f"    {line}")
                output.append("")

            if section['notes']:
                wrapped = textwrap.fill(section['notes'], width=76, initial_indent="NOTE: ")
                output.append(wrapped)
                output.append("")

            output.append("-" * 78)
            output.append("")

        # Footer
        output.append("CONCLUSION")
        output.append("")
        output.append("You've completed the my-grid tutorial! Now go create amazing diagrams.")
        output.append("And remember: DON'T PANIC.")
        output.append("")
        output.append("Answer to everything: Try :goto 42 42 and :text The Answer")
        output.append("")
        output.append("=" * 78)
        output.append("Generated on a small planet in the Western Spiral Arm of the Galaxy")
        output.append("=" * 78)

        return '\n'.join(output)


def generate_tutorial(output_format: str = 'markdown', output_path: str = None):
    """
    Generate my-grid tutorial in specified format.

    Args:
        output_format: 'markdown' or 'text'
        output_path: Path to save output, or None for stdout
    """
    generator = TutorialGenerator()
    generator.generate_basics_tutorial()

    if output_format == 'markdown':
        content = generator.generate_markdown()
        default_name = 'my-grid-tutorial.md'
    else:
        content = generator.generate_plain_text()
        default_name = 'my-grid-tutorial.txt'

    if output_path:
        path = Path(output_path)
        path.write_text(content)
        print(f"Tutorial saved to: {path}")
    else:
        # Default output path
        path = Path(default_name)
        path.write_text(content)
        print(f"Tutorial saved to: {path}")

    return content


if __name__ == "__main__":
    import sys

    # Parse arguments
    format_type = sys.argv[1] if len(sys.argv) > 1 else 'markdown'
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if format_type not in ['markdown', 'text']:
        print("Usage: python headless_demo.py [markdown|text] [output_file]")
        print("Examples:")
        print("  python headless_demo.py markdown tutorial.md")
        print("  python headless_demo.py text tutorial.txt")
        sys.exit(1)

    generate_tutorial(format_type, output_file)
