# my-grid Quick Test
# Short 10-second test for development/debugging
# Use this to verify demo module works before full recording

Output "/home/be-dev-agent/projects/active/my-grid/demo/output/quick-test.mp4"

Set Shell "bash"
Set FontSize 14
Set Width 1920
Set Height 1080
Set Framerate 30
Set Theme "Dracula"

Type "clear"
Enter
Sleep 300ms

Type "# my-grid Quick Test (10s)"
Enter
Sleep 1s

Type "cd ~/projects/active/my-grid"
Enter
Sleep 300ms

# Run 10-second demo
Type "python -c 'import sys; sys.path.insert(0, \"src\"); from demo import run_demo; run_demo(10)'"
Enter

Sleep 12s
