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
  "bookmarks": { "a": {"x": 10, "y": 20}, "b": {"x": 50, "y": 100} }
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
