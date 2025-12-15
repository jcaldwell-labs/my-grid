# my-grid [Demo Name]
# Description: [What this demo showcases]
# Duration: ~[N] seconds

Output "/home/be-dev-agent/projects/active/my-grid/demo/output/[demo-name].mp4"

Set Shell "bash"
Set FontSize 14
Set Width 1920
Set Height 1080
Set Framerate 30
Set Theme "Dracula"
Set TypingSpeed 30ms

# Introduction
Type "clear"
Enter
Sleep 300ms

Type "# my-grid: [Feature Description]"
Enter
Sleep 1s

Type "# [Tagline or use case]"
Enter
Sleep 1.5s

# Navigate to project
Type "cd ~/projects/active/my-grid"
Enter
Sleep 500ms

# Run demo
Type "python -c 'import sys; sys.path.insert(0, \"src\"); from demo import run_demo; run_demo([duration])'"
Enter

# Wait for demo + buffer
Sleep [duration + 5]s

# Closing
Type "# github.com/yourusername/my-grid"
Enter
Sleep 2s
