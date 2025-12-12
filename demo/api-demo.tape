# my-grid API Demo - External Control via mygrid-ctl
# Demonstrates programmatic canvas manipulation from external scripts.
# Duration: ~90 seconds
#
# Prerequisites:
# 1. my-grid must be running with --server flag
# 2. mygrid-ctl must be in PATH or demo directory
#
# Recording:
#   vhs demo/api-demo.tape

Output "demo/output/my-grid-api-demo.mp4"

Set Shell "bash"
Set FontSize 14
Set Width 1920
Set Height 1080
Set Framerate 30
Set Theme "Dracula"
Set TypingSpeed 30ms

# Start my-grid with server in background (left terminal)
# For VHS, we use tmux or split setup
# Simpler: show the commands, then the results

Type "clear"
Enter
Sleep 300ms

Type "# my-grid API Demo - External Control"
Enter
Sleep 1s

Type "# First, start my-grid with the --server flag"
Enter
Sleep 500ms

# Navigate to project
Type "cd ~/projects/active/my-grid"
Enter
Sleep 500ms

# Start my-grid in background
Type "# Terminal 1: Start my-grid server (in background for demo)"
Enter
Sleep 500ms

Type "python src/main.py --server &"
Enter
Sleep 2s

Type "# Server started on port 8765"
Enter
Sleep 1s

# Show mygrid-ctl help
Type "# Terminal 2: Use mygrid-ctl to control the canvas"
Enter
Sleep 1s

Type "python mygrid-ctl --help | head -20"
Enter
Sleep 2s

# Basic commands
Type "# Send drawing commands to my-grid"
Enter
Sleep 1s

Type "python mygrid-ctl clear"
Enter
Sleep 500ms

Type "python mygrid-ctl goto 10 5"
Enter
Sleep 500ms

Type 'python mygrid-ctl text "Hello from mygrid-ctl!"'
Enter
Sleep 1s

Type "python mygrid-ctl goto 10 8"
Enter
Sleep 300ms

Type "python mygrid-ctl rect 25 5"
Enter
Sleep 1s

# Query status
Type "# Query current status"
Enter
Sleep 500ms

Type "python mygrid-ctl status"
Enter
Sleep 2s

# Pipe content
Type "# Pipe command output to canvas"
Enter
Sleep 1s

Type "ls -la | head -5 | python mygrid-ctl region 10 15"
Enter
Sleep 2s

# External tools integration (if available)
Type "# Integration with external tools (boxes)"
Enter
Sleep 1s

Type 'echo "API Gateway" | python mygrid-ctl pipe 50 5 --filter "boxes -d stone" 2>/dev/null || echo "boxes not installed"'
Enter
Sleep 2s

# Batch commands
Type "# Batch command execution"
Enter
Sleep 1s

Type "cat << 'EOF' | python mygrid-ctl batch -"
Enter
Type ":goto 10 25"
Enter
Type ":text Batch Demo"
Enter
Type ":goto 10 27"
Enter
Type ":rect 15 3"
Enter
Type "EOF"
Enter
Sleep 2s

# Run the full API demo
Type "# Run the full API demo script"
Enter
Sleep 1s

Type "python demo/api_demo.py --delay 0.1"
Enter
Sleep 15s

# Final status
Type "python mygrid-ctl status"
Enter
Sleep 2s

# Cleanup
Type "# Cleanup: stop the server"
Enter
Sleep 500ms

Type "pkill -f 'python src/main.py --server' 2>/dev/null || true"
Enter
Sleep 1s

# Closing
Type "# my-grid: Infinite canvas + External API = Powerful automation"
Enter
Sleep 2s

Type "# github.com/yourusername/my-grid"
Enter
Sleep 2s
