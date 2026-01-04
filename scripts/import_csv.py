#!/usr/bin/env python3
"""
Import CSV data as a formatted table on my-grid canvas.

Usage:
    python import_csv.py data.csv [x] [y]

Examples:
    python import_csv.py servers.csv
    python import_csv.py data.csv 10 5
"""

import sys
import csv
from pathlib import Path

try:
    from mygrid_client import MyGridClient, MyGridError
except ImportError:
    # Allow running from different directory
    sys.path.insert(0, str(Path(__file__).parent))
    from mygrid_client import MyGridClient, MyGridError


def format_table(rows, padding=2):
    """Format rows as aligned table with borders."""
    if not rows:
        return []

    # Calculate column widths
    num_cols = len(rows[0])
    col_widths = [0] * num_cols
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Add padding
    col_widths = [w + padding for w in col_widths]

    # Build output lines
    lines = []

    # Top border
    border = "+" + "+".join("-" * w for w in col_widths) + "+"
    lines.append(border)

    for i, row in enumerate(rows):
        # Data row
        cells = []
        for j, cell in enumerate(row):
            cells.append(str(cell).ljust(col_widths[j] - padding).center(col_widths[j]))
        lines.append("|" + "|".join(cells) + "|")

        # Header separator
        if i == 0:
            lines.append(border.replace("-", "="))

    # Bottom border
    lines.append(border)

    return lines


def import_csv(filepath, start_x=0, start_y=0):
    """Import CSV file to my-grid canvas."""
    # Read CSV
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print("CSV file is empty")
        return

    print(f"Loaded {len(rows)} rows, {len(rows[0])} columns")

    # Format as table
    table_lines = format_table(rows)

    # Send to my-grid
    client = MyGridClient()

    for i, line in enumerate(table_lines):
        client.goto(start_x, start_y + i)
        client.text(line)

    print(f"Table written at ({start_x}, {start_y})")
    print(f"Size: {len(table_lines[0])} x {len(table_lines)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = sys.argv[1]
    start_x = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    start_y = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        sys.exit(1)

    try:
        import_csv(filepath, start_x, start_y)
    except MyGridError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
