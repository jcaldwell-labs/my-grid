#!/usr/bin/env python3
"""
Tmux pane management for my-grid Claude Code plugin.

Handles spawning, tracking, reusing, and controlling tmux panes
for the my-grid ASCII canvas editor.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

# Pane tracking file
PANE_ID_FILE = Path("/tmp/mygrid-pane-id")


def find_mygrid_root() -> Path:
    """
    Find the my-grid project root directory.

    Searches in order:
    1. MYGRID_ROOT environment variable
    2. Marketplace directory (when installed as Claude plugin)
    3. Relative to this file (development mode)
    4. Current working directory

    Returns:
        Path to my-grid root directory

    Raises:
        RuntimeError: If mygrid.py cannot be found
    """
    # Check environment variable first
    if env_root := os.environ.get("MYGRID_ROOT"):
        root = Path(env_root)
        if (root / "mygrid.py").exists():
            return root

    # Check marketplace directory (plugin installed from marketplace)
    # Cache path: ~/.claude/plugins/cache/my-grid/grid/<VERSION>/src/terminal.py
    # Marketplace: ~/.claude/plugins/marketplaces/my-grid/
    plugin_file = Path(__file__)
    cache_path = plugin_file.parent.parent  # cache/my-grid/grid/<VERSION>/
    plugins_root = cache_path.parent.parent.parent.parent  # ~/.claude/plugins/
    marketplace_path = plugins_root / "marketplaces" / "my-grid"
    if (marketplace_path / "mygrid.py").exists():
        return marketplace_path

    # Development mode: plugin is inside my-grid project
    # Path: my-grid/claude-plugin/src/terminal.py
    dev_root = plugin_file.parent.parent.parent
    if (dev_root / "mygrid.py").exists():
        return dev_root

    # Try current working directory
    cwd = Path.cwd()
    if (cwd / "mygrid.py").exists():
        return cwd

    raise RuntimeError(
        "Cannot find my-grid installation. Set MYGRID_ROOT environment variable "
        "or ensure my-grid is installed in the Claude plugins marketplace."
    )


def find_python_executable(mygrid_root: Path) -> Tuple[str, Optional[Path]]:
    """
    Find the best Python executable for running my-grid.

    Checks for virtual environment in the project root.

    Args:
        mygrid_root: Path to my-grid project root

    Returns:
        Tuple of (python executable path/command, venv path or None)
    """
    # Check for .venv in project root
    venv_python = mygrid_root / ".venv" / "bin" / "python3"
    if venv_python.exists():
        return str(venv_python), mygrid_root / ".venv"

    # Check for venv (alternative name)
    venv_python = mygrid_root / "venv" / "bin" / "python3"
    if venv_python.exists():
        return str(venv_python), mygrid_root / "venv"

    # Fall back to system Python
    return "python3", None


def ensure_venv_ready(mygrid_root: Path) -> Tuple[str, bool]:
    """
    Ensure virtual environment exists and has dependencies installed.

    Creates venv and installs requirements if needed.

    Args:
        mygrid_root: Path to my-grid project root

    Returns:
        Tuple of (python executable, whether bootstrap was needed)
    """
    python_exe, venv_path = find_python_executable(mygrid_root)

    if venv_path:
        # Venv exists, assume it's ready
        return python_exe, False

    # No venv - check if we should create one
    requirements = mygrid_root / "requirements.txt"
    if not requirements.exists():
        # No requirements file, use system Python
        return "python3", False

    # Create venv and install dependencies
    venv_path = mygrid_root / ".venv"
    print(f"Creating virtual environment at {venv_path}...", file=sys.stderr)

    result = subprocess.run(
        ["python3", "-m", "venv", str(venv_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Warning: Failed to create venv: {result.stderr}", file=sys.stderr)
        return "python3", False

    # Install requirements
    pip_exe = venv_path / "bin" / "pip"
    print(f"Installing dependencies from {requirements}...", file=sys.stderr)

    result = subprocess.run(
        [str(pip_exe), "install", "-r", str(requirements)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Warning: Failed to install deps: {result.stderr}", file=sys.stderr)
        return "python3", False

    python_exe = str(venv_path / "bin" / "python3")
    print("Bootstrap complete!", file=sys.stderr)
    return python_exe, True


# Initialize paths
try:
    MYGRID_ROOT = find_mygrid_root()
    PYTHON_EXE, _venv = find_python_executable(MYGRID_ROOT)
except RuntimeError:
    # Defer error to runtime when spawn is actually called
    MYGRID_ROOT = Path(__file__).parent.parent.parent
    PYTHON_EXE = "python3"


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


def spawn_pane(
    ratio: int = 67,
    port: int = 8765,
    layout: Optional[str] = None,
    bootstrap: bool = True,
) -> str:
    """
    Create new tmux pane running my-grid.

    Args:
        ratio: Width percentage for new pane (default 67 = 2/3)
        port: TCP server port
        layout: Optional layout to load on startup
        bootstrap: Auto-create venv and install deps if needed (default True)

    Returns:
        Pane ID of created pane

    Raises:
        RuntimeError: If not in tmux or spawn fails
    """
    if not in_tmux():
        raise RuntimeError("Not in tmux session. Run: tmux new -s grid")

    # Find project root and ensure dependencies are available
    try:
        mygrid_root = find_mygrid_root()
    except RuntimeError as e:
        raise RuntimeError(str(e))

    # Bootstrap venv if needed
    if bootstrap:
        python_exe, bootstrapped = ensure_venv_ready(mygrid_root)
        if bootstrapped:
            print("Dependencies installed successfully", file=sys.stderr)
    else:
        python_exe, _ = find_python_executable(mygrid_root)

    # Build command
    mygrid_path = mygrid_root / "mygrid.py"
    cmd = f"{python_exe} {mygrid_path} --server --port {port}"
    if layout:
        cmd += f" --layout {layout}"

    # Spawn split pane
    # -h: horizontal split (side by side)
    # -p: percentage width
    # -P -F: print new pane ID
    # -c: start in project directory
    result = subprocess.run(
        [
            "tmux",
            "split-window",
            "-h",
            "-p",
            str(ratio),
            "-c",
            str(mygrid_root),
            "-P",
            "-F",
            "#{pane_id}",
            cmd,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to spawn pane: {result.stderr}")

    pane_id = result.stdout.strip()
    save_pane_id(pane_id)
    return pane_id


def reuse_pane(
    pane_id: str,
    port: int = 8765,
    layout: Optional[str] = None,
    bootstrap: bool = True,
) -> bool:
    """
    Reuse existing pane by killing current process and starting new.

    Args:
        pane_id: Existing pane ID
        port: TCP server port
        layout: Optional layout to load
        bootstrap: Auto-create venv and install deps if needed (default True)

    Returns:
        True if successful
    """
    # Send Ctrl+C to kill current process
    subprocess.run(["tmux", "send-keys", "-t", pane_id, "C-c"], check=False)
    time.sleep(0.2)

    # Find project root and ensure dependencies are available
    try:
        mygrid_root = find_mygrid_root()
    except RuntimeError:
        mygrid_root = MYGRID_ROOT

    # Bootstrap venv if needed
    if bootstrap:
        python_exe, _ = ensure_venv_ready(mygrid_root)
    else:
        python_exe, _ = find_python_executable(mygrid_root)

    # Build new command
    mygrid_path = mygrid_root / "mygrid.py"
    cmd = f"clear && {python_exe} {mygrid_path} --server --port {port}"
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
    bootstrap: bool = True,
) -> str:
    """
    Spawn new pane or reuse existing one.

    Args:
        ratio: Width percentage for new pane
        port: TCP server port
        layout: Optional layout to load
        force_new: Force creation of new pane
        bootstrap: Auto-create venv and install deps if needed (default True)

    Returns:
        Pane ID
    """
    if not force_new:
        existing = get_pane_id()
        if existing:
            reuse_pane(existing, port, layout, bootstrap=bootstrap)
            return existing

    return spawn_pane(ratio, port, layout, bootstrap=bootstrap)


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
