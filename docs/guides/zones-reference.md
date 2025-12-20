# Zones and FIFO Pipes Reference

## Table of Contents
1. [What are Zones?](#what-are-zones)
2. [Zone Types](#zone-types)
3. [FIFO Zones Deep Dive](#fifo-zones-deep-dive)
4. [Socket Zones](#socket-zones)
5. [Watch Zones](#watch-zones)
6. [PTY Zones](#pty-zones)
7. [Command Reference](#command-reference)
8. [Use Cases](#use-cases)
9. [Layouts](#layouts)

---

## What are Zones?

Zones are **named rectangular regions** on the infinite canvas that act as "windows" or "panels" in your workspace. Instead of switching between tabs or application windows, you **navigate spatially** to different zones on a 2D canvas.

### The Spatial Philosophy

This design is inspired by **Jef Raskin's "The Humane Interface"** - the concept of a spatial document where you move through information rather than opening/closing windows. Benefits include:

- **Spatial memory**: Your brain remembers where things are
- **No context switching**: Everything stays in place
- **Infinite workspace**: Canvas has no size limits
- **Quick navigation**: Bookmarks let you jump instantly

### Zone Anatomy

```
+--- ZONE_NAME [T] ---------------+
|                                 |
|   Content area                  |
|   (filled by zone type)         |
|                                 |
+---------------------------------+
```

- **Name**: Unique identifier (case-insensitive)
- **Type indicator**: `[W]` watch, `[P]` pipe, `[T]` PTY, etc.
- **Content area**: Automatically updated based on zone type
- **Bookmark**: Optional single-key shortcut (a-z, 0-9)

---

## Zone Types

### Overview

| Type | Symbol | Purpose | Update Method | Unix Only |
|------|--------|---------|---------------|-----------|
| **STATIC** | `[S]` | Plain text notes | Manual editing | No |
| **PIPE** | `[P]` | Command output (one-shot) | Run once | No |
| **WATCH** | `[W]` | Refreshing command | Auto-refresh (timer) | No |
| **PTY** | `[T]` | Live terminal | Interactive shell | Yes |
| **FIFO** | `[F]` | Named pipe listener | External writes | Yes |
| **SOCKET** | `[N]` | TCP port listener | Network connections | No |
| **CLIPBOARD** | `[C]` | Copy/paste buffer | Yank/paste ops | No |

### STATIC Zones

Plain text areas you edit manually. Good for:
- Notes and documentation
- Task lists
- Reference information

```bash
:zone create NOTES 0 0 50 20
# Then navigate and type normally in EDIT mode
```

### PIPE Zones

Execute a command **once** and display the output.

```bash
:zone pipe TREE 60 20 tree -L 2
:zone refresh TREE  # Re-run command
```

Good for:
- Directory listings
- One-time reports
- Configuration dumps

### WATCH Zones

Execute a command **periodically** and update the display.

```bash
# Refresh every 5 seconds
:zone watch CPU 40 10 5s uptime

# Refresh every 30 seconds
:zone watch DISK 50 12 30s df -h
```

Good for:
- System monitoring (CPU, memory, disk)
- Log tailing
- Process watching
- Git status

**Commands:**
- `:zone pause ZONENAME` - Stop refreshing
- `:zone resume ZONENAME` - Resume refreshing
- `:zone refresh ZONENAME` - Manual refresh now

---

## FIFO Zones Deep Dive

FIFO (First In, First Out) zones use **Unix named pipes** to receive data from external processes in real-time.

### How FIFO Zones Work

1. **my-grid creates the named pipe** (FIFO file in filesystem)
2. **my-grid opens pipe for reading** and waits
3. **External processes open pipe for writing** and send data
4. **Data appears live** in the zone on the canvas

### Creating a FIFO Zone

```bash
:zone fifo EVENTS 60 20 /tmp/mygrid-events.fifo
```

This creates:
- A zone named EVENTS (60x20 characters)
- A named pipe at `/tmp/mygrid-events.fifo`
- A background thread listening on the pipe

### Sending Data to FIFO Zones

From any terminal or script:

```bash
# Simple message
echo "Build started at $(date)" > /tmp/mygrid-events.fifo

# Stream logs
tail -f /var/log/app.log > /tmp/mygrid-events.fifo

# From a script
while true; do
  echo "[$(date +%T)] Status: OK" > /tmp/mygrid-events.fifo
  sleep 5
done

# Pipe command output
make all 2>&1 | while read line; do
  echo "$line" > /tmp/mygrid-events.fifo
done
```

### FIFO Zone Characteristics

**Blocking writes**: Writers block until my-grid reads the data
**Non-blocking reads**: my-grid doesn't block waiting for data
**Auto-scroll**: New lines appear at bottom (configurable)
**Buffer limit**: Default 1000 lines (configurable)
**Line buffering**: Best to send line-by-line for predictable display

### Real-World FIFO Examples

#### Build Monitor

```bash
# Create zone
:zone fifo BUILD 70 25 /tmp/build.fifo

# Build script (build.sh):
#!/bin/bash
FIFO=/tmp/build.fifo

echo "=== Build started at $(date) ===" > $FIFO
make clean 2>&1 | while read line; do echo "$line" > $FIFO; done
make all 2>&1 | while read line; do echo "$line" > $FIFO; done
echo "=== Build complete at $(date) ===" > $FIFO
```

#### Test Runner Integration

```bash
# Create zone
:zone fifo TESTS 60 20 /tmp/tests.fifo

# Test script:
#!/bin/bash
pytest -v tests/ 2>&1 | while read line; do
  echo "$line" > /tmp/tests.fifo
done
```

#### Deployment Status

```bash
# Create zone
:zone fifo DEPLOY 80 30 /tmp/deploy.fifo

# Deploy script:
echo "Starting deployment to production..." > /tmp/deploy.fifo
kubectl apply -f deployment.yaml 2>&1 > /tmp/deploy.fifo
echo "Deployment complete!" > /tmp/deploy.fifo
```

#### Multi-Process Dashboard

```bash
# Create multiple FIFO zones
:zone fifo WEB_LOGS 60 15 /tmp/web.fifo
:zone fifo API_LOGS 60 15 /tmp/api.fifo
:zone fifo DB_LOGS 60 15 /tmp/db.fifo

# Feed logs from different services:
tail -f /var/log/web.log > /tmp/web.fifo &
tail -f /var/log/api.log > /tmp/api.fifo &
tail -f /var/log/db.log > /tmp/db.fifo &
```

### FIFO Zone Caveats

- **Unix/WSL only**: Named pipes don't work on native Windows
- **Cleanup**: Remove FIFO files manually if needed: `rm /tmp/*.fifo`
- **Permission**: Ensure my-grid can create files in target directory
- **Path collisions**: Use unique paths for each zone
- **Blocking**: Don't send data faster than my-grid can display

---

## Socket Zones

Socket zones listen on **TCP network ports** for incoming data. Unlike FIFO zones, they work on all platforms including Windows.

### Creating a Socket Zone

```bash
:zone socket MESSAGES 60 20 9999
```

This:
- Creates a zone named MESSAGES (60x20 characters)
- Opens TCP port 9999
- Accepts connections from any source
- Displays received data line-by-line

### Sending Data to Socket Zones

#### Using netcat (nc)

```bash
# Single message
echo "Status update" | nc localhost 9999

# Multiple messages
echo -e "Line 1\nLine 2\nLine 3" | nc localhost 9999

# Stream data
tail -f /var/log/app.log | nc localhost 9999
```

#### Using telnet

```bash
telnet localhost 9999
# Then type messages and press Enter
```

#### From Python

```python
import socket

def send_to_mygrid(message, port=9999):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', port))
    s.sendall(f"{message}\n".encode())
    s.close()

send_to_mygrid("Alert: CPU usage high")
send_to_mygrid("Deployment completed successfully")
```

#### From Bash Script

```bash
#!/bin/bash
PORT=9999
HOST=localhost

send_message() {
  echo "$1" | nc -N $HOST $PORT
}

send_message "Build started"
make all && send_message "Build success" || send_message "Build failed"
```

### Socket Zone Use Cases

- **Cross-machine monitoring**: Send updates from remote servers
- **Webhook receiver**: Accept HTTP POST data (with parsing)
- **Chat/notifications**: Real-time message delivery
- **CI/CD integration**: Build/deploy status updates
- **Microservices dashboard**: Service health checks
- **WSL + Windows integration**: Windows apps → WSL my-grid

### Windows + WSL Integration

Socket zones enable seamless Windows ↔ WSL communication:

```powershell
# From Windows PowerShell, send to my-grid in WSL
$client = New-Object System.Net.Sockets.TcpClient("localhost", 9999)
$stream = $client.GetStream()
$writer = New-Object System.IO.StreamWriter($stream)
$writer.WriteLine("Message from Windows!")
$writer.Flush()
$client.Close()
```

---

## Watch Zones

Watch zones automatically refresh command output at regular intervals.

### Creating Watch Zones

```bash
# Refresh every 5 seconds (default)
:zone watch STATUS 50 10 5s uptime

# Refresh every 30 seconds
:zone watch DISK 50 8 30s df -h

# Refresh every minute
:zone watch LOGS 70 20 60s tail -20 /var/log/app.log
```

### Interval Formats

- `5s` - 5 seconds
- `30s` - 30 seconds
- `1m` - 1 minute
- `5m` - 5 minutes
- `5` - Also 5 seconds (default unit)

### Watch Zone Commands

```bash
:zone pause ZONENAME    # Stop auto-refresh
:zone resume ZONENAME   # Resume auto-refresh
:zone refresh ZONENAME  # Refresh immediately (manual)
```

### Common Watch Zone Examples

```bash
# System monitoring
:zone watch CPU 40 8 5s uptime
:zone watch MEMORY 40 8 5s free -h | head -3
:zone watch DISK 50 10 30s df -h | grep -E '^/dev'
:zone watch NET 50 10 10s ss -tuln | head -10

# Process monitoring
:zone watch PROCESSES 60 15 5s ps aux --sort=-%cpu | head -10

# Git status
:zone watch GIT 50 12 5s git status --short

# File watching
:zone watch FILES 50 15 10s ls -lht | head -10

# Docker
:zone watch CONTAINERS 70 15 10s docker ps --format 'table {{.Names}}\t{{.Status}}'

# Kubernetes
:zone watch PODS 80 20 15s kubectl get pods
```

---

## PTY Zones

PTY (Pseudo-Terminal) zones provide **live interactive terminals** within your canvas. Unix/WSL only.

### Creating PTY Zones

```bash
# Default shell (bash)
:zone pty TERMINAL 80 24

# Specific shell
:zone pty PYTHON 60 20 /usr/bin/python3
:zone pty ZSH 80 24 /bin/zsh

# Custom command
:zone pty TOP 70 30 /usr/bin/htop
```

### Using PTY Zones

1. **Navigate** cursor into the PTY zone
2. **Press Enter** to focus (captures keyboard)
3. **Type normally** - keys go directly to shell
4. **Press Escape** to unfocus (return to canvas navigation)

### Sending Commands to PTY

```bash
# Send text with newline to execute
:zone send TERMINAL ls -la\n

# Send without newline (type but don't execute)
:zone send TERMINAL cd /tmp

# Send control characters
:zone send TERMINAL ^C   # Ctrl+C
```

### PTY Zone Examples

```bash
# Main development terminal
:zone pty DEV 100 30 /bin/bash

# Python REPL
:zone pty PYTHON 60 20 /usr/bin/python3

# MySQL client
:zone pty MYSQL 80 25 mysql -u root -p

# SSH session
:zone pty PROD 100 30 ssh user@production.example.com

# System monitor
:zone pty HTOP 80 30 /usr/bin/htop
```

### PTY Zone Limitations

- **Unix/WSL only**: Requires POSIX pty system calls
- **Not a full terminal**: Some advanced terminal features may not work
- **ANSI stripping**: Color codes are stripped for simpler rendering
- **Single focus**: Only one PTY zone can be focused at a time

---

## Command Reference

### Creating Zones

```bash
:zone create NAME X Y W H          # Static zone
:zone create NAME here W H         # Static zone at cursor

:zone pipe NAME W H CMD            # One-shot command
:zone watch NAME W H INTERVAL CMD  # Auto-refreshing command
:zone pty NAME W H [SHELL]         # Interactive terminal (Unix)
:zone fifo NAME W H PATH           # Named pipe listener (Unix)
:zone socket NAME W H PORT         # Network socket listener
:clipboard zone                    # Create clipboard zone
```

### Managing Zones

```bash
:zones                  # List all zones
:zone info [NAME]       # Show zone details
:zone goto NAME         # Jump cursor to zone center
:zone delete NAME       # Delete zone
```

### Zone Content Control

```bash
:zone refresh NAME      # Refresh pipe/watch zone
:zone pause NAME        # Pause watch zone
:zone resume NAME       # Resume watch zone
:zone focus NAME        # Focus PTY zone
:zone send NAME TEXT    # Send text to PTY zone
```

### Bookmarks

```bash
# In NAV mode:
m + KEY           # Set bookmark at cursor (a-z, 0-9)
' + KEY           # Jump to bookmark

# Commands:
:mark KEY [X Y]   # Set bookmark
:marks            # List all bookmarks
:delmark KEY      # Delete bookmark
```

---

## Use Cases

### System Administrator Dashboard

```bash
# Layout with system monitoring
:zone watch CPU 0 0 45 8 5s uptime
:zone watch MEM 0 10 45 8 5s free -h | head -3
:zone watch DISK 50 0 50 8 30s df -h | head -5
:zone watch NET 50 10 50 10 10s ss -tuln | head -8
:zone fifo ALERTS 0 20 100 15 /tmp/alerts.fifo
:zone pty ADMIN 0 37 100 25

# Feed alerts
echo "WARNING: High CPU usage" > /tmp/alerts.fifo
```

### Development Workspace

```bash
# Git + files + terminal
:zone watch GIT 0 0 50 12 5s git status --short
:zone watch FILES 0 14 50 12 10s ls -lah | head -10
:zone pty EDITOR 55 0 90 28
:zone fifo BUILD 0 28 145 20 /tmp/build.fifo
```

### Multi-Service Monitoring

```bash
# Microservices dashboard
:zone watch WEB 0 0 50 10 10s curl -s http://web:8080/health
:zone watch API 55 0 50 10 10s curl -s http://api:3000/health
:zone watch DB 110 0 50 10 30s echo "SELECT 1" | mysql -u root

:zone fifo WEB_LOG 0 12 50 15 /tmp/web.fifo
:zone fifo API_LOG 55 12 50 15 /tmp/api.fifo
:zone fifo DB_LOG 110 12 50 15 /tmp/db.fifo

# Feed logs
tail -f /var/log/web.log > /tmp/web.fifo &
tail -f /var/log/api.log > /tmp/api.fifo &
tail -f /var/log/db.log > /tmp/db.fifo &
```

### CI/CD Integration

```bash
# Build monitor
:zone fifo BUILD 0 0 80 20 /tmp/build.fifo
:zone fifo TESTS 85 0 80 20 /tmp/tests.fifo
:zone socket DEPLOY 0 22 165 15 9999

# From CI scripts:
echo "[BUILD] Starting..." > /tmp/build.fifo
make all 2>&1 | tee /tmp/build.fifo

pytest -v | tee /tmp/tests.fifo

curl -X POST http://monitoring.example.com:9999 \
  -d "Deployment to production started"
```

---

## Layouts

Save and load complete zone configurations.

### Layout Commands

```bash
:layout save NAME [DESC]    # Save current zones
:layout load NAME           # Load layout
:layout load NAME --clear   # Load and clear existing
:layout list                # List available layouts
:layout delete NAME         # Delete layout
:layout info NAME           # Show layout details
```

### Default Layouts

Three layouts are pre-installed:

```bash
:layout load devops        # System monitoring
:layout load development   # Git + files + terminal
:layout load monitoring    # CPU, memory, network, disk
```

### Creating Custom Layouts

1. Create and arrange your zones
2. Save as a layout: `:layout save my-workspace "My custom workspace"`
3. Load anytime: `:layout load my-workspace`

Layouts are stored in:
- Unix: `~/.config/mygrid/layouts/`
- Windows: `%APPDATA%/mygrid/layouts/`

### Layout File Format (YAML)

```yaml
name: my-workspace
description: Custom workspace with monitoring and dev tools
cursor:
  x: 0
  y: 0
zones:
  - name: CPU
    type: watch
    x: 0
    y: 0
    width: 45
    height: 8
    command: "uptime"
    interval: 5
    bookmark: "c"
    description: "CPU load"

  - name: EVENTS
    type: fifo
    x: 50
    y: 0
    width: 60
    height: 20
    path: "/tmp/events.fifo"
    bookmark: "e"

  - name: TERMINAL
    type: pty
    x: 0
    y: 10
    width: 80
    height: 24
    bookmark: "t"
```

---

## Tips and Best Practices

### Performance

- Keep watch intervals reasonable (≥5s for most uses)
- Limit command output (use `head`, `tail`, `grep`)
- Pause zones you're not actively watching
- Use appropriate zone sizes

### FIFO Zones

- Send line-by-line for predictable updates
- Use unique FIFO paths per zone
- Clean up FIFO files when done: `rm /tmp/*.fifo`
- Consider logrotate-style management for long-running FIFOs

### Socket Zones

- Use high port numbers (1024-65535)
- Firewall appropriately for remote access
- Consider localhost-only for security
- Handle connection errors gracefully in senders

### Organization

- Use descriptive zone names (uppercase convention)
- Set bookmarks for frequently used zones
- Group related zones spatially on canvas
- Save layouts for different workflows
- Document your layouts with description field

### Integration

- Write wrapper scripts for common workflows
- Use layouts for project-specific setups
- Integrate with CI/CD via sockets or FIFOs
- Create tmux-like sessions with PTY zones

---

## Troubleshooting

### FIFO Zone Not Receiving Data

```bash
# Check if FIFO exists
ls -l /tmp/mygrid-events.fifo

# Check permissions
# Should show: prw-r--r-- (p = pipe)

# Try manual write
echo "test" > /tmp/mygrid-events.fifo
# Should appear in zone immediately
```

### Socket Zone Connection Refused

```bash
# Check if port is listening
netstat -tuln | grep 9999
# or
ss -tuln | grep 9999

# Try telnet
telnet localhost 9999

# Check firewall
sudo ufw status  # Ubuntu
```

### PTY Zone Not Available

```bash
# Check platform
uname -a  # Must be Linux/macOS/WSL

# Check shell exists
which /bin/bash
```

### Watch Zone Not Updating

```bash
# Check if zone is paused
:zone info ZONENAME

# Resume if paused
:zone resume ZONENAME

# Force refresh
:zone refresh ZONENAME
```

---

## See Also

- `CLAUDE.md` - Main project documentation
- `FIGLET-REFERENCE.md` - ASCII art text reference
- `src/zones.py` - Zone implementation
- `src/layouts.py` - Layout management
- `:help` - In-app help system
