# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**my-grid** - An ASCII canvas editor with vim-style navigation, using curses for terminal rendering.

The canvas is a sparse, unlimited coordinate space where users can draw/type ASCII characters. The viewport shows a portion of the canvas in the terminal, supporting panning and navigation.

---

## Build & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the editor
python mygrid.py

# Open existing file
python mygrid.py project.json
python mygrid.py drawing.txt

# Run tests
python -m pytest tests/ -v
```

---

## Architecture

```
src/
├── canvas.py      # Sparse canvas - dict[(x,y)] storage, drawing primitives
├── viewport.py    # Coordinate transforms, cursor, origin, Y-direction
├── renderer.py    # Curses terminal rendering, grid overlay, colors
├── input.py       # Action enum, key bindings (pygame-style constants)
├── modes.py       # State machine: NAV, PAN, EDIT, COMMAND modes
├── project.py     # JSON save/load, text export/import
├── zones.py       # Zone management - named regions with dynamic content
├── external.py    # External tool integration (boxes, figlet, pipes)
├── joystick.py    # USB controller/joystick input handling
└── main.py        # Application class, main loop, command handlers

tests/
├── test_canvas.py
├── test_viewport.py
├── test_input.py
├── test_modes.py
└── test_project.py
```

### Component Flow

```
User Input → Renderer.get_input() → curses_key_to_event() → InputEvent
    ↓
ModeStateMachine.process(event) → ModeResult
    ↓
Application handles: mode changes, commands, quit, messages
    ↓
Renderer.render(canvas, viewport, status) → Terminal Display
```

### Key Design Decisions

1. **Sparse Storage**: Canvas uses `dict[tuple[int,int], Cell]` - only non-empty cells consume memory, enabling unlimited canvas size

2. **Coordinate System**: Configurable origin, supports both Y-down (screen) and Y-up (mathematical) directions

3. **Mode State Machine**: Clean separation of input handling per mode with command registration system

4. **Curses Rendering**: Pure terminal - no pygame display window, just using curses for cross-platform terminal output

---

## Modes

| Mode | Entry | Keys | Behavior |
|------|-------|------|----------|
| NAV | default | wasd/arrows | Move cursor |
| PAN | `p` | wasd/arrows | Pan viewport, cursor follows |
| EDIT | `i` | typing | Draw characters on canvas |
| COMMAND | `:` | typing | Execute commands |
| MARK_SET | `m` | a-z, 0-9 | Set bookmark at cursor |
| MARK_JUMP | `'` | a-z, 0-9 | Jump to bookmark |

Exit any mode with `Esc`.

---

## Bookmarks

Quick navigation using vim-style marks. 36 slots available (a-z, 0-9).

**Quick keys (in NAV mode):**
| Key | Action |
|-----|--------|
| `m` + key | Set bookmark at cursor position |
| `'` + key | Jump to bookmark |

**Commands:**
| Command | Description |
|---------|-------------|
| `:marks` | List all bookmarks |
| `:mark KEY [X Y]` | Set bookmark (at cursor or coords) |
| `:delmark KEY` | Delete a bookmark |
| `:delmarks` | Delete all bookmarks |

Bookmarks are saved with project files and cleared on new canvas.

---

## Zones (Spatial Workspace)

Zones are named rectangular regions that can contain dynamic content. Inspired by Jef Raskin's "The Humane Interface" - zones enable a spatial filesystem metaphor where you navigate to information rather than opening windows.

### Zone Types

| Type | Description | Command |
|------|-------------|---------|
| STATIC | Plain text region (default) | `:zone create NAME X Y W H` |
| PIPE | One-shot command output | `:zone pipe NAME W H CMD` |
| WATCH | Periodic refresh command | `:zone watch NAME W H INTERVAL CMD` |
| PTY | Live terminal session | `:zone pty NAME W H [SHELL]` |
| FIFO | Named pipe listener (planned) | - |
| SOCKET | Network listener (planned) | - |

### Zone Commands

| Command | Description |
|---------|-------------|
| `:zone create NAME X Y W H` | Create static zone at coordinates |
| `:zone create NAME here W H` | Create zone at cursor position |
| `:zone pipe NAME W H CMD` | Create pipe zone, execute command once |
| `:zone watch NAME W H 5s CMD` | Create watch zone, refresh every 5 seconds |
| `:zone pty NAME W H [SHELL]` | Create PTY zone with live terminal |
| `:zone delete NAME` | Delete zone |
| `:zone goto NAME` | Jump cursor to zone center |
| `:zone info [NAME]` | Show zone info |
| `:zone refresh NAME` | Manually refresh pipe/watch zone |
| `:zone pause NAME` | Pause watch zone refresh |
| `:zone resume NAME` | Resume watch zone refresh |
| `:zone send NAME TEXT` | Send text to PTY zone |
| `:zone focus NAME` | Focus PTY zone for keyboard input |
| `:zones` | List all zones |

### Examples

```bash
# Show disk usage, refresh every 30 seconds
:zone watch DISK 40 10 30s df -h

# Show git status, refresh every 5 seconds
:zone watch GIT 50 15 5s git status --short

# One-shot command output
:zone pipe TREE 60 20 tree -L 2

# Static zone for notes
:zone create NOTES 0 0 40 20

# Live terminal session (Unix/WSL only)
:zone pty TERM 80 24

# Python REPL zone
:zone pty PYTHON 60 20 /usr/bin/python3

# Send commands to PTY
:zone send TERM ls -la\n
```

Zones display with borders showing type indicator: `[P]` for pipe, `[W]` for watch, `[T]` for PTY, etc.

### PTY Focus Model (Unix/WSL only)

PTY zones provide live interactive terminals:

1. Create PTY zone: `:zone pty TERM 80 24`
2. Navigate cursor into the zone
3. Press **Enter** to focus (or use `:zone focus TERM`)
4. All keystrokes go directly to the terminal
5. Press **Escape** to unfocus and return to canvas navigation

Note: PTY zones require Unix-like systems (Linux, macOS, WSL). Not available on native Windows.

---

## Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `quit` | `q` | Exit editor |
| `write` | `w` | Save project |
| `wq` | - | Save and quit |
| `goto X Y` | `g` | Move cursor to coordinates |
| `origin [X Y\|here]` | - | Set canvas origin |
| `clear` | - | Clear entire canvas |
| `rect W H [char]` | - | Draw rectangle at cursor |
| `line X2 Y2 [char]` | - | Draw line from cursor |
| `text MESSAGE` | - | Write text at cursor |
| `grid major\|minor\|N` | - | Toggle/configure grid |
| `ydir up\|down` | - | Set Y-axis direction |
| `export [file]` | - | Export as plain text |
| `import file` | - | Import text file |
| `marks` | - | List all bookmarks |
| `mark KEY [X Y]` | - | Set bookmark |
| `delmark KEY` | - | Delete bookmark |
| `delmarks` | - | Delete all bookmarks |
| `zone SUBCMD` | - | Zone management (see Zones section) |
| `zones` | - | List all zones |
| `box [STYLE] TEXT` | - | Draw ASCII box (requires `boxes`) |
| `figlet [-f FONT] TEXT` | - | Draw ASCII art text (requires `figlet`) |
| `pipe COMMAND` | - | Execute command, write output at cursor |
| `tools` | - | Show external tool status |

---

## Key Bindings

| Key | Action |
|-----|--------|
| `wasd` / arrows | Move cursor |
| `WASD` | Fast move (10x) |
| `i` | Enter edit mode |
| `p` | Toggle pan mode |
| `:` or `/` | Enter command mode |
| `m` + key | Set bookmark (a-z, 0-9) |
| `'` + key | Jump to bookmark |
| `Esc` | Exit current mode |
| `g` / `G` | Toggle major/minor grid |
| `0` | Toggle origin marker |
| `Ctrl+S` | Save |
| `Ctrl+O` | Open |
| `Ctrl+N` | New |
| `q` | Quit |
| `F1` | Help |

---

## Project File Format (JSON)

```json
{
  "version": "1.0",
  "metadata": { "name": "...", "created": "...", "modified": "..." },
  "canvas": { "cells": [{"x": 0, "y": 0, "char": "A"}, ...] },
  "viewport": { "x": 0, "y": 0, "cursor": {}, "origin": {} },
  "grid": { "show_origin": true, "major_interval": 10 },
  "bookmarks": { "a": {"x": 10, "y": 20}, "b": {"x": 50, "y": 100} },
  "zones": {
    "zones": [
      {
        "name": "INBOX",
        "x": 0, "y": 0, "width": 40, "height": 20,
        "config": {
          "zone_type": "watch",
          "command": "ls -la",
          "refresh_interval": 10
        }
      }
    ]
  }
}
```

---

## Testing

Tests use pytest and can run standalone:

```bash
# All tests
python -m pytest tests/ -v

# Single module
python tests/test_canvas.py

# Specific test
python -m pytest tests/test_modes.py::TestModeStateMachine::test_edit_mode_typing -v
```

---

## API Server (Headless Control)

my-grid can be controlled by external processes via TCP or Unix FIFO.

### Enable Server Mode

```bash
# Start with API server enabled
python mygrid.py --server

# Custom port
python mygrid.py --server --port 9000

# Disable FIFO (TCP only)
python mygrid.py --server --no-fifo
```

### Using mygrid-ctl

Control a running my-grid instance from another terminal:

```bash
# Basic commands
python mygrid-ctl text "Hello World"    # Write text at cursor
python mygrid-ctl rect 20 10            # Draw 20x10 rectangle
python mygrid-ctl goto 50 25            # Move cursor
python mygrid-ctl status                # Get current state (JSON)
python mygrid-ctl clear                 # Clear canvas

# Execute any command
python mygrid-ctl exec ":rect 10 5 #"

# Pipe stdin into a box
ls -la | python mygrid-ctl box 0 0 80 25

# Pipe stdin at position
git status | python mygrid-ctl region 10 5

# Batch commands from file
cat commands.txt | python mygrid-ctl batch -
```

### TCP Protocol

- **Port**: 8765 (default)
- **Format**: Newline-delimited commands, JSON responses

```bash
# Using netcat
echo ':rect 10 5' | nc localhost 8765

# Response format
{"status": "ok", "message": "Drew 10x5 rectangle"}
```

### Unix FIFO (Linux/WSL/macOS)

```bash
# Fire-and-forget commands
echo ':rect 10 5' > /tmp/mygrid.fifo
echo ':text Hello' > /tmp/mygrid.fifo
```

### Cross-Platform (Windows + WSL)

When running my-grid in WSL with `--server`, you can send commands from Windows via TCP:

```powershell
# From Windows PowerShell
$client = New-Object System.Net.Sockets.TcpClient("localhost", 8765)
$stream = $client.GetStream()
$writer = New-Object System.IO.StreamWriter($stream)
$writer.WriteLine(":text Hello from Windows")
$writer.Flush()
```
