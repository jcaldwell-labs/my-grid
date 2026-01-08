---
name: grid
description: Spawn and control my-grid ASCII canvas editor in tmux split pane
---

# Grid Command

Spawn and control an interactive ASCII canvas for visual workspace organization.

## Prerequisites

**tmux is required.** The grid spawns in a tmux split pane alongside Claude Code.

**First, check if you're in tmux:**

```bash
echo $TMUX
```

**If empty (not in tmux), start a tmux session first:**

```bash
tmux new -s claude
# Then run Claude Code inside this tmux session
```

**If you see a path (already in tmux), you're ready to use /grid.**

## Quick Start

```bash
# Spawn my-grid in side panel
cd ${CLAUDE_PLUGIN_ROOT}
python3 src/cli.py spawn

# Send commands to the grid
python3 src/cli.py send ":text Hello World"
python3 src/cli.py send ":rect 20 10"

# Control pane layout
python3 src/cli.py zoom       # Toggle fullscreen
python3 src/cli.py ratio 50   # 50/50 split
python3 src/cli.py hide       # Hide pane
python3 src/cli.py show       # Restore pane
```

## Commands

### spawn

Spawn my-grid in a tmux split pane (or reuse existing).

```bash
python3 src/cli.py spawn [--ratio 67] [--layout NAME] [--new]
```

Options:

- `--ratio N`: Pane width percentage (default: 67 = 2/3 of terminal)
- `--layout NAME`: Load layout on startup (devops, development, monitoring)
- `--new`: Force create new pane instead of reusing

### send

Send any my-grid command.

```bash
python3 src/cli.py send COMMAND
```

Examples:

```bash
# Drawing
python3 src/cli.py send ":text Hello"
python3 src/cli.py send ":rect 30 15"
python3 src/cli.py send ":goto 50 25"

# Zones
python3 src/cli.py send ":zone watch GIT 50 15 5s git status --short"
python3 src/cli.py send ":zone pipe FILES 40 20 tree -L 2"
python3 src/cli.py send ":zone pty TERM 80 24"

# Layouts
python3 src/cli.py send ":layout load devops"
python3 src/cli.py send ":layout save myworkspace"
```

### Pane Management

```bash
# Toggle fullscreen zoom
python3 src/cli.py zoom

# Resize pane (25%, 50%, or 75% width)
python3 src/cli.py ratio 25
python3 src/cli.py ratio 50
python3 src/cli.py ratio 75

# Hide/show pane
python3 src/cli.py hide
python3 src/cli.py show

# Close pane
python3 src/cli.py close

# Focus pane
python3 src/cli.py focus
```

### status

Get current grid status.

```bash
python3 src/cli.py status [--json]
```

## Common Workflows

### DevOps Dashboard

```bash
python3 src/cli.py spawn --layout devops
```

### Git Monitoring

```bash
python3 src/cli.py spawn
python3 src/cli.py send ":zone watch GIT 50 15 5s git status --short"
python3 src/cli.py send ":zone watch LOG 50 10 10s git log --oneline -10"
```

### Side-by-Side Coding

```bash
python3 src/cli.py spawn --ratio 50
python3 src/cli.py send ":zone pty EDITOR 80 30 vim"
```

## Requirements

- **tmux**: Must be running inside a tmux session
- **my-grid**: The ASCII canvas editor (this repository)

## Notes

- Pane is reused across spawns unless `--new` is specified
- Server runs on port 8765 by default (override with `--port`)
- All my-grid commands are supported via `send`
