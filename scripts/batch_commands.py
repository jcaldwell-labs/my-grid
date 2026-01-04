#!/usr/bin/env python3
"""
Execute batch commands from a file.

Usage:
    python batch_commands.py <command-file>
    python batch_commands.py -  # Read from stdin

Command file format:
    # Comments start with #
    :goto 0 0
    :text Hello World
    :rect 20 10

Examples:
    python batch_commands.py setup.txt
    echo ':text Quick' | python batch_commands.py -
"""

import sys
from pathlib import Path

try:
    from mygrid_client import MyGridClient, MyGridError
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from mygrid_client import MyGridClient, MyGridError


def run_batch(source):
    """Execute commands from file or stdin."""
    client = MyGridClient()

    if source == "-":
        lines = sys.stdin.readlines()
    else:
        with open(source) as f:
            lines = f.readlines()

    executed = 0
    skipped = 0

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            skipped += 1
            continue

        print(f"> {line}")
        try:
            response = client.send(line)
            if response:
                print(f"  {response}")
            executed += 1
        except MyGridError as e:
            print(f"  Error: {e}")

    print(f"\nExecuted: {executed}, Skipped: {skipped}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    source = sys.argv[1]

    if source != "-" and not Path(source).exists():
        print(f"File not found: {source}")
        sys.exit(1)

    try:
        run_batch(source)
    except MyGridError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
