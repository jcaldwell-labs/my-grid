#!/usr/bin/env python3
"""
Quick visual test of grid modes via API.

Run my-grid with --server, then run this script to test grid features.
"""

import socket
import time
import json


def send_command(cmd: str, port: int = 8765) -> dict:
    """Send command to my-grid API server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', port))
        s.sendall((cmd + '\n').encode())
        response = s.recv(4096).decode()
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw": response}


def main():
    print("Testing my-grid grid modes...")
    print("Make sure my-grid is running with --server\n")

    # Test grid mode commands
    tests = [
        (":grid", "Show current grid status"),
        (":grid major", "Toggle major grid"),
        (":grid minor", "Toggle minor grid"),
        (":grid lines", "Switch to LINES mode"),
        (":grid markers", "Switch to MARKERS mode"),
        (":grid dots", "Switch to DOTS mode"),
        (":grid off", "Turn grid off"),
        (":grid markers", "Back to markers"),
        (":grid rulers", "Toggle rulers"),
        (":grid labels", "Toggle coordinate labels"),
        (":grid interval 20 5", "Set intervals to 20/5"),
        (":grid", "Show final status"),
    ]

    for cmd, desc in tests:
        print(f"  {desc}...")
        print(f"    Command: {cmd}")
        try:
            result = send_command(cmd)
            print(f"    Result: {result.get('message', result)}")
        except ConnectionRefusedError:
            print("    ERROR: Connection refused - is my-grid running with --server?")
            return
        except Exception as e:
            print(f"    ERROR: {e}")
        time.sleep(0.5)
        print()

    print("Done! Check my-grid window to see the changes.")


if __name__ == "__main__":
    main()
