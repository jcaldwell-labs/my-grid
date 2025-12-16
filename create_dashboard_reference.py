#!/usr/bin/env python3
"""
Create a dashboard reference canvas with zone examples.

Demonstrates all zone types with practical dashboard layouts.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from canvas import Canvas
from viewport import Viewport
from project import Project, ProjectMetadata
from zones import Zone, ZoneConfig, ZoneType, ZoneManager

def create_dashboard_reference():
    """Create a canvas with zone dashboard examples."""

    # Create canvas and viewport
    canvas = Canvas()
    viewport = Viewport(width=150, height=80)
    zone_manager = ZoneManager()

    # =========================================================================
    # TITLE
    # =========================================================================
    title = "ZONE DASHBOARD REFERENCE"
    title_y = 0
    for i, char in enumerate(title):
        canvas.set(i, title_y, char)

    subtitle = "Examples of all zone types for monitoring, development, and integration"
    for i, char in enumerate(subtitle):
        canvas.set(i, title_y + 1, char)

    # =========================================================================
    # SECTION 1: MONITORING DASHBOARD (Watch Zones)
    # =========================================================================
    section1_y = 5
    section1_label = "=== MONITORING DASHBOARD (Watch Zones) ==="
    for i, char in enumerate(section1_label):
        canvas.set(0, section1_y, char)

    # CPU Monitor
    zone_manager.create_watch(
        name="CPU",
        x=0,
        y=section1_y + 2,
        width=45,
        height=8,
        command="uptime",
        interval=5,
        bookmark="c"
    )
    zone_manager.get("CPU").description = "CPU load and uptime"

    # Memory Monitor
    zone_manager.create_watch(
        name="MEMORY",
        x=0,
        y=section1_y + 11,
        width=45,
        height=8,
        command="free -h | head -3",
        interval=5,
        bookmark="m"
    )
    zone_manager.get("MEMORY").description = "Memory usage"

    # Disk Usage
    zone_manager.create_watch(
        name="DISK",
        x=50,
        y=section1_y + 2,
        width=50,
        height=8,
        command="df -h | grep -E '^/dev' | head -5",
        interval=30,
        bookmark="d"
    )
    zone_manager.get("DISK").description = "Disk space"

    # Network Connections
    zone_manager.create_watch(
        name="NETWORK",
        x=50,
        y=section1_y + 11,
        width=50,
        height=8,
        command="ss -tuln 2>/dev/null | head -8 || netstat -tuln | head -8",
        interval=10,
        bookmark="n"
    )
    zone_manager.get("NETWORK").description = "Active connections"

    # =========================================================================
    # SECTION 2: DEVELOPMENT WORKSPACE (Mixed Zones)
    # =========================================================================
    section2_y = 30
    section2_label = "=== DEVELOPMENT WORKSPACE (Watch + PTY Zones) ==="
    for i, char in enumerate(section2_label):
        canvas.set(0, section2_y, char)

    # Git Status
    zone_manager.create_watch(
        name="GIT",
        x=0,
        y=section2_y + 2,
        width=50,
        height=10,
        command="git -C ~ status --short 2>/dev/null | head -8 || echo 'Not in git repo'",
        interval=5,
        bookmark="g"
    )
    zone_manager.get("GIT").description = "Git repository status"

    # File Listing
    zone_manager.create_watch(
        name="FILES",
        x=0,
        y=section2_y + 13,
        width=50,
        height=10,
        command="ls -lah ~/projects 2>/dev/null | head -8 || ls -lah ~ | head -8",
        interval=10,
        bookmark="f"
    )
    zone_manager.get("FILES").description = "Directory contents"

    # Interactive Terminal
    zone_manager.create_pty(
        name="TERMINAL",
        x=55,
        y=section2_y + 2,
        width=70,
        height=21,
        bookmark="t",
        shell="/bin/bash"
    )
    zone_manager.get("TERMINAL").description = "Interactive shell (Press Enter to focus, Esc to unfocus)"

    # =========================================================================
    # SECTION 3: INTEGRATION ZONES (FIFO + Socket)
    # =========================================================================
    section3_y = 58
    section3_label = "=== INTEGRATION ZONES (FIFO + Socket) ==="
    for i, char in enumerate(section3_label):
        canvas.set(0, section3_y, char)

    # FIFO Zone for external events
    zone_manager.create(
        name="EVENTS",
        x=0,
        y=section3_y + 2,
        width=60,
        height=15,
        description="FIFO pipe listener: echo 'event' > /tmp/mygrid-events.fifo",
        bookmark="v",
        config=ZoneConfig(
            zone_type=ZoneType.FIFO,
            path="/tmp/mygrid-events.fifo"
        )
    )

    # Socket Zone for network messages
    zone_manager.create(
        name="MESSAGES",
        x=65,
        y=section3_y + 2,
        width=60,
        height=15,
        description="Socket listener on port 9999: echo 'msg' | nc localhost 9999",
        bookmark="s",
        config=ZoneConfig(
            zone_type=ZoneType.SOCKET,
            port=9999
        )
    )

    # =========================================================================
    # SECTION 4: USAGE NOTES (Static Zone)
    # =========================================================================
    notes_y = 78
    notes_label = "=== QUICK REFERENCE ==="
    for i, char in enumerate(notes_label):
        canvas.set(0, notes_y, char)

    usage_notes = [
        "",
        "Zone Commands:",
        "  :zones              - List all zones",
        "  :zone goto NAME     - Jump to zone",
        "  :zone info NAME     - Show zone details",
        "  :zone refresh NAME  - Manually refresh watch zone",
        "  :zone pause NAME    - Pause watch zone",
        "  :zone resume NAME   - Resume watch zone",
        "  :zone focus NAME    - Focus PTY zone for input",
        "  :zone send NAME txt - Send text to PTY zone",
        "",
        "Bookmarks (press ' + key in NAV mode):",
        "  'c - Jump to CPU       'd - Jump to DISK      'n - Jump to NETWORK",
        "  'g - Jump to GIT       'f - Jump to FILES     't - Jump to TERMINAL",
        "  'v - Jump to EVENTS    's - Jump to MESSAGES",
        "",
        "Zone Types:",
        "  [W] WATCH  - Auto-refreshing command output",
        "  [P] PIPE   - One-shot command output",
        "  [T] PTY    - Interactive terminal (Unix only)",
        "  [F] FIFO   - Named pipe listener (Unix only)",
        "  [N] SOCKET - Network socket listener",
        "  [S] STATIC - Manual text entry",
        "  [C] CLIPBOARD - Yank/paste buffer",
        "",
        "Testing FIFO and Socket Zones:",
        "  # Send to FIFO (Unix/WSL):",
        "  echo 'Build started' > /tmp/mygrid-events.fifo",
        "  echo 'Tests passed!' > /tmp/mygrid-events.fifo",
        "",
        "  # Send to Socket (Any platform):",
        "  echo 'Status update' | nc localhost 9999",
        "  echo 'Alert message' | nc localhost 9999",
        "",
        "Layout Management:",
        "  :layout save dashboard - Save current zone layout",
        "  :layout load dashboard - Restore saved layout",
        "  :layout list          - List available layouts",
    ]

    zone_manager.create(
        name="NOTES",
        x=0,
        y=notes_y + 2,
        width=130,
        height=40,
        description="Usage notes and commands",
        bookmark="h",
        config=ZoneConfig(zone_type=ZoneType.STATIC)
    )

    # Write usage notes to canvas
    notes_x = 1
    notes_content_y = notes_y + 3
    for i, line in enumerate(usage_notes):
        for j, char in enumerate(line):
            if char != ' ':
                canvas.set(notes_x + j, notes_content_y + i, char)

    # Draw zone borders on canvas
    for zone in zone_manager:
        draw_simple_border(canvas, zone)

    # =========================================================================
    # SAVE PROJECT
    # =========================================================================
    output_file = "dashboard-reference.json"
    metadata = ProjectMetadata(
        name="Zone Dashboard Reference",
        description="Complete reference showing all zone types with practical examples"
    )

    project = Project(metadata=metadata)
    viewport.y = 0
    project.save(canvas, viewport, zones=zone_manager, filepath=output_file)

    print(f"Created {output_file}")
    print(f"Open with: python3 mygrid.py {output_file}")
    print(f"\nCreated {len(list(zone_manager))} zones:")
    for zone in zone_manager:
        print(f"  {zone.name:12} ({zone.zone_type.value:8}) - {zone.description}")
    print("\nBookmarks: c, m, d, n, g, f, t, v, s, h")
    print("\nUsage:")
    print("  1. Navigate with wasd/arrows")
    print("  2. Press ' + letter to jump to bookmarked zones")
    print("  3. Use :zone commands to manage zones")
    print("  4. Load with: :layout load dashboard-reference")

    return 0


def draw_simple_border(canvas: Canvas, zone: Zone) -> None:
    """Draw a simple ASCII border around a zone."""
    # Top and bottom borders
    for x in range(zone.width):
        canvas.set(zone.x + x, zone.y, '-')
        canvas.set(zone.x + x, zone.y + zone.height - 1, '-')

    # Left and right borders
    for y in range(zone.height):
        canvas.set(zone.x, zone.y + y, '|')
        canvas.set(zone.x + zone.width - 1, zone.y + y, '|')

    # Corners
    canvas.set(zone.x, zone.y, '+')
    canvas.set(zone.x + zone.width - 1, zone.y, '+')
    canvas.set(zone.x, zone.y + zone.height - 1, '+')
    canvas.set(zone.x + zone.width - 1, zone.y + zone.height - 1, '+')

    # Zone name and type indicator in top border
    type_indicator = f"[{zone.type_indicator()}]"
    name_label = f" {zone.name} {type_indicator} "
    label_x = zone.x + 2
    for i, char in enumerate(name_label):
        if label_x + i < zone.x + zone.width - 2:
            canvas.set(label_x + i, zone.y, char)


if __name__ == "__main__":
    sys.exit(create_dashboard_reference())
