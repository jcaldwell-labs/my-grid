#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for my-grid.

Exposes my-grid functionality to AI agents like Claude Code, enabling:
- Canvas manipulation (text, rect, line)
- Zone management (create, list, delete)
- Navigation (goto, cursor position)
- Project operations (save, load)

Uses the FastMCP framework for simple tool definitions.
Run with: python -m src.mcp_server
"""

import asyncio
import json
import logging
import socket
import sys
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


@dataclass
class MyGridConnection:
    """Connection configuration for my-grid API server."""

    host: str = "127.0.0.1"
    port: int = 8765
    timeout: float = 5.0


class MyGridClient:
    """
    Client for communicating with my-grid API server.

    Sends commands via TCP to a running my-grid instance.
    """

    def __init__(self, config: MyGridConnection | None = None):
        self.config = config or MyGridConnection()

    def send_command(self, command: str) -> dict[str, Any]:
        """
        Send a command to my-grid and return the response.

        Args:
            command: The command string (e.g., ":rect 10 5" or "text Hello")

        Returns:
            Response dict with status and message

        Raises:
            ConnectionError: If cannot connect to my-grid
            TimeoutError: If command times out
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.config.timeout)
                sock.connect((self.config.host, self.config.port))

                # Send command with newline
                sock.sendall((command.strip() + "\n").encode("utf-8"))

                # Receive response
                data = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if b"\n" in data:
                        break

                if data:
                    response_text = data.decode("utf-8").strip()
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        return {"status": "ok", "message": response_text}

                return {"status": "ok", "message": "Command sent"}

        except socket.timeout:
            raise TimeoutError(f"Command timed out after {self.config.timeout}s")
        except ConnectionRefusedError:
            raise ConnectionError(
                f"Cannot connect to my-grid at {self.config.host}:{self.config.port}. "
                "Ensure my-grid is running with --server flag."
            )
        except Exception as e:
            raise ConnectionError(f"Failed to send command: {e}")

    def is_connected(self) -> bool:
        """Check if my-grid server is reachable."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                sock.connect((self.config.host, self.config.port))
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False


# Initialize MCP server and my-grid client
mcp = FastMCP(
    name="my-grid",
    instructions="""
my-grid MCP Server - ASCII Canvas Editor Integration

This server provides tools to control my-grid, an ASCII canvas editor with
vim-style navigation. Use these tools to draw on the canvas, manage zones
(named regions), and navigate the workspace.

Common workflows:
1. Draw text and shapes: Use canvas_text, canvas_rect, canvas_line
2. Create dashboard layouts: Use zone_create, zone_watch for live content
3. Navigate: Use canvas_goto to move cursor, zone_goto to jump to zones

Prerequisites:
- my-grid must be running with --server flag
- Default connection: localhost:8765
""",
)

client = MyGridClient()


def _execute(command: str) -> str:
    """Execute command and return formatted result."""
    try:
        result = client.send_command(command)
        if result.get("status") == "error":
            return f"Error: {result.get('message', 'Unknown error')}"
        return result.get("message", "OK")
    except ConnectionError as e:
        return f"Connection error: {e}"
    except TimeoutError as e:
        return f"Timeout: {e}"


# =============================================================================
# Canvas Tools - Drawing and manipulation
# =============================================================================


@mcp.tool()
def canvas_text(text: str, x: int | None = None, y: int | None = None) -> str:
    """
    Write text at the current cursor position or specified coordinates.

    Args:
        text: The text to write on the canvas
        x: Optional X coordinate (uses cursor position if not specified)
        y: Optional Y coordinate (uses cursor position if not specified)

    Returns:
        Result message confirming the text was written
    """
    if x is not None and y is not None:
        _execute(f":goto {x} {y}")
    return _execute(f":text {text}")


@mcp.tool()
def canvas_rect(width: int, height: int, char: str = "#") -> str:
    """
    Draw a rectangle at the current cursor position.

    Args:
        width: Width of the rectangle
        height: Height of the rectangle
        char: Character to use for drawing (default: #)

    Returns:
        Result message confirming the rectangle was drawn
    """
    return _execute(f":rect {width} {height} {char}")


@mcp.tool()
def canvas_line(x2: int, y2: int, char: str = "*") -> str:
    """
    Draw a line from cursor position to the specified endpoint.

    Args:
        x2: X coordinate of line endpoint
        y2: Y coordinate of line endpoint
        char: Character to use for drawing (default: *)

    Returns:
        Result message confirming the line was drawn
    """
    return _execute(f":line {x2} {y2} {char}")


@mcp.tool()
def canvas_clear() -> str:
    """
    Clear the entire canvas.

    Returns:
        Result message confirming canvas was cleared
    """
    return _execute(":clear")


@mcp.tool()
def canvas_fill(x: int, y: int, width: int, height: int, char: str = " ") -> str:
    """
    Fill a rectangular region with a character.

    Args:
        x: X coordinate of top-left corner
        y: Y coordinate of top-left corner
        width: Width of the region
        height: Height of the region
        char: Character to fill with (default: space)

    Returns:
        Result message confirming the fill operation
    """
    return _execute(f":fill {x} {y} {width} {height} {char}")


@mcp.tool()
def canvas_box(text: str, style: str = "unicode") -> str:
    """
    Draw a box around text using ASCII art (requires 'boxes' command).

    Args:
        text: The text to put inside the box
        style: Box style - unicode, ascii, rounded, double (default: unicode)

    Returns:
        Result message confirming the box was drawn
    """
    return _execute(f":box {style} {text}")


@mcp.tool()
def canvas_figlet(text: str, font: str | None = None) -> str:
    """
    Draw ASCII art text using figlet (requires 'figlet' command).

    Args:
        text: The text to render as ASCII art
        font: Optional figlet font name

    Returns:
        Result message confirming the ASCII art was drawn
    """
    if font:
        return _execute(f":figlet -f {font} {text}")
    return _execute(f":figlet {text}")


# =============================================================================
# Navigation Tools - Cursor and viewport control
# =============================================================================


@mcp.tool()
def canvas_goto(x: int, y: int) -> str:
    """
    Move the cursor to specific coordinates.

    Args:
        x: X coordinate to move to
        y: Y coordinate to move to

    Returns:
        Result message confirming cursor position
    """
    return _execute(f":goto {x} {y}")


@mcp.tool()
def canvas_status() -> str:
    """
    Get the current canvas status including cursor position.

    Returns:
        JSON string with cursor position, canvas bounds, and mode
    """
    return _execute(":status")


@mcp.tool()
def canvas_origin(x: int | None = None, y: int | None = None) -> str:
    """
    Set the canvas origin point (for coordinate reference).

    Args:
        x: Optional X coordinate (uses cursor position if not specified)
        y: Optional Y coordinate (uses cursor position if not specified)

    Returns:
        Result message confirming origin was set
    """
    if x is not None and y is not None:
        return _execute(f":origin {x} {y}")
    return _execute(":origin here")


# =============================================================================
# Zone Tools - Workspace region management
# =============================================================================


@mcp.tool()
def zone_create(
    name: str,
    width: int,
    height: int,
    x: int | None = None,
    y: int | None = None,
) -> str:
    """
    Create a static zone (named rectangular region) on the canvas.

    Args:
        name: Unique name for the zone (e.g., "NOTES", "INBOX")
        width: Width of the zone
        height: Height of the zone
        x: Optional X position (uses cursor position if not specified)
        y: Optional Y position (uses cursor position if not specified)

    Returns:
        Result message confirming zone creation
    """
    if x is not None and y is not None:
        return _execute(f":zone create {name} {x} {y} {width} {height}")
    return _execute(f":zone create {name} here {width} {height}")


@mcp.tool()
def zone_pipe(name: str, width: int, height: int, command: str) -> str:
    """
    Create a pipe zone that displays output of a command (one-shot).

    Args:
        name: Unique name for the zone
        width: Width of the zone
        height: Height of the zone
        command: Shell command to execute

    Returns:
        Result message confirming zone creation
    """
    return _execute(f":zone pipe {name} {width} {height} {command}")


@mcp.tool()
def zone_watch(name: str, width: int, height: int, interval: str, command: str) -> str:
    """
    Create a watch zone that periodically refreshes command output.

    Args:
        name: Unique name for the zone
        width: Width of the zone
        height: Height of the zone
        interval: Refresh interval (e.g., "5s", "30s", "1m")
        command: Shell command to execute periodically

    Returns:
        Result message confirming zone creation
    """
    return _execute(f":zone watch {name} {width} {height} {interval} {command}")


@mcp.tool()
def zone_http(
    name: str, width: int, height: int, url: str, interval: str | None = None
) -> str:
    """
    Create an HTTP zone that fetches and displays URL content.

    Args:
        name: Unique name for the zone
        width: Width of the zone
        height: Height of the zone
        url: URL to fetch content from
        interval: Optional refresh interval (e.g., "30s")

    Returns:
        Result message confirming zone creation
    """
    if interval:
        return _execute(f":zone http {name} {width} {height} '{url}' {interval}")
    return _execute(f":zone http {name} {width} {height} '{url}'")


@mcp.tool()
def zone_pty(name: str, width: int, height: int, shell: str | None = None) -> str:
    """
    Create a PTY zone with an interactive terminal session (Unix only).

    Args:
        name: Unique name for the zone
        width: Width of the zone
        height: Height of the zone
        shell: Optional shell path (default: /bin/bash)

    Returns:
        Result message confirming zone creation
    """
    if shell:
        return _execute(f":zone pty {name} {width} {height} {shell}")
    return _execute(f":zone pty {name} {width} {height}")


@mcp.tool()
def zone_delete(name: str) -> str:
    """
    Delete a zone by name.

    Args:
        name: Name of the zone to delete

    Returns:
        Result message confirming deletion
    """
    return _execute(f":zone delete {name}")


@mcp.tool()
def zone_goto(name: str) -> str:
    """
    Jump the cursor to a zone's center position.

    Args:
        name: Name of the zone to jump to

    Returns:
        Result message confirming jump
    """
    return _execute(f":zone goto {name}")


@mcp.tool()
def zone_list() -> str:
    """
    List all zones with their positions and types.

    Returns:
        List of zones in JSON format
    """
    return _execute(":zones")


@mcp.tool()
def zone_info(name: str | None = None) -> str:
    """
    Get detailed information about a zone.

    Args:
        name: Optional zone name (shows all zones if not specified)

    Returns:
        Zone information in JSON format
    """
    if name:
        return _execute(f":zone info {name}")
    return _execute(":zone info")


@mcp.tool()
def zone_refresh(name: str) -> str:
    """
    Manually refresh a pipe or watch zone.

    Args:
        name: Name of the zone to refresh

    Returns:
        Result message confirming refresh
    """
    return _execute(f":zone refresh {name}")


@mcp.tool()
def zone_send(name: str, text: str) -> str:
    """
    Send text input to a PTY zone.

    Args:
        name: Name of the PTY zone
        text: Text to send (use \\n for Enter)

    Returns:
        Result message confirming send
    """
    return _execute(f":zone send {name} {text}")


# =============================================================================
# Bookmark Tools - Quick navigation
# =============================================================================


@mcp.tool()
def bookmark_set(key: str, x: int | None = None, y: int | None = None) -> str:
    """
    Set a bookmark for quick navigation.

    Args:
        key: Single character key (a-z or 0-9)
        x: Optional X coordinate (uses cursor position if not specified)
        y: Optional Y coordinate (uses cursor position if not specified)

    Returns:
        Result message confirming bookmark was set
    """
    if x is not None and y is not None:
        return _execute(f":mark {key} {x} {y}")
    return _execute(f":mark {key}")


@mcp.tool()
def bookmark_jump(key: str) -> str:
    """
    Jump to a bookmark position.

    Args:
        key: Single character key of the bookmark

    Returns:
        Result message confirming jump
    """
    return _execute(f":goto mark {key}")


@mcp.tool()
def bookmark_list() -> str:
    """
    List all bookmarks with their positions.

    Returns:
        List of bookmarks
    """
    return _execute(":marks")


@mcp.tool()
def bookmark_delete(key: str) -> str:
    """
    Delete a bookmark.

    Args:
        key: Single character key of the bookmark to delete

    Returns:
        Result message confirming deletion
    """
    return _execute(f":delmark {key}")


# =============================================================================
# Layout Tools - Workspace templates
# =============================================================================


@mcp.tool()
def layout_load(name: str, clear_existing: bool = False) -> str:
    """
    Load a saved layout (zone configuration).

    Args:
        name: Name of the layout to load
        clear_existing: If True, clear existing zones first

    Returns:
        Result message confirming layout was loaded
    """
    if clear_existing:
        return _execute(f":layout load {name} --clear")
    return _execute(f":layout load {name}")


@mcp.tool()
def layout_save(name: str, description: str | None = None) -> str:
    """
    Save current zones as a layout.

    Args:
        name: Name for the layout
        description: Optional description

    Returns:
        Result message confirming layout was saved
    """
    if description:
        return _execute(f":layout save {name} {description}")
    return _execute(f":layout save {name}")


@mcp.tool()
def layout_list() -> str:
    """
    List all available layouts.

    Returns:
        List of available layouts
    """
    return _execute(":layout list")


# =============================================================================
# Project Tools - Save/load operations
# =============================================================================


@mcp.tool()
def project_save(filename: str | None = None) -> str:
    """
    Save the current canvas and zones to a file.

    Args:
        filename: Optional filename (uses current file if not specified)

    Returns:
        Result message confirming save
    """
    if filename:
        return _execute(f":write {filename}")
    return _execute(":write")


@mcp.tool()
def project_export(filename: str) -> str:
    """
    Export the canvas as plain text.

    Args:
        filename: Filename to export to

    Returns:
        Result message confirming export
    """
    return _execute(f":export {filename}")


@mcp.tool()
def execute_command(command: str) -> str:
    """
    Execute an arbitrary my-grid command.

    This is a low-level tool for commands not covered by other tools.
    Commands should start with ':' (e.g., ':rect 10 5').

    Args:
        command: The command to execute

    Returns:
        Result of command execution
    """
    return _execute(command)


# =============================================================================
# Connection Tools - Server connectivity
# =============================================================================


@mcp.tool()
def check_connection() -> str:
    """
    Check if my-grid server is reachable.

    Returns:
        Connection status message
    """
    if client.is_connected():
        return f"Connected to my-grid at {client.config.host}:{client.config.port}"
    return (
        f"Cannot connect to my-grid at {client.config.host}:{client.config.port}. "
        "Ensure my-grid is running with --server flag."
    )


# =============================================================================
# Main entry point
# =============================================================================


def main():
    """Run the MCP server using stdio transport."""
    import asyncio

    # Configure logging to stderr (stdout is used for MCP communication)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    logger.info("Starting my-grid MCP server...")

    # Run the server with stdio transport
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
