# my-grid Educational Demo - Massive Canvas Feature Tour
#
# Demonstrates the infinite canvas concept with a 1600x480 canvas
# (20x typical terminal size) featuring 8 educational zones.
#
# Duration: ~150 seconds
# Canvas: 1600x480 (20x terminal)
#
# Zones:
#   w - Welcome (giant figlet banner)
#   d - Drawing primitives
#   n - Navigation & bookmarks
#   m - Editor modes
#   a - Architecture diagrams
#   p - Productivity (TODO, notes)
#   i - API external control
#   4 - Easter egg at (1337, 420)
#
# Recording:
#   cd ~/projects/active/my-grid
#   export PATH="$HOME/go/bin:$PATH"
#   vhs demo/educational-demo.tape

Output "/home/be-dev-agent/projects/active/my-grid/demo/output/my-grid-educational-demo.mp4"

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

Type "# my-grid: Educational Demo - Infinite Canvas"
Enter
Sleep 1s

Type "# Canvas size: 1600x480 (20x terminal)"
Enter
Type "# 8 demo zones with figlet banners"
Enter
Type "# Smooth scrolling navigation"
Enter
Sleep 1.5s

# ============================================================================
# START SERVER
# ============================================================================

Type "cd ~/projects/active/my-grid"
Enter
Sleep 300ms

Type "# Start my-grid with API server"
Enter
Sleep 500ms

Type "python3 src/main.py --server &"
Enter
Sleep 2s

Type "# Server running - now run the educational demo"
Enter
Sleep 1s

# ============================================================================
# RUN EDUCATIONAL DEMO
# ============================================================================

Type "python3 demo/educational_demo.py"
Enter

# Wait for demo to complete
# Drawing: ~30s, Tour: ~90s, Total: ~120s
Sleep 125s

# ============================================================================
# INTERACTIVE EXPLORATION
# ============================================================================

Type ""
Enter
Sleep 1s

Type "# Now let's explore manually using mygrid-ctl"
Enter
Sleep 1s

Type "# Jump to the giant banner"
Enter
Type "python3 mygrid-ctl goto 400 25"
Enter
Sleep 1.5s

Type "# Pan across the banner to see its full width"
Enter
Type "python3 mygrid-ctl goto 600 25"
Enter
Sleep 1.5s

Type "# Jump to Architecture zone using bookmark 'a'"
Enter
Type "python3 mygrid-ctl goto 100 310"
Enter
Sleep 1.5s

Type "# Jump to the Easter Egg at (1337, 420)"
Enter
Type "python3 mygrid-ctl goto 1337 420"
Enter
Sleep 2s

Type "# Query status"
Enter
Type "python3 mygrid-ctl status"
Enter
Sleep 2s

# ============================================================================
# CLEANUP
# ============================================================================

Type "# Stop server"
Enter
Type "pkill -f 'python3 src/main.py --server' 2>/dev/null"
Enter
Sleep 1s

# ============================================================================
# CLOSING
# ============================================================================

Type ""
Enter
Type "# my-grid: Infinite Canvas ASCII Editor"
Enter
Sleep 1s

Type "# Features demonstrated:"
Enter
Type "#   - 1600x480 canvas (20x terminal size)"
Enter
Type "#   - Giant figlet banners requiring pan to view"
Enter
Type "#   - 8 educational zones with bookmarks"
Enter
Type "#   - Drawing, navigation, modes, architecture"
Enter
Type "#   - External API control via mygrid-ctl"
Enter
Type "#   - Easter egg at (1337, 420): The Answer is 42"
Enter
Sleep 3s

Type "# github.com/yourusername/my-grid"
Enter
Sleep 2s
