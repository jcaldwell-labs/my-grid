# Why Your Terminal Needs a Second Dimension: Building Spatial Workspaces with my-grid

*How I stopped juggling tmux panes and learned to think spatially*

---

## The Problem with Linear Terminals

Picture this: You're debugging a production issue. You have `tail -f` watching logs in one terminal, `top` monitoring processes in another, a shell ready for commands in a third, and your text editor open somewhere in the mix. You're constantly switching between windows, losing context, and mentally mapping "which terminal was that command in again?"

Sound familiar?

Traditional terminals are fundamentally **linear**. Even with tmux or screen, you're still confined to a grid of rectangular panes that compete for precious screen real estate. You navigate with pane numbers or cycling commands, not with spatial memory.

But here's the thing: **humans think spatially**. We remember where things are, not what number they were assigned.

## Enter Spatial Computing for Terminals

What if your terminal was an infinite 2D canvas? What if you could navigate to your logs by muscle memory, just like you navigate to the coffee machine in your kitchen? What if monitoring dashboards, interactive terminals, and note-taking could coexist in one continuous workspace?

This is the philosophy behind [my-grid](https://github.com/jcaldwell-labs/my-grid) – a spatial canvas editor that brings the power of infinite 2D space to your terminal.

> *"Navigate to information, don't open windows."*
> – Jef Raskin, *The Humane Interface*

## What Makes a Terminal "Spatial"?

Instead of managing window IDs or pane numbers, you work with **coordinates and bookmarks**. The canvas is infinite in all directions. Need a monitoring dashboard at coordinates (0,0)? Put it there. Want your notes 100 units to the right? No problem. Need to jump between them? Set bookmarks and navigate with a single keypress.

Think of it as **vim meets infinite whiteboard meets tmux**.

### Key Differences from Traditional Terminals

| Traditional Terminal | Spatial Terminal (my-grid) |
|---------------------|----------------------------|
| Fixed window/pane grid | Infinite 2D canvas |
| Navigate by window ID | Navigate by location/bookmark |
| Information in windows | Information in space |
| One thing per pane | Multiple things can coexist |
| Mental overhead for layout | Spatial memory works for you |

## Real Example: A DevOps Dashboard

Let me show you something practical. Here's how I use my-grid for monitoring a production server:

```bash
# Start my-grid
python mygrid.py

# Create a disk usage monitor that refreshes every 30 seconds
:zone watch DISK 40 10 30s df -h

# Add git status for the repo I'm working on
:zone watch GIT 50 15 5s git status --short

# Create a live terminal for ad-hoc commands
:zone pty TERM 80 24

# Add a static zone for notes and runbooks
:zone create NOTES 0 0 40 20

# Set bookmarks for quick navigation
m d  # Mark DISK as 'd'
m g  # Mark GIT as 'g'
m t  # Mark TERM as 't'
m n  # Mark NOTES as 'n'

# Save this layout for future use
:layout save production-monitor
```

Now, whenever I need to check disk space, I just press `'d` and I'm there. Git status? `'g`. Need to run a command? `'t` drops me into the terminal. My spatial memory knows where everything is.

**The magic?** This entire workspace lives in ONE terminal window, but it feels like navigating a physical space, not managing window IDs.

## The Killer Feature: Dynamic Zones

Here's where it gets interesting. Those "zones" I mentioned aren't just static text boxes. They're **live, dynamic content areas** that can:

### 1. Auto-Refresh Commands (WATCH zones)
```bash
# Monitor your Rails logs
:zone watch RAILS 100 30 2s tail -30 log/production.log

# Keep an eye on Docker containers
:zone watch DOCKER 60 15 5s docker ps

# Track system resources
:zone watch CPU 40 8 1s top -b -n 1 | head -20
```

Every zone updates independently on its own schedule. No manual refreshing needed.

### 2. Embedded Live Terminals (PTY zones)
This is the game-changer. PTY zones are **fully interactive terminal sessions** embedded directly in your canvas:

```bash
# Create a Python REPL zone
:zone pty PYTHON 60 20 /usr/bin/python3

# Or a dedicated shell for deployment commands
:zone pty DEPLOY 80 30

# Even run vim inside a zone
:zone pty VIM 120 40 vim
```

Navigate your cursor into the zone, press Enter to focus, and you're typing into that terminal. Press Escape to unfocus and return to canvas navigation. **NEW:** Full scrollback support with PgUp/PgDn!

### 3. Network Listeners (SOCKET zones)
Want to push data into your canvas from external processes?

```bash
# Create a socket listener
:zone socket EVENTS 60 20 9999

# From another terminal or script:
echo "Deployment started" | nc localhost 9999
echo "Build completed" | nc localhost 9999
```

Perfect for CI/CD notifications, webhook receivers, or inter-process communication.

## Vim-Style Navigation Done Right

If you're a vim user, the navigation will feel instantly familiar:

```
wasd / arrow keys  → Move cursor
WASD               → Fast move (10x speed)
i                  → Insert mode (type ASCII art)
v                  → Visual selection mode
D                  → Draw mode (trace lines)
m + key            → Set bookmark
' + key            → Jump to bookmark
:                  → Command mode
```

But here's the beauty: **the entire canvas uses vim keybindings**. Not just for editing text, but for navigating space itself.

Want to draw a box? `:rect 20 10`
Need to move to coordinates? `:goto 100 50`
Drawing an ASCII diagram? Press `D` and trace lines with arrow keys.

## Use Cases Beyond Monitoring

### 1. ASCII Diagramming
```bash
# Set Unicode box-drawing style
:border unicode

# Enter draw mode and trace
D
→→→→↓↓↓←←←←↑↑↑  # Draw a rectangle

# Add labels with text
:text "API Server"
```

Create flowcharts, network diagrams, or UI mockups directly in ASCII. The infinite canvas means you're never constrained by screen size.

### 2. Spatial Documentation
Instead of Markdown files scattered across directories, organize documentation spatially:

```
(0,0)       → Project overview
(100,0)     → API documentation
(0,100)     → Deployment runbook
(100,100)   → Troubleshooting guide
```

Set bookmarks (`m o`, `m a`, `m d`, `m t`) and navigate your docs like a physical space.

### 3. Development Workspace
```bash
:layout load development

# Creates:
# - Git status watch zone (top-left)
# - File tree pipe zone (top-right)
# - Main terminal PTY zone (bottom)
# - Scratchpad notes zone (side)
```

Your entire development context in one spatial view. No window switching required.

### 4. System Administration
```bash
:zone watch SYSLOG 100 25 3s sudo tail -f /var/log/syslog
:zone watch SERVICES 50 15 10s systemctl list-units --failed
:zone watch DISK 40 8 30s df -h
:zone pty ROOT 80 30 sudo -i
```

Monitor logs, services, disk space, and have a root shell ready – all visible simultaneously.

## Layouts: Workspace Templates

Once you've built the perfect workspace, save it:

```bash
:layout save my-devops-dashboard "Production monitoring workspace"
```

This creates a YAML file in `~/.config/mygrid/layouts/`:

```yaml
name: my-devops-dashboard
description: Production monitoring workspace
zones:
  - name: DISK
    type: watch
    x: 0
    y: 0
    width: 40
    height: 10
    command: df -h
    interval: 30
    bookmark: d

  - name: TERM
    type: pty
    x: 45
    y: 0
    width: 80
    height: 24
    bookmark: t
```

Load it anytime with `:layout load my-devops-dashboard`. Share it with your team. Version control it with your infrastructure code.

**Three default layouts included:**
- `devops` – System monitoring and logs
- `development` – Git, file browser, terminal
- `monitoring` – CPU, memory, network, disk

## Integration with the Outside World

my-grid isn't isolated. It's designed to integrate with your existing tools:

### API Server for Automation
```bash
# Start with API server enabled
python mygrid.py --server --port 8765

# Control from scripts
echo ':text Deploy started' | nc localhost 8765
echo ':zone refresh LOGS' | nc localhost 8765

# Or use the CLI tool
python mygrid-ctl text "Build completed!"
git diff | python mygrid-ctl box 0 0 80 40
```

### Claude Code / AI Assistant Integration
Create a socket zone to receive AI responses:

```bash
:zone socket CLAUDE 80 30 9999
:layout save ai-workspace

# From Claude Code hook:
echo "$CLAUDE_RESPONSE" | nc localhost 9999
```

Now your AI assistant's output appears in your spatial workspace, alongside code, terminals, and documentation.

### Cross-Platform (Windows + WSL)
Run my-grid in WSL, control it from Windows PowerShell via TCP sockets. The API server works across the WSL boundary.

## The Philosophy: Spatial Thinking

This project is heavily inspired by Jef Raskin's book *The Humane Interface*, which argues that spatial navigation is more natural than hierarchical navigation (files, folders, windows).

**Key insight:** You remember WHERE things are better than WHAT they're called.

Think about your physical desk. You don't remember "file_2023_taxes.pdf in folder Documents/Finance/2023/". You remember "taxes are in the drawer on the left." Spatial memory is powerful and effortless.

my-grid applies this to terminal workflows. Your logs aren't in "tmux pane 3" – they're over there, to the left, where they've always been. Your muscle memory does the navigation.

## Getting Started

```bash
# Clone and install
git clone https://github.com/jcaldwell-labs/my-grid.git
cd my-grid
pip install -r requirements.txt

# Run
python mygrid.py

# Try a pre-built layout
:layout load devops
```

**First time?** Press `F1` for help, or check out [CLAUDE.md](https://github.com/jcaldwell-labs/my-grid/blob/main/CLAUDE.md) for the complete reference.

## What's Next?

The roadmap includes:

- **Terminal recording playback zones** – Replay asciinema recordings in zones
- **Mouse support** – Click to focus zones
- **WebSocket zones** – Browser integration
- **Plugin system** – Custom zone types
- **Collaborative editing** – Network-synced canvases

## Why This Matters

We spend countless hours in terminals. Why not make that experience more intuitive, more spatial, more *human*?

my-grid isn't just another terminal multiplexer. It's a different way of thinking about terminal workflows. It's about **organizing information in space** rather than juggling windows.

Once you start thinking spatially, you can't go back to pane numbers.

---

## Try It Yourself

**Repository:** https://github.com/jcaldwell-labs/my-grid
**License:** MIT
**Requirements:** Python 3.8+, curses (included on Unix/Mac/WSL)

**Share your layouts!** If you build an interesting workspace, I'd love to see it. Tag `#mygrid` on Twitter or open a discussion on GitHub.

---

*Have thoughts on spatial interfaces? Found a clever use case? Drop a comment below or open an issue on GitHub. PRs welcome!*

**Star the project** if you found this interesting! ⭐

---

## Further Reading

- [The Humane Interface](https://en.wikipedia.org/wiki/The_Humane_Interface) – Jef Raskin's vision for spatial computing
- [Curses Programming](https://docs.python.org/3/howto/curses.html) – Python's terminal control library
- [tmux vs. spatial interfaces](https://github.com/jcaldwell-labs/my-grid/blob/main/CLAUDE.md) – Why coordinates beat pane numbers

---

*Published: 2025-12-20*
*Author: [Your Name]*
*Tags: #terminal #python #devops #vim #spatial-computing #cli*
