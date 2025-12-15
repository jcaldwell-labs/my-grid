# my-grid Visual Auto-Demo
# Description: Records actual curses UI with programmed actions
# Duration: ~75 seconds

Output "/home/be-dev-agent/projects/active/my-grid/demo/output/my-grid-visual-demo.mp4"

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

Type "# my-grid: Infinite ASCII Canvas Editor"
Enter
Sleep 1s

Type "# Visual demo with programmed actions for VHS recording"
Enter
Sleep 1s

Type "cd ~/projects/active/my-grid"
Enter
Sleep 300ms

Type "python3 demo/visual_auto_demo.py 75"
Enter

# Wait for full demo (75s + 10s buffer)
Sleep 85s

Type "echo 'Demo complete! Check github.com/jcaldwell/my-grid'"
Enter
Sleep 2s
