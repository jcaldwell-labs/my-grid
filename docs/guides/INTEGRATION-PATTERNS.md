# my-grid Integration Patterns

## Overview

my-grid can integrate with development tools in several ways. The key insight is that my-grid's TCP API (`--server` on port 8765) allows bidirectional communication regardless of which tool is "outer" vs "inner".

---

## Pattern A: my-grid as Outer Shell

```
┌─────────────────────────────────────────────────────┐
│ my-grid                                             │
│  ┌───────────────────────────────────────────────┐  │
│  │ PTY Zone: claude / vim / nvim                 │  │
│  │                                               │  │
│  │  Your editor/CC runs inside a PTY zone        │  │
│  │                                               │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [CONTEXT]  [GIT]  [NOTES]  ... other zones        │
└─────────────────────────────────────────────────────┘
```

**How to use:**
```bash
# Start my-grid
cd ~/jcaldwell-labs/my-grid
python mygrid.py --server

# Load the claude-dev layout
:layout load claude-dev

# Jump to CLAUDE zone and start CC
'c
# Press Enter to focus PTY
claude
```

**Pros:**
- Full spatial navigation around your editor
- Watch zones update while you work
- Notes/scratch areas persist
- Jump out to check things, jump back

**Cons:**
- PTY zones have some limitations vs raw terminal
- Key capture can be tricky (Esc conflicts)

---

## Pattern B: my-grid as Background Service

```
┌─────────────────────────────────────────────────────┐
│ Terminal (tmux pane 1)                              │
│  $ claude                                           │
│  > Working on feature...                            │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Terminal (tmux pane 2)                              │
│  $ python mygrid.py --server                        │
│  (my-grid running, receiving commands)              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**How to use:**
```bash
# In one tmux pane / terminal
cd ~/jcaldwell-labs/my-grid
python mygrid.py --server

# In another pane - your main work
claude

# CC or scripts can send commands:
echo ':text Working on auth feature' | nc -q0 localhost 8765
echo ':zone refresh CONTEXT' | nc -q0 localhost 8765
```

**Pros:**
- Full terminal for your editor (no PTY limitations)
- my-grid becomes a live dashboard/scratchpad
- Easy to script interactions

**Cons:**
- Need to switch panes to see my-grid
- Two windows to manage

---

## Pattern C: my-grid as Headless Recorder

```
┌─────────────────────────────────────────────────────┐
│ Terminal                                            │
│  $ claude                                           │
│                                                     │
│  (git hooks send events to my-grid in background)  │
│  (my-grid records everything to canvas file)       │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         │ post-commit hook: echo ':text commit...' | nc ...
         ▼
┌─────────────────────────────────────────────────────┐
│ my-grid (headless, --server only)                   │
│  - Receives commands via TCP                        │
│  - Writes to canvas file                            │
│  - Can be opened later to review session            │
└─────────────────────────────────────────────────────┘
```

**How to use:**
```bash
# Start headless (need to implement this mode)
# For now, run in a background terminal
python mygrid.py --server &

# Work normally - hooks capture events
claude

# Later, open my-grid to see the session timeline
python mygrid.py session-2026-01-29.json
```

---

## Pattern D: Inside Vim/Neovim

```vim
" In vim, open a terminal split running my-grid
:terminal python ~/jcaldwell-labs/my-grid/mygrid.py --server

" Or use vim's job system to run it background
:call job_start(['python', 'mygrid.py', '--server'])

" Send commands from vim
:!echo ':text editing %' | nc -q0 localhost 8765
```

**Neovim Lua integration:**
```lua
-- Send current file to my-grid
vim.keymap.set('n', '<leader>mg', function()
  local file = vim.fn.expand('%')
  os.execute('echo ":text editing ' .. file .. '" | nc -q0 localhost 8765')
end)
```

---

## Pattern E: Socket Zone for Bidirectional

my-grid can create a SOCKET zone that *listens* for input:

```bash
# In my-grid
:zone socket CLAUDE-IN 80 30 9999

# From CC or scripts, send output TO the zone
echo "Claude response here..." | nc localhost 9999
```

This creates a dedicated area for CC output while my-grid runs.

---

## Recommended Setup for jcaldwell-labs

For your workflow, I recommend **Pattern B** (background service) with hooks:

1. **tmux** with two panes:
   - Pane 1: my-grid with `jcaldwell-dev` layout
   - Pane 2: Your main terminal for CC/vim

2. **Git hooks** (already installed) capture commits/checkouts

3. **Keybind** in your shell to quick-capture notes:
   ```bash
   # Add to ~/.bashrc
   mgnote() { echo ":goto 300 0" | nc -q0 localhost 8765; echo ":text $*" | nc -q0 localhost 8765; }
   ```

4. **CC integration** via socket zone for responses (optional)

---

## Files

Layouts created:
- `~/.config/mygrid/layouts/jcaldwell-cicd.yaml` - Dashboard focused
- `~/.config/mygrid/layouts/jcaldwell-dev.yaml` - Full spatial workspace  
- `~/.config/mygrid/layouts/claude-dev.yaml` - CC integration focused

Load with:
```bash
echo ':layout load jcaldwell-dev' | nc -q0 localhost 8765
# or interactively: :layout load jcaldwell-dev
```
