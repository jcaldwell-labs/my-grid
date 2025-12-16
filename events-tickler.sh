#!/bin/bash
# Events Tickler - Send periodic heartbeat to EVENTS zone

FIFO="/tmp/dashboard-events.fifo"
INTERVAL=${1:-5}  # Default 5 seconds

echo "Starting events tickler (interval: ${INTERVAL}s)"
echo "Press Ctrl+C to stop"
echo ""

COUNT=1
while true; do
    TIMESTAMP=$(date '+%H:%M:%S')
    echo "[$TIMESTAMP] ⏱️  Heartbeat #$COUNT" > "$FIFO" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Sent heartbeat #$COUNT"
    else
        echo "✗ Failed to send (is my-grid running?)"
    fi
    COUNT=$((COUNT + 1))
    sleep "$INTERVAL"
done
