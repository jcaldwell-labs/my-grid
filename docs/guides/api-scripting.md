# API Scripting Guide

Control my-grid programmatically from Python, Bash, or any language that can open TCP sockets. The `--server` mode exposes the full command set for external automation.

---

## Quick Start

### 1. Start my-grid with Server Mode

```bash
python mygrid.py --server
```

This enables:

- **TCP socket** on port 8765 (configurable with `--port`)
- **Unix FIFO** at `/tmp/mygrid.fifo` (Linux/macOS/WSL)

### 2. Send Commands

**Python:**

```python
import socket

def send_command(cmd):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 8765))
    sock.sendall((cmd + '\n').encode())
    response = sock.recv(4096).decode()
    sock.close()
    return response

send_command(':goto 0 0')
send_command(':text Hello World')
```

**Bash:**

```bash
echo ':rect 10 5' | nc localhost 8765
```

**FIFO (fire-and-forget):**

```bash
echo ':text Quick note' > /tmp/mygrid.fifo
```

---

## Protocol Reference

### TCP Socket Interface

| Property     | Value                      |
| ------------ | -------------------------- |
| Default Port | 8765                       |
| Protocol     | TCP                        |
| Format       | Newline-delimited commands |
| Response     | JSON                       |

**Command Format:**

```
:command arg1 arg2\n
```

**Response Format:**

```json
{"status": "ok", "message": "Command executed"}
{"status": "error", "message": "Unknown command: xyz"}
```

### Unix FIFO Interface

| Property | Value                  |
| -------- | ---------------------- |
| Path     | `/tmp/mygrid.fifo`     |
| Mode     | Write-only             |
| Response | None (fire-and-forget) |

The FIFO is ideal for quick commands where you don't need confirmation:

```bash
echo ':goto 50 50' > /tmp/mygrid.fifo
echo ':text Marker' > /tmp/mygrid.fifo
```

### Command Line Options

```bash
python mygrid.py --server              # Enable API server
python mygrid.py --server --port 9000  # Custom port
python mygrid.py --server --no-fifo    # Disable FIFO (TCP only)
python mygrid.py --server --headless   # No display (CI/CD mode)
```

---

## Python Client Library

Here's a reusable client class for Python scripts:

```python
#!/usr/bin/env python3
"""my-grid API client library."""

import socket
import json
import time

class MyGridClient:
    """Client for my-grid API server."""

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port

    def send(self, command):
        """Send command and return response."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        try:
            sock.connect((self.host, self.port))
            sock.sendall((command + '\n').encode())
            response = sock.recv(4096).decode()
            sock.close()
            return json.loads(response) if response.startswith('{') else response
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def goto(self, x, y):
        """Move cursor to position."""
        return self.send(f':goto {x} {y}')

    def text(self, message):
        """Write text at cursor."""
        return self.send(f':text {message}')

    def rect(self, width, height, char='#'):
        """Draw rectangle at cursor."""
        return self.send(f':rect {width} {height} {char}')

    def clear(self):
        """Clear the canvas."""
        return self.send(':clear')

    def save(self, filepath=None):
        """Save project."""
        if filepath:
            return self.send(f':w {filepath}')
        return self.send(':w')

    def zone_create(self, name, x, y, width, height):
        """Create a static zone."""
        return self.send(f':zone create {name} {x} {y} {width} {height}')

    def zone_pipe(self, name, width, height, command):
        """Create a pipe zone."""
        return self.send(f':zone pipe {name} {width} {height} {command}')

    def zone_watch(self, name, width, height, interval, command):
        """Create a watch zone."""
        return self.send(f':zone watch {name} {width} {height} {interval} {command}')

# Usage
if __name__ == '__main__':
    client = MyGridClient()
    client.goto(0, 0)
    client.text('Hello from Python!')
    client.rect(20, 10)
```

---

## Common Patterns

### Pattern 1: Data Processing Pipeline

Load data, transform it, and display on canvas:

```python
import json
from mygrid_client import MyGridClient

client = MyGridClient()

# Load data
with open('servers.json') as f:
    servers = json.load(f)

# Display in grid
client.clear()
y = 0
for server in servers:
    status = '✓' if server['online'] else '✗'
    client.goto(0, y)
    client.text(f"{status} {server['name']:20} {server['ip']}")
    y += 1

client.save('server-status.json')
```

### Pattern 2: Loops and Iteration

Generate repetitive structures:

```python
client = MyGridClient()

# Create coordinate grid
for x in range(0, 100, 10):
    for y in range(0, 100, 10):
        client.goto(x, y)
        client.text('+')

# Draw grid lines
for x in range(0, 100, 10):
    client.send(f':line {x} 0 {x} 100 |')

for y in range(0, 100, 10):
    client.send(f':line 0 {y} 100 {y} -')
```

### Pattern 3: Conditional Formatting

Apply different formatting based on data:

```python
def status_marker(status):
    markers = {
        'healthy': ('✓', 'green'),
        'warning': ('!', 'yellow'),
        'error': ('✗', 'red'),
        'unknown': ('?', 'default')
    }
    return markers.get(status, markers['unknown'])

for i, service in enumerate(services):
    marker, color = status_marker(service['status'])
    client.send(f':color {color}')
    client.goto(0, i)
    client.text(f"{marker} {service['name']}")

client.send(':color off')  # Reset colors
```

### Pattern 4: Zone-Based Dashboards

Create monitoring dashboards with zones:

```python
client = MyGridClient()

# Clear and set up zones
client.clear()

# System metrics zone
client.send(':zone watch SYSTEM 40 10 5s top -b -n1 | head -10')

# Disk usage zone
client.send(':zone watch DISK 40 8 30s df -h')

# Git status zone
client.send(':zone watch GIT 50 15 10s git status --short')

# Log tail zone
client.send(':zone watch LOGS 80 20 2s tail -20 /var/log/syslog')

# Save layout
client.save('dashboard.json')
```

### Pattern 5: Template Population

Use templates to generate formatted output:

```python
from string import Template

report_template = Template("""
╔══════════════════════════════════════╗
║  $title
╠══════════════════════════════════════╣
║  Generated: $date
║  Author: $author
╠══════════════════════════════════════╣
║  Summary:
║  - Total items: $total
║  - Processed: $processed
║  - Errors: $errors
╚══════════════════════════════════════╝
""")

output = report_template.substitute(
    title='Daily Report',
    date='2025-01-04',
    author='Automation',
    total=150,
    processed=148,
    errors=2
)

for i, line in enumerate(output.strip().split('\n')):
    client.goto(0, i)
    client.text(line)
```

### Pattern 6: Batch Command Execution

Execute commands from a file:

```python
#!/usr/bin/env python3
"""Execute batch commands from file."""

import sys
from mygrid_client import MyGridClient

def run_batch(filename):
    client = MyGridClient()

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                print(f'> {line}')
                response = client.send(line)
                print(f'  {response}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: batch_commands.py <command-file>')
        sys.exit(1)
    run_batch(sys.argv[1])
```

**Example command file (`setup.txt`):**

```
# Clear and set up workspace
:clear
:goto 0 0
:text Project Dashboard
:goto 0 2
:rect 80 20
:zone watch STATUS 75 15 10s ./check-status.sh
```

---

## Bash Scripting

### Simple Command Sender

```bash
#!/bin/bash
# mygrid-send - Send command to my-grid

PORT=${MYGRID_PORT:-8765}
HOST=${MYGRID_HOST:-localhost}

if [ -z "$1" ]; then
    echo "Usage: mygrid-send '<command>'"
    exit 1
fi

echo "$1" | nc -q0 "$HOST" "$PORT"
```

### Pipe Input to Canvas

```bash
#!/bin/bash
# mygrid-pipe - Pipe stdin to canvas region

X=${1:-0}
Y=${2:-0}
PORT=${MYGRID_PORT:-8765}

echo ":goto $X $Y" | nc -q0 localhost $PORT

while IFS= read -r line; do
    echo ":text $line" | nc -q0 localhost $PORT
    ((Y++))
    echo ":goto $X $Y" | nc -q0 localhost $PORT
done
```

**Usage:**

```bash
ls -la | ./mygrid-pipe 10 5
git log --oneline -10 | ./mygrid-pipe 0 0
```

### FIFO Helper

```bash
#!/bin/bash
# mygrid-fifo - Send commands via FIFO (faster, no response)

FIFO="/tmp/mygrid.fifo"

if [ ! -p "$FIFO" ]; then
    echo "Error: my-grid FIFO not available. Start with --server"
    exit 1
fi

if [ -z "$1" ]; then
    # Read from stdin
    while IFS= read -r line; do
        echo "$line" > "$FIFO"
    done
else
    echo "$1" > "$FIFO"
fi
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Update Architecture Diagram

on:
  push:
    paths:
      - "docs/architecture/**"

jobs:
  update-diagram:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate diagram
        run: |
          python mygrid.py --server --headless &
          MYGRID_PID=$!
          sleep 2

          python scripts/generate_architecture.py
          echo ':w docs/architecture.json' | nc localhost 8765

          kill $MYGRID_PID

      - name: Commit changes
        run: |
          git config user.name 'GitHub Actions'
          git config user.email 'actions@github.com'
          git add docs/architecture.json
          git diff --staged --quiet || git commit -m 'Update architecture diagram'
          git push
```

### Local Automation Script

```bash
#!/bin/bash
# update_diagram.sh - Update and save diagram

set -e

# Start headless my-grid
python mygrid.py diagram.json --server --headless &
MYGRID_PID=$!
trap "kill $MYGRID_PID 2>/dev/null" EXIT

sleep 2

# Run update script
python scripts/update_components.py

# Save
echo ':w' | nc -q1 localhost 8765

echo "Diagram updated successfully"
```

---

## Error Handling

### Python Error Handling

```python
import socket
import json

class MyGridError(Exception):
    """my-grid API error."""
    pass

def send_command(cmd, timeout=5.0):
    """Send command with error handling."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        sock.connect(('localhost', 8765))
    except ConnectionRefusedError:
        raise MyGridError('Cannot connect - is my-grid running with --server?')
    except socket.timeout:
        raise MyGridError('Connection timed out')

    try:
        sock.sendall((cmd + '\n').encode())
        response = sock.recv(4096).decode()
    except socket.timeout:
        raise MyGridError(f'Command timed out: {cmd}')
    finally:
        sock.close()

    # Parse response
    try:
        data = json.loads(response)
        if data.get('status') == 'error':
            raise MyGridError(data.get('message', 'Unknown error'))
        return data
    except json.JSONDecodeError:
        return response  # Plain text response
```

### Retry Logic

```python
import time

def send_with_retry(cmd, max_retries=3, delay=1.0):
    """Send command with automatic retry."""
    for attempt in range(max_retries):
        try:
            return send_command(cmd)
        except MyGridError as e:
            if attempt < max_retries - 1:
                print(f'Retry {attempt + 1}/{max_retries}: {e}')
                time.sleep(delay)
            else:
                raise
```

---

## Best Practices

### 1. Connection Management

For scripts sending many commands, consider connection pooling:

```python
class MyGridSession:
    """Persistent connection for batch operations."""

    def __init__(self, host='localhost', port=8765):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def send(self, cmd):
        self.sock.sendall((cmd + '\n').encode())
        return self.sock.recv(4096).decode()

    def close(self):
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

# Usage
with MyGridSession() as session:
    for i in range(100):
        session.send(f':goto 0 {i}')
        session.send(f':text Line {i}')
```

### 2. Rate Limiting

Add small delays for visual operations:

```python
import time

def animate_text(client, text, x, y, delay=0.05):
    """Type text with animation effect."""
    for i, char in enumerate(text):
        client.goto(x + i, y)
        client.text(char)
        time.sleep(delay)
```

### 3. Coordinate Planning

Plan your canvas layout before scripting:

```python
# Define layout constants
HEADER_Y = 0
CONTENT_Y = 3
SIDEBAR_X = 60
ZONE_WIDTH = 50
ZONE_HEIGHT = 15

# Use consistently
client.goto(0, HEADER_Y)
client.text('=== Dashboard ===')

client.goto(0, CONTENT_Y)
client.zone_create('MAIN', 0, CONTENT_Y, ZONE_WIDTH, ZONE_HEIGHT)

client.goto(SIDEBAR_X, CONTENT_Y)
client.zone_create('SIDEBAR', SIDEBAR_X, CONTENT_Y, 30, ZONE_HEIGHT)
```

### 4. Use Zones for Dynamic Content

Prefer zones over manual refresh loops:

```python
# Good: Let my-grid handle refresh
client.send(':zone watch LOGS 80 20 2s tail -20 app.log')

# Avoid: Manual refresh loop
# while True:
#     output = subprocess.check_output(['tail', '-20', 'app.log'])
#     # Send each line...
#     time.sleep(2)
```

---

## Troubleshooting

### Connection Refused

```
Error: Cannot connect - is my-grid running with --server?
```

**Solution:** Start my-grid with `--server` flag:

```bash
python mygrid.py --server
```

### Port Already in Use

```
Error: Address already in use
```

**Solution:** Use a different port:

```bash
python mygrid.py --server --port 9000
```

Update your client:

```python
client = MyGridClient(port=9000)
```

### FIFO Not Available

```
Error: my-grid FIFO not available
```

**Solutions:**

1. Ensure my-grid is running with `--server`
2. Check the FIFO exists: `ls -la /tmp/mygrid.fifo`
3. FIFO is not available on Windows (use TCP instead)

### Commands Not Executing

Ensure commands are newline-terminated:

```python
# Correct
sock.sendall((cmd + '\n').encode())

# Wrong - missing newline
sock.sendall(cmd.encode())
```

---

## See Also

- [Zones Reference](zones-reference.md) - Complete zone command reference
- [CLAUDE.md](../../CLAUDE.md) - Full command reference
- [mygrid-ctl](../../mygrid-ctl.py) - Command-line control utility
- [Example Scripts](../../scripts/) - Ready-to-use automation scripts

---

**[Back to Documentation Index](../README.md)**
