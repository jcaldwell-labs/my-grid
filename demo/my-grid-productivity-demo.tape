# my-grid Productivity Canvas Demo
# Showcases my-grid as a terminal-based productivity tool for creating
# system diagrams, architecture drawings, and visual planning.
# Duration: ~80 seconds

Output "/home/be-dev-agent/projects/active/my-grid/demo/output/my-grid-productivity-demo.mp4"

Set Shell "bash"
Set FontSize 14
Set Width 1920
Set Height 1080
Set Framerate 30
Set Theme "Dracula"
Set TypingSpeed 30ms

# Intro
Type "clear"
Enter
Sleep 300ms

Type "# my-grid: Terminal-Based Productivity Canvas"
Enter
Sleep 1s

Type "# Create diagrams, flowcharts, and architecture designs"
Enter
Sleep 1s

Type "# Like Miro or Lucidchart, but in your terminal"
Enter
Sleep 1.5s

# Navigate to project
Type "cd ~/projects/active/my-grid"
Enter
Sleep 500ms

# Show quick demo command
Type "# Watch my-grid create a system architecture diagram"
Enter
Sleep 1s

# Run the auto-demo (60 second demo + 5 second buffer)
Type "./run-demo.sh"
Enter

# Wait for full demo duration
Sleep 65s

# Closing message
Type "# my-grid: Infinite canvas, vim-style navigation, bookmark system"
Enter
Sleep 2s

Type "# github.com/yourusername/my-grid"
Enter
Sleep 2s
