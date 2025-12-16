# Live Dashboard Quick Start

## What You Get

Two **working layouts** with real FIFO zones for live interaction:

1. **live-dashboard** - System monitoring + live event stream
2. **claude-chat** - Interactive chat workspace for Claude ↔ User communication

---

## Option 1: Live Dashboard (System Monitoring)

### Start the Dashboard

**Terminal 1 (my-grid):**
```bash
cd ~/projects/active/my-grid
python3 mygrid.py
```

**In my-grid, load the layout:**
```
:layout load live-dashboard
```

You'll see:
- `TIME` [W] - Current time and uptime (bookmark: `'t`)
- `MEMORY` [W] - Memory usage (bookmark: `'m`)
- `DISK` [W] - Disk usage (bookmark: `'d`)
- `PROCESSES` [W] - Top processes (bookmark: `'p`)
- `NETWORK` [W] - Network stats (bookmark: `'n`)
- **`EVENTS` [F] - Live FIFO event stream** (bookmark: `'e`)
- `NOTES` [S] - Static notes (bookmark: `'h`)

### Send Events to the Dashboard

**Terminal 2 (send events):**
```bash
cd ~/projects/active/my-grid

# Test the connection
./dashboard-helper.sh test

# Send a greeting
./dashboard-helper.sh hello

# Simulate a build
./dashboard-helper.sh build

# Count down
./dashboard-helper.sh countdown 10

# Continuous monitoring
./dashboard-helper.sh monitor

# Send custom message
./dashboard-helper.sh send "Deploy started on production"
```

### Navigation

Press `'e` (apostrophe + e) to jump to the EVENTS zone and watch messages appear in real-time!

---

## Option 2: Claude Chat (Interactive Communication)

This layout is designed for **back-and-forth communication** between you and Claude.

### Start Claude Chat

**Terminal 1 (my-grid):**
```bash
python3 mygrid.py
```

**In my-grid:**
```
:layout load claude-chat
```

You'll see:
- **`CLAUDE_OUT` [F]** - Messages FROM Claude (bookmark: `'c`)
- **`USER_IN` [F]** - Messages TO Claude (bookmark: `'u`)
- `STATUS` [W] - System status (bookmark: `'s`)
- **`ACTIVITY` [F]** - Activity log (bookmark: `'a`)
- `NOTES` [S] - Static notes (bookmark: `'n`)

### Claude Sends Messages

**Terminal 2 (Claude's terminal):**
```bash
cd ~/projects/active/my-grid

# Run a demo
./claude-chat.sh demo

# Send a message
./claude-chat.sh send "Hello! How can I help you today?"

# Count down
./claude-chat.sh countdown 5

# Tell a joke
./claude-chat.sh joke

# Send system status
./claude-chat.sh status

# Continuous updates
./claude-chat.sh monitor
```

### You Send Messages Back

**Terminal 3 (your terminal):**
```bash
# Send to Claude
echo "[$(date +%H:%M:%S)] User: Can you help me with Python?" > /tmp/user-in.fifo
echo "[$(date +%H:%M:%S)] User: What's the weather like?" > /tmp/user-in.fifo
```

---

## How It Works

### FIFO Zones = Real-Time Pipes

When you load a layout with FIFO zones:

1. **my-grid creates the named pipe** (e.g., `/tmp/dashboard-events.fifo`)
2. **my-grid opens it for reading** and displays incoming data
3. **External scripts write to the pipe** using `echo "message" > /tmp/fifo-path.fifo`
4. **Text appears instantly** in the zone!

### Watch Zones = Auto-Refresh

Watch zones run commands periodically:
- `TIME` refreshes every 1 second
- `MEMORY` and `PROCESSES` refresh every 5 seconds
- `DISK` refreshes every 30 seconds
- `NETWORK` refreshes every 10 seconds

---

## Claude and User Testing Together

Let's test it **right now**! Here's what to do:

### Step 1: You Start my-grid

In your current terminal:
```bash
python3 mygrid.py
```

Then in my-grid:
```
:layout load live-dashboard
```

### Step 2: I (Claude) Send Events

Once you confirm my-grid is running, I'll send messages to your dashboard using bash commands.

### Step 3: Watch Real-Time Updates

Press `'e` to jump to the EVENTS zone and watch my messages appear!

---

## Available Scripts

| Script | Purpose |
|--------|---------|
| `dashboard-helper.sh` | Send events to live-dashboard |
| `claude-chat.sh` | Claude sends messages in chat layout |
| `setup-claude-chat.sh` | Setup guide and verification |

---

## Quick Reference

### Bookmarks (press ' + letter in NAV mode)

**live-dashboard:**
- `'t` - TIME
- `'m` - MEMORY
- `'d` - DISK
- `'p` - PROCESSES
- `'n` - NETWORK
- `'e` - EVENTS (FIFO)
- `'h` - NOTES

**claude-chat:**
- `'c` - CLAUDE_OUT (Claude's messages)
- `'u` - USER_IN (your messages)
- `'s` - STATUS
- `'a` - ACTIVITY
- `'n` - NOTES

### Commands

```bash
:zones              # List all zones
:zone info NAME     # Show zone details
:zone goto NAME     # Jump to zone
:zone pause NAME    # Pause watch zone
:zone resume NAME   # Resume watch zone
:zone refresh NAME  # Manual refresh
```

---

## Troubleshooting

### FIFO not receiving data?

1. Make sure my-grid is running
2. Make sure the layout is loaded (`:layout load live-dashboard`)
3. Check FIFO exists: `ls -l /tmp/dashboard-events.fifo`
4. Try sending manually: `echo "test" > /tmp/dashboard-events.fifo`

### Zone not updating?

1. Check if paused: `:zone info ZONENAME`
2. Resume if needed: `:zone resume ZONENAME`
3. Force refresh: `:zone refresh ZONENAME`

### Permission denied?

FIFOs are created by my-grid when the layout loads. If you get permission errors:
```bash
rm -f /tmp/*.fifo  # Clean up old FIFOs
# Then reload the layout in my-grid
```

---

## Ready to Test!

Let me know when you have my-grid running with the dashboard, and I'll start sending you messages in real-time! 🚀
