---
name: my-grid
description: |
  **ASCII canvas editor integration.** Covers spawning my-grid in tmux, controlling via IPC, and zone management.
  Use when creating visual workspaces, monitoring dashboards, or organizing spatial content.
---

# my-grid Integration

**Start here when using the ASCII canvas editor.** This skill covers spawning, controlling, and integrating my-grid with Claude Code.

## Overview

my-grid is a persistent ASCII canvas editor with:

- **Zones**: Dynamic content regions (WATCH, PTY, PIPE, SOCKET)
- **Infinite canvas**: Navigate freely with vim-style keys
- **TCP API**: Control via external processes
- **Layouts**: Save/restore workspace templates

## Quick Start

```bash
cd ${CLAUDE_PLUGIN_ROOT}

# Spawn in tmux (67% width by default)
python3 claude-plugin/src/cli.py spawn

# Send commands
python3 claude-plugin/src/cli.py send ":text Hello World"
python3 claude-plugin/src/cli.py send ":rect 20 10"

# Create zones
python3 claude-plugin/src/cli.py send ":zone watch GIT 50 15 5s git status --short"
```

## Pane Management

| Command            | Description               |
| ------------------ | ------------------------- |
| `spawn`            | Create/reuse my-grid pane |
| `zoom`             | Toggle fullscreen         |
| `ratio 25\|50\|75` | Set width percentage      |
| `hide` / `show`    | Toggle visibility         |
| `close`            | Kill pane                 |
| `focus`            | Switch to my-grid pane    |

## Zone Types

| Type     | Description              | Example                            |
| -------- | ------------------------ | ---------------------------------- |
| `watch`  | Periodic command refresh | `:zone watch DISK 40 10 30s df -h` |
| `pipe`   | One-shot command         | `:zone pipe TREE 60 20 tree -L 2`  |
| `pty`    | Live terminal            | `:zone pty TERM 80 24`             |
| `socket` | TCP listener             | `:zone socket MSG 50 15 9999`      |

## Common Patterns

### DevOps Dashboard

```bash
python3 claude-plugin/src/cli.py spawn --layout devops
```

### Real-time Monitoring

```bash
python3 claude-plugin/src/cli.py send ":zone watch LOG 80 20 watch:/var/log/app.log tail -20 {file}"
```

### Side-by-Side with Claude

```bash
python3 claude-plugin/src/cli.py spawn --ratio 50
```

## Requirements

- **tmux**: Must run inside tmux session
- **Python 3.8+**: For plugin CLI
