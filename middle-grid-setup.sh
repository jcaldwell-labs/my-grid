#!/bin/bash
# Middle Grid Setup - Complete project map initialization

echo "╔═══════════════════════════════════════════════════════╗"
echo "║         MIDDLE GRID - Project Realm Setup            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Create all needed FIFOs
echo "📝 Cleaning up old FIFOs..."
rm -f /tmp/claude-says.fifo /tmp/you-say.fifo /tmp/household.fifo /tmp/music.fifo /tmp/dev-progress.fifo /tmp/context-events.fifo

echo ""
echo "🏗️  Setting up project zones:"
echo ""
echo "THE SHIRE - Household Management"
echo "  FIFO: /tmp/household.fifo"
echo "  Usage: echo 'Books - living room' > /tmp/household.fifo"
echo ""
echo "RIVENDELL - Sheet Music Library"
echo "  FIFO: /tmp/music.fifo"
echo "  Usage: echo 'Moonlight Sonata - C# minor' > /tmp/music.fifo"
echo ""
echo "CROSSROADS - Communication Hub"
echo "  Claude → You: /tmp/claude-says.fifo"
echo "  You → Claude: /tmp/you-say.fifo"
echo "  Usage: echo 'Hello Claude!' > /tmp/you-say.fifo"
echo ""
echo "GONDOR - Development Zone"
echo "  FIFO: /tmp/dev-progress.fifo"
echo "  (Claude sends development updates here)"
echo ""
echo "PATHS OF THE DEAD - my-context"
echo "  FIFO: /tmp/context-events.fifo"
echo "  (Context change notifications)"
echo ""
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Start my-grid:"
echo "   python3 mygrid.py --server"
echo ""
echo "2. In my-grid, run these commands:"
echo ""
cat << 'EOF'
# Title
:goto 20 2
:figlet -f banner MIDDLE GRID
:goto 20 9
:text === A Project Management Realm ===

# The Shire (Household)
:goto 0 12
:text === THE SHIRE ===
:goto 0 13
:text Household Management
:zone fifo HOUSEHOLD 40 12 /tmp/household.fifo

# Rivendell (Music)
:goto 100 12
:text === RIVENDELL ===
:goto 100 13
:text Sheet Music Library
:zone fifo MUSIC 45 12 /tmp/music.fifo

# Crossroads (Chat)
:goto 45 28
:text === THE CROSSROADS ===
:goto 45 29
:text Communication Hub
:zone fifo CLAUDE_SAYS 50 10 /tmp/claude-says.fifo
:zone fifo YOU_SAY 50 10 /tmp/you-say.fifo

# Gondor (Development)
:goto 0 55
:text === GONDOR ===
:goto 0 56
:text Development Projects
:zone fifo DEV_LOG 40 12 /tmp/dev-progress.fifo

# Paths of the Dead (my-context)
:goto 100 55
:text === PATHS OF THE DEAD ===
:goto 100 56
:text Context History
:zone fifo CONTEXT_LOG 45 12 /tmp/context-events.fifo

# Mount Doom (Issues)
:goto 45 75
:text === MOUNT DOOM ===
:goto 45 76
:text Active Issues
:zone watch ISSUES 60 10 10s gh issue list --repo jcaldwell-labs/my-grid --limit 5

EOF

echo ""
echo "3. Test communication:"
echo "   echo 'Hello from the Shire!' > /tmp/you-say.fifo"
echo ""
echo "4. Watch Claude respond in CLAUDE_SAYS zone!"
echo ""
echo "✨ Ready to explore Middle Grid!"
