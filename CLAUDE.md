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
├── layouts.py     # Workspace templates - YAML save/load for zone layouts
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

| Mode      | Entry   | Keys        | Behavior                     |
| --------- | ------- | ----------- | ---------------------------- |
| NAV       | default | wasd/arrows | Move cursor                  |
| PAN       | `p`     | wasd/arrows | Pan viewport, cursor follows |
| EDIT      | `i`     | typing      | Draw characters on canvas    |
| COMMAND   | `:`     | typing      | Execute commands             |
| MARK_SET  | `m`     | a-z, 0-9    | Set bookmark at cursor       |
| MARK_JUMP | `'`     | a-z, 0-9    | Jump to bookmark             |
| VISUAL    | `v`     | wasd/arrows | Visual selection mode        |
| DRAW      | `D`     | wasd/arrows | Line drawing mode            |

Exit any mode with `Esc`.

---

## Visual Selection

Visual selection mode allows selecting a rectangular region on the canvas for bulk operations.

**Enter**: Press `v` in NAV mode
**Exit**: Press `Esc`

| Key             | Action                                        |
| --------------- | --------------------------------------------- |
| `wasd` / arrows | Extend/shrink selection                       |
| `y`             | Yank (copy) selection to clipboard            |
| `d`             | Delete selection (clear cells)                |
| `f`             | Fill selection with character (opens command) |
| `Esc`           | Cancel selection                              |

The selection is highlighted in cyan. The cursor shows one corner, the anchor is at the starting position.

---

## Draw Mode

Draw mode allows tracing lines with box-drawing characters using cursor movement.

**Enter**: Press `D` in NAV mode or use `:draw` command
**Exit**: Press `Esc`

| Key             | Action                                             |
| --------------- | -------------------------------------------------- |
| `wasd` / arrows | Draw line in direction (pen down) or move (pen up) |
| `Space`         | Toggle pen up/down                                 |
| `Esc`           | Exit draw mode                                     |

**Pen States**:

- **Pen DOWN**: Movement draws lines
- **Pen UP**: Movement just moves cursor without drawing

**Joystick Support**:

- D-pad/stick: Move and draw
- Button A: Toggle pen up/down
- Button B: Exit draw mode

**Features**:

- Uses current border style (`:border ascii/unicode/rounded/double/heavy`)
- Auto-detects corners when changing direction
- Smart junctions when lines cross (┼) or meet (├ ┤ ┬ ┴)
- Uses current drawing colors (`:color`)

**Example**:

```
:border unicode    # Set line style
D                  # Enter draw mode (pen down)
→→→↓↓↓            # Draw L-shape
Space             # Lift pen
→→→               # Move without drawing
Space             # Lower pen
↓↓↓←←←↑↑↑        # Continue drawing
Esc               # Exit
```

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

| Type      | Description                       | Command                                           |
| --------- | --------------------------------- | ------------------------------------------------- |
| STATIC    | Plain text region (default)       | `:zone create NAME X Y W H`                       |
| PIPE      | One-shot command output           | `:zone pipe NAME W H CMD`                         |
| WATCH     | Periodic or event-driven refresh  | `:zone watch NAME W H (INTERVAL\|watch:PATH) CMD` |
| PTY       | Live terminal session (Unix)      | `:zone pty NAME W H [SHELL]`                      |
| PAGER     | Paginated file viewer with colors | `:zone pager NAME W H FILE`                       |
| FIFO      | Named pipe listener (Unix)        | `:zone fifo NAME W H PATH`                        |
| SOCKET    | TCP port listener                 | `:zone socket NAME W H PORT`                      |
| CLIPBOARD | Yank/paste buffer                 | `:clipboard zone`                                 |

### Zone Commands

| Command                               | Description                                     |
| ------------------------------------- | ----------------------------------------------- |
| `:zone create NAME X Y W H`           | Create static zone at coordinates               |
| `:zone create NAME here W H`          | Create zone at cursor position                  |
| `:zone pipe NAME W H CMD`             | Create pipe zone, execute command once          |
| `:zone watch NAME W H 5s CMD`         | Create watch zone, refresh every 5 seconds      |
| `:zone watch NAME W H watch:PATH CMD` | Create watch zone triggered by file changes     |
| `:zone pty NAME W H [SHELL]`          | Create PTY zone with live terminal (Unix)       |
| `:zone fifo NAME W H PATH`            | Create FIFO zone listening on named pipe (Unix) |
| `:zone socket NAME W H PORT`          | Create socket zone listening on TCP port        |
| `:zone delete NAME`                   | Delete zone                                     |
| `:zone goto NAME`                     | Jump cursor to zone center                      |
| `:zone info [NAME]`                   | Show zone info                                  |
| `:zone refresh NAME`                  | Manually refresh pipe/watch zone                |
| `:zone pause NAME`                    | Pause watch zone refresh                        |
| `:zone resume NAME`                   | Resume watch zone refresh                       |
| `:zone send NAME TEXT`                | Send text to PTY zone                           |
| `:zone focus NAME`                    | Focus PTY zone for keyboard input               |
| `:zones`                              | List all zones                                  |

### Examples

```bash
# Show disk usage, refresh every 30 seconds
:zone watch DISK 40 10 30s df -h

# Show git status, refresh every 5 seconds
:zone watch GIT 50 15 5s git status --short

# Watch log file - instant refresh when file changes (Linux/WSL)
:zone watch LOG 80 20 watch:/var/log/app.log "tail -20 {file}"

# Watch .git directory - instant refresh on git operations
:zone watch GIT 50 15 watch:.git "git status --short"

# Watch config file for changes
:zone watch CONFIG 60 10 watch:/etc/nginx/nginx.conf "cat {file}"

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

# FIFO zone - receive data from external processes (Unix only)
:zone fifo EVENTS 50 15 /tmp/my-events.fifo
# Then from another terminal: echo "New event" > /tmp/my-events.fifo

# Socket zone - receive data over TCP
:zone socket MESSAGES 60 20 9876
# Then from another terminal: echo "Hello" | nc localhost 9876
```

Zones display with borders showing type indicator: `[P]` for pipe, `[W]` for watch, `[T]` for PTY, `[R]` for pager (reader), `[F]` for FIFO, `[S]` for socket, `[C]` for clipboard.

### PTY Focus Model (Unix/WSL only)

PTY zones provide live interactive terminals with full echo, ANSI color support, and scrollback:

**Basic Usage:**

1. Create PTY zone: `:zone pty TERM 80 24`
2. Navigate cursor into the zone
3. Press **Enter** to focus (or use `:zone focus TERM`)
4. All keystrokes go directly to the terminal
5. Input echo works - you can see what you're typing!
6. Press **Escape** to unfocus and return to canvas navigation

**Terminal Emulation:**

- Full VT100/ANSI terminal emulation via `pyte`
- ANSI color support (foreground/background, 256-color palette mapped to 8 colors)
- Cursor control, backspace, escape sequences all work
- Run any terminal program: bash, vim, python REPL, Claude Code, etc.

**Scrollback Navigation:**

When focused on a PTY zone, you can scroll through terminal history:

| Key          | Action                                   |
| ------------ | ---------------------------------------- |
| `Shift+PgUp` | Scroll up half page (enters scroll mode) |
| `Shift+PgDn` | Scroll down half page                    |
| `Shift+Home` | Go to top of history                     |
| `Shift+End`  | Go to bottom (re-enables auto-scroll)    |
| `Esc`        | Unfocus PTY                              |

**Note:** Raw `PgUp`/`PgDn` are forwarded to the PTY application. Use `Shift+` versions for scrollback.

**Scroll Modes:**

- **Auto-scroll** (default): Always shows latest output, scrolls automatically
- **Manual scroll**: Shift+PgUp enters this mode, shows scroll position in status line
- Press `Shift+End` to return to auto-scroll

**Status Line:**

- Auto-scroll mode: `[PTY] TERM - Shift+PgUp:scroll Esc:unfocus`
- Scroll mode: `[PTY SCROLL] TERM - 50/200 - Shift+End:auto Esc:unfocus`

**Color Support:**

- ANSI colors display correctly (foreground and background)
- 256-color palette supported (mapped to basic 8 colors)
- Colors preserved on current screen AND in scrollback history
- Full VT100/ANSI terminal emulation via pyte library

**Use Cases:**

- Review command output that scrolled past
- Copy error messages from history
- Navigate through log files
- Run interactive programs with full color support
- Run nested instances of Claude Code inside my-grid!

Note: PTY zones require Unix-like systems (Linux, macOS, WSL). Not available on native Windows.

---

## Colors

Set drawing colors for text and regions. Colors persist until changed.

### Color Commands

| Command            | Description                                         |
| ------------------ | --------------------------------------------------- |
| `:color FG [BG]`   | Set drawing color (foreground, optional background) |
| `:color off`       | Reset to default (terminal) colors                  |
| `:color apply W H` | Apply current color to region at cursor             |
| `:palette`         | Show available color names                          |
| `:color`           | Show current color setting                          |

### Available Colors

| Name      | Value | Description      |
| --------- | ----- | ---------------- |
| `black`   | 0     | Black            |
| `red`     | 1     | Red              |
| `green`   | 2     | Green            |
| `yellow`  | 3     | Yellow           |
| `blue`    | 4     | Blue             |
| `magenta` | 5     | Magenta          |
| `cyan`    | 6     | Cyan             |
| `white`   | 7     | White            |
| `default` | -1    | Terminal default |

### Examples

```bash
# Set red foreground
:color red

# Set green text on black background
:color green black

# Type in edit mode - text appears in set color
i Hello World <Esc>

# Apply blue background to 10x5 region at cursor
:color default blue
:color apply 10 5

# Reset to default colors
:color off
```

Colors are saved with the canvas in project files.

---

## Layouts (Workspace Templates)

Layouts save and restore zone configurations. Stored in `~/.config/mygrid/layouts/` (Unix) or `%APPDATA%/mygrid/layouts/` (Windows).

### Layout Commands

| Command                     | Description                                |
| --------------------------- | ------------------------------------------ |
| `:layout list`              | List available layouts                     |
| `:layout load NAME`         | Load a layout (creates zones)              |
| `:layout load NAME --clear` | Load layout, clearing existing zones first |
| `:layout save NAME [DESC]`  | Save current zones as layout               |
| `:layout delete NAME`       | Delete a layout                            |
| `:layout info NAME`         | Show layout details                        |

### Default Layouts

Three default layouts are installed automatically:

- **devops** - System monitoring with logs, processes, disk, and terminal
- **development** - Git status, file listing, and editor terminal
- **monitoring** - CPU, memory, network, and disk monitoring

### Layout File Format (YAML)

```yaml
name: My Workspace
description: Custom workspace layout
cursor:
  x: 0
  y: 0
zones:
  - name: LOGS
    type: watch
    x: 0
    y: 0
    width: 80
    height: 15
    command: "tail -f /var/log/syslog"
    interval: 5
    bookmark: "l"

  - name: TERMINAL
    type: pty
    x: 85
    y: 0
    width: 60
    height: 20
    bookmark: "t"
```

---

## Commands

| Command                 | Aliases | Description                             |
| ----------------------- | ------- | --------------------------------------- |
| `quit`                  | `q`     | Exit editor                             |
| `write`                 | `w`     | Save project                            |
| `wq`                    | -       | Save and quit                           |
| `goto X Y`              | `g`     | Move cursor to coordinates              |
| `origin [X Y\|here]`    | -       | Set canvas origin                       |
| `clear`                 | -       | Clear entire canvas                     |
| `rect W H [char]`       | -       | Draw rectangle at cursor                |
| `line X2 Y2 [char]`     | -       | Draw line from cursor                   |
| `text MESSAGE`          | -       | Write text at cursor                    |
| `grid major\|minor\|N`  | -       | Toggle/configure grid                   |
| `ydir up\|down`         | -       | Set Y-axis direction                    |
| `export [file]`         | -       | Export as plain text                    |
| `import file`           | -       | Import text file                        |
| `marks`                 | -       | List all bookmarks                      |
| `mark KEY [X Y]`        | -       | Set bookmark                            |
| `delmark KEY`           | -       | Delete bookmark                         |
| `delmarks`              | -       | Delete all bookmarks                    |
| `zone SUBCMD`           | -       | Zone management (see Zones section)     |
| `zones`                 | -       | List all zones                          |
| `layout SUBCMD`         | -       | Layout management (see Layouts section) |
| `yank W H`              | `y`     | Yank region at cursor to clipboard      |
| `yank zone NAME`        | -       | Yank zone content to clipboard          |
| `yank system`           | -       | Read from system clipboard              |
| `paste`                 | `p`     | Paste clipboard at cursor               |
| `paste system`          | -       | Copy clipboard to system clipboard      |
| `clipboard`             | -       | Show clipboard info                     |
| `clipboard clear`       | -       | Clear clipboard                         |
| `clipboard zone`        | -       | Create clipboard zone                   |
| `box [STYLE] TEXT`      | -       | Draw ASCII box (requires `boxes`)       |
| `figlet [-f FONT] TEXT` | -       | Draw ASCII art text (requires `figlet`) |
| `pipe COMMAND`          | -       | Execute command, write output at cursor |
| `tools`                 | -       | Show external tool status               |

---

## Key Bindings

| Key             | Action                  |
| --------------- | ----------------------- |
| `wasd` / arrows | Move cursor             |
| `WASD`          | Fast move (10x)         |
| `i`             | Enter edit mode         |
| `p`             | Toggle pan mode         |
| `:` or `/`      | Enter command mode      |
| `m` + key       | Set bookmark (a-z, 0-9) |
| `'` + key       | Jump to bookmark        |
| `Esc`           | Exit current mode       |
| `g` / `G`       | Toggle major/minor grid |
| `0`             | Toggle origin marker    |
| `Ctrl+S`        | Save                    |
| `Ctrl+O`        | Open                    |
| `Ctrl+N`        | New                     |
| `q`             | Quit                    |
| `F1`            | Help                    |

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

### Python Client Library

Use the included Python client for scripting:

```python
from scripts.mygrid_client import MyGridClient

client = MyGridClient()
client.goto(0, 0)
client.text('Hello from Python!')
client.rect(20, 10)
client.zone_watch('STATUS', 60, 15, '10s', 'uptime')
client.save('dashboard.json')
```

### Bash Helpers

```bash
# Send single command
./scripts/mygrid-send ':text Hello'

# Pipe command output to canvas
ls -la | ./scripts/mygrid-pipe 0 0

# Execute batch commands
./scripts/batch_commands.py commands.txt
```

### Additional Resources

- **[API Scripting Guide](docs/guides/api-scripting.md)** - Full documentation with patterns
- **[Notepad++ Integration](docs/guides/notepadpp-integration.md)** - Send text from Notepad++ to canvas
- **[scripts/](scripts/)** - Ready-to-use Python and Bash scripts
- **[examples/music-organization/](examples/music-organization/)** - Real-world automation example

---

## Claude Code Integration

my-grid can integrate with Claude Code sessions to create a visual workspace for AI-assisted development. Several integration patterns are available.

### Pattern 1: Socket Zone for Claude Output

Create a socket zone to receive Claude Code output:

```bash
# In my-grid
:zone socket CLAUDE 80 30 9999

# In Claude Code hook (.claude/hooks/post-response.sh)
#!/bin/bash
echo "$CLAUDE_RESPONSE" | nc localhost 9999
```

### Pattern 2: FIFO Zone (Unix/WSL)

Use a named pipe for one-way communication:

```bash
# In my-grid
:zone fifo CLAUDE 80 30 /tmp/claude-output.fifo

# From Claude Code or scripts
echo "Response content here" > /tmp/claude-output.fifo
```

### Pattern 3: API Server for Bidirectional Control

Use the API server for full control from external processes:

```bash
# Start my-grid with server
python mygrid.py --server --port 8765

# From Claude Code - send commands
echo ':zone pipe STATUS 40 10 git status' | nc localhost 8765
echo ':text Generated code here' | nc localhost 8765

# Query state
echo ':status' | nc localhost 8765
```

### Pattern 4: Workspace Layout

Create a dedicated Claude Code workspace layout:

```yaml
# ~/.config/mygrid/layouts/claude-code.yaml
name: claude-code
description: Claude Code integration workspace
zones:
  - name: CLAUDE
    type: socket
    x: 0
    y: 0
    width: 80
    height: 25
    port: 9999
    bookmark: "c"
    description: "Claude responses"

  - name: CONTEXT
    type: static
    x: 85
    y: 0
    width: 50
    height: 15
    bookmark: "x"
    description: "Context notes"

  - name: TERMINAL
    type: pty
    x: 85
    y: 16
    width: 50
    height: 12
    bookmark: "t"
    description: "Terminal"
```

Load with: `:layout load claude-code`

### Pattern 5: Meta-Inception - Claude Code Inside my-grid

Run Claude Code directly inside a my-grid PTY zone for the ultimate meta-development experience:

**Setup:**

```bash
# Start my-grid with server mode
python3 mygrid.py --server --layout pty-test

# Jump to Claude PTY zone and focus it
# Press 'c (bookmark) then Enter (focus)

# Start Claude Code inside the zone
claude
```

**What You Get:**

- Claude Code's full TUI running inside my-grid
- Full color support for Claude's interface
- Scrollback through Claude's responses (Shift+PgUp/PgDn)
- Multiple PTY zones for parallel Claude sessions
- README/docs visible alongside Claude

**Use Cases:**

- Ask Claude to help develop my-grid itself (meta!)
- View documentation while chatting with Claude
- Multiple Claude contexts in different zones
- Compare responses from different Claude sessions side-by-side

**Tips:**

- Use `Esc` to unfocus PTY and navigate my-grid
- Press `'c` to quickly jump back to Claude zone
- Scrollback works - review Claude's previous responses with `Shift+PgUp`
- Colors work - Claude's syntax highlighting displays correctly
- Run bash commands in a separate PTY zone while Claude is running

**Meta-Development Workflow:**

```
┌──────────────┬──────────────┐
│   README     │  BASH shell  │
│  (reference) │ (run tests)  │
├──────────────┼──────────────┤
│ CLAUDE CODE  │              │
│ (AI assist)  │              │
└──────────────┴──────────────┘
```

### Integration Tips

1. **WSL + Windows**: Socket zones work across the WSL boundary - run my-grid in WSL, connect from Windows
2. **Multiple zones**: Create separate zones for different Claude tools or contexts
3. **Bookmarks**: Use bookmarks for quick navigation between Claude output and your work areas
4. **Persistence**: Layouts preserve your integration setup across sessions
5. **Meta-inception**: Run Claude Code inside PTY zones to develop my-grid with Claude's help!
