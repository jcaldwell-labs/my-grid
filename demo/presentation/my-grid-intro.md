---
title: my-grid - Terminal Productivity Canvas
author: ASCII Canvas Editor
patat:
  wrap: true
  margins:
    left: 5
    right: 5
  incrementalLists: true
  theme:
    codeBlock: [vividWhite, onRgb#282a36]
    code: [vividWhite, onRgb#282a36]
---

# my-grid

## Terminal-Based Productivity Canvas

---

# The Problem

💻 **Developers need diagrams**

- Architecture diagrams
- Flow charts
- Mind maps
- Sprint planning boards

🌐 **Current solutions require leaving the terminal**

- Miro, Lucidchart, Draw.io
- Context switching
- No version control integration
- Not keyboard-driven

---

# The Solution: my-grid

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Frontend   │──────>│     API      │──────>│   Database   │
└──────────────┘       └──────────────┘       └──────────────┘
        |                      |                      |
    React.js            Spring Boot              PostgreSQL
```

✨ **ASCII canvas editor with vim-style navigation**

- Infinite canvas
- Sparse storage (only stores non-empty cells)
- Multiple modes (NAV, PAN, EDIT, COMMAND)
- Bookmark system for quick navigation
- JSON project files (git-friendly!)

---

# Key Features

## 📐 Drawing Primitives

```bash
:rect 20 5        # Draw rectangle
:line 50 10       # Draw line to point
:text Hello!      # Write text
```

## 🔖 Bookmarks (vim-style)

```bash
m + a            # Set bookmark 'a' at cursor
' + a            # Jump to bookmark 'a'
:marks           # List all bookmarks
```

## 🗺️ Navigation

```bash
wasd / arrows    # Move cursor
WASD             # Fast move (10x)
p                # Pan mode (move viewport)
```

---

# Modes

| Mode | Key | Purpose |
|------|-----|---------|
| **NAV** | default | Navigate canvas |
| **PAN** | `p` | Pan viewport |
| **EDIT** | `i` | Type/draw |
| **COMMAND** | `:` | Execute commands |
| **MARK_SET** | `m` | Set bookmark |
| **MARK_JUMP** | `'` | Jump to mark |

Press `Esc` to exit any mode

---

# Use Cases

## 1. System Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │ HTTP │   Gateway   │ REST │  Services   │
│             │─────>│             │─────>│             │
└─────────────┘      └─────────────┘      └─────────────┘
```

**Set bookmarks at each service → jump between them instantly**

---

# Use Cases

## 2. Flow Charts

```
        ┌──────────┐
        │  Start   │
        └────┬─────┘
             │
        ┌────▼─────┐
     ┌──┤ Valid?   │──┐
     │  └──────────┘  │
    Yes              No
     │                │
┌────▼─────┐    ┌────▼─────┐
│ Process  │    │  Error   │
└──────────┘    └──────────┘
```

**Use grid overlay to align perfectly**

---

# Use Cases

## 3. Sprint Planning

```
TO DO              IN PROGRESS         DONE
─────────────      ────────────────    ─────────────
┌───────────┐      ┌───────────┐       ┌───────────┐
│ Feature A │      │ Feature B │       │ Feature C │
└───────────┘      └───────────┘       └───────────┘
┌───────────┐      ┌───────────┐       ┌───────────┐
│ Bug #123  │      │ Bug #456  │       │ Bug #789  │
└───────────┘      └───────────┘       └───────────┘
```

**Visual kanban board in your terminal**

---

# Installation

```bash
# Clone repository
git clone https://github.com/yourusername/my-grid.git
cd my-grid

# Install dependencies
pip install -r requirements.txt

# Run
python mygrid.py
```

---

# Quick Start

```bash
# Start with empty canvas
python mygrid.py

# Open existing project
python mygrid.py project.json

# Import text file
python mygrid.py diagram.txt
```

**First steps:**

1. Press `i` to enter EDIT mode → type some text
2. Press `Esc` → back to NAV mode
3. Press `:` → enter COMMAND mode
4. Type `rect 20 5` → draw a box
5. Type `w` → save project
6. Type `q` → quit

---

# File Format

## JSON Projects (git-friendly!)

```json
{
  "version": "1.0",
  "metadata": {
    "name": "architecture",
    "created": "2025-12-12T10:00:00Z"
  },
  "canvas": {
    "cells": [
      {"x": 0, "y": 0, "char": "A"},
      {"x": 1, "y": 0, "char": "P"}
    ]
  },
  "bookmarks": {
    "f": {"x": 10, "y": 20},
    "b": {"x": 50, "y": 100}
  }
}
```

**Perfect for:**
- Version control (git diff shows changes!)
- Team collaboration
- CI/CD documentation

---

# Export to Text

```bash
# Export current canvas
:export diagram.txt

# Include in documentation
cat diagram.txt >> README.md

# Or use directly in comments
/* Architecture Overview:

┌──────────┐      ┌──────────┐
│ Frontend │─────>│ Backend  │
└──────────┘      └──────────┘

*/
```

**Diagrams become living documentation**

---

# Advanced Features

## Grid Overlay

```bash
g          # Toggle major grid
G          # Toggle minor grid
0          # Toggle origin marker
:grid 10   # Set grid interval
```

## Coordinate System

```bash
:origin here        # Set origin at cursor
:origin 100 100     # Set origin at coordinates
:ydir up            # Y increases upward (math style)
:ydir down          # Y increases downward (screen style)
```

## Goto

```bash
:goto 50 25        # Jump to specific coordinates
```

---

# Demo

**Let's see it in action!**

Run the automated demo:

```bash
cd ~/projects/active/my-grid

# 10-second quick demo
python -c 'import sys; sys.path.insert(0, "src"); \
  from demo import run_demo; run_demo(10)'

# Full 75-second productivity demo
python -c 'import sys; sys.path.insert(0, "src"); \
  from demo import run_demo; run_demo(75)'
```

Or record with VHS:

```bash
vhs demo/my-grid-productivity-demo.tape
```

---

# Roadmap

## Planned Features

- **Colors and styling** (ANSI color support)
- **Shapes library** (diamonds, circles, clouds)
- **Templates** (common diagram patterns)
- **Collaborative mode** (real-time editing)
- **Export formats** (PNG, SVG, PDF)
- **Plugins** (custom drawing tools)

---

# Why my-grid?

✅ **Stay in the terminal** - No context switching

✅ **Keyboard-driven** - Fast navigation and editing

✅ **Git-friendly** - JSON format, perfect for version control

✅ **Infinite canvas** - Never run out of space

✅ **Lightweight** - Pure Python + curses

✅ **Portable** - Works anywhere with a terminal

✅ **No dependencies** - Just Python standard library

---

# Comparison

|  | my-grid | Miro | Lucidchart | ASCII Art |
|---|---------|------|------------|-----------|
| **Terminal** | ✅ | ❌ | ❌ | ✅ |
| **Vim keys** | ✅ | ❌ | ❌ | ❌ |
| **Git friendly** | ✅ | ❌ | ❌ | ✅ |
| **Bookmarks** | ✅ | ❌ | ❌ | ❌ |
| **Infinite canvas** | ✅ | ✅ | ❌ | ❌ |
| **Visual editing** | ✅ | ✅ | ✅ | ❌ |

---

# Get Started

```bash
# Repository
github.com/yourusername/my-grid

# Quick install
git clone https://github.com/yourusername/my-grid.git
cd my-grid
pip install -r requirements.txt

# Run
python mygrid.py

# Help
python mygrid.py --help
```

**Press F1 in the editor for full help**

---

# Thank You!

## Questions?

**my-grid** - Terminal-based productivity canvas

📧 Contact: your.email@example.com
🐙 GitHub: github.com/yourusername/my-grid
📺 Demo: (run VHS recording)

---

**To view this presentation:**

```bash
# Install patat
sudo apt install patat

# Run presentation
patat demo/presentation/my-grid-intro.md

# Controls:
# Space/Enter - Next slide
# Backspace    - Previous slide
# q            - Quit
```
