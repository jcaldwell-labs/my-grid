#!/usr/bin/env bash
# Demo runner for my-grid - supports multiple demo modes
#
# Usage:
#   ./demo/run-demo.sh              # Run internal curses demo (default)
#   ./demo/run-demo.sh internal     # Run internal curses demo
#   ./demo/run-demo.sh api          # Run API demo (requires server)
#   ./demo/run-demo.sh sticky       # Run sticky notes demo (requires server)
#
# For API/sticky demos, start my-grid server first:
#   python src/main.py --server &

set -e
cd "$(dirname "$0")/.."

DEMO_TYPE="${1:-internal}"
DURATION="${2:-60}"

case "$DEMO_TYPE" in
    internal|curses)
        echo "Running internal curses demo (${DURATION}s)..."
        python3 -c "import sys; sys.path.insert(0, 'src'); from demo import run_demo; run_demo(${DURATION})"
        ;;
    api)
        echo "Running API demo..."
        echo "Note: my-grid server must be running (python src/main.py --server)"
        python3 demo/api_demo.py
        ;;
    sticky|notes)
        echo "Running sticky notes demo..."
        echo "Note: my-grid server must be running (python src/main.py --server)"
        python3 demo/sticky_notes_demo.py
        ;;
    edu|educational)
        echo "Running educational demo (1600x480 canvas)..."
        echo "Note: my-grid server must be running (python src/main.py --server)"
        python3 demo/educational_demo.py
        ;;
    visual|vhs)
        echo "Running visual auto-demo for VHS recording (${DURATION}s)..."
        echo "This runs the actual curses UI with programmed actions"
        python3 demo/visual_auto_demo.py ${DURATION}
        ;;
    help|--help|-h)
        echo "my-grid Demo Runner"
        echo ""
        echo "Usage: $0 [demo_type] [duration]"
        echo ""
        echo "Demo types:"
        echo "  internal  - Internal curses demo (default, no server needed)"
        echo "  visual    - Visual auto-demo for VHS recording (no server needed)"
        echo "  api       - API demo using mygrid-ctl (requires server)"
        echo "  sticky    - Sticky notes large canvas demo (requires server)"
        echo "  edu       - Educational demo 1600x480 canvas (requires server)"
        echo ""
        echo "For API demos, start the server first:"
        echo "  python src/main.py --server &"
        echo ""
        echo "Examples:"
        echo "  $0                  # 60-second internal demo"
        echo "  $0 internal 90      # 90-second internal demo"
        echo "  $0 visual 75        # 75-second visual demo (for VHS)"
        echo "  $0 api              # API demo"
        echo "  $0 sticky           # Sticky notes demo"
        echo "  $0 edu              # Educational demo (1600x480 canvas)"
        ;;
    *)
        echo "Unknown demo type: $DEMO_TYPE"
        echo "Use '$0 help' for available options"
        exit 1
        ;;
esac
