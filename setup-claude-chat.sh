#!/bin/bash
# Setup script for Claude Chat with my-grid

echo "=========================================="
echo "Claude Chat Setup for my-grid"
echo "=========================================="
echo ""

# Check if my-grid is available
if [ ! -f "mygrid.py" ]; then
    echo "❌ Error: mygrid.py not found in current directory"
    exit 1
fi

echo "✅ Found mygrid.py"

# Check if layout exists
LAYOUT_FILE="$HOME/.config/mygrid/layouts/claude-chat.yaml"
if [ ! -f "$LAYOUT_FILE" ]; then
    echo "❌ Error: claude-chat layout not found at $LAYOUT_FILE"
    exit 1
fi

echo "✅ Found claude-chat layout"

# Check if chat script exists
if [ ! -f "claude-chat.sh" ]; then
    echo "❌ Error: claude-chat.sh not found"
    exit 1
fi

echo "✅ Found claude-chat.sh"
echo ""

# Clean up any existing FIFOs
echo "🧹 Cleaning up old FIFO pipes..."
rm -f /tmp/claude-out.fifo /tmp/user-in.fifo /tmp/activity.fifo
echo "✅ Cleanup complete"
echo ""

echo "=========================================="
echo "Setup Complete! Here's how to use it:"
echo "=========================================="
echo ""
echo "1. In THIS terminal window, start my-grid:"
echo "   python3 mygrid.py"
echo ""
echo "2. In my-grid, load the claude-chat layout:"
echo "   :layout load claude-chat"
echo ""
echo "3. In ANOTHER terminal, use the chat script:"
echo "   ./claude-chat.sh demo"
echo "   ./claude-chat.sh send 'Hello!'"
echo "   ./claude-chat.sh countdown 5"
echo "   ./claude-chat.sh monitor"
echo ""
echo "Available zones and bookmarks:"
echo "   'c - CLAUDE_OUT  (Messages from Claude)"
echo "   'u - USER_IN     (Messages to Claude)"
echo "   's - STATUS      (System status)"
echo "   'a - ACTIVITY    (Activity log)"
echo "   'n - NOTES       (Static notes)"
echo ""
echo "Commands:"
echo "   ./claude-chat.sh help     - Show all commands"
echo "   ./claude-chat.sh demo     - Run demo sequence"
echo "   ./claude-chat.sh monitor  - Continuous updates"
echo ""
echo "Ready to start! 🚀"
