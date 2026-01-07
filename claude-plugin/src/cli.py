#!/usr/bin/env python3
"""
CLI entry point for my-grid Claude Code plugin.

Provides commands for spawning, controlling, and managing my-grid
instances from Claude Code.
"""

import argparse
import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from terminal import (
    in_tmux,
    spawn_or_reuse,
    get_pane_id,
    zoom_pane,
    resize_pane,
    hide_pane,
    show_pane,
    kill_pane,
    focus_pane,
)
from ipc import GridIPCClient, MyGridError


def cmd_spawn(args):
    """Spawn or reuse my-grid pane."""
    if not in_tmux():
        print("Error: Not in tmux session. Run: tmux new -s grid", file=sys.stderr)
        sys.exit(1)

    try:
        pane_id = spawn_or_reuse(
            ratio=args.ratio,
            port=args.port,
            layout=args.layout,
            force_new=args.new,
        )
        print(f"my-grid spawned in pane {pane_id}")

        # Wait for server to be ready
        if args.wait:
            client = GridIPCClient(port=args.port)
            if client.wait_ready(timeout=10.0):
                print("Server ready")
            else:
                print("Warning: Server may not be ready yet", file=sys.stderr)

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_send(args):
    """Send command to my-grid."""
    client = GridIPCClient(port=args.port)

    if not client.is_ready():
        print("Error: my-grid server not running. Use 'spawn' first.", file=sys.stderr)
        sys.exit(1)

    try:
        command = " ".join(args.command)
        result = client.send(command)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            status = result.get("status", "unknown")
            message = result.get("message", "")
            if status == "ok":
                print(message)
            else:
                print(f"Error: {message}", file=sys.stderr)
                sys.exit(1)

    except MyGridError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args):
    """Get my-grid status."""
    pane_id = get_pane_id()
    client = GridIPCClient(port=args.port)

    status = {
        "pane": pane_id,
        "pane_active": pane_id is not None,
        "server_ready": client.is_ready(),
    }

    if client.is_ready():
        try:
            grid_status = client.status()
            status["grid"] = grid_status.get("data", {})
        except MyGridError:
            pass

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(f"Pane: {pane_id or 'not spawned'}")
        print(f"Server: {'ready' if status['server_ready'] else 'not running'}")


def cmd_zoom(args):
    """Toggle pane zoom."""
    if zoom_pane():
        print("Toggled zoom")
    else:
        print("Error: No my-grid pane found", file=sys.stderr)
        sys.exit(1)


def cmd_ratio(args):
    """Set pane width ratio."""
    if args.percent not in [25, 50, 75]:
        print("Error: Ratio must be 25, 50, or 75", file=sys.stderr)
        sys.exit(1)

    if resize_pane(args.percent):
        print(f"Resized to {args.percent}%")
    else:
        print("Error: No my-grid pane found", file=sys.stderr)
        sys.exit(1)


def cmd_hide(args):
    """Hide my-grid pane."""
    new_pane = hide_pane()
    if new_pane:
        print(f"Hidden pane (new ID: {new_pane})")
    else:
        print("Error: No my-grid pane found", file=sys.stderr)
        sys.exit(1)


def cmd_show(args):
    """Show hidden my-grid pane."""
    if show_pane(ratio=args.ratio):
        print("Restored pane")
    else:
        print("Error: No hidden my-grid pane found", file=sys.stderr)
        sys.exit(1)


def cmd_close(args):
    """Close my-grid pane."""
    if kill_pane():
        print("Closed my-grid pane")
    else:
        print("Error: No my-grid pane found", file=sys.stderr)
        sys.exit(1)


def cmd_focus(args):
    """Focus my-grid pane."""
    if focus_pane():
        print("Focused my-grid pane")
    else:
        print("Error: No my-grid pane found", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="my-grid Claude Code plugin CLI",
        prog="grid",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8765,
        help="my-grid server port (default: 8765)",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output in JSON format",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # spawn
    spawn_parser = subparsers.add_parser("spawn", help="Spawn my-grid in tmux pane")
    spawn_parser.add_argument(
        "--ratio",
        "-r",
        type=int,
        default=67,
        help="Pane width percentage (default: 67)",
    )
    spawn_parser.add_argument(
        "--layout",
        "-l",
        type=str,
        help="Layout to load on startup",
    )
    spawn_parser.add_argument(
        "--new",
        "-n",
        action="store_true",
        help="Force create new pane (don't reuse)",
    )
    spawn_parser.add_argument(
        "--wait",
        "-w",
        action="store_true",
        default=True,
        help="Wait for server to be ready (default: true)",
    )
    spawn_parser.set_defaults(func=cmd_spawn)

    # send
    send_parser = subparsers.add_parser("send", help="Send command to my-grid")
    send_parser.add_argument(
        "command",
        nargs="+",
        help="Command to send (e.g., ':text Hello')",
    )
    send_parser.set_defaults(func=cmd_send)

    # status
    status_parser = subparsers.add_parser("status", help="Get my-grid status")
    status_parser.set_defaults(func=cmd_status)

    # zoom
    zoom_parser = subparsers.add_parser("zoom", help="Toggle pane zoom")
    zoom_parser.set_defaults(func=cmd_zoom)

    # ratio
    ratio_parser = subparsers.add_parser("ratio", help="Set pane width ratio")
    ratio_parser.add_argument(
        "percent",
        type=int,
        choices=[25, 50, 75],
        help="Width percentage (25, 50, or 75)",
    )
    ratio_parser.set_defaults(func=cmd_ratio)

    # hide
    hide_parser = subparsers.add_parser("hide", help="Hide my-grid pane")
    hide_parser.set_defaults(func=cmd_hide)

    # show
    show_parser = subparsers.add_parser("show", help="Show hidden my-grid pane")
    show_parser.add_argument(
        "--ratio",
        "-r",
        type=int,
        default=67,
        help="Restored pane width percentage",
    )
    show_parser.set_defaults(func=cmd_show)

    # close
    close_parser = subparsers.add_parser("close", help="Close my-grid pane")
    close_parser.set_defaults(func=cmd_close)

    # focus
    focus_parser = subparsers.add_parser("focus", help="Focus my-grid pane")
    focus_parser.set_defaults(func=cmd_focus)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
