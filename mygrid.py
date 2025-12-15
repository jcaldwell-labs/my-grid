#!/usr/bin/env python3
"""
my-grid launcher script.

Run from project root: python mygrid.py [file]
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import parse_args, main
import curses

if __name__ == "__main__":
    args = parse_args()
    try:
        curses.wrapper(lambda stdscr: main(stdscr, args))
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        print("\nExiting...")
