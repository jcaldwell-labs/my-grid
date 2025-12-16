# my-grid

An ASCII canvas editor with vim-style navigation for terminal-based diagramming.

## Features

- **Infinite canvas** - Sparse storage, unlimited space
- **Vim-style modes** - NAV, EDIT, PAN, COMMAND, MARK
- **Bookmarks** - Quick navigation with `m`/`'` + key
- **Zones** - Named regions with dynamic content (pipe, watch, PTY, FIFO, socket)
- **Layouts** - Save/load workspace configurations
- **Grid overlay** - Configurable major/minor grid lines
- **Project files** - JSON save/load, text export/import

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the editor
python mygrid.py

# Open existing file
python mygrid.py project.json
```

## Key Bindings

| Key | Action |
|-----|--------|
| `wasd` / arrows | Move cursor |
| `WASD` | Fast move (10x) |
| `i` | Enter edit mode |
| `p` | Toggle pan mode |
| `:` | Enter command mode |
| `m` + key | Set bookmark |
| `'` + key | Jump to bookmark |
| `Esc` | Exit current mode |
| `F1` | Help |

## Commands

| Command | Description |
|---------|-------------|
| `:w` | Save project |
| `:q` | Quit |
| `:goto X Y` | Move cursor |
| `:rect W H` | Draw rectangle |
| `:text MSG` | Write text |
| `:zone create NAME W H` | Create zone |
| `:layout load NAME` | Load layout |

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Full command reference and architecture
- **[demo/README.md](demo/README.md)** - Demo system for showcases

## License

MIT
