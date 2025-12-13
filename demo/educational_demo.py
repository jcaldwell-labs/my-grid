#!/usr/bin/env python3
"""
Educational Demo - Massive Canvas Feature Tour

Creates a canvas 20x larger than terminal (1600x480) with distinct
educational zones demonstrating my-grid features.

Canvas Layout (1600x480):
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ZONE 1: WELCOME (center-top)                                              │
│   Giant figlet "my-grid" banner that requires panning to see fully          │
│   Position: (400, 20) - spans ~200 chars wide                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ZONE 2: DRAWING       │  ZONE 3: NAVIGATION    │  ZONE 4: MODES           │
│  (100, 120)            │  (600, 120)            │  (1100, 120)             │
│  - Rectangles          │  - Bookmarks           │  - NAV mode              │
│  - Lines               │  - Fast movement       │  - EDIT mode             │
│  - Text                │  - Goto command        │  - PAN mode              │
│                        │  - Pan mode            │  - COMMAND mode          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ZONE 5: ARCHITECTURE  │  ZONE 6: PRODUCTIVITY  │  ZONE 7: API             │
│  (100, 300)            │  (600, 300)            │  (1100, 300)             │
│  - System diagrams     │  - TODO lists          │  - mygrid-ctl            │
│  - Flowcharts          │  - Meeting notes       │  - TCP control           │
│  - Connections         │  - Brainstorming       │  - External tools        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ZONE 8: THE ANSWER (bottom-right corner)                                  │
│   Easter egg at position (1337, 420) - "42"                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Usage:
    python src/main.py --server &
    python demo/educational_demo.py
"""

import subprocess
import sys
import time
import math
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple


# Configuration
MYGRID_CTL = Path(__file__).parent.parent / "mygrid-ctl"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

# Canvas: 20x typical terminal (80x24 -> 1600x480)
CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 480

# Animation settings
SMOOTH_STEPS = 25
SMOOTH_DELAY = 0.025
CMD_DELAY = 0.02


@dataclass
class Zone:
    """A demo zone on the canvas."""
    name: str
    bookmark: str
    x: int
    y: int
    description: str
    figlet_font: str = "small"


# Define educational zones
ZONES = [
    Zone("Welcome", "w", 400, 40, "Giant banner - pan to see it all!", "banner"),
    Zone("Drawing", "d", 100, 130, "Drawing primitives", "small"),
    Zone("Navigation", "n", 600, 130, "Movement & bookmarks", "small"),
    Zone("Modes", "m", 1100, 130, "Editor modes", "small"),
    Zone("Architecture", "a", 100, 310, "System diagrams", "small"),
    Zone("Productivity", "p", 600, 310, "TODO & notes", "small"),
    Zone("API", "i", 1100, 310, "External control", "small"),
    Zone("Answer", "4", 1337, 420, "The ultimate answer", "big"),
]


def ctl(*args) -> Tuple[int, str]:
    """Execute mygrid-ctl command."""
    cmd = [sys.executable, str(MYGRID_CTL), "--host", DEFAULT_HOST, "--port", str(DEFAULT_PORT), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def batch(commands: List[str]) -> Tuple[int, str]:
    """Execute batch of commands."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('\n'.join(commands))
        temp_path = f.name
    result = ctl("batch", temp_path)
    Path(temp_path).unlink()
    return result


def wait(seconds: float = CMD_DELAY):
    time.sleep(seconds)


def get_position() -> Tuple[int, int]:
    """Get current cursor position."""
    import json
    code, output = ctl("status", "--json")
    if code == 0:
        try:
            data = json.loads(output.strip().split('\n')[0])
            if data.get('status') == 'ok':
                state = json.loads(data.get('message', '{}'))
                return state['cursor']['x'], state['cursor']['y']
        except:
            pass
    return 0, 0


def smooth_scroll(target_x: int, target_y: int, steps: int = SMOOTH_STEPS):
    """Smoothly scroll to position with easing."""
    start_x, start_y = get_position()

    for i in range(1, steps + 1):
        # Ease-out cubic for smooth deceleration
        t = i / steps
        ease = 1 - (1 - t) ** 3

        new_x = int(start_x + (target_x - start_x) * ease)
        new_y = int(start_y + (target_y - start_y) * ease)
        ctl("goto", str(new_x), str(new_y))
        time.sleep(SMOOTH_DELAY)


def run_filter(text: str, cmd: str) -> Optional[str]:
    """Run text through shell filter."""
    try:
        result = subprocess.run(cmd, shell=True, input=text, capture_output=True, text=True, timeout=5)
        return result.stdout if result.returncode == 0 else None
    except:
        return None


def draw_figlet(x: int, y: int, text: str, font: str = "standard") -> int:
    """Draw figlet text, return height."""
    output = run_filter(text, f"figlet -f {font}")
    if output:
        lines = [l for l in output.split('\n') if l]
        commands = []
        for i, line in enumerate(lines):
            if line.strip():
                commands.append(f":goto {x} {y + i}")
                commands.append(f":text {line}")
        if commands:
            batch(commands)
        return len(lines)
    return 0


def draw_box(x: int, y: int, w: int, h: int, label: str = ""):
    """Draw box with optional label."""
    commands = [f":goto {x} {y}", f":rect {w} {h}"]
    if label:
        lx = x + (w - len(label)) // 2
        ly = y + h // 2
        commands.extend([f":goto {lx} {ly}", f":text {label}"])
    batch(commands)


def draw_boxed_text(x: int, y: int, text: str, style: str = "stone") -> int:
    """Draw text in boxes style."""
    output = run_filter(text, f"boxes -d {style}")
    if output:
        lines = [l for l in output.split('\n') if l]
        commands = []
        for i, line in enumerate(lines):
            commands.append(f":goto {x} {y + i}")
            commands.append(f":text {line}")
        if commands:
            batch(commands)
        return len(lines)
    return 0


def draw_arrow(x1: int, y1: int, x2: int, y2: int, char: str = "-"):
    """Draw arrow between points."""
    commands = [f":goto {x1} {y1}", f":line {x2} {y2} {char}"]
    if x2 > x1:
        commands.extend([f":goto {x2 - 1} {y2}", ":text >"])
    elif x2 < x1:
        commands.extend([f":goto {x2 + 1} {y2}", ":text <"])
    elif y2 > y1:
        commands.extend([f":goto {x2} {y2 - 1}", ":text v"])
    else:
        commands.extend([f":goto {x2} {y2 + 1}", ":text ^"])
    batch(commands)


# ============================================================================
# ZONE DRAWING FUNCTIONS
# ============================================================================

def draw_zone_welcome():
    """Zone 1: Giant welcome banner."""
    print("  Drawing WELCOME zone (giant banner)...")

    # The banner font creates HUGE text - perfect for demonstrating pan
    draw_figlet(300, 20, "my-grid", "banner")
    wait(0.1)

    # Subtitle below
    ctl("goto", "450", "32")
    ctl("text", "Infinite Canvas ASCII Editor")
    ctl("goto", "430", "34")
    ctl("text", "Pan around to see the entire banner!")

    # Corner markers showing canvas extent
    corners = [
        (10, 5, "TOP-LEFT (10,5)"),
        (1500, 5, "TOP-RIGHT (1500,5)"),
        (10, 460, "BOTTOM-LEFT (10,460)"),
        (1500, 460, "BOTTOM-RIGHT (1500,460)"),
    ]
    for x, y, label in corners:
        ctl("goto", str(x), str(y))
        ctl("text", f"+ {label}")


def draw_zone_drawing():
    """Zone 2: Drawing primitives demo."""
    print("  Drawing DRAWING zone...")
    z = ZONES[1]  # Drawing zone

    # Zone title
    draw_figlet(z.x, z.y - 15, "Drawing", "small")

    # Rectangles demo
    ctl("goto", str(z.x), str(z.y))
    ctl("text", "RECTANGLES:")
    draw_box(z.x, z.y + 2, 15, 5, "Box 1")
    draw_box(z.x + 20, z.y + 2, 15, 5, "Box 2")
    draw_box(z.x + 40, z.y + 2, 15, 5, "Box 3")

    # Lines demo
    ctl("goto", str(z.x), str(z.y + 10))
    ctl("text", "LINES:")
    batch([
        f":goto {z.x} {z.y + 12}",
        f":line {z.x + 50} {z.y + 12} -",
        f":goto {z.x} {z.y + 14}",
        f":line {z.x + 50} {z.y + 18} .",
        f":goto {z.x + 50} {z.y + 14}",
        f":line {z.x} {z.y + 18} *",
    ])

    # Text demo
    ctl("goto", str(z.x), str(z.y + 22))
    ctl("text", "TEXT: The quick brown fox jumps over the lazy dog")
    draw_boxed_text(z.x, z.y + 25, "Boxed Text!", "ansi")


def draw_zone_navigation():
    """Zone 3: Navigation features."""
    print("  Drawing NAVIGATION zone...")
    z = ZONES[2]

    draw_figlet(z.x, z.y - 15, "Navigate", "small")

    content = """
MOVEMENT:
  wasd / arrows  - Move cursor
  WASD          - Fast move (10x)
  :goto X Y     - Jump to position

BOOKMARKS:
  m + key       - Set bookmark
  ' + key       - Jump to bookmark
  :marks        - List all marks

PAN MODE:
  p             - Toggle pan mode
  Move viewport, cursor follows
"""

    lines = content.strip().split('\n')
    for i, line in enumerate(lines):
        ctl("goto", str(z.x), str(z.y + i))
        ctl("text", line)

    # Visual bookmark example
    draw_box(z.x + 250, z.y + 5, 20, 8, "")
    ctl("goto", str(z.x + 255), str(z.y + 8))
    ctl("text", "Bookmark 'a'")
    ctl("goto", str(z.x + 258), str(z.y + 10))
    ctl("text", "(600,130)")


def draw_zone_modes():
    """Zone 4: Editor modes."""
    print("  Drawing MODES zone...")
    z = ZONES[3]

    draw_figlet(z.x, z.y - 15, "Modes", "small")

    modes = [
        ("NAV", "Default mode - move around", "wasd/arrows"),
        ("EDIT", "Type on canvas", "i to enter"),
        ("PAN", "Move viewport", "p to toggle"),
        ("COMMAND", "Execute commands", ": to enter"),
        ("MARK", "Set/jump bookmarks", "m or '"),
    ]

    for i, (mode, desc, key) in enumerate(modes):
        y_pos = z.y + i * 8
        draw_box(z.x, y_pos, 12, 5, mode)
        ctl("goto", str(z.x + 15), str(y_pos + 1))
        ctl("text", desc)
        ctl("goto", str(z.x + 15), str(y_pos + 3))
        ctl("text", f"Key: {key}")


def draw_zone_architecture():
    """Zone 5: System architecture diagrams."""
    print("  Drawing ARCHITECTURE zone...")
    z = ZONES[4]

    draw_figlet(z.x, z.y - 15, "Diagrams", "small")

    # Three-tier architecture
    components = [
        (z.x + 30, z.y, 20, 6, "Client"),
        (z.x + 30, z.y + 20, 20, 6, "Server"),
        (z.x + 30, z.y + 40, 20, 6, "Database"),
    ]

    for x, y, w, h, label in components:
        draw_box(x, y, w, h, label)

    # Arrows
    draw_arrow(z.x + 40, z.y + 6, z.x + 40, z.y + 20, "|")
    draw_arrow(z.x + 40, z.y + 26, z.x + 40, z.y + 40, "|")

    # Labels
    ctl("goto", str(z.x + 45), str(z.y + 12))
    ctl("text", "HTTP/REST")
    ctl("goto", str(z.x + 45), str(z.y + 32))
    ctl("text", "SQL/ORM")

    # Microservices on the right
    services = ["Auth", "API", "Worker", "Cache"]
    for i, svc in enumerate(services):
        draw_box(z.x + 100 + (i * 25), z.y + 15, 18, 5, svc)

    # Connect them
    for i in range(len(services) - 1):
        x1 = z.x + 100 + (i * 25) + 18
        x2 = z.x + 100 + ((i + 1) * 25)
        draw_arrow(x1, z.y + 17, x2, z.y + 17)


def draw_zone_productivity():
    """Zone 6: Productivity features."""
    print("  Drawing PRODUCTIVITY zone...")
    z = ZONES[5]

    draw_figlet(z.x, z.y - 15, "Workflow", "small")

    # TODO list
    todo = """Sprint TODO
============
[x] Design API
[x] Implement core
[ ] Write tests
[ ] Documentation
[ ] Deploy"""

    draw_boxed_text(z.x, z.y, todo, "stone")

    # Meeting notes
    notes = """Meeting Notes
=============
- Ship v2.0
- Add dark mode
- Fix bug #42"""

    draw_boxed_text(z.x + 80, z.y, notes, "ansi")

    # Brainstorm sticky notes
    ideas = [
        (z.x + 160, z.y, "Feature A"),
        (z.x + 180, z.y + 8, "Feature B"),
        (z.x + 165, z.y + 16, "Feature C"),
    ]
    for x, y, text in ideas:
        draw_boxed_text(x, y, text, "stone")


def draw_zone_api():
    """Zone 7: API and external control."""
    print("  Drawing API zone...")
    z = ZONES[6]

    draw_figlet(z.x, z.y - 15, "API", "small")

    content = """
EXTERNAL CONTROL:
  python mygrid.py --server

mygrid-ctl COMMANDS:
  mygrid-ctl text "Hello"
  mygrid-ctl rect 20 10
  mygrid-ctl goto 50 25
  mygrid-ctl status

PIPING:
  ls -la | mygrid-ctl region 0 0
  echo "Hi" | mygrid-ctl pipe 10 5 \\
    --filter "boxes -d stone"

TCP PROTOCOL:
  Port: 8765
  Format: JSON responses
  echo ':rect 10 5' | nc localhost 8765
"""

    lines = content.strip().split('\n')
    for i, line in enumerate(lines):
        ctl("goto", str(z.x), str(z.y + i))
        ctl("text", line)


def draw_zone_answer():
    """Zone 8: Easter egg - The Answer."""
    print("  Drawing THE ANSWER zone...")
    z = ZONES[7]

    # At position 1337, 420 - because of course
    draw_figlet(z.x - 50, z.y - 30, "42", "big")

    answer_text = """
"The Answer to the Ultimate Question
 of Life, the Universe, and Everything"

        - Deep Thought

 Position: (1337, 420)
 Because every canvas needs an easter egg.
"""

    lines = answer_text.strip().split('\n')
    for i, line in enumerate(lines):
        ctl("goto", str(z.x - 40), str(z.y - 15 + i))
        ctl("text", line)

    draw_box(z.x - 60, z.y - 35, 80, 30, "")


def setup_bookmarks():
    """Set up bookmarks for all zones."""
    print("\nSetting up bookmarks...")
    for zone in ZONES:
        ctl("exec", f":mark {zone.bookmark} {zone.x} {zone.y}")
        print(f"  '{zone.bookmark}' -> {zone.name} ({zone.x}, {zone.y})")
        wait(0.05)


def run_tour():
    """Guided tour of all zones with smooth scrolling."""
    print("\n" + "=" * 60)
    print("EDUCATIONAL TOUR - Smooth navigation between zones")
    print("=" * 60)

    # Start at origin
    print("\nStarting at origin...")
    ctl("goto", "0", "0")
    time.sleep(1)

    # Tour order for educational flow
    tour_order = [
        ("Welcome", "See the giant banner - pan to see it all"),
        ("Drawing", "Learn drawing primitives"),
        ("Navigation", "Master movement and bookmarks"),
        ("Modes", "Understand editor modes"),
        ("Architecture", "Create system diagrams"),
        ("Productivity", "TODO lists and notes"),
        ("API", "External control via mygrid-ctl"),
        ("Answer", "The ultimate easter egg"),
    ]

    for zone_name, description in tour_order:
        zone = next((z for z in ZONES if z.name == zone_name), None)
        if zone:
            print(f"\n-> {zone.name}: {description}")
            smooth_scroll(zone.x, zone.y, steps=30)
            time.sleep(2)

    # Return to welcome
    print("\n-> Returning to Welcome banner...")
    smooth_scroll(ZONES[0].x, ZONES[0].y, steps=35)
    time.sleep(1)


def pan_across_banner():
    """Slowly pan across the giant welcome banner."""
    print("\nPanning across welcome banner...")

    # Start at left edge of banner
    ctl("goto", "200", "25")
    time.sleep(0.5)

    # Slow pan to the right
    for x in range(200, 700, 10):
        ctl("goto", str(x), "25")
        time.sleep(0.05)

    time.sleep(1)


def check_connection() -> bool:
    code, output = ctl("status")
    if code != 0:
        print("Error: Cannot connect to my-grid server")
        print("Start with: python src/main.py --server")
        return False
    return True


def run_demo():
    """Run the complete educational demo."""
    print("=" * 70)
    print("my-grid EDUCATIONAL DEMO")
    print(f"Canvas: {CANVAS_WIDTH}x{CANVAS_HEIGHT} (20x terminal size)")
    print("=" * 70)

    if not check_connection():
        return 1

    # Clear and start fresh
    print("\nClearing canvas...")
    ctl("clear")
    time.sleep(0.5)

    # Draw all zones
    print("\n" + "-" * 50)
    print("DRAWING ZONES")
    print("-" * 50)

    draw_zone_welcome()
    draw_zone_drawing()
    draw_zone_navigation()
    draw_zone_modes()
    draw_zone_architecture()
    draw_zone_productivity()
    draw_zone_api()
    draw_zone_answer()

    # Set up bookmarks
    setup_bookmarks()

    # Pan across banner first
    pan_across_banner()

    # Guided tour
    run_tour()

    # Final status
    print("\n" + "=" * 70)
    code, output = ctl("status")
    print("Final Status:")
    print(output)
    print("=" * 70)
    print("\nDemo complete!")
    print(f"Canvas: {CANVAS_WIDTH}x{CANVAS_HEIGHT}")
    print("Bookmarks: " + ", ".join(f"'{z.bookmark}'={z.name}" for z in ZONES))

    return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Educational Demo - Massive Canvas Tour")
    parser.add_argument('--host', default=DEFAULT_HOST)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--no-tour', action='store_true', help='Skip guided tour')
    parser.add_argument('--zone', choices=[z.name.lower() for z in ZONES], help='Draw single zone')

    args = parser.parse_args()

    global DEFAULT_HOST, DEFAULT_PORT
    DEFAULT_HOST = args.host
    DEFAULT_PORT = args.port

    return run_demo()


if __name__ == "__main__":
    sys.exit(main())
