#!/bin/bash
# Claude Chat Script - Send messages to my-grid FIFO zones

CLAUDE_OUT="/tmp/claude-out.fifo"
USER_IN="/tmp/user-in.fifo"
ACTIVITY="/tmp/activity.fifo"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to send message with timestamp
send_claude() {
    local msg="$1"
    local timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] Claude: $msg" > "$CLAUDE_OUT"
    echo -e "${GREEN}[Claude → Grid]${NC} $msg"
}

# Function to log activity
log_activity() {
    local msg="$1"
    local timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] $msg" > "$ACTIVITY"
}

# Function to read user message
read_user() {
    if [ -p "$USER_IN" ]; then
        # This would block, so we just check if pipe exists
        echo "User input FIFO is ready"
    fi
}

# Main command dispatcher
case "$1" in
    send)
        shift
        send_claude "$*"
        log_activity "Claude sent message"
        ;;

    demo)
        echo -e "${YELLOW}Starting Claude Chat Demo...${NC}"
        log_activity "Demo started"
        sleep 1

        send_claude "Hello! I'm Claude."
        sleep 2

        send_claude "I can send messages to your my-grid dashboard."
        sleep 2

        send_claude "This is using FIFO pipes for real-time communication."
        sleep 2

        send_claude "Try typing in your terminal and I'll respond!"
        log_activity "Demo completed"
        ;;

    countdown)
        COUNT=${2:-10}
        log_activity "Countdown started: $COUNT"
        send_claude "Starting countdown from $COUNT..."
        for i in $(seq $COUNT -1 1); do
            send_claude "$i..."
            log_activity "Countdown: $i"
            sleep 1
        done
        send_claude "🎉 Countdown complete!"
        log_activity "Countdown complete"
        ;;

    status)
        send_claude "System time: $(date)"
        send_claude "Uptime: $(uptime -p)"
        send_claude "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
        log_activity "Status check sent"
        ;;

    joke)
        send_claude "Why do programmers prefer dark mode?"
        sleep 2
        send_claude "Because light attracts bugs! 🐛"
        log_activity "Joke told"
        ;;

    monitor)
        echo -e "${BLUE}Monitoring mode - Press Ctrl+C to stop${NC}"
        log_activity "Monitor mode started"
        COUNT=1
        while true; do
            send_claude "Update #$COUNT - $(date '+%H:%M:%S')"
            log_activity "Monitor update $COUNT"
            COUNT=$((COUNT + 1))
            sleep 3
        done
        ;;

    help|*)
        echo "Claude Chat Script - Interact with my-grid via FIFO"
        echo ""
        echo "Usage: $0 COMMAND [args]"
        echo ""
        echo "Commands:"
        echo "  send MESSAGE      - Send a message to the grid"
        echo "  demo              - Run a demo sequence"
        echo "  countdown [N]     - Count down from N (default 10)"
        echo "  status            - Send system status"
        echo "  joke              - Tell a programming joke"
        echo "  monitor           - Continuous updates every 3s"
        echo "  help              - Show this help"
        echo ""
        echo "Example:"
        echo "  $0 send 'Hello from Claude!'"
        echo "  $0 demo"
        echo "  $0 countdown 5"
        ;;
esac
