#!/usr/bin/env bash
# Convenience script for recording my-grid demos with VHS

set -e

# Ensure VHS is in PATH
export PATH="$HOME/go/bin:$PATH"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check VHS installation
if ! command -v vhs &> /dev/null; then
    echo -e "${RED}Error: VHS not found in PATH${NC}"
    echo "Install with: go install github.com/charmbracelet/vhs@latest"
    echo "Then add to PATH: export PATH=\"\$HOME/go/bin:\$PATH\""
    exit 1
fi

echo -e "${GREEN}VHS found:${NC} $(which vhs)"
echo -e "${GREEN}Version:${NC} $(vhs --version)"
echo

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Parse command
case "${1:-help}" in
    quick|test)
        echo -e "${YELLOW}Recording quick test (10s)...${NC}"
        vhs demo/quick-test.tape
        echo -e "${GREEN}✓ Recorded:${NC} demo/output/quick-test.mp4"
        ;;

    full|productivity)
        echo -e "${YELLOW}Recording full productivity demo (75s)...${NC}"
        vhs demo/my-grid-productivity-demo.tape
        echo -e "${GREEN}✓ Recorded:${NC} demo/output/my-grid-productivity-demo.mp4"
        ;;

    custom)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Provide tape file${NC}"
            echo "Usage: $0 custom path/to/demo.tape"
            exit 1
        fi
        echo -e "${YELLOW}Recording custom demo: $2${NC}"
        vhs "$2"
        echo -e "${GREEN}✓ Recording complete${NC}"
        ;;

    list)
        echo -e "${GREEN}Available demos:${NC}"
        echo
        find demo -name "*.tape" -type f | while read -r tape; do
            echo "  - $tape"
        done
        echo
        ;;

    view)
        echo -e "${GREEN}Recorded videos:${NC}"
        echo
        if [ -d "demo/output" ] && [ -n "$(ls -A demo/output/*.mp4 2>/dev/null)" ]; then
            ls -lh demo/output/*.mp4 | awk '{print "  " $9 " (" $5 ")"}'
            echo
            echo -e "${YELLOW}View with:${NC} mpv demo/output/<filename>.mp4"
        else
            echo "  No recordings found"
            echo
            echo -e "${YELLOW}Run:${NC} $0 quick    # to record a test"
        fi
        ;;

    clean)
        echo -e "${YELLOW}Cleaning output directory...${NC}"
        rm -f demo/output/*.mp4
        echo -e "${GREEN}✓ Cleaned demo/output/${NC}"
        ;;

    help|*)
        cat <<EOF
${GREEN}my-grid Demo Recording Script${NC}

${YELLOW}Usage:${NC}
  $0 [command]

${YELLOW}Commands:${NC}
  quick, test          Record 10-second quick test
  full, productivity   Record 75-second productivity demo
  custom <tape-file>   Record custom VHS tape
  list                 List available tape files
  view                 List recorded videos
  clean                Remove all recordings
  help                 Show this help

${YELLOW}Examples:${NC}
  $0 quick                           # Quick test
  $0 full                            # Full demo
  $0 custom demo/my-demo.tape        # Custom tape
  $0 view                            # List recordings

${YELLOW}Output:${NC}
  Videos are saved to: demo/output/

${YELLOW}Requirements:${NC}
  - VHS: go install github.com/charmbracelet/vhs@latest
  - Add to PATH: export PATH="\$HOME/go/bin:\$PATH"

${YELLOW}Viewing:${NC}
  mpv demo/output/my-grid-productivity-demo.mp4
  vlc demo/output/my-grid-productivity-demo.mp4

${YELLOW}More Info:${NC}
  demo/README.md                 - Quick start guide
  demo/PRODUCTION-GUIDE.md       - Complete production guide
EOF
        ;;
esac
