#!/usr/bin/env python3
"""
API-driven demo controller for my-grid.

Demonstrates external control of my-grid via mygrid-ctl TCP API.
Perfect for VHS recordings showcasing programmatic canvas manipulation.

Usage:
    1. Start my-grid with --server:
       python mygrid.py --server

    2. Run this demo:
       python demo/api_demo.py

    3. (Optional) Record with VHS:
       vhs demo/api-demo.tape
"""

import subprocess
import sys
import time
from pathlib import Path


# Configuration
MYGRID_CTL = Path(__file__).parent.parent / "mygrid-ctl"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEMO_DELAY = 0.3  # Delay between commands for visibility


def ctl(*args, host=DEFAULT_HOST, port=DEFAULT_PORT) -> tuple[int, str]:
    """
    Execute mygrid-ctl command.

    Returns:
        (return_code, output)
    """
    cmd = [
        sys.executable,
        str(MYGRID_CTL),
        "--host", host,
        "--port", str(port),
        *args
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def wait(seconds: float = DEMO_DELAY):
    """Wait between commands for visual effect."""
    time.sleep(seconds)


def check_connection(host=DEFAULT_HOST, port=DEFAULT_PORT) -> bool:
    """Check if my-grid server is running."""
    code, output = ctl("status", host=host, port=port)
    if code != 0:
        print(f"Error: Cannot connect to my-grid at {host}:{port}")
        print(f"Start my-grid with: python mygrid.py --server --port {port}")
        print(f"Output: {output}")
        return False
    return True


def demo_system_architecture():
    """Demo: Create a system architecture diagram."""
    print("\n=== System Architecture Demo ===\n")

    # Clear canvas
    ctl("clear")
    wait(0.5)

    # Title
    ctl("goto", "5", "2")
    ctl("text", "System Architecture - Created via API")
    wait()

    # Draw service boxes
    print("Drawing services...")

    # Frontend
    ctl("goto", "10", "6")
    ctl("rect", "16", "5")
    ctl("goto", "13", "8")
    ctl("text", "Frontend")
    wait()

    # API Gateway
    ctl("goto", "35", "6")
    ctl("rect", "16", "5")
    ctl("goto", "37", "8")
    ctl("text", "API Gateway")
    wait()

    # Backend
    ctl("goto", "60", "6")
    ctl("rect", "16", "5")
    ctl("goto", "64", "8")
    ctl("text", "Backend")
    wait()

    # Database
    ctl("goto", "85", "6")
    ctl("rect", "16", "5")
    ctl("goto", "88", "8")
    ctl("text", "Database")
    wait()

    # Draw connections
    print("Connecting services...")

    ctl("goto", "26", "8")
    ctl("exec", ":line 35 8 -")
    ctl("goto", "34", "8")
    ctl("text", ">")
    wait()

    ctl("goto", "51", "8")
    ctl("exec", ":line 60 8 -")
    ctl("goto", "59", "8")
    ctl("text", ">")
    wait()

    ctl("goto", "76", "8")
    ctl("exec", ":line 85 8 -")
    ctl("goto", "84", "8")
    ctl("text", ">")
    wait()

    # Add protocol labels
    print("Adding labels...")
    ctl("goto", "29", "6")
    ctl("text", "HTTP")
    ctl("goto", "54", "6")
    ctl("text", "gRPC")
    ctl("goto", "79", "6")
    ctl("text", "SQL")
    wait()

    print("Architecture diagram complete!")


def demo_todo_list():
    """Demo: Create a TODO list."""
    print("\n=== TODO List Demo ===\n")

    # Position for TODO
    ctl("goto", "10", "15")

    # Header
    ctl("text", "Sprint TODO List")
    ctl("goto", "10", "16")
    ctl("text", "================")
    wait()

    # Tasks
    tasks = [
        "[x] Design API schema",
        "[x] Implement endpoints",
        "[ ] Write unit tests",
        "[ ] Add integration tests",
        "[ ] Documentation",
        "[ ] Deploy to staging",
    ]

    print("Adding tasks...")
    for i, task in enumerate(tasks):
        ctl("goto", "10", str(18 + i))
        ctl("text", task)
        wait(0.15)

    print("TODO list complete!")


def demo_external_tools():
    """Demo: Integration with external tools (boxes, figlet)."""
    print("\n=== External Tools Demo ===\n")

    # Check if boxes is available
    result = subprocess.run(["which", "boxes"], capture_output=True)
    has_boxes = result.returncode == 0

    if has_boxes:
        print("Using 'boxes' for styled text...")

        # Create styled box using pipe command
        process = subprocess.Popen(
            ["echo", "API Gateway\nVersion 2.0"],
            stdout=subprocess.PIPE
        )

        code, output = ctl("pipe", "60", "15", "--filter", "boxes -d stone")
        if code == 0:
            print("Stone box created!")
        else:
            print(f"Note: pipe command result: {output}")
    else:
        print("'boxes' not available - using standard rectangles")
        ctl("goto", "60", "15")
        ctl("rect", "20", "6")
        ctl("goto", "62", "17")
        ctl("text", "API Gateway")
        ctl("goto", "62", "18")
        ctl("text", "Version 2.0")

    wait()

    # Check if figlet is available
    result = subprocess.run(["which", "figlet"], capture_output=True)
    has_figlet = result.returncode == 0

    if has_figlet:
        print("Using 'figlet' for ASCII banner...")
        # Use stamp command
        code, output = ctl("stamp", "10", "28", "banner", "API")
        if code == 0:
            print("ASCII banner created!")
        else:
            print(f"Note: stamp command result: {output}")
    else:
        print("'figlet' not available - using plain text")
        ctl("goto", "10", "28")
        ctl("text", "=== API ===")

    print("External tools demo complete!")


def demo_batch_commands():
    """Demo: Batch command execution."""
    print("\n=== Batch Commands Demo ===\n")

    # Create a batch script in memory
    batch_script = """
# Move to new section
:goto 10 35
:text Batch Execution Demo
:goto 10 36
:text =====================

# Draw a quick diagram
:goto 10 38
:rect 12 4
:goto 13 40
:text Node A

:goto 30 38
:rect 12 4
:goto 33 40
:text Node B

# Connect them
:goto 22 40
:line 30 40 -
"""

    print("Executing batch commands...")

    # Write batch to temp file and execute
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(batch_script)
        temp_path = f.name

    code, output = ctl("batch", temp_path)
    print(f"Batch result: {output[:100]}..." if len(output) > 100 else f"Batch result: {output}")

    # Cleanup
    Path(temp_path).unlink()

    print("Batch demo complete!")


def demo_bookmarks():
    """Demo: Bookmark navigation."""
    print("\n=== Bookmark Navigation Demo ===\n")

    # Set bookmarks at key locations
    print("Setting bookmarks...")

    ctl("exec", ":mark a 50 8")  # Architecture
    wait(0.2)
    print("  Bookmark 'a' -> Architecture")

    ctl("exec", ":mark t 10 18")  # TODO
    wait(0.2)
    print("  Bookmark 't' -> TODO List")

    ctl("exec", ":mark b 60 15")  # Box demo
    wait(0.2)
    print("  Bookmark 'b' -> External Tools")

    # Jump between bookmarks
    print("\nJumping between bookmarks...")

    ctl("exec", ":goto 0 0")  # Go to origin first
    wait(0.5)

    for mark, name in [('a', 'Architecture'), ('t', 'TODO'), ('b', 'Tools'), ('a', 'Architecture')]:
        print(f"  Jumping to '{mark}' ({name})...")
        # Use goto with bookmark coordinates (would need :jump command in practice)
        # For now, demonstrate the concept
        wait(0.5)

    print("Bookmark demo complete!")


def demo_status_query():
    """Demo: Querying status via API."""
    print("\n=== Status Query Demo ===\n")

    code, output = ctl("status", "--json")

    if code == 0:
        print("Current my-grid status:")
        print(output)
    else:
        print(f"Error getting status: {output}")


def run_full_demo():
    """Run the complete API demo sequence."""
    print("=" * 60)
    print("my-grid API Demo - External Control via mygrid-ctl")
    print("=" * 60)

    if not check_connection():
        return 1

    # Run demo sections
    demo_system_architecture()
    time.sleep(1)

    demo_todo_list()
    time.sleep(1)

    demo_external_tools()
    time.sleep(1)

    demo_batch_commands()
    time.sleep(1)

    demo_bookmarks()
    time.sleep(1)

    demo_status_query()

    print("\n" + "=" * 60)
    print("Demo complete! Canvas populated via external API.")
    print("=" * 60)

    return 0


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="API-driven demo for my-grid",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo/api_demo.py                    Run full demo
  python demo/api_demo.py --host localhost   Custom host
  python demo/api_demo.py --section arch     Run only architecture demo
"""
    )

    parser.add_argument('--host', default=DEFAULT_HOST, help='my-grid host')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='my-grid port')
    parser.add_argument('--section', choices=['arch', 'todo', 'tools', 'batch', 'marks', 'status'],
                        help='Run specific section only')
    parser.add_argument('--delay', type=float, default=DEMO_DELAY,
                        help='Delay between commands (seconds)')

    args = parser.parse_args()

    # Update globals
    global DEFAULT_HOST, DEFAULT_PORT, DEMO_DELAY
    DEFAULT_HOST = args.host
    DEFAULT_PORT = args.port
    DEMO_DELAY = args.delay

    if not check_connection():
        return 1

    if args.section:
        sections = {
            'arch': demo_system_architecture,
            'todo': demo_todo_list,
            'tools': demo_external_tools,
            'batch': demo_batch_commands,
            'marks': demo_bookmarks,
            'status': demo_status_query,
        }
        sections[args.section]()
        return 0

    return run_full_demo()


if __name__ == "__main__":
    sys.exit(main())
