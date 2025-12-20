# Quick Start - Simple Dashboard

## Step 1: Open the Dashboard

```bash
cd ~/projects/active/my-grid
python3 mygrid.py simple-dashboard.json
```

You'll see:
- **Instructions** at the top
- **TIME** zone (updates every 1 second) - Press `'t` to jump here
- **MEMORY** zone (updates every 5 seconds) - Press `'m` to jump here
- **CPU** zone (updates every 5 seconds) - Press `'c` to jump here
- **PROCESSES** zone (updates every 5 seconds) - Press `'p` to jump here

These zones should already be updating automatically!

## Step 2: Create FIFO Zone for Live Communication

**In my-grid, press `:` (colon) and type:**

```
:zone fifo EVENTS 80 20 /tmp/events.fifo
```

This creates a new zone called EVENTS that listens on `/tmp/events.fifo`.

## Step 3: Navigate to the EVENTS Zone

Press `'` (apostrophe) then `e` to jump to the EVENTS zone (if bookmark worked), or use arrow keys to navigate there.

## Step 4: Tell Me You're Ready!

Once you can see the EVENTS zone (it will be empty at first), **tell me "ready"** and I'll start sending you messages!

## What I'll Send You

From another terminal, I'll use commands like:

```bash
echo "Hello from Claude!" > /tmp/events.fifo
./dashboard-helper.sh test
./smart-tickler.sh 3
```

You'll see these messages appear **live** in the EVENTS zone!

## Quick Commands to Try Yourself

Open a second terminal and try:

```bash
cd ~/projects/active/my-grid

# Send a test message
echo "[$(date +%H:%M:%S)] Test message!" > /tmp/events.fifo

# Run the smart tickler (sends updates every 3 seconds)
./smart-tickler.sh 3

# Run dashboard helper
./dashboard-helper.sh test
./dashboard-helper.sh hello
./dashboard-helper.sh countdown 5
```

## Navigation Tips

- `wasd` or arrow keys - Move cursor
- `'t` - Jump to TIME zone
- `'m` - Jump to MEMORY zone
- `'c` - Jump to CPU zone
- `'p` - Jump to PROCESSES zone
- `:zones` - List all zones
- `:zone info EVENTS` - Show EVENTS zone details
- `q` or `:quit` - Exit

---

**Ready? Open simple-dashboard.json and let's collaborate!** 🚀
