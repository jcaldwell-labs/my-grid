# my-grid Spatial Workspace Demo
# Description: Records Sprint 1-5 features - zones, dynamic content, layouts, external connectors
# Duration: ~120 seconds

Output "/home/be-dev-agent/projects/active/my-grid/demo/output/my-grid-spatial-workspace.mp4"

Set Shell "bash"
Set FontSize 16
Set Width 1920
Set Height 1080
Set Framerate 30
Set Theme "Dracula"
Set TypingSpeed 30ms

Type "clear"
Enter
Sleep 300ms

Type "# my-grid: Spatial Workspace Demo"
Enter
Sleep 1s

Type "# Sprint 1-5: Zones, Dynamic Content, Layouts, External Connectors"
Enter
Sleep 1s

Type "cd ~/projects/active/my-grid"
Enter
Sleep 300ms

Type "python3 demo/spatial_workspace_demo.py 120"
Enter

# Wait for full demo (120s + 10s buffer)
Sleep 135s

Type "echo 'Demo complete! github.com/jcaldwell-labs/my-grid'"
Enter
Sleep 2s
