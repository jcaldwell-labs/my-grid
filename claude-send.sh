#!/bin/bash
# Claude Send - Simple script for Claude to send messages to my-grid

FIFO="/tmp/events.fifo"

if [ ! -p "$FIFO" ]; then
    echo "⚠️  FIFO not found at $FIFO"
    echo "Make sure my-grid is running with EVENTS zone created:"
    echo "  :zone fifo EVENTS 80 20 /tmp/events.fifo"
    exit 1
fi

# Send message with timestamp
send() {
    echo "[$(date '+%H:%M:%S')] $*" > "$FIFO"
    echo "✓ Sent: $*"
}

# Main command
case "$1" in
    "")
        echo "Usage: $0 MESSAGE"
        echo "Example: $0 Hello from Claude!"
        ;;
    *)
        send "$@"
        ;;
esac
