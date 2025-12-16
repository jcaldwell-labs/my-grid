# my-grid Showcase Demo - Feature-Rich Training Video
# Duration: ~200 seconds (3+ minutes)
# Features: figlet banners, live data, boxes styling, grid config, zones

Output "/home/be-dev-agent/projects/active/my-grid/demo/output/my-grid-showcase.mp4"

Set Shell "bash"
Set FontSize 14
Set Width 1920
Set Height 1080
Set Framerate 30
Set Theme "Dracula"
Set TypingSpeed 30ms

Type "clear"
Enter
Sleep 300ms

Type "# my-grid Showcase Demo"
Enter
Sleep 500ms

Type "# A comprehensive tour of spatial workspace features"
Enter
Sleep 1s

Type "cd ~/projects/active/my-grid"
Enter
Sleep 300ms

Type "python3 demo/showcase_demo.py 180"
Enter

# Wait for full demo (180s + 15s buffer)
Sleep 200s

Type "echo ''"
Enter
Type "echo 'Demo complete! Visit: github.com/jcaldwell-labs/my-grid'"
Enter
Sleep 3s
