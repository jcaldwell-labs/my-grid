# my-grid Sticky Notes Demo - Large Canvas Navigation
# Demonstrates infinite canvas with clustered sticky notes and smooth scrolling.
# Duration: ~120 seconds
#
# This demo creates a canvas 12x larger than terminal (960x288)
# with 4 clusters of sticky notes that can be navigated via bookmarks.
#
# Prerequisites:
# 1. my-grid must support --server mode
# 2. boxes and figlet should be installed
#
# Recording:
#   vhs demo/sticky-notes-demo.tape

Output "demo/output/my-grid-sticky-notes-demo.mp4"

Set Shell "bash"
Set FontSize 14
Set Width 1920
Set Height 1080
Set Framerate 30
Set Theme "Dracula"
Set TypingSpeed 25ms

# ============================================================================
# INTRO
# ============================================================================

Type "clear"
Enter
Sleep 300ms

Type "# my-grid: Infinite Canvas with Sticky Notes"
Enter
Sleep 1s

Type "# Canvas: 960x288 (12x terminal size)"
Enter
Type "# Clusters: Ideas, Sprint, Architecture, Notes"
Enter
Type "# Navigation: Smooth scroll + Bookmark jumps"
Enter
Sleep 1.5s

# ============================================================================
# START MY-GRID SERVER
# ============================================================================

Type "cd ~/projects/active/my-grid"
Enter
Sleep 300ms

Type "# Start my-grid with API server"
Enter
Sleep 500ms

# Start my-grid server in background
Type "python src/main.py --server &"
Enter
Sleep 2s

Type "# Server running on port 8765"
Enter
Sleep 1s

# ============================================================================
# RUN THE DEMO
# ============================================================================

Type "# Run the sticky notes demo"
Enter
Sleep 500ms

Type "python demo/sticky_notes_demo.py"
Enter

# Wait for demo to complete (drawing + navigation)
Sleep 90s

# ============================================================================
# SHOW MANUAL NAVIGATION
# ============================================================================

Type ""
Enter
Sleep 1s

Type "# Manual navigation using mygrid-ctl"
Enter
Sleep 1s

Type "# Jump to Ideas cluster (bookmark 'i')"
Enter
Type "python mygrid-ctl goto 80 50"
Enter
Sleep 2s

Type "# Jump to Architecture (bookmark 'a')"
Enter
Type "python mygrid-ctl goto 120 180"
Enter
Sleep 2s

Type "# Query current status"
Enter
Type "python mygrid-ctl status"
Enter
Sleep 2s

# ============================================================================
# CLEANUP
# ============================================================================

Type "# Stop server"
Enter
Type "pkill -f 'python src/main.py --server' 2>/dev/null"
Enter
Sleep 1s

# ============================================================================
# CLOSING
# ============================================================================

Type ""
Enter
Type "# my-grid: Infinite canvas, vim-style navigation, external API"
Enter
Sleep 2s

Type "# Features demonstrated:"
Enter
Type "#   - 960x288 canvas (12x terminal)"
Enter
Type "#   - Sticky note clusters with boxes styles"
Enter
Type "#   - Figlet ASCII art headers"
Enter
Type "#   - Smooth scrolling navigation"
Enter
Type "#   - Bookmark-based jumps"
Enter
Type "#   - External API control via mygrid-ctl"
Enter
Sleep 3s

Type "# github.com/yourusername/my-grid"
Enter
Sleep 2s
