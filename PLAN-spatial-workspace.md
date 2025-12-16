# my-grid Spatial Workspace Vision

## Overview

Transform my-grid from an ASCII canvas editor into a **spatial computing interface** where the infinite canvas becomes a persistent workspace - a "spatial filesystem" metaphor rather than the Desktop metaphor.

Inspired by Jef Raskin's *The Humane Interface*:
- Spatial memory: Users remember *where* things are, not how to navigate hierarchies
- Reduced modality: Actions available from anywhere
- Persistence: The workspace persists across sessions
- Zooming: Navigate by moving through space, not clicking through folders

## Core Concept: The Map as Interface

```
┌────────────────────────────────────────────────────────────────────────────┐
│  INFINITE SPATIAL WORKSPACE                                                │
│                                                                            │
│  ┌─[c]──────────┐    ┌─[t]──────────────┐    ┌─[l]──────────┐            │
│  │ CLAUDE       │    │ TERMINAL         │    │ LOGS         │            │
│  │              │    │ $ _              │    │              │            │
│  │ AI assistant │    │                  │    │ tail -f      │            │
│  │ responses    │    │ (live PTY)       │    │ system.log   │            │
│  └──────────────┘    └──────────────────┘    └──────────────┘            │
│                                                                            │
│  ┌─[s]──────────┐    ┌─[w]──────────────┐    ┌─[n]──────────┐            │
│  │ SCRATCH      │    │ WORKSPACE        │    │ NOTES        │            │
│  │              │    │                  │    │              │            │
│  │ temp work    │    │ current project  │    │ persistent   │            │
│  │              │    │ code/docs here   │    │ reference    │            │
│  └──────────────┘    └──────────────────┘    └──────────────┘            │
│                                                                            │
│  Navigate: 'bookmark to jump │ joystick/wasd to pan │ :zone list         │
└────────────────────────────────────────────────────────────────────────────┘
```

## Architecture

### Phase 1: Zone Types & Connectors (Foundation)

Extend the existing Zone system with typed zones:

```python
class ZoneType(Enum):
    STATIC = "static"       # Plain text region (current behavior)
    PIPE = "pipe"           # One-shot command output (:pipe zone ls -la)
    WATCH = "watch"         # Periodic refresh (:watch zone 5s "date")
    PTY = "pty"             # Live terminal session
    FIFO = "fifo"           # Read from named pipe, display in zone
    SOCKET = "socket"       # Listen on port, display incoming data
    CLIPBOARD = "clipboard" # Yank/paste buffer region
```

**Zone Configuration:**
```python
@dataclass
class ZoneConfig:
    zone_type: ZoneType = ZoneType.STATIC

    # For PIPE/WATCH
    command: str | None = None
    refresh_interval: float | None = None  # seconds, for WATCH

    # For PTY
    shell: str = "/bin/bash"

    # For FIFO/SOCKET
    path: str | None = None  # FIFO path or "host:port"

    # Display options
    scroll: bool = True      # Auto-scroll to bottom
    wrap: bool = False       # Wrap long lines
    max_lines: int = 1000    # Buffer limit
```

### Phase 2: Zone Commands

```
:zone create NAME W H [type]     Create zone at cursor
:zone delete NAME                Delete zone
:zone list                       List all zones
:zone goto NAME                  Jump to zone
:zone resize NAME W H            Resize zone
:zone bind NAME KEY              Bind bookmark to zone

# Typed zone creation
:zone pipe NAME W H COMMAND      Create pipe zone (one-shot)
:zone watch NAME W H INTERVAL CMD  Create watch zone (periodic)
:zone pty NAME W H [SHELL]       Create live terminal zone
:zone fifo NAME W H PATH         Create FIFO listener zone
:zone socket NAME W H PORT       Create socket listener zone

# Zone interaction
:zone send NAME TEXT             Send input to PTY zone
:zone refresh NAME               Manually refresh pipe/watch zone
:zone pause NAME                 Pause watch/pty zone
:zone resume NAME                Resume paused zone
```

### Phase 3: Live Terminal (PTY) Zones

The most powerful feature - embed a live shell in a zone:

```python
class PTYZone:
    """A zone connected to a pseudo-terminal."""

    def __init__(self, zone: Zone, shell: str = "/bin/bash"):
        self.zone = zone
        self.master_fd, self.slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            [shell],
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            preexec_fn=os.setsid
        )
        self.output_buffer = deque(maxlen=1000)
        self._reader_thread = Thread(target=self._read_output, daemon=True)
        self._reader_thread.start()

    def send_input(self, text: str):
        """Send keystrokes to the terminal."""
        os.write(self.master_fd, text.encode())

    def _read_output(self):
        """Background thread reading terminal output."""
        while self.process.poll() is None:
            data = os.read(self.master_fd, 1024)
            # Parse ANSI, update buffer, signal canvas update
```

**PTY Zone Interaction:**
- Navigate to zone, press `Enter` to "focus" the PTY
- While focused, keystrokes go to the PTY
- Press `Escape` to unfocus, return to canvas navigation
- Zone content updates in real-time as the shell outputs

### Phase 4: Zone Layout & Templates

Pre-defined workspace layouts:

```yaml
# ~/.config/mygrid/layouts/devops.yaml
name: DevOps Workspace
zones:
  - name: LOGS
    type: watch
    x: 0
    y: 0
    width: 80
    height: 20
    command: "journalctl -f -n 20"
    bookmark: "l"

  - name: TERMINAL
    type: pty
    x: 85
    y: 0
    width: 80
    height: 24
    bookmark: "t"

  - name: SERVICES
    type: watch
    x: 0
    y: 25
    width: 80
    height: 10
    command: "systemctl status nginx mysql redis --no-pager"
    interval: 10
    bookmark: "s"
```

```
:layout load devops       Load a layout
:layout save myworkspace  Save current layout
:layout list              List available layouts
```

### Phase 5: Connectors & Integration

**Claude Code Integration:**
- Zone that receives Claude Code output
- Could connect via the existing API server
- AI responses render to a designated zone

**Clipboard Integration:**
```
:yank                     Yank selected region to clipboard zone
:paste                    Paste from clipboard zone at cursor
:yank zone ZONENAME       Copy entire zone content
```

**File Sync:**
```
:zone sync NAME FILE      Two-way sync zone ↔ file
:zone import NAME FILE    One-time import file to zone
:zone export NAME FILE    Export zone content to file
```

## Implementation Phases

### Sprint 1: Zone Type Foundation
- [ ] Add `ZoneType` enum and `ZoneConfig` to zones.py
- [ ] Implement PIPE zone (one-shot command output)
- [ ] Add zone rendering in renderer (show borders, type indicators)
- [ ] Commands: `:zone pipe`, `:zone refresh`

### Sprint 2: Watch Zones
- [ ] Implement periodic refresh for WATCH zones
- [ ] Background thread for interval-based updates
- [ ] Commands: `:zone watch`, `:zone pause`, `:zone resume`

### Sprint 3: PTY Zones (Core)
- [ ] PTY creation and management
- [ ] Output buffering and ANSI parsing (basic)
- [ ] Focus/unfocus mechanism
- [ ] Keyboard forwarding when focused
- [ ] Commands: `:zone pty`, `:zone send`

### Sprint 4: Layout System
- [ ] YAML layout file format
- [ ] Save/load layouts
- [ ] Default layouts for common use cases
- [ ] Commands: `:layout load/save/list`

### Sprint 5: Integration & Polish
- [ ] FIFO/Socket zones for external integration
- [ ] Clipboard zone with yank/paste
- [ ] Zone navigation improvements (tab between zones?)
- [ ] Status bar showing focused zone

## GitHub Issues to Create

1. **Zone Types Foundation** - Add ZoneType enum and ZoneConfig
2. **Pipe Zones** - One-shot command output to zones
3. **Watch Zones** - Periodic refresh zones
4. **PTY Zones** - Live terminal embedding
5. **Zone Rendering** - Visual indicators for zone types
6. **Layout System** - Save/load workspace configurations
7. **Clipboard Zone** - Yank/paste region management
8. **External Connectors** - FIFO/Socket zone types
9. **Claude Integration** - AI response zone connector

## Open Questions

1. **ANSI Handling**: How much ANSI escape sequence support for PTY zones?
   - Minimal (strip all ANSI)?
   - Basic (colors only)?
   - Full (cursor positioning, clear screen)?

2. **Focus Model**: How do users "enter" a PTY zone?
   - Navigate cursor into zone + Enter?
   - `:zone focus NAME`?
   - Joystick button?

3. **Zone Overlap**: Allow zones to overlap?
   - Probably no - enforce non-overlapping
   - Could have z-order for layering?

4. **Persistence**: Auto-save zone state?
   - PTY zones can't persist (process state)
   - Watch/Pipe zones could cache last output

5. **Resource Limits**: Max PTY zones? Max refresh rate?
   - Prevent runaway resource consumption
   - Maybe 4-8 PTY zones max?
