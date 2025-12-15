#!/usr/bin/env bash
# Generate my-grid tutorial documentation (headless - no terminal required)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo -e "${YELLOW}Generating my-grid tutorial (headless mode)...${NC}"
echo

case "${1:-both}" in
    markdown|md)
        echo -e "${YELLOW}Generating Markdown tutorial...${NC}"
        python3 src/headless_demo.py markdown demo/output/tutorial.md
        echo -e "${GREEN}✓ Markdown tutorial:${NC} demo/output/tutorial.md"
        echo
        echo "Preview with: less demo/output/tutorial.md"
        echo "Or open in editor: code demo/output/tutorial.md"
        ;;

    text|txt)
        echo -e "${YELLOW}Generating plain text tutorial...${NC}"
        python3 src/headless_demo.py text demo/output/tutorial.txt
        echo -e "${GREEN}✓ Text tutorial:${NC} demo/output/tutorial.txt"
        echo
        echo "View with: less demo/output/tutorial.txt"
        echo "Or: cat demo/output/tutorial.txt"
        ;;

    both|all)
        echo -e "${YELLOW}Generating both formats...${NC}"
        python3 src/headless_demo.py markdown demo/output/tutorial.md
        python3 src/headless_demo.py text demo/output/tutorial.txt
        echo
        echo -e "${GREEN}✓ Markdown tutorial:${NC} demo/output/tutorial.md"
        echo -e "${GREEN}✓ Text tutorial:${NC} demo/output/tutorial.txt"
        echo
        echo "Preview:"
        echo "  Markdown: less demo/output/tutorial.md"
        echo "  Text:     less demo/output/tutorial.txt"
        ;;

    readme)
        echo -e "${YELLOW}Generating tutorial and copying to README-TUTORIAL.md...${NC}"
        python3 src/headless_demo.py markdown demo/output/tutorial.md
        cp demo/output/tutorial.md README-TUTORIAL.md
        echo -e "${GREEN}✓ Tutorial copied to README-TUTORIAL.md${NC}"
        echo
        echo "Include in main README.md:"
        echo "  See [Tutorial](README-TUTORIAL.md) for complete guide"
        ;;

    help|*)
        cat <<EOF
${GREEN}my-grid Tutorial Generator (Headless)${NC}

${YELLOW}Usage:${NC}
  $0 [format]

${YELLOW}Formats:${NC}
  markdown, md     Generate Markdown tutorial
  text, txt        Generate plain text tutorial
  both, all        Generate both formats (default)
  readme           Generate and copy to README-TUTORIAL.md
  help             Show this help

${YELLOW}Examples:${NC}
  $0                    # Generate both formats
  $0 markdown           # Markdown only
  $0 text               # Text only
  $0 readme             # Copy to root README-TUTORIAL.md

${YELLOW}Features:${NC}
  ✓ No terminal/curses required (headless)
  ✓ Perfect for CI/CD pipelines
  ✓ Includes ASCII diagram examples
  ✓ Hitchhiker's Guide easter eggs
  ✓ Complete command reference

${YELLOW}Output Location:${NC}
  demo/output/tutorial.md   (Markdown)
  demo/output/tutorial.txt  (Plain text)

${YELLOW}About Headless Mode:${NC}
  Unlike VHS recording, headless mode generates tutorial content
  directly without requiring a terminal. Perfect for:
  - CI/CD documentation generation
  - Automated README updates
  - Static documentation sites
  - Email or text-based distribution
EOF
        ;;
esac
