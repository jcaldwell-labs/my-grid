#!/usr/bin/env python3
"""
Sticky Notes Demo - Large canvas with clustered note areas.

Creates a canvas approximately 12x larger than a typical terminal (80x24 -> 960x288)
with several "piles" of sticky notes that can be navigated via bookmarks.

Demonstrates:
- Large infinite canvas with content spread across regions
- Smooth scrolling between areas
- Bookmark-based navigation
- External tool integration (boxes, figlet)
- Clustered "sticky note" layouts

Usage:
    1. Start my-grid with --server:
       python mygrid.py --server

    2. Run this demo:
       python demo/sticky_notes_demo.py

Cluster Layout (12x terminal size = ~960x288):

    [0,0]                                                              [960,0]
    +------------------------------------------------------------------+
    |  CLUSTER A: Ideas       |                  CLUSTER B: Sprint     |
    |  (50, 30)               |                  (500, 40)             |
    |  +-----------+          |                  +-----------+         |
    |  | Sticky 1  |          |                  | Task 1    |         |
    |  +-----------+          |                  +-----------+         |
    |       +-----------+     |                       +-----------+    |
    |       | Sticky 2  |     |                       | Task 2    |    |
    |       +-----------+     |                       +-----------+    |
    |                         |                                        |
    |-------------------------|----------------------------------------|
    |                         |                                        |
    |  CLUSTER C: Architecture|                  CLUSTER D: Notes      |
    |  (100, 180)             |                  (600, 200)            |
    |  +-------+   +-------+  |                  +-----------+         |
    |  | Box A |-->| Box B |  |                  | Meeting   |         |
    |  +-------+   +-------+  |                  | notes...  |         |
    |                         |                  +-----------+         |
    +------------------------------------------------------------------+
    [0,288]                                                            [960,288]
"""

import subprocess
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


# Configuration
MYGRID_CTL = Path(__file__).parent.parent / "mygrid-ctl"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

# Canvas dimensions (12x typical terminal)
CANVAS_WIDTH = 960  # 80 * 12
CANVAS_HEIGHT = 288  # 24 * 12

# Animation settings
SMOOTH_SCROLL_STEPS = 15
SMOOTH_SCROLL_DELAY = 0.03
COMMAND_DELAY = 0.05


@dataclass
class Cluster:
    """A cluster of sticky notes at a location."""

    name: str
    bookmark: str
    center_x: int
    center_y: int
    description: str


# Define the four clusters
CLUSTERS = [
    Cluster("Ideas", "i", 80, 50, "Brainstorming & Feature Ideas"),
    Cluster("Sprint", "s", 550, 60, "Current Sprint Tasks"),
    Cluster("Architecture", "a", 120, 180, "System Architecture"),
    Cluster("Notes", "n", 620, 200, "Meeting Notes & Documentation"),
]


def ctl(*args, host=DEFAULT_HOST, port=DEFAULT_PORT) -> tuple[int, str]:
    """Execute mygrid-ctl command."""
    cmd = [sys.executable, str(MYGRID_CTL), "--host", host, "--port", str(port), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def ctl_batch(
    commands: list[str], host=DEFAULT_HOST, port=DEFAULT_PORT
) -> tuple[int, str]:
    """Execute batch commands."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("\n".join(commands))
        temp_path = f.name

    result = ctl("batch", temp_path, host=host, port=port)
    Path(temp_path).unlink()
    return result


def wait(seconds: float = COMMAND_DELAY):
    """Wait between commands."""
    time.sleep(seconds)


def check_connection() -> bool:
    """Check if my-grid server is running."""
    code, output = ctl("status")
    if code != 0:
        print(f"Error: Cannot connect to my-grid server")
        print(f"Start my-grid with: python mygrid.py --server")
        return False
    return True


def get_current_position() -> tuple[int, int]:
    """Get current cursor position from status."""
    code, output = ctl("status", "--json")
    if code == 0:
        import json

        try:
            # Parse the nested JSON
            data = json.loads(output.strip().split("\n")[0])
            if data.get("status") == "ok":
                state = json.loads(data.get("message", "{}"))
                return state["cursor"]["x"], state["cursor"]["y"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return 0, 0


def smooth_scroll_to(target_x: int, target_y: int, steps: int = SMOOTH_SCROLL_STEPS):
    """Smoothly scroll to target position."""
    current_x, current_y = get_current_position()

    dx = (target_x - current_x) / steps
    dy = (target_y - current_y) / steps

    for i in range(1, steps + 1):
        new_x = int(current_x + dx * i)
        new_y = int(current_y + dy * i)
        ctl("goto", str(new_x), str(new_y))
        time.sleep(SMOOTH_SCROLL_DELAY)


def run_shell_filter(text: str, filter_cmd: str) -> Optional[str]:
    """Run text through a shell filter command.

    Note: Uses shell=True intentionally for demo scripts - command is
    constructed internally, not from user input.
    """
    try:
        result = subprocess.run(
            filter_cmd,
            shell=True,
            input=text,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass
    return None


def draw_figlet_text(x: int, y: int, text: str, font: str = "standard"):
    """Draw figlet text at position."""
    figlet_output = run_shell_filter(text, f"figlet -f {font}")
    if figlet_output:
        lines = figlet_output.split("\n")
        commands = []
        for i, line in enumerate(lines):
            if line:
                commands.append(f":goto {x} {y + i}")
                commands.append(f":text {line}")
        if commands:
            ctl_batch(commands)
        return len(lines)
    else:
        # Fallback to plain text
        ctl("goto", str(x), str(y))
        ctl("text", f"=== {text} ===")
        return 1


def draw_boxed_text(x: int, y: int, text: str, style: str = "stone") -> int:
    """Draw text in a boxes-style box. Returns height."""
    boxed = run_shell_filter(text, f"boxes -d {style}")
    if boxed:
        lines = boxed.split("\n")
        commands = []
        for i, line in enumerate(lines):
            if line:
                commands.append(f":goto {x} {y + i}")
                commands.append(f":text {line}")
        if commands:
            ctl_batch(commands)
        return len([l for l in lines if l])
    else:
        # Fallback to simple box
        ctl("goto", str(x), str(y))
        ctl("rect", "20", "5")
        ctl("goto", str(x + 2), str(y + 2))
        ctl("text", text)
        return 5


def draw_sticky_note(
    x: int, y: int, title: str, lines: list[str], style: str = "stone"
):
    """Draw a sticky note with title and content."""
    # Combine title and content
    content = title + "\n" + "-" * len(title)
    for line in lines:
        content += "\n" + line

    return draw_boxed_text(x, y, content, style)


def draw_simple_box(x: int, y: int, width: int, height: int, label: str = ""):
    """Draw a simple ASCII box with optional centered label."""
    commands = [
        f":goto {x} {y}",
        f":rect {width} {height}",
    ]
    if label:
        label_x = x + (width - len(label)) // 2
        label_y = y + height // 2
        commands.extend(
            [
                f":goto {label_x} {label_y}",
                f":text {label}",
            ]
        )
    ctl_batch(commands)


def draw_arrow(x1: int, y1: int, x2: int, y2: int, char: str = "-"):
    """Draw an arrow between two points."""
    commands = [
        f":goto {x1} {y1}",
        f":line {x2} {y2} {char}",
    ]
    # Add arrowhead
    if x2 > x1:
        commands.extend([f":goto {x2 - 1} {y2}", ":text >"])
    elif x2 < x1:
        commands.extend([f":goto {x2 + 1} {y2}", ":text <"])
    elif y2 > y1:
        commands.extend([f":goto {x2} {y2 - 1}", ":text v"])
    elif y2 < y1:
        commands.extend([f":goto {x2} {y2 + 1}", ":text ^"])

    ctl_batch(commands)


# ============================================================================
# CLUSTER DRAWING FUNCTIONS
# ============================================================================


def draw_cluster_ideas(cluster: Cluster):
    """Draw the Ideas cluster - brainstorming sticky notes."""
    print(
        f"  Drawing {cluster.name} cluster at ({cluster.center_x}, {cluster.center_y})..."
    )

    base_x, base_y = cluster.center_x - 40, cluster.center_y - 20

    # Title using figlet
    draw_figlet_text(base_x, base_y, "Ideas", "small")
    wait(0.2)

    # Sticky notes scattered around
    notes = [
        (
            base_x + 5,
            base_y + 8,
            "Feature",
            ["- Dark mode", "- Export SVG", "- Templates"],
            "stone",
        ),
        (
            base_x + 35,
            base_y + 6,
            "UX Ideas",
            ["- Shortcuts", "- Tutorials", "- Themes"],
            "ansi",
        ),
        (
            base_x + 15,
            base_y + 18,
            "Tech",
            ["- WebSocket", "- IndexedDB", "- WASM"],
            "stone",
        ),
        (
            base_x + 50,
            base_y + 15,
            "Future",
            ["- Plugins", "- Mobile", "- Cloud sync"],
            "ansi",
        ),
        (
            base_x + 70,
            base_y + 8,
            "Quick Win",
            ["- Bug #42", "- Docs", "- Tests"],
            "stone",
        ),
    ]

    for x, y, title, lines, style in notes:
        draw_sticky_note(x, y, title, lines, style)
        wait(0.1)

    # Add connecting arrows between related notes
    draw_arrow(base_x + 25, base_y + 12, base_x + 35, base_y + 12, ".")
    draw_arrow(base_x + 55, base_y + 14, base_x + 50, base_y + 17, ".")


def draw_cluster_sprint(cluster: Cluster):
    """Draw the Sprint cluster - kanban-style task board."""
    print(
        f"  Drawing {cluster.name} cluster at ({cluster.center_x}, {cluster.center_y})..."
    )

    base_x, base_y = cluster.center_x - 60, cluster.center_y - 25

    # Title
    draw_figlet_text(base_x + 20, base_y, "Sprint", "small")
    wait(0.2)

    # Column headers
    columns = [
        (base_x, "TODO"),
        (base_x + 35, "IN PROGRESS"),
        (base_x + 75, "DONE"),
    ]

    for col_x, col_title in columns:
        ctl("goto", str(col_x), str(base_y + 6))
        ctl("text", f"[ {col_title} ]")
        ctl("goto", str(col_x), str(base_y + 7))
        ctl("text", "=" * (len(col_title) + 4))
    wait(0.1)

    # Tasks in each column
    todo_tasks = [
        (base_x, base_y + 10, "Task", ["Write docs", "for API"], "stone"),
        (base_x + 3, base_y + 18, "Bug", ["Fix #123", "login"], "stone"),
    ]

    progress_tasks = [
        (base_x + 35, base_y + 10, "Feature", ["Add export", "to PDF"], "ansi"),
        (base_x + 38, base_y + 18, "Review", ["PR #456", "tests"], "ansi"),
    ]

    done_tasks = [
        (base_x + 75, base_y + 10, "Done!", ["Setup CI", "pipeline"], "stone"),
        (base_x + 78, base_y + 18, "Done!", ["Dark mode", "toggle"], "stone"),
        (base_x + 81, base_y + 26, "Done!", ["Unit tests", "added"], "stone"),
    ]

    for tasks in [todo_tasks, progress_tasks, done_tasks]:
        for x, y, title, lines, style in tasks:
            draw_sticky_note(x, y, title, lines, style)
            wait(0.05)


def draw_cluster_architecture(cluster: Cluster):
    """Draw the Architecture cluster - system diagram."""
    print(
        f"  Drawing {cluster.name} cluster at ({cluster.center_x}, {cluster.center_y})..."
    )

    base_x, base_y = cluster.center_x - 50, cluster.center_y - 30

    # Title
    draw_figlet_text(base_x + 10, base_y, "Arch", "small")
    wait(0.2)

    # Architecture boxes
    components = [
        (base_x + 5, base_y + 10, 18, 6, "Frontend"),
        (base_x + 40, base_y + 10, 18, 6, "API"),
        (base_x + 75, base_y + 10, 18, 6, "Backend"),
        (base_x + 40, base_y + 25, 18, 6, "Cache"),
        (base_x + 75, base_y + 25, 18, 6, "Database"),
    ]

    for x, y, w, h, label in components:
        draw_simple_box(x, y, w, h, label)
        wait(0.1)

    # Connections
    arrows = [
        (base_x + 23, base_y + 13, base_x + 40, base_y + 13),  # Frontend -> API
        (base_x + 58, base_y + 13, base_x + 75, base_y + 13),  # API -> Backend
        (base_x + 49, base_y + 16, base_x + 49, base_y + 25),  # API -> Cache
        (base_x + 84, base_y + 16, base_x + 84, base_y + 25),  # Backend -> DB
    ]

    for x1, y1, x2, y2 in arrows:
        draw_arrow(x1, y1, x2, y2)
        wait(0.05)

    # Labels
    labels = [
        (base_x + 27, base_y + 11, "REST"),
        (base_x + 62, base_y + 11, "gRPC"),
        (base_x + 51, base_y + 20, "Redis"),
        (base_x + 86, base_y + 20, "SQL"),
    ]

    for x, y, text in labels:
        ctl("goto", str(x), str(y))
        ctl("text", text)


def draw_cluster_notes(cluster: Cluster):
    """Draw the Notes cluster - meeting notes and docs."""
    print(
        f"  Drawing {cluster.name} cluster at ({cluster.center_x}, {cluster.center_y})..."
    )

    base_x, base_y = cluster.center_x - 50, cluster.center_y - 25

    # Title
    draw_figlet_text(base_x + 15, base_y, "Notes", "small")
    wait(0.2)

    # Large meeting notes box
    meeting_notes = """Meeting Notes - Q4 Planning
============================
Date: 2024-01-15
Attendees: Team Alpha

Key Decisions:
- Ship v2.0 by March
- Add WebSocket support
- Deprecate legacy API

Action Items:
[ ] Create roadmap doc
[ ] Schedule sprint review
[x] Update dependencies"""

    lines = meeting_notes.split("\n")
    commands = []
    for i, line in enumerate(lines):
        commands.append(f":goto {base_x + 5} {base_y + 8 + i}")
        commands.append(f":text {line}")
    ctl_batch(commands)

    # Draw border around notes
    draw_simple_box(base_x + 3, base_y + 6, 30, len(lines) + 4, "")
    wait(0.2)

    # Smaller notes
    side_notes = [
        (base_x + 45, base_y + 8, "Reminder", ["Review PR", "by Friday"], "ansi"),
        (base_x + 48, base_y + 18, "Contact", ["Bob: API", "Eve: FE"], "stone"),
        (base_x + 70, base_y + 12, "Links", ["wiki/arch", "docs/api"], "ansi"),
    ]

    for x, y, title, lines, style in side_notes:
        draw_sticky_note(x, y, title, lines, style)
        wait(0.1)


def draw_center_marker():
    """Draw a marker at canvas center showing it's a large canvas."""
    center_x, center_y = CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2

    commands = [
        f":goto {center_x - 15} {center_y}",
        ":text +",
        f":goto {center_x - 15} {center_y - 1}",
        f":text Canvas: {CANVAS_WIDTH}x{CANVAS_HEIGHT}",
    ]
    ctl_batch(commands)


def setup_bookmarks():
    """Set up bookmarks for each cluster."""
    print("\nSetting up bookmarks...")
    for cluster in CLUSTERS:
        ctl("exec", f":mark {cluster.bookmark} {cluster.center_x} {cluster.center_y}")
        print(
            f"  Bookmark '{cluster.bookmark}' -> {cluster.name} ({cluster.center_x}, {cluster.center_y})"
        )
        wait(0.1)


def navigate_tour():
    """Take a tour of all clusters with smooth scrolling."""
    print("\n" + "=" * 50)
    print("NAVIGATION TOUR - Smooth scrolling between clusters")
    print("=" * 50)

    # Start at origin
    print("\nStarting at origin (0, 0)...")
    ctl("goto", "0", "0")
    time.sleep(1)

    # Visit each cluster
    for cluster in CLUSTERS:
        print(f"\n-> Scrolling to {cluster.name} (bookmark '{cluster.bookmark}')...")
        print(f"   {cluster.description}")
        smooth_scroll_to(cluster.center_x, cluster.center_y, steps=20)
        time.sleep(1.5)

    # Return to first cluster
    print(f"\n-> Returning to {CLUSTERS[0].name}...")
    smooth_scroll_to(CLUSTERS[0].center_x, CLUSTERS[0].center_y, steps=25)
    time.sleep(1)


def quick_jump_demo():
    """Demonstrate quick bookmark jumps."""
    print("\n" + "=" * 50)
    print("BOOKMARK JUMPS - Instant navigation")
    print("=" * 50)

    # Jump sequence
    jumps = [
        ("a", "Architecture"),
        ("n", "Notes"),
        ("s", "Sprint"),
        ("i", "Ideas"),
    ]

    for bookmark, name in jumps:
        print(f"\n-> Jump to '{bookmark}' ({name})")
        # Get bookmark position and jump
        cluster = next((c for c in CLUSTERS if c.bookmark == bookmark), None)
        if cluster:
            ctl("goto", str(cluster.center_x), str(cluster.center_y))
            time.sleep(0.8)


def run_demo():
    """Run the complete sticky notes demo."""
    print("=" * 60)
    print("my-grid Sticky Notes Demo")
    print(f"Canvas size: {CANVAS_WIDTH}x{CANVAS_HEIGHT} (12x terminal)")
    print("=" * 60)

    if not check_connection():
        return 1

    # Clear canvas
    print("\nClearing canvas...")
    ctl("clear")
    time.sleep(0.5)

    # Draw title at top
    print("\nDrawing title...")
    draw_figlet_text(10, 5, "my-grid", "standard")
    ctl("goto", "10", "12")
    ctl("text", "Infinite Canvas Demo - Sticky Notes & Clusters")
    time.sleep(0.5)

    # Draw each cluster
    print("\n" + "-" * 40)
    print("DRAWING CLUSTERS")
    print("-" * 40)

    draw_cluster_ideas(CLUSTERS[0])
    draw_cluster_sprint(CLUSTERS[1])
    draw_cluster_architecture(CLUSTERS[2])
    draw_cluster_notes(CLUSTERS[3])

    # Draw center marker
    draw_center_marker()

    # Set up bookmarks
    setup_bookmarks()

    # Navigation demo
    navigate_tour()

    # Quick jump demo
    quick_jump_demo()

    # Final status
    print("\n" + "=" * 60)
    code, output = ctl("status")
    print("Final Status:")
    print(output)
    print("=" * 60)
    print("\nDemo complete!")
    print(
        f"Canvas populated with 4 clusters across {CANVAS_WIDTH}x{CANVAS_HEIGHT} area"
    )
    print("Use bookmarks 'i', 's', 'a', 'n' to jump between clusters")

    return 0


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sticky Notes Demo - Large canvas with clustered notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Clusters and bookmarks:
  'i' - Ideas (brainstorming)
  's' - Sprint (kanban board)
  'a' - Architecture (system diagram)
  'n' - Notes (meeting notes)

Examples:
  python demo/sticky_notes_demo.py              # Full demo
  python demo/sticky_notes_demo.py --no-tour    # Skip navigation tour
  python demo/sticky_notes_demo.py --draw-only  # Draw only, no navigation
""",
    )

    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-tour", action="store_true", help="Skip navigation tour")
    parser.add_argument(
        "--draw-only", action="store_true", help="Only draw, skip all navigation"
    )

    args = parser.parse_args()

    global DEFAULT_HOST, DEFAULT_PORT
    DEFAULT_HOST = args.host
    DEFAULT_PORT = args.port

    return run_demo()


if __name__ == "__main__":
    sys.exit(main())
