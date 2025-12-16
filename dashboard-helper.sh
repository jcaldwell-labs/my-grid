#!/bin/bash
# Dashboard Helper - Send events to my-grid dashboard FIFO

EVENTS_FIFO="/tmp/dashboard-events.fifo"

# Function to send event
send_event() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $msg" > "$EVENTS_FIFO"
}

# Check if FIFO exists
check_fifo() {
    if [ ! -p "$EVENTS_FIFO" ]; then
        echo "⚠️  Warning: FIFO not found at $EVENTS_FIFO"
        echo "Make sure my-grid is running with the live-dashboard layout loaded"
        echo ""
        echo "Start my-grid:"
        echo "  python3 mygrid.py"
        echo ""
        echo "Then in my-grid:"
        echo "  :layout load live-dashboard"
        return 1
    fi
    return 0
}

# Main command dispatcher
case "$1" in
    test)
        check_fifo || exit 1
        send_event "✅ Test message - FIFO is working!"
        echo "✅ Sent test message"
        ;;

    hello)
        check_fifo || exit 1
        send_event "👋 Hello from the terminal!"
        send_event "This is a test of the FIFO event system."
        send_event "Events appear in real-time in the my-grid dashboard."
        echo "✅ Sent hello messages"
        ;;

    build)
        check_fifo || exit 1
        send_event "🔨 Build started..."
        sleep 1
        send_event "  → Compiling sources..."
        sleep 1
        send_event "  → Running tests..."
        sleep 1
        send_event "  → Packaging..."
        sleep 1
        send_event "✅ Build complete!"
        echo "✅ Build simulation complete"
        ;;

    countdown)
        check_fifo || exit 1
        COUNT=${2:-5}
        send_event "⏱️  Starting countdown from $COUNT..."
        for i in $(seq $COUNT -1 1); do
            send_event "  $i..."
            sleep 1
        done
        send_event "🚀 Launch!"
        echo "✅ Countdown complete"
        ;;

    monitor)
        check_fifo || exit 1
        echo "📊 Monitoring mode - sending updates every 3 seconds"
        echo "Press Ctrl+C to stop"
        send_event "📊 Monitor started"
        COUNT=1
        while true; do
            CPU=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}')
            MEM=$(free | awk '/Mem:/ {printf "%.1f%%", $3/$2 * 100}')
            send_event "Update #$COUNT - CPU: $CPU | Mem: $MEM | Time: $(date '+%H:%M:%S')"
            COUNT=$((COUNT + 1))
            sleep 3
        done
        ;;

    log)
        check_fifo || exit 1
        shift
        LOG_FILE="$1"
        if [ -z "$LOG_FILE" ]; then
            echo "Usage: $0 log <file>"
            exit 1
        fi
        if [ ! -f "$LOG_FILE" ]; then
            echo "❌ File not found: $LOG_FILE"
            exit 1
        fi
        send_event "📄 Tailing $LOG_FILE..."
        tail -f "$LOG_FILE" | while read line; do
            echo "$line" > "$EVENTS_FIFO"
        done
        ;;

    send)
        check_fifo || exit 1
        shift
        send_event "$*"
        echo "✅ Sent: $*"
        ;;

    clear)
        check_fifo || exit 1
        for i in {1..20}; do
            echo "" > "$EVENTS_FIFO"
        done
        send_event "🧹 Event log cleared"
        echo "✅ Cleared event log"
        ;;

    help|*)
        cat << 'EOF'
Dashboard Helper - Send events to my-grid live dashboard

Usage: ./dashboard-helper.sh COMMAND [args]

Commands:
  test              - Send a test message
  hello             - Send greeting messages
  build             - Simulate a build process
  countdown [N]     - Count down from N (default 5)
  monitor           - Send continuous system updates
  log FILE          - Stream a log file to dashboard
  send MESSAGE      - Send custom message
  clear             - Clear the event log
  help              - Show this help

Setup:
  1. Start my-grid:
     python3 mygrid.py

  2. Load the live-dashboard layout:
     :layout load live-dashboard

  3. Send events from this script:
     ./dashboard-helper.sh test
     ./dashboard-helper.sh hello
     ./dashboard-helper.sh monitor

Examples:
  ./dashboard-helper.sh test
  ./dashboard-helper.sh countdown 10
  ./dashboard-helper.sh send "Deployment started"
  ./dashboard-helper.sh monitor

The EVENTS zone in the dashboard will show all messages in real-time!
EOF
        ;;
esac
