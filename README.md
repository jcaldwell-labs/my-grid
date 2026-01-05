# my-grid

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)

**A spatial canvas editor for your terminal.** Think vim meets infinite whiteboard, with live terminal zones and system monitoring built in.

> _"Navigate to information, don't open windows."_ – Inspired by Jef Raskin's _The Humane Interface_

---

## Why my-grid?

Traditional terminals are linear. my-grid gives you **infinite 2D space** where you can:

- ✏️ **Draw and diagram** directly in ASCII
- 📊 **Embed live terminals** (PTY zones) anywhere on the canvas
- 🔄 **Monitor commands** that auto-refresh (watch zones)
- 🗺️ **Spatially organize** your development workspace
- 🚀 **Navigate like vim** with bookmarks and modal editing

**Perfect for:**

- DevOps dashboards (disk usage, logs, git status in one spatial view)
- System administration (live terminals + monitoring + notes)
- ASCII art and diagramming
- Spatial note-taking and documentation
- Terminal-native project workspaces

---

## 🎬 Demo

<!-- TODO: Add terminal recording GIF here -->

```
# Demo recording coming soon!
# Run: asciinema rec demo/basic-usage.cast
```

**Try it yourself:**

```bash
pip install -r requirements.txt
python mygrid.py
:layout load devops    # Load DevOps monitoring layout
```

---

## ⚡ Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/jcaldwell-labs/my-grid.git
cd my-grid

# Install dependencies
pip install -r requirements.txt

# Run the editor
python mygrid.py
```

### First Steps

```bash
# Navigate with vim keys or arrows
wasd / ←↓↑→

# Enter edit mode and type
i
Hello World!
<Esc>

# Draw a rectangle
:rect 20 10

# Create a live terminal zone (Unix/WSL)
:zone pty TERM 80 24

# Save your work
:w myproject.json

# Load a pre-built workspace
:layout load development
```

---

## 🎯 Core Features

### Infinite Canvas

- **Sparse storage** – Only stores non-empty cells, unlimited space
- **Configurable origin** – Y-up (mathematical) or Y-down (screen) coordinates
- **Grid overlay** – Major/minor grid lines for alignment

### Vim-Style Navigation

- **Modal editing** – NAV, EDIT, PAN, COMMAND, VISUAL, DRAW modes
- **Bookmarks** – Quick jump with `m`/`'` + 36 slots (a-z, 0-9)
- **Fast movement** – `WASD` for 10x speed

### Dynamic Zones (The Killer Feature)

| Zone Type  | Description                | Use Case                          |
| ---------- | -------------------------- | --------------------------------- |
| **PIPE**   | One-shot command output    | `tree`, `ls`, snapshot data       |
| **WATCH**  | Auto-refreshing commands   | `git status`, `df -h`, monitoring |
| **PTY**    | Live interactive terminal  | Full shell, Python REPL, vim      |
| **FIFO**   | Named pipe listener (Unix) | External process communication    |
| **SOCKET** | TCP port listener          | Remote control, API integration   |

**Example: DevOps Dashboard**

```bash
:zone watch DISK 40 10 30s df -h
:zone watch GIT 50 15 5s git status --short
:zone pty TERM 80 24
:zone create NOTES 0 0 40 20
```

### Layouts (Workspace Templates)

- **Save/load** zone configurations
- **Pre-built layouts:** `devops`, `development`, `monitoring`
- **YAML format** – Easy to share and version control

### Visual Selection & Drawing

- **Visual mode** – Select rectangular regions, yank/delete/fill
- **Draw mode** – Trace lines with box-drawing characters
- **Box tools** – Integrate `boxes`, `figlet` for ASCII art

---

## 🎮 Key Bindings

### Navigation Mode (default)

| Key             | Action                  |
| --------------- | ----------------------- |
| `wasd` / arrows | Move cursor             |
| `WASD`          | Fast move (10x)         |
| `i`             | Enter edit mode         |
| `p`             | Toggle pan mode         |
| `v`             | Visual selection mode   |
| `D`             | Draw mode               |
| `:` or `/`      | Command mode            |
| `m` + key       | Set bookmark (a-z, 0-9) |
| `'` + key       | Jump to bookmark        |
| `g` / `G`       | Toggle grid             |
| `0`             | Toggle origin marker    |
| `Esc`           | Exit current mode       |

### Edit Mode

| Key   | Action             |
| ----- | ------------------ |
| Type  | Insert characters  |
| `Esc` | Return to NAV mode |

### Visual Mode

| Key             | Action              |
| --------------- | ------------------- |
| `wasd` / arrows | Extend selection    |
| `y`             | Yank (copy)         |
| `d`             | Delete selection    |
| `f`             | Fill with character |
| `Esc`           | Cancel              |

---

## 📝 Essential Commands

### File Operations

```bash
:w [file]          # Save project (default: mygrid.json)
:q                 # Quit
:wq                # Save and quit
:export [file]     # Export as plain text
:import file       # Import text file
```

### Drawing

```bash
:rect W H [char]   # Draw rectangle at cursor
:line X2 Y2 [char] # Draw line from cursor to point
:text MESSAGE      # Write text at cursor
:box [STYLE] TEXT  # ASCII box (requires boxes)
:figlet TEXT       # ASCII art text (requires figlet)
```

### Zones

```bash
:zone create NAME X Y W H              # Static zone
:zone pipe NAME W H COMMAND            # One-shot command
:zone watch NAME W H 5s COMMAND        # Auto-refresh every 5s
:zone pty NAME W H [SHELL]             # Live terminal (Unix/WSL)
:zone socket NAME W H PORT             # TCP listener
:zones                                  # List all zones
:zone goto NAME                         # Jump to zone
:zone delete NAME                       # Remove zone
```

### Layouts

```bash
:layout list           # Show available layouts
:layout load NAME      # Load layout
:layout save NAME      # Save current zones
```

### Clipboard

```bash
:yank W H              # Copy region to clipboard
:paste                 # Paste clipboard
:yank system           # Import from system clipboard
:paste system          # Export to system clipboard
```

---

## 🔧 Use Cases

### 1. DevOps Monitoring Dashboard

```bash
:layout load devops
# Creates zones for: system logs, disk usage, processes, git status
# Navigate with bookmarks: 'l (logs), 'd (disk), 't (terminal)
```

### 2. Development Workspace

```bash
:zone watch GIT 60 12 5s git status
:zone pty VIM 80 30 vim
:zone pipe TREE 40 20 tree -L 2
:zone create NOTES 0 0 40 15
```

### 3. ASCII Diagramming

```bash
:border unicode
D  # Enter draw mode
# Draw flowcharts, network diagrams, UI mockups
:box stone "Server Architecture"
```

### 4. System Administration

```bash
:zone watch LOGS 100 20 2s tail -f /var/log/syslog
:zone watch DISK 40 10 30s df -h
:zone pty ADMIN 80 24
```

---

## 🆚 Comparison

| Feature                      | my-grid          | vim/emacs | tmux | Traditional Editor |
| ---------------------------- | ---------------- | --------- | ---- | ------------------ |
| **Infinite 2D canvas**       | ✅               | ❌        | ❌   | ❌                 |
| **Embedded live terminals**  | ✅ (PTY zones)   | ❌        | ✅   | ❌                 |
| **Spatial bookmarks**        | ✅               | Limited   | ❌   | ❌                 |
| **Auto-refreshing commands** | ✅ (Watch zones) | ❌        | ❌   | ❌                 |
| **Modal editing**            | ✅ (Vim-style)   | ✅        | ❌   | ❌                 |
| **ASCII drawing tools**      | ✅               | Limited   | ❌   | Limited            |
| **Workspace layouts**        | ✅ (Save/load)   | Limited   | ✅   | ❌                 |

**my-grid = tmux + vim + infinite whiteboard + system monitoring**

---

## 🏗️ Architecture

```
User Input → Renderer → InputEvent → ModeStateMachine → Application
                ↓                            ↓              ↓
            curses                    Mode-specific     Commands
                                       handlers          Zones
                                                         Canvas
```

**Key components:**

- `canvas.py` – Sparse dict storage, drawing primitives
- `viewport.py` – Coordinate transforms, cursor management
- `renderer.py` – Curses rendering, colors, grid overlay
- `modes.py` – State machine for NAV/EDIT/PAN/COMMAND
- `zones.py` – Dynamic content regions (pipe/watch/PTY/socket)
- `layouts.py` – YAML workspace templates

See [CLAUDE.md](CLAUDE.md) for complete architecture and API documentation.

---

## 🚀 Advanced Features

### API Server (Headless Control)

Control my-grid from external processes:

```bash
# Start with API server
python mygrid.py --server --port 8765

# From another terminal
echo ':rect 10 5' | nc localhost 8765
python mygrid-ctl text "Hello from script"
ls -la | python mygrid-ctl box 0 0 80 25
```

**Cross-platform:** Works from Windows → WSL via TCP sockets.

### Scripting & Automation

Automate my-grid with Python, Bash, or any language:

```python
from scripts.mygrid_client import MyGridClient

client = MyGridClient()
client.goto(0, 0)
client.text('Automated dashboard')
client.zone_watch('STATUS', 60, 15, '10s', 'uptime')
```

```bash
# Pipe any command output to canvas
ls -la | ./scripts/mygrid-pipe 0 0

# Batch commands from file
./scripts/batch_commands.py setup.txt
```

See **[API Scripting Guide](docs/guides/api-scripting.md)** for full documentation.

### PTY Zones with Full Terminal Emulation

Interactive terminals powered by pyte for proper VT100/ANSI emulation:

```bash
:zone pty TERM 80 24
# Press Enter in zone to focus
# PgUp/PgDn to scroll through history (colors preserved!)
# Home/End for top/bottom
# Esc to unfocus
```

Features: Full color support, cursor control, backspace handling, scrollback with colors.

### Claude Code Integration

my-grid integrates with AI coding assistants via socket zones:

```bash
:zone socket CLAUDE 80 30 9999
# Send Claude Code responses: echo "$OUTPUT" | nc localhost 9999
:layout load claude-code  # Pre-built AI workspace
```

See [CLAUDE.md](CLAUDE.md) for full integration patterns.

---

## 📚 Documentation

- **[Documentation Hub](docs/README.md)** – Guides, tutorials, and examples
- **[API Scripting Guide](docs/guides/api-scripting.md)** – External automation with Python/Bash
- **[CLAUDE.md](CLAUDE.md)** – Complete command reference, architecture, API docs
- **[Getting Started](docs/guides/getting-started.md)** – First steps with my-grid
- **[Zones Reference](docs/guides/zones-reference.md)** – Complete guide to zone types
- **[Demo System](demo/README.md)** – Demos and production deployment

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Test** with `python -m pytest tests/ -v`
4. **Commit** (`git commit -m 'Add amazing feature'`)
5. **Push** and create a **Pull Request**

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest

# Run tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_canvas.py -v
```

**Ideas for contribution:**

- 🎨 New border styles or color schemes
- 🔌 Integration with external tools
- 📦 Pre-built layouts for specific workflows
- 🐛 Bug fixes and performance improvements
- 📖 Documentation and tutorials

---

## 🗺️ Roadmap

- [ ] Terminal recording playback zones
- [ ] Mouse support for zone interaction
- [ ] WebSocket zone type for browser integration
- [ ] Plugin system for custom zone types
- [ ] Collaborative editing over network
- [ ] Mobile/tablet SSH client optimizations

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by **Jef Raskin's** _The Humane Interface_ (spatial navigation philosophy)
- Built with **curses** (terminal rendering)
- Vim-style modal editing concepts

---

## 📬 Contact & Community

- **Issues:** [GitHub Issues](https://github.com/jcaldwell-labs/my-grid/issues)
- **Discussions:** [GitHub Discussions](https://github.com/jcaldwell-labs/my-grid/discussions)
- **Twitter:** Share your creations with `#mygrid`

---

**Star ⭐ this repository if you find it useful!**

Made with ❤️ for terminal enthusiasts.
