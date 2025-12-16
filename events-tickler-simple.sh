#!/bin/bash
# Simple tickler for /tmp/events.fifo

FIFO="/tmp/events.fifo"
INTERVAL=${1:-2}  # Default 2 seconds

echo "Starting tickler for $FIFO (interval: ${INTERVAL}s)"
echo "This keeps the EVENTS zone updating"
echo "Press Ctrl+C to stop"

COUNT=1
while true; do
    TIMESTAMP=$(date '+%H:%M:%S')
    echo "[$TIMESTAMP] ⏱️  Heartbeat #$COUNT" > "$FIFO" 2>/dev/null
    COUNT=$((COUNT + 1))
    sleep "$INTERVAL"
done
