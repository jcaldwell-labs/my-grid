#!/bin/bash
# Claude Monitor - Watch user messages and enable responses

USER_INPUT="/tmp/you-say.fifo"
CLAUDE_OUTPUT="/tmp/claude-says.fifo"

echo "🤖 Claude Monitor Active"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Watching: $USER_INPUT"
echo "Reply to: $CLAUDE_OUTPUT"
echo ""
echo "When user sends a message, it will appear below."
echo "Press Ctrl+C to stop."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to send response (for manual use)
send() {
    local msg="$*"
    echo "[$(date +%H:%M:%S)] 🤖 Claude: $msg" > "$CLAUDE_OUTPUT"
    echo "✓ Sent: $msg"
}

# Check if FIFOs exist
if [ ! -p "$USER_INPUT" ]; then
    echo "⚠️  User FIFO doesn't exist yet: $USER_INPUT"
    echo "   It will be created when you set up the zone in my-grid"
fi

if [ ! -p "$CLAUDE_OUTPUT" ]; then
    echo "⚠️  Claude FIFO doesn't exist yet: $CLAUDE_OUTPUT"
    echo "   It will be created when you set up the zone in my-grid"
fi

echo ""
echo "📨 Waiting for messages..."
echo ""

# Monitor the user's FIFO
if [ -p "$USER_INPUT" ]; then
    tail -f "$USER_INPUT" | while read line; do
        echo "📬 USER: $line"
        # Claude Code will send responses manually via commands
    done
else
    echo "Waiting for $USER_INPUT to be created..."
    while [ ! -p "$USER_INPUT" ]; do
        sleep 1
    done
    echo "✅ FIFO created! Monitoring now..."
    exec "$0"  # Restart script
fi
