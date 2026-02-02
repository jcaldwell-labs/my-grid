#!/usr/bin/env python3
"""
my-grid launcher script.

Run from project root: python mygrid.py [file]
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import parse_args, main, main_headless
import curses
import sys

if __name__ == "__main__":
    args = parse_args()
    try:
        if args.headless:
            if not args.server:
                print("Error: --headless requires --server")
                sys.exit(1)
            main_headless(args)
        else:
            curses.wrapper(lambda stdscr: main(stdscr, args))
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        print("\nExiting...")
