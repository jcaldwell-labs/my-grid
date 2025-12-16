#!/bin/bash
# Simulate realistic my-grid project log traffic

FIFO="/tmp/events.fifo"

send() {
    echo "[$(date '+%H:%M:%S.%3N')] $*" > "$FIFO"
}

echo "Simulating 200+ log messages for my-grid project..."

# Session start
send "🚀 [SYSTEM] my-grid v1.0 starting..."
send "[INIT] Loading configuration from ~/.config/mygrid/"
send "[INIT] Terminal size detected: 120x40"
send "[INIT] Initializing canvas with sparse storage"
send "[INIT] Viewport positioned at (0, 0)"

# Layout loading simulation
send "[LAYOUT] Loading layout: simple-dashboard"
send "[ZONE] Creating TIME zone (50x8) at (0,10)"
send "[ZONE] Starting watch: 'date +%A, %B %d, %Y...' interval=1s"
send "[ZONE] Creating MEMORY zone (50x8) at (55,10)"
send "[ZONE] Starting watch: 'free -h' interval=5s"
send "[ZONE] Creating CPU zone (50x8) at (0,20)"
send "[ZONE] Starting watch: 'uptime' interval=5s"
send "[ZONE] Creating PROCESSES zone (50x10) at (55,20)"
send "[ZONE] Starting watch: 'ps aux --sort=-%cpu' interval=5s"
send "[LAYOUT] Successfully loaded 4 zones"

# User interactions
send "[INPUT] User pressed ':' - entering COMMAND mode"
send "[CMD] Executing: zone fifo EVENTS 80 20 /tmp/events.fifo"
send "[ZONE] Creating FIFO zone 'EVENTS'"
send "[FIFO] Creating named pipe at /tmp/events.fifo"
send "[FIFO] Started listener thread for EVENTS"
send "[ZONE] EVENTS zone ready at (0,32)"
send "[MODE] Returning to NAV mode"

# Simulated development activity
send "[RENDER] Frame rendered (23ms) - 5 zones, 142 cells"
send "[INPUT] Cursor moved to (0, 32)"
send "[RENDER] Frame rendered (19ms) - 5 zones, 142 cells"

# Git operations
send "[EXT] Running external tool: git"
send "[GIT] On branch master"
send "[GIT] Your branch is up to date with 'origin/master'"
send "[GIT] Changes not staged for commit:"
send "[GIT]   modified:   src/zones.py"
send "[GIT]   modified:   ZONES-REFERENCE.md"
send "[GIT]   new file:   simple-dashboard.json"

# Zone updates
send "[WATCH:TIME] Update #47 completed (12ms)"
send "[WATCH:MEMORY] Update #12 completed (45ms)"
send "[WATCH:CPU] Update #12 completed (8ms)"
send "[WATCH:PROCESSES] Update #12 completed (156ms)"

# FIFO events
send "[FIFO:EVENTS] Received 18 bytes from external process"
send "[FIFO:EVENTS] Appended line to buffer (23 lines total)"
send "[FIFO:EVENTS] Received 42 bytes from external process"
send "[FIFO:EVENTS] Appended line to buffer (24 lines total)"

# Performance metrics
send "[PERF] Average frame time: 21ms (47.6 FPS)"
send "[PERF] Canvas cells: 142 active / 4800 viewport"
send "[PERF] Memory usage: 47.2 MB RSS"
send "[PERF] Zone executor threads: 4 active"

# More user activity
send "[INPUT] User pressed 'w' - cursor moved up"
send "[INPUT] User pressed 'w' - cursor moved up"
send "[INPUT] User pressed 'a' - cursor moved left"
send "[RENDER] Frame rendered (18ms)"

# Bookmark operations
send "[BOOKMARK] User set bookmark 'e' at (0, 32)"
send "[BOOKMARK] Bookmarks saved to project file"

# File operations
send "[PROJECT] Auto-save triggered"
send "[PROJECT] Saving to simple-dashboard.json"
send "[PROJECT] Serializing 5 zones"
send "[PROJECT] Serializing 4 bookmarks"
send "[PROJECT] Write complete (1.2KB)"
send "[PROJECT] File marked as clean"

# Zone management
send "[CMD] Executing: zone info EVENTS"
send "[ZONE:EVENTS] Type: FIFO"
send "[ZONE:EVENTS] Position: (0, 32)"
send "[ZONE:EVENTS] Size: 80x20"
send "[ZONE:EVENTS] Buffer: 24/1000 lines"
send "[ZONE:EVENTS] FIFO path: /tmp/events.fifo"
send "[ZONE:EVENTS] Status: active"

# External tool integration
send "[EXT] Executing: figlet -f banner 'My Grid'"
send "[EXT] Command completed (127ms, 7 lines output)"
send "[CANVAS] Drawing figlet output at (10, 5)"

# More watch updates
send "[WATCH:TIME] Update #48 completed (11ms)"
send "[WATCH:TIME] Output: Monday, December 16, 2024"
send "[WATCH:TIME] Output: 12:15:34"
send "[WATCH:MEMORY] Update #13 completed (43ms)"
send "[WATCH:MEMORY] Total: 15Gi | Used: 2.7Gi | Free: 11Gi"

# Error simulation
send "[ERROR] Watch command failed for TIME zone"
send "[ERROR] Command: date +'%A, %B %d, %Y%n%H:%M:%S'"
send "[ERROR] Exit code: 127"
send "[ERROR] Retrying in 5 seconds..."
send "[WATCH:TIME] Retry successful - zone recovered"

# Clipboard operations
send "[CLIPBOARD] Yank region initiated at (0, 32)"
send "[CLIPBOARD] Selected area: 80x20"
send "[CLIPBOARD] Copied 24 lines to clipboard"
send "[CLIPBOARD] Source: zone EVENTS"
send "[CLIPBOARD] Buffer size: 892 characters"

# Network activity (simulated)
send "[SERVER] API server listening on 0.0.0.0:8765"
send "[SERVER] New connection from 127.0.0.1:54321"
send "[API] Received command: 'status'"
send "[API] Sent response: {\"zones\": 5, \"fps\": 47.6}"
send "[SERVER] Connection closed"

# More FIFO activity
send "[FIFO:EVENTS] Received 67 bytes"
send "[FIFO:EVENTS] Appended line (25 lines total)"
send "[FIFO:EVENTS] Received 102 bytes"
send "[FIFO:EVENTS] Appended 3 lines (28 lines total)"

# Canvas operations
send "[CANVAS] Cell set at (45, 12): 'A'"
send "[CANVAS] Cell set at (46, 12): 'B'"
send "[CANVAS] Cell set at (47, 12): 'C'"
send "[CANVAS] Sparse storage: 145 cells in use"

# Viewport operations
send "[VIEWPORT] Pan to (10, 5)"
send "[VIEWPORT] Cursor follows viewport"
send "[VIEWPORT] New position: (10, 5)"
send "[RENDER] Viewport bounds: (10, 5) to (130, 45)"

# Zone refresh
send "[CMD] Executing: zone refresh MEMORY"
send "[ZONE:MEMORY] Manual refresh triggered"
send "[WATCH:MEMORY] Executing: free -h"
send "[WATCH:MEMORY] Command completed (41ms)"
send "[ZONE:MEMORY] Content updated (8 lines)"

# More bookmarks
send "[INPUT] User pressed 'm' - entering MARK_SET mode"
send "[INPUT] User pressed 't' - setting bookmark"
send "[BOOKMARK] Bookmark 't' set at (0, 10)"
send "[MODE] Returning to NAV mode"

# Performance monitoring
send "[PERF] GC triggered - pausing for collection"
send "[PERF] GC completed (3ms)"
send "[PERF] Heap size: 52.1 MB"
send "[PERF] Frame time spike detected: 156ms"
send "[PERF] Investigating slow frame..."
send "[PERF] Cause: ps aux command in PROCESSES zone"

# External script execution
send "[EXT] Running: ./dashboard-helper.sh test"
send "[EXT] Script output redirected to FIFO"
send "[FIFO:EVENTS] Receiving data from dashboard-helper"

# Keyboard macro simulation
send "[INPUT] Fast input detected - key repeat"
send "[INPUT] Processed 15 'w' keys in 200ms"
send "[VIEWPORT] Rapid scroll in progress"

# Thread activity
send "[THREAD:watch-TIME] Thread ID 12345 active"
send "[THREAD:watch-MEMORY] Thread ID 12346 active"
send "[THREAD:watch-CPU] Thread ID 12347 active"
send "[THREAD:watch-PROCESSES] Thread ID 12348 active"
send "[THREAD:fifo-EVENTS] Thread ID 12349 active"

# Save operations
send "[CMD] Executing: write"
send "[PROJECT] Save initiated by user"
send "[PROJECT] Backing up to simple-dashboard.json.bak"
send "[PROJECT] Writing new file"
send "[PROJECT] Save successful (1.4KB)"

# Zone state
send "[ZONE:TIME] State: active, updating"
send "[ZONE:MEMORY] State: active, updating"
send "[ZONE:CPU] State: active, updating"
send "[ZONE:PROCESSES] State: active, updating"
send "[ZONE:EVENTS] State: active, listening"

# Help system
send "[CMD] Executing: help"
send "[HELP] Displaying command reference"
send "[HELP] Available commands: 47"
send "[HELP] Available modes: 6"

# More FIFO traffic
send "[FIFO:EVENTS] Connection from PID 23456"
send "[FIFO:EVENTS] Received: '[12:16:01] System check'"
send "[FIFO:EVENTS] Buffer: 32/1000 lines"

# Cursor navigation
send "[INPUT] User pressed '\'' - entering MARK_JUMP mode"
send "[INPUT] User pressed 'e' - jumping to bookmark"
send "[BOOKMARK] Jumping to bookmark 'e' at (0, 32)"
send "[VIEWPORT] Panning to keep cursor visible"

# Zone resize simulation
send "[CMD] Executing: zone resize EVENTS 100 25"
send "[ZONE:EVENTS] Resizing from 80x20 to 100x25"
send "[ZONE:EVENTS] Redrawing border"
send "[ZONE:EVENTS] Rerendering content"

# Watch zone pause/resume
send "[CMD] Executing: zone pause CPU"
send "[ZONE:CPU] Pausing watch updates"
send "[WATCH:CPU] Thread notified to pause"
send "[ZONE:CPU] State changed to: paused"

send "[CMD] Executing: zone resume CPU"
send "[ZONE:CPU] Resuming watch updates"
send "[WATCH:CPU] Thread notified to resume"
send "[ZONE:CPU] State changed to: active"

# Layout save
send "[CMD] Executing: layout save my-workspace"
send "[LAYOUT] Saving current configuration"
send "[LAYOUT] Capturing 5 zones"
send "[LAYOUT] Capturing 4 bookmarks"
send "[LAYOUT] Capturing viewport state"
send "[LAYOUT] Writing to ~/.config/mygrid/layouts/my-workspace.yaml"
send "[LAYOUT] Save complete"

# Cleanup simulation
send "[INPUT] User pressed 'q' - quit requested"
send "[SHUTDOWN] Initiating graceful shutdown"
send "[ZONE] Stopping watch thread: TIME"
send "[ZONE] Stopping watch thread: MEMORY"
send "[ZONE] Stopping watch thread: CPU"
send "[ZONE] Stopping watch thread: PROCESSES"
send "[FIFO] Closing listener: EVENTS"
send "[FIFO] Removing named pipe: /tmp/events.fifo"
send "[SERVER] Stopping API server"
send "[CANVAS] Saving final state"
send "[TERMINAL] Restoring terminal settings"
send "👋 [SYSTEM] my-grid shutdown complete"

# Final stats
send "---"
send "📊 [STATS] Session Summary:"
send "  Uptime: 5m 42s"
send "  Frames rendered: 6,847"
send "  Average FPS: 20.1"
send "  Commands executed: 24"
send "  FIFO messages received: 45"
send "  Zones created: 5"
send "  Bookmarks set: 4"
send "  Files saved: 3"
send "✅ [SYSTEM] Log simulation complete - 200+ messages sent"

echo "✅ Done! Sent 200+ messages to $FIFO"
