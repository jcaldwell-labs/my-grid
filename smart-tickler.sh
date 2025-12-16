#!/bin/bash
# Smart Tickler - Send periodic useful updates to EVENTS zone

FIFO="/tmp/dashboard-events.fifo"
INTERVAL=${1:-3}  # Default 3 seconds

echo "🎯 Starting smart tickler (interval: ${INTERVAL}s)"
echo "Sending: time, load, memory, disk activity"
echo "Press Ctrl+C to stop"
echo ""

# Initial message
echo "[$(date '+%H:%M:%S')] 🚀 Smart tickler started (updates every ${INTERVAL}s)" >> "$FIFO"

COUNT=1
while true; do
    TIMESTAMP=$(date '+%H:%M:%S')

    # Every update: timestamp
    echo "[$TIMESTAMP] ⏱️  Update #$COUNT" >> "$FIFO"

    # Rotate through different info types
    case $((COUNT % 4)) in
        0)
            # Load average
            LOAD=$(uptime | awk -F'load average:' '{print $2}')
            echo "[$TIMESTAMP]   CPU Load: $LOAD" >> "$FIFO"
            ;;
        1)
            # Memory
            MEM=$(free -h | awk '/^Mem:/ {print $3 "/" $2 " (" int($3/$2*100) "%)"}')
            echo "[$TIMESTAMP]   Memory: $MEM" >> "$FIFO"
            ;;
        2)
            # Disk I/O (if iostat available)
            if command -v iostat &> /dev/null; then
                IO=$(iostat -d -x 1 2 | tail -n +4 | head -1 | awk '{print $4 "r/s " $5 "w/s"}')
                echo "[$TIMESTAMP]   Disk I/O: $IO" >> "$FIFO"
            else
                echo "[$TIMESTAMP]   Disk: $(df -h / | awk 'NR==2 {print $5 " used"}')" >> "$FIFO"
            fi
            ;;
        3)
            # Process count
            PROCS=$(ps aux | wc -l)
            echo "[$TIMESTAMP]   Processes: $PROCS running" >> "$FIFO"
            ;;
    esac

    COUNT=$((COUNT + 1))
    sleep "$INTERVAL"
done
