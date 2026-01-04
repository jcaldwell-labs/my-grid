#!/usr/bin/env python3
"""
my-grid API Client Library

Reusable client for controlling my-grid via TCP socket.

Usage:
    from mygrid_client import MyGridClient

    client = MyGridClient()
    client.goto(0, 0)
    client.text('Hello World!')
    client.rect(20, 10)
"""

import socket
import json


class MyGridError(Exception):
    """Error from my-grid API."""

    pass


class MyGridClient:
    """Client for my-grid API server."""

    def __init__(self, host="localhost", port=8765, timeout=5.0):
        """
        Initialize client.

        Args:
            host: Server hostname (default: localhost)
            port: Server port (default: 8765)
            timeout: Socket timeout in seconds (default: 5.0)
        """
        self.host = host
        self.port = port
        self.timeout = timeout

    def send(self, command):
        """
        Send command and return response.

        Args:
            command: Command string (e.g., ':goto 0 0')

        Returns:
            dict or str: Parsed JSON response or raw string

        Raises:
            MyGridError: On connection or command error
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            sock.connect((self.host, self.port))
        except ConnectionRefusedError:
            raise MyGridError(
                f"Cannot connect to {self.host}:{self.port}. "
                "Is my-grid running with --server?"
            )
        except socket.timeout:
            raise MyGridError("Connection timed out")

        try:
            sock.sendall((command + "\n").encode())
            response = sock.recv(4096).decode()
        except socket.timeout:
            raise MyGridError(f"Command timed out: {command}")
        finally:
            sock.close()

        # Parse response
        if response.startswith("{"):
            try:
                data = json.loads(response)
                if data.get("status") == "error":
                    raise MyGridError(data.get("message", "Unknown error"))
                return data
            except json.JSONDecodeError:
                pass
        return response.strip()

    # Navigation commands
    def goto(self, x, y):
        """Move cursor to (x, y)."""
        return self.send(f":goto {x} {y}")

    # Drawing commands
    def text(self, message):
        """Write text at cursor position."""
        return self.send(f":text {message}")

    def rect(self, width, height, char="#"):
        """Draw rectangle at cursor."""
        return self.send(f":rect {width} {height} {char}")

    def line(self, x2, y2, char=None):
        """Draw line from cursor to (x2, y2)."""
        if char:
            return self.send(f":line {x2} {y2} {char}")
        return self.send(f":line {x2} {y2}")

    def clear(self):
        """Clear the entire canvas."""
        return self.send(":clear")

    # Color commands
    def color(self, fg, bg=None):
        """Set drawing color."""
        if bg:
            return self.send(f":color {fg} {bg}")
        return self.send(f":color {fg}")

    def color_off(self):
        """Reset to default colors."""
        return self.send(":color off")

    # File commands
    def save(self, filepath=None):
        """Save project to file."""
        if filepath:
            return self.send(f":w {filepath}")
        return self.send(":w")

    def load(self, filepath):
        """Load project from file."""
        return self.send(f":e {filepath}")

    # Zone commands
    def zone_create(self, name, x, y, width, height):
        """Create a static zone."""
        return self.send(f":zone create {name} {x} {y} {width} {height}")

    def zone_pipe(self, name, width, height, command):
        """Create a pipe zone (one-shot command)."""
        return self.send(f":zone pipe {name} {width} {height} {command}")

    def zone_watch(self, name, width, height, interval, command):
        """Create a watch zone (periodic refresh)."""
        return self.send(f":zone watch {name} {width} {height} {interval} {command}")

    def zone_delete(self, name):
        """Delete a zone."""
        return self.send(f":zone delete {name}")

    def zone_goto(self, name):
        """Jump cursor to zone center."""
        return self.send(f":zone goto {name}")

    def zone_refresh(self, name):
        """Manually refresh a zone."""
        return self.send(f":zone refresh {name}")

    # Layout commands
    def layout_load(self, name, clear=False):
        """Load a layout."""
        if clear:
            return self.send(f":layout load {name} --clear")
        return self.send(f":layout load {name}")

    def layout_save(self, name, description=None):
        """Save current zones as layout."""
        if description:
            return self.send(f":layout save {name} {description}")
        return self.send(f":layout save {name}")


class MyGridSession:
    """
    Persistent connection for batch operations.

    More efficient than MyGridClient for sending many commands.

    Usage:
        with MyGridSession() as session:
            for i in range(100):
                session.send(f':goto 0 {i}')
                session.send(f':text Line {i}')
    """

    def __init__(self, host="localhost", port=8765, timeout=30.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        """Establish connection."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

    def send(self, command):
        """Send command over persistent connection."""
        if not self.sock:
            raise MyGridError("Not connected")
        self.sock.sendall((command + "\n").encode())
        return self.sock.recv(4096).decode().strip()

    def close(self):
        """Close connection."""
        if self.sock:
            self.sock.close()
            self.sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()


if __name__ == "__main__":
    # Demo usage
    print("my-grid API Client Demo")
    print("=" * 40)

    try:
        client = MyGridClient()

        print("Moving to origin...")
        client.goto(0, 0)

        print("Writing text...")
        client.text("Hello from mygrid_client.py!")

        print("Drawing rectangle...")
        client.goto(0, 2)
        client.rect(30, 5)

        print("Done!")

    except MyGridError as e:
        print(f"Error: {e}")
        print("Make sure my-grid is running with --server")
