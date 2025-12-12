# my-grid Headless API Implementation Plan

## Goal

Enable external processes to send commands to a running my-grid instance in real-time, allowing:
- CLI piping: `echo ':text Hello' | mygrid-ctl`
- Stdout capture: `ls -la | mygrid-ctl box 10 5 80 20`
- Programmatic control: scripts/automation tools manipulating the canvas
- Cross-platform (Windows/WSL) communication

---

## Architecture Overview

```
┌─────────────────────────┐     ┌─────────────────────────────────────────┐
│   External Processes    │     │         my-grid Instance                │
│                         │     │                                         │
│  mygrid-ctl text "Hi"   │────>│  ┌─────────────┐   ┌────────────────┐  │
│  echo cmd > fifo        │     │  │ API Server  │──>│ Command Queue  │  │
│  curl localhost:8765    │     │  │ (threaded)  │   │ (thread-safe)  │  │
│                         │     │  └─────────────┘   └───────┬────────┘  │
└─────────────────────────┘     │                            │           │
                                │  ┌─────────────────────────v────────┐  │
                                │  │          Main Loop               │  │
                                │  │  1. Poll command queue           │  │
                                │  │  2. Execute external commands    │  │
                                │  │  3. Render frame                 │  │
                                │  │  4. Get keyboard input (timeout) │  │
                                │  │  5. Process input                │  │
                                │  └──────────────────────────────────┘  │
                                │                                         │
                                │  Canvas ← Viewport ← Renderer → Screen  │
                                └─────────────────────────────────────────┘
```

---

## Phase 1: Core Infrastructure

### 1.1 Command Queue Module (`src/command_queue.py`)

Thread-safe queue for external commands with optional response channel.

```python
@dataclass
class ExternalCommand:
    command: str                    # The command string (e.g., ":rect 10 5")
    response_queue: Queue | None    # Optional queue for response
    timestamp: float                # When command was received

class CommandQueue:
    def __init__(self, max_size: int = 1000)
    def put(self, cmd: str, response_queue: Queue = None) -> None
    def get_nowait(self) -> ExternalCommand | None
    def clear(self) -> None
    @property
    def pending_count(self) -> int
```

### 1.2 API Server Module (`src/server.py`)

Multi-protocol server running in background thread(s).

```python
class APIServer:
    def __init__(self, command_queue: CommandQueue)
    def start(self, config: ServerConfig) -> None
    def stop(self) -> None

    # Protocol handlers (each in own thread)
    def _tcp_listener(self, port: int) -> None
    def _fifo_listener(self, path: str) -> None  # Unix only
    def _named_pipe_listener(self, name: str) -> None  # Windows only

@dataclass
class ServerConfig:
    tcp_enabled: bool = True
    tcp_port: int = 8765
    tcp_host: str = "127.0.0.1"
    fifo_enabled: bool = True       # Auto-disabled on Windows
    fifo_path: str = "/tmp/mygrid.fifo"
    pipe_enabled: bool = True       # Windows named pipe
    pipe_name: str = r"\\.\pipe\mygrid"
```

### 1.3 Main Loop Modifications (`src/main.py`)

```python
class Application:
    def __init__(self, stdscr, server_config: ServerConfig = None):
        # ... existing init ...
        self.command_queue = CommandQueue()
        self.api_server = APIServer(self.command_queue)
        if server_config:
            self.api_server.start(server_config)

    def run(self) -> None:
        # Change to non-blocking input
        self.stdscr.timeout(50)  # 50ms = ~20 FPS max

        while running:
            # NEW: Process external commands first
            self._process_external_commands()

            # ... existing render/input/process ...

    def _process_external_commands(self) -> None:
        """Process up to N commands per frame to prevent flooding."""
        for _ in range(10):  # Max 10 commands per frame
            ext_cmd = self.command_queue.get_nowait()
            if not ext_cmd:
                break
            result = self._execute_command(ext_cmd.command)
            if ext_cmd.response_queue:
                ext_cmd.response_queue.put(result)
```

---

## Phase 2: Protocol Implementations

### 2.1 TCP Socket Protocol

**Port**: 8765 (configurable)
**Format**: Newline-delimited commands, JSON responses

```
# Request (one command per line)
:rect 10 5\n
:text Hello World\n

# Response (JSON)
{"status": "ok", "message": "Drew 10x5 rectangle"}
{"status": "ok", "message": "Wrote 11 characters"}
```

**Implementation**:
- Non-blocking accept with 1s timeout
- Read full message, split by newlines
- Execute each command, collect responses
- Return JSON array of results

### 2.2 Named FIFO (Unix/WSL)

**Path**: `/tmp/mygrid.fifo` (configurable)
**Format**: Newline-delimited commands (fire-and-forget)

```bash
# Send commands
echo ':rect 10 5' > /tmp/mygrid.fifo
echo ':text Hello' > /tmp/mygrid.fifo

# Pipe output
ls -la | while read line; do echo ":text $line" > /tmp/mygrid.fifo; done
```

**Implementation**:
- Create FIFO if not exists (`os.mkfifo`)
- Open in read mode (blocks until writer connects)
- Read lines, queue commands
- Re-open after EOF (writer disconnected)

### 2.3 Windows Named Pipe

**Name**: `\\.\pipe\mygrid` (configurable)
**Format**: Same as TCP

```powershell
# PowerShell example
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "mygrid", "Out")
$pipe.Connect()
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.WriteLine(":rect 10 5")
$writer.Flush()
```

**Implementation**:
- Use `win32pipe` or `pywin32` for Windows native pipes
- Fallback to TCP-only if pywin32 not available

---

## Phase 3: CLI Control Tool (`mygrid-ctl`)

Standalone CLI tool for sending commands to my-grid.

### 3.1 Basic Commands

```bash
mygrid-ctl [OPTIONS] COMMAND [ARGS...]

Options:
  --host HOST        TCP host (default: 127.0.0.1)
  --port PORT        TCP port (default: 8765)
  --fifo PATH        Use FIFO instead of TCP
  --pipe NAME        Use Windows named pipe
  --timeout SECS     Command timeout (default: 5)
  --json             Output responses as JSON

Commands:
  exec CMD           Execute any my-grid command
  text TEXT          Write text at cursor
  rect W H [CHAR]    Draw rectangle
  line X2 Y2 [CHAR]  Draw line to point
  goto X Y           Move cursor
  clear              Clear canvas
  save [FILE]        Save project
  status             Get current state (cursor, mode, cells)
```

### 3.2 Advanced Commands

```bash
# Pipe stdin into a region
mygrid-ctl box X Y W H      # Create box, pipe stdin as content
mygrid-ctl region X Y       # Pipe stdin starting at position

# Batch operations
mygrid-ctl batch FILE       # Execute commands from file
mygrid-ctl batch -          # Execute commands from stdin

# Examples
ls -la | mygrid-ctl box 0 0 80 25
git status | mygrid-ctl region 10 5
cat commands.txt | mygrid-ctl batch -
```

### 3.3 Implementation

Single Python file, minimal dependencies:

```python
#!/usr/bin/env python3
"""mygrid-ctl - Control a running my-grid instance."""

import argparse
import socket
import json
import sys

def send_tcp(host: str, port: int, commands: list[str]) -> list[dict]:
    """Send commands via TCP and return responses."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall('\n'.join(commands).encode() + b'\n')
        s.shutdown(socket.SHUT_WR)
        response = s.recv(65536).decode()
        return [json.loads(line) for line in response.strip().split('\n')]

def cmd_exec(args):
    """Execute arbitrary command."""
    return send_tcp(args.host, args.port, [args.command])

def cmd_box(args):
    """Create box and fill with stdin."""
    lines = sys.stdin.read().split('\n')
    commands = [
        f':goto {args.x} {args.y}',
        f':rect {args.width} {args.height}',
    ]
    for i, line in enumerate(lines[:args.height-2]):
        truncated = line[:args.width-2]
        commands.append(f':goto {args.x+1} {args.y+1+i}')
        commands.append(f':text {truncated}')
    return send_tcp(args.host, args.port, commands)

# ... more command handlers ...
```

---

## Phase 4: Extended Features

### 4.1 State Query Protocol

```bash
mygrid-ctl status
```

Response:
```json
{
  "cursor": {"x": 10, "y": 5},
  "viewport": {"x": 0, "y": 0, "width": 80, "height": 24},
  "mode": "NAV",
  "cells": 42,
  "dirty": true,
  "file": "diagram.json"
}
```

Requires new command in my-grid:
```python
def _cmd_status(self, args: list[str]) -> ModeResult:
    """Return current state as JSON."""
    state = {
        "cursor": {"x": self.viewport.cursor.x, "y": self.viewport.cursor.y},
        "viewport": {
            "x": self.viewport.x, "y": self.viewport.y,
            "width": self.viewport.width, "height": self.viewport.height
        },
        "mode": self.state_machine.mode_name,
        "cells": self.canvas.cell_count,
        "dirty": self.project.dirty,
        "file": self.project.filename
    }
    return ModeResult(message=json.dumps(state))
```

### 4.2 Event Streaming (Future)

WebSocket or long-poll for real-time updates:
```bash
mygrid-ctl watch --format=json
```

Output stream:
```json
{"event": "cell_changed", "x": 10, "y": 5, "char": "A"}
{"event": "cursor_moved", "x": 11, "y": 5}
{"event": "mode_changed", "mode": "EDIT"}
```

---

## Phase 5: Testing & Documentation

### 5.1 Test Files

```
tests/
├── test_command_queue.py    # Queue operations, thread safety
├── test_server.py           # Server start/stop, protocol handling
├── test_integration.py      # End-to-end with mygrid-ctl
└── test_mygrid_ctl.py       # CLI tool unit tests
```

### 5.2 Documentation Updates

- Update `CLAUDE.md` with API usage
- Create `docs/API.md` with protocol spec
- Add examples in `examples/` directory
- Update `--help` output

---

## Implementation Order

| Step | Component | Files | Dependencies |
|------|-----------|-------|--------------|
| 1 | Command Queue | `src/command_queue.py` | None |
| 2 | TCP Server | `src/server.py` | command_queue |
| 3 | Main Loop Integration | `src/main.py` | server, command_queue |
| 4 | Basic mygrid-ctl | `mygrid-ctl` | TCP protocol |
| 5 | Tests | `tests/test_*.py` | All above |
| 6 | FIFO Support | `src/server.py` | Step 2 |
| 7 | Windows Pipe | `src/server.py` | Step 2 |
| 8 | Box/Region Commands | `mygrid-ctl` | Step 4 |
| 9 | Status Query | `src/main.py`, `mygrid-ctl` | Step 3-4 |
| 10 | Documentation | `docs/`, `CLAUDE.md` | All |

---

## Configuration

### Command Line Arguments

```bash
python mygrid.py [OPTIONS] [FILE]

New Options:
  --server              Enable API server (default: disabled)
  --port PORT           TCP port (default: 8765)
  --no-tcp              Disable TCP listener
  --fifo PATH           FIFO path (Unix, default: /tmp/mygrid.fifo)
  --no-fifo             Disable FIFO listener
```

### Config File (~/.mygrid/config.json)

```json
{
  "server": {
    "enabled": true,
    "tcp_port": 8765,
    "tcp_host": "127.0.0.1",
    "fifo_path": "/tmp/mygrid.fifo"
  }
}
```

---

## Security Considerations

1. **Local Only**: TCP binds to 127.0.0.1 by default (no remote access)
2. **No Auth**: Suitable for single-user local dev (add token auth if needed later)
3. **Command Validation**: All commands go through existing command parser
4. **Rate Limiting**: Max 10 commands per frame prevents flooding
5. **FIFO Permissions**: Create with 0600 (owner only)

---

## Cross-Platform Notes

| Feature | Windows | Linux/WSL | macOS |
|---------|---------|-----------|-------|
| TCP Socket | Yes | Yes | Yes |
| Named FIFO | No | Yes | Yes |
| Named Pipe | Yes (pywin32) | No | No |
| mygrid-ctl | Yes | Yes | Yes |

WSL users can use TCP from Windows to connect to my-grid running in WSL:
```powershell
# From Windows PowerShell
Invoke-RestMethod -Uri "http://localhost:8765" -Method Post -Body ":text Hello from Windows"
```

---

## Success Criteria

- [ ] External process can send command, see result in running my-grid
- [ ] `echo ':rect 10 5' | mygrid-ctl` works
- [ ] `ls -la | mygrid-ctl box 0 0 80 25` renders ls output in a box
- [ ] Windows and WSL can communicate via TCP
- [ ] No performance degradation in interactive use
- [ ] All existing tests pass
- [ ] New tests for server/queue components

---

## Open Questions

1. **Default server state**: Should server be enabled by default, or require `--server` flag?
   - Recommend: Disabled by default, enable with flag or config

2. **Response format**: JSON only, or support plain text responses?
   - Recommend: JSON by default, plain text via flag

3. **pywin32 dependency**: Make Windows named pipe optional?
   - Recommend: Yes, fallback to TCP-only if not installed

4. **Batch atomicity**: Should batch commands be atomic (all-or-nothing)?
   - Recommend: No, execute sequentially, return individual results
