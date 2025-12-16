"""
External tool integration for content generation.

Provides integration with:
- boxes: ASCII art box frames around text
- figlet: Large ASCII text banners
- shell commands: Pipe stdout to canvas
"""

import subprocess
import shutil
from dataclasses import dataclass
from typing import Callable


@dataclass
class ExternalToolResult:
    """Result from external tool execution."""
    success: bool
    lines: list[str]
    error: str = ""


def tool_available(name: str) -> bool:
    """Check if an external tool is available."""
    return shutil.which(name) is not None


# =============================================================================
# BOXES INTEGRATION
# =============================================================================

_boxes_styles_cache: list[str] | None = None


def get_boxes_styles() -> list[str]:
    """
    Get list of available boxes styles.

    Returns cached list after first call.
    """
    global _boxes_styles_cache

    if _boxes_styles_cache is not None:
        return _boxes_styles_cache

    if not tool_available("boxes"):
        _boxes_styles_cache = []
        return []

    try:
        result = subprocess.run(
            ["boxes", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Parse style names from output
        # Format: "stylename alias othername" or "stylename"
        styles = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line and not line.startswith("-") and not line.startswith("("):
                # Extract first word as style name
                parts = line.split()
                if parts and parts[0].isalnum():
                    styles.append(parts[0])

        _boxes_styles_cache = sorted(set(styles))
        return _boxes_styles_cache
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        _boxes_styles_cache = []
        return []


def draw_box(content: str, style: str = "ansi") -> ExternalToolResult:
    """
    Draw a box around content using the boxes tool.

    Args:
        content: Text content to put in box
        style: boxes style name (default: ansi)

    Returns:
        ExternalToolResult with box lines
    """
    if not tool_available("boxes"):
        return ExternalToolResult(
            success=False,
            lines=[],
            error="boxes command not found"
        )

    try:
        result = subprocess.run(
            ["boxes", "-d", style],
            input=content,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return ExternalToolResult(
                success=False,
                lines=[],
                error=result.stderr.strip() or f"boxes exited with code {result.returncode}"
            )

        lines = result.stdout.split("\n")
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        return ExternalToolResult(success=True, lines=lines)

    except subprocess.TimeoutExpired:
        return ExternalToolResult(
            success=False,
            lines=[],
            error="boxes command timed out"
        )
    except subprocess.SubprocessError as e:
        return ExternalToolResult(
            success=False,
            lines=[],
            error=str(e)
        )


def remove_box(content: str, style: str = "ansi") -> ExternalToolResult:
    """
    Remove a box from content using boxes -r.

    Args:
        content: Boxed text content
        style: boxes style name

    Returns:
        ExternalToolResult with unboxed lines
    """
    if not tool_available("boxes"):
        return ExternalToolResult(
            success=False,
            lines=[],
            error="boxes command not found"
        )

    try:
        result = subprocess.run(
            ["boxes", "-d", style, "-r"],
            input=content,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return ExternalToolResult(
                success=False,
                lines=[],
                error=result.stderr.strip()
            )

        lines = result.stdout.split("\n")
        while lines and not lines[-1]:
            lines.pop()

        return ExternalToolResult(success=True, lines=lines)

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        return ExternalToolResult(success=False, lines=[], error=str(e))


# =============================================================================
# FIGLET INTEGRATION
# =============================================================================

_figlet_fonts_cache: list[str] | None = None


def get_figlet_fonts() -> list[str]:
    """
    Get list of available figlet fonts.

    Returns cached list after first call.
    """
    global _figlet_fonts_cache

    if _figlet_fonts_cache is not None:
        return _figlet_fonts_cache

    if not tool_available("figlet"):
        _figlet_fonts_cache = []
        return []

    try:
        result = subprocess.run(
            ["figlet", "-I", "2"],  # List fonts directory
            capture_output=True,
            text=True,
            timeout=5
        )
        # This gives font directory, we need to list .flf files
        # Alternative: use figlet -l or parse showfigfonts
        # For simplicity, return common fonts
        _figlet_fonts_cache = [
            "banner", "big", "block", "bubble", "digital",
            "ivrit", "lean", "mini", "script", "shadow",
            "slant", "small", "smscript", "smshadow", "smslant",
            "standard", "term"
        ]
        return _figlet_fonts_cache

    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        _figlet_fonts_cache = []
        return []


def draw_figlet(text: str, font: str = "standard") -> ExternalToolResult:
    """
    Generate ASCII art text using figlet.

    Args:
        text: Text to render
        font: figlet font name (default: standard)

    Returns:
        ExternalToolResult with figlet lines
    """
    if not tool_available("figlet"):
        return ExternalToolResult(
            success=False,
            lines=[],
            error="figlet command not found"
        )

    try:
        cmd = ["figlet"]
        if font and font != "standard":
            cmd.extend(["-f", font])
        cmd.append(text)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return ExternalToolResult(
                success=False,
                lines=[],
                error=result.stderr.strip() or f"figlet exited with code {result.returncode}"
            )

        lines = result.stdout.split("\n")
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        return ExternalToolResult(success=True, lines=lines)

    except subprocess.TimeoutExpired:
        return ExternalToolResult(
            success=False,
            lines=[],
            error="figlet command timed out"
        )
    except subprocess.SubprocessError as e:
        return ExternalToolResult(
            success=False,
            lines=[],
            error=str(e)
        )


# =============================================================================
# SHELL COMMAND PIPE
# =============================================================================

def pipe_command(command: str, shell: bool = True, timeout: int = 10) -> ExternalToolResult:
    """
    Execute a shell command and capture output.

    Args:
        command: Shell command to execute
        shell: Use shell execution (default True)
        timeout: Command timeout in seconds

    Returns:
        ExternalToolResult with command output lines
    """
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            if output:
                output += "\n--- stderr ---\n"
            output += result.stderr

        lines = output.split("\n")
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        return ExternalToolResult(
            success=result.returncode == 0,
            lines=lines,
            error="" if result.returncode == 0 else f"Exit code: {result.returncode}"
        )

    except subprocess.TimeoutExpired:
        return ExternalToolResult(
            success=False,
            lines=[],
            error=f"Command timed out after {timeout}s"
        )
    except subprocess.SubprocessError as e:
        return ExternalToolResult(
            success=False,
            lines=[],
            error=str(e)
        )


# =============================================================================
# CANVAS HELPERS
# =============================================================================

def write_lines_to_canvas(
    canvas,
    lines: list[str],
    x: int,
    y: int,
    clear_area: bool = False
) -> tuple[int, int]:
    """
    Write lines of text to a canvas at position.

    Args:
        canvas: Canvas object to write to
        lines: Lines of text
        x, y: Starting position (top-left)
        clear_area: If True, clear the area first

    Returns:
        (width, height) of written content
    """
    if not lines:
        return (0, 0)

    max_width = max(len(line) for line in lines)
    height = len(lines)

    # Clear area if requested
    if clear_area:
        for row in range(height):
            for col in range(max_width):
                canvas.clear(x + col, y + row)

    # Write lines
    for row, line in enumerate(lines):
        for col, char in enumerate(line):
            if char != ' ':
                canvas.set(x + col, y + row, char)

    return (max_width, height)


def get_tool_status() -> dict[str, bool]:
    """
    Get availability status of external tools.

    Returns:
        Dict mapping tool name to availability
    """
    return {
        "boxes": tool_available("boxes"),
        "figlet": tool_available("figlet"),
    }
