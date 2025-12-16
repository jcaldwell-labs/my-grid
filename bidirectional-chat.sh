#!/bin/bash
# Bidirectional FIFO Chat - Claude monitors user input and responds

USER_FIFO="/tmp/you-say.fifo"
CLAUDE_FIFO="/tmp/claude-says.fifo"

echo "🤖 Claude chat monitor starting..."
echo "   Listening: $USER_FIFO"
echo "   Responding: $CLAUDE_FIFO"
echo ""
echo "Instructions for user:"
echo "  Send messages: echo 'your message' > /tmp/you-say.fifo"
echo "  I'll see them and can respond via commands"
echo ""

# Initial greeting
if [ -p "$CLAUDE_FIFO" ]; then
    echo "[$(date +%H:%M:%S)] 🤖 Claude: Hello! I'm listening..." > "$CLAUDE_FIFO"
fi

# Note: In practice, I (Claude) will send responses by running:
#   echo "[timestamp] 🤖 Claude: response" > /tmp/claude-says.fifo
# from my terminal when I see your messages come through the conversation

# This script just shows it's ready - actual responses come from Claude Code commands
echo "✅ Ready! Waiting for your messages..."
echo "   (I'll respond through Claude Code terminal commands)"
