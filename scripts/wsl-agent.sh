#!/usr/bin/env bash
# wsl-agent.sh - Execute Claude Code commands in WSL environment
#
# This script allows orchestration from Windows while leveraging
# Linux tools (vhs, figlet, boxes, ffmpeg) in the WSL environment.
#
# Usage:
#   ./scripts/wsl-agent.sh "Record the sticky notes demo using VHS"
#   ./scripts/wsl-agent.sh --print "Generate a figlet banner for 'my-grid'"
#   ./scripts/wsl-agent.sh --allowedTools "Bash,Read" "List files in demo/"
#
# The script runs claude with the jcaldwell-labs-media skill context.

set -e

PROJECT_DIR="/home/be-dev-agent/projects/active/my-grid"
SKILL_DIR="/home/be-dev-agent/.claude/skills/jcaldwell-labs-media"

# Default options
PRINT_MODE=""
ALLOWED_TOOLS=""
MAX_TURNS="10"

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --print|-p)
            PRINT_MODE="--print"
            shift
            ;;
        --allowedTools)
            ALLOWED_TOOLS="--allowedTools $2"
            shift 2
            ;;
        --maxTurns)
            MAX_TURNS="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

PROMPT="$1"

if [[ -z "$PROMPT" ]]; then
    echo "Usage: $0 [options] \"prompt\""
    echo ""
    echo "Options:"
    echo "  --print, -p           Print response only (no tool execution)"
    echo "  --allowedTools LIST   Comma-separated list of allowed tools"
    echo "  --maxTurns N          Maximum conversation turns (default: 10)"
    echo ""
    echo "Examples:"
    echo "  $0 \"Record the sticky notes demo\""
    echo "  $0 --print \"What VHS settings should I use?\""
    echo "  $0 --allowedTools Bash,Read \"Run the demo script\""
    exit 1
fi

# Build context about available tools
CONTEXT="You are running in the my-grid project at $PROJECT_DIR.

Available Linux tools:
- vhs (~/go/bin/vhs) - Terminal recording
- figlet - ASCII art text
- boxes - Text box decoration
- ffmpeg - Video encoding

VHS path must use: export PATH=\"\$HOME/go/bin:\$PATH\"

The jcaldwell-labs-media skill is available for video production patterns.
Demo files are in demo/ directory.
"

# Execute claude in WSL with the prompt
echo "=== WSL Agent: Executing in $PROJECT_DIR ==="
echo "Prompt: $PROMPT"
echo "---"

wsl -d Debian bash -c "
cd '$PROJECT_DIR'
export PATH=\"\$HOME/go/bin:\$PATH\"
claude $PRINT_MODE $ALLOWED_TOOLS --max-turns $MAX_TURNS -p '$CONTEXT

Task: $PROMPT'
"
