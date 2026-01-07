#!/usr/bin/env python3
"""
Tmux pane management for my-grid Claude Code plugin.

Handles spawning, tracking, reusing, and controlling tmux panes
for the my-grid ASCII canvas editor.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional

# Pane tracking file
PANE_ID_FILE = Path("/tmp/mygrid-pane-id")

# Default my-grid location (relative to plugin root)
MYGRID_ROOT = Path(__file__).parent.parent.parent

# Python executable (prefer venv if exists)
VENV_PYTHON = MYGRID_ROOT / ".venv" / "bin" / "python3"
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else "python3"


def in_tmux() -> bool:
    """Check if running inside a tmux session."""
    return bool(os.environ.get("TMUX"))


def get_pane_id() -> Optional[str]:
    """
    Get tracked pane ID if it still exists.

    Returns:
        Pane ID string if valid, None otherwise
    """
    if not PANE_ID_FILE.exists():
        return None

    pane_id = PANE_ID_FILE.read_text().strip()
    if not pane_id:
        return None

    # Verify pane still exists
    result = subprocess.run(
        ["tmux", "display-message", "-t", pane_id, "-p", "#{pane_id}"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and result.stdout.strip() == pane_id:
        return pane_id

    # Stale reference - clean up
    PANE_ID_FILE.unlink(missing_ok=True)
    return None


def save_pane_id(pane_id: str) -> None:
    """Save pane ID for future reuse."""
    PANE_ID_FILE.write_text(pane_id)


def spawn_pane(ratio: int = 67, port: int = 8765, layout: Optional[str] = None) -> str:
    """
    Create new tmux pane running my-grid.

    Args:
        ratio: Width percentage for new pane (default 67 = 2/3)
        port: TCP server port
        layout: Optional layout to load on startup

    Returns:
        Pane ID of created pane

    Raises:
        RuntimeError: If not in tmux or spawn fails
    """
    if not in_tmux():
        raise RuntimeError("Not in tmux session. Run: tmux new -s grid")

    # Build command
    mygrid_path = MYGRID_ROOT / "mygrid.py"
    cmd = f"{PYTHON_EXE} {mygrid_path} --server --port {port}"
    if layout:
        cmd += f" --layout {layout}"

    # Spawn split pane
    # -h: horizontal split (side by side)
    # -p: percentage width
    # -P -F: print new pane ID
    result = subprocess.run(
        ["tmux", "split-window", "-h", "-p", str(ratio), "-P", "-F", "#{pane_id}", cmd],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to spawn pane: {result.stderr}")

    pane_id = result.stdout.strip()
    save_pane_id(pane_id)
    return pane_id


def reuse_pane(pane_id: str, port: int = 8765, layout: Optional[str] = None) -> bool:
    """
    Reuse existing pane by killing current process and starting new.

    Args:
        pane_id: Existing pane ID
        port: TCP server port
        layout: Optional layout to load

    Returns:
        True if successful
    """
    # Send Ctrl+C to kill current process
    subprocess.run(["tmux", "send-keys", "-t", pane_id, "C-c"], check=False)
    time.sleep(0.2)

    # Build new command
    mygrid_path = MYGRID_ROOT / "mygrid.py"
    cmd = f"clear && {PYTHON_EXE} {mygrid_path} --server --port {port}"
    if layout:
        cmd += f" --layout {layout}"

    # Send command
    result = subprocess.run(
        ["tmux", "send-keys", "-t", pane_id, cmd, "Enter"],
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


def spawn_or_reuse(
    ratio: int = 67,
    port: int = 8765,
    layout: Optional[str] = None,
    force_new: bool = False,
) -> str:
    """
    Spawn new pane or reuse existing one.

    Args:
        ratio: Width percentage for new pane
        port: TCP server port
        layout: Optional layout to load
        force_new: Force creation of new pane

    Returns:
        Pane ID
    """
    if not force_new:
        existing = get_pane_id()
        if existing:
            reuse_pane(existing, port, layout)
            return existing

    return spawn_pane(ratio, port, layout)


# === Pane Management Functions ===


def zoom_pane(pane_id: Optional[str] = None) -> bool:
    """
    Toggle zoom (fullscreen) for pane.

    Args:
        pane_id: Pane to zoom (default: tracked pane)

    Returns:
        True if successful
    """
    pane_id = pane_id or get_pane_id()
    if not pane_id:
        return False

    result = subprocess.run(
        ["tmux", "resize-pane", "-Z", "-t", pane_id], capture_output=True
    )
    return result.returncode == 0


def resize_pane(percent: int, pane_id: Optional[str] = None) -> bool:
    """
    Resize pane to percentage width.

    Args:
        percent: Width percentage (e.g., 25, 50, 75)
        pane_id: Pane to resize (default: tracked pane)

    Returns:
        True if successful
    """
    pane_id = pane_id or get_pane_id()
    if not pane_id:
        return False

    result = subprocess.run(
        ["tmux", "resize-pane", "-t", pane_id, "-x", f"{percent}%"], capture_output=True
    )
    return result.returncode == 0


def hide_pane(pane_id: Optional[str] = None) -> Optional[str]:
    """
    Hide pane by breaking it out to background window.

    Args:
        pane_id: Pane to hide (default: tracked pane)

    Returns:
        New window ID for hidden pane, or None on failure
    """
    pane_id = pane_id or get_pane_id()
    if not pane_id:
        return None

    # Break pane to new background window
    # -d: don't switch to new window
    # -P -F: print new pane ID
    # Note: Select pane first to avoid -t flag conflicts in tmux 3.5+
    subprocess.run(["tmux", "select-pane", "-t", pane_id], capture_output=True)
    result = subprocess.run(
        ["tmux", "break-pane", "-d", "-P", "-F", "#{pane_id}"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        new_pane_id = result.stdout.strip()
        save_pane_id(new_pane_id)
        return new_pane_id
    return None


def show_pane(pane_id: Optional[str] = None, ratio: int = 67) -> bool:
    """
    Show hidden pane by joining it back.

    Args:
        pane_id: Pane to show (default: tracked pane)
        ratio: Width percentage when restored

    Returns:
        True if successful
    """
    pane_id = pane_id or get_pane_id()
    if not pane_id:
        return False

    # Join pane back to current window
    # -h: horizontal (side by side)
    # -l: size (percentage)
    result = subprocess.run(
        ["tmux", "join-pane", "-h", "-s", pane_id, "-l", f"{ratio}%"],
        capture_output=True,
    )
    return result.returncode == 0


def kill_pane(pane_id: Optional[str] = None) -> bool:
    """
    Kill the my-grid pane.

    Args:
        pane_id: Pane to kill (default: tracked pane)

    Returns:
        True if successful
    """
    pane_id = pane_id or get_pane_id()
    if not pane_id:
        return False

    result = subprocess.run(["tmux", "kill-pane", "-t", pane_id], capture_output=True)

    if result.returncode == 0:
        PANE_ID_FILE.unlink(missing_ok=True)
        return True
    return False


def focus_pane(pane_id: Optional[str] = None) -> bool:
    """
    Focus (select) the my-grid pane.

    Args:
        pane_id: Pane to focus (default: tracked pane)

    Returns:
        True if successful
    """
    pane_id = pane_id or get_pane_id()
    if not pane_id:
        return False

    result = subprocess.run(["tmux", "select-pane", "-t", pane_id], capture_output=True)
    return result.returncode == 0
