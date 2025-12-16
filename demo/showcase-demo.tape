# my-grid Showcase Demo v2 - Feature-Rich Training Video
# Duration: ~260 seconds (4+ minutes)
# Features: readable figlet, real boxes borders, live typing, top output, navigation

Output "/home/be-dev-agent/projects/active/my-grid/demo/output/my-grid-showcase-v2.mp4"

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

Type "# my-grid Showcase Demo v2"
Enter
Sleep 500ms

Type "# Terminal-based ASCII canvas with vim-style navigation"
Enter
Sleep 1s

Type "cd ~/projects/active/my-grid"
Enter
Sleep 300ms

Type "python3 demo/showcase_demo.py 240"
Enter

# Wait for full demo (240s + 15s buffer)
Sleep 260s

Type "echo ''"
Enter
Type "echo 'Demo complete! Visit: github.com/jcaldwell-labs/my-grid'"
Enter
Sleep 3s
