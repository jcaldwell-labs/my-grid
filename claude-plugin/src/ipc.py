#!/usr/bin/env python3
"""
IPC client for my-grid Claude Code plugin.

Wraps the existing mygrid_client.py to provide server readiness
waiting and convenient command methods.
"""

import socket
import json
import time
from pathlib import Path
from typing import Any, Optional

# Add parent directories to find mygrid_client
import sys

MYGRID_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MYGRID_ROOT / "scripts"))

try:
    from mygrid_client import MyGridClient, MyGridError
except ImportError:
    # Fallback: define minimal client inline
    class MyGridError(Exception):
        """Error from my-grid API."""

        pass

    class MyGridClient:
        """Minimal client for my-grid API server."""

        def __init__(
            self, host: str = "localhost", port: int = 8765, timeout: float = 5.0
        ):
            self.host = host
            self.port = port
            self.timeout = timeout

        def send(self, command: str) -> dict:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            try:
                sock.connect((self.host, self.port))
            except ConnectionRefusedError:
                raise MyGridError(f"Cannot connect to {self.host}:{self.port}")
            except socket.timeout:
                raise MyGridError("Connection timed out")

            try:
                sock.sendall((command + "\n").encode())
                response = sock.recv(4096).decode()
            except socket.timeout:
                raise MyGridError(f"Command timed out: {command}")
            finally:
                sock.close()

            if response.startswith("{"):
                return json.loads(response)
            return {"status": "ok", "message": response.strip()}


class GridIPCClient:
    """
    IPC client for Claude Code integration with my-grid.

    Provides:
    - Server readiness waiting
    - Command execution with JSON responses
    - Convenience methods for common operations
    """

    def __init__(self, host: str = "localhost", port: int = 8765, timeout: float = 5.0):
        """
        Initialize IPC client.

        Args:
            host: Server hostname
            port: Server port
            timeout: Socket timeout
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._client = MyGridClient(host=host, port=port, timeout=timeout)

    def is_ready(self) -> bool:
        """Check if server is accepting connections."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def wait_ready(self, timeout: float = 10.0, poll_interval: float = 0.5) -> bool:
        """
        Wait for server to be ready.

        Args:
            timeout: Maximum wait time in seconds
            poll_interval: Time between connection attempts

        Returns:
            True if server is ready, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.is_ready():
                return True
            time.sleep(poll_interval)
        return False

    def send(self, command: str) -> dict:
        """
        Send command and return parsed response.

        Args:
            command: Command string (with or without leading :)

        Returns:
            Response dict with 'status', 'message', and optional 'data'

        Raises:
            MyGridError: On connection or command error
        """
        # Ensure command has leading :
        if not command.startswith(":") and not command.startswith("/"):
            command = ":" + command

        return self._client.send(command)

    def send_silent(self, command: str) -> bool:
        """
        Send command without waiting for response (fire-and-forget via FIFO).

        Args:
            command: Command string

        Returns:
            True if sent successfully
        """
        fifo_path = Path("/tmp/mygrid.fifo")
        if not fifo_path.exists():
            # Fall back to TCP
            try:
                self.send(command)
                return True
            except MyGridError:
                return False

        try:
            with open(fifo_path, "w") as f:
                f.write(command + "\n")
            return True
        except Exception:
            return False

    # === Convenience Methods ===

    def goto(self, x: int, y: int) -> dict:
        """Move cursor to coordinates."""
        return self.send(f":goto {x} {y}")

    def text(self, message: str) -> dict:
        """Write text at cursor position."""
        return self.send(f":text {message}")

    def rect(self, width: int, height: int, char: str = "#") -> dict:
        """Draw rectangle at cursor."""
        return self.send(f":rect {width} {height} {char}")

    def line(self, x2: int, y2: int, char: str = "*") -> dict:
        """Draw line from cursor to target."""
        return self.send(f":line {x2} {y2} {char}")

    def clear(self) -> dict:
        """Clear entire canvas."""
        return self.send(":clear")

    def save(self, path: Optional[str] = None) -> dict:
        """Save project."""
        if path:
            return self.send(f":write {path}")
        return self.send(":write")

    # === Zone Methods ===

    def zone_create(self, name: str, x: int, y: int, width: int, height: int) -> dict:
        """Create static zone."""
        return self.send(f":zone create {name} {x} {y} {width} {height}")

    def zone_watch(
        self, name: str, width: int, height: int, interval: str, command: str
    ) -> dict:
        """Create watch zone with periodic refresh."""
        return self.send(f":zone watch {name} {width} {height} {interval} {command}")

    def zone_pipe(self, name: str, width: int, height: int, command: str) -> dict:
        """Create pipe zone with one-shot command."""
        return self.send(f":zone pipe {name} {width} {height} {command}")

    def zone_pty(
        self, name: str, width: int, height: int, shell: Optional[str] = None
    ) -> dict:
        """Create PTY zone with live terminal."""
        cmd = f":zone pty {name} {width} {height}"
        if shell:
            cmd += f" {shell}"
        return self.send(cmd)

    def zone_delete(self, name: str) -> dict:
        """Delete zone."""
        return self.send(f":zone delete {name}")

    def zone_goto(self, name: str) -> dict:
        """Jump to zone."""
        return self.send(f":zone goto {name}")

    def zone_refresh(self, name: str) -> dict:
        """Refresh zone content."""
        return self.send(f":zone refresh {name}")

    def zones(self) -> dict:
        """List all zones."""
        return self.send(":zones")

    # === Layout Methods ===

    def layout_load(self, name: str, clear: bool = False) -> dict:
        """Load layout template."""
        cmd = f":layout load {name}"
        if clear:
            cmd += " --clear"
        return self.send(cmd)

    def layout_save(self, name: str, description: Optional[str] = None) -> dict:
        """Save current zones as layout."""
        cmd = f":layout save {name}"
        if description:
            cmd += f" {description}"
        return self.send(cmd)

    def layout_list(self) -> dict:
        """List available layouts."""
        return self.send(":layout list")

    # === Status Methods ===

    def status(self) -> dict:
        """Get grid status (cursor, zones, etc.)."""
        # Note: This command may need to be added to my-grid
        try:
            return self.send(":status")
        except MyGridError:
            # Fallback: just return basic info
            return {
                "status": "ok",
                "message": "Grid is running",
                "data": {"connected": True},
            }
