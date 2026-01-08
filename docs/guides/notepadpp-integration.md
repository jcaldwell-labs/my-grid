# Notepad++ Integration Guide

Send text directly from Notepad++ to your my-grid canvas using the PythonScript plugin.

## Overview

This integration allows you to:

- Send selected text or entire documents to the canvas
- Send text to specific coordinates
- Create ASCII art boxes from text
- Create zones with content
- All via keyboard shortcuts or menu

## Requirements

| Component           | Version | Notes                        |
| ------------------- | ------- | ---------------------------- |
| Notepad++           | 8.0+    | Windows only                 |
| PythonScript plugin | 3.0+    | Install via Plugins Admin    |
| my-grid             | Latest  | Running with `--server` flag |

## Installation

### Step 1: Install PythonScript Plugin

1. Open Notepad++
2. Go to `Plugins > Plugins Admin`
3. Search for "PythonScript"
4. Check the checkbox and click **Install**
5. Restart Notepad++ when prompted

### Step 2: Copy Integration Scripts

The scripts are located in `scripts/notepadpp/` in the my-grid repository.

**Option A: PowerShell (recommended)**

```powershell
# Navigate to my-grid repository
cd path\to\my-grid

# Copy scripts to Notepad++ config
$dest = "$env:APPDATA\Notepad++\plugins\config\PythonScript\scripts\mygrid"
New-Item -ItemType Directory -Path $dest -Force
Copy-Item -Path "scripts\notepadpp\*" -Destination $dest -Recurse
```

**Option B: Manual copy**

1. Navigate to `scripts/notepadpp/` in the my-grid folder
2. Copy all files to:
   ```
   %APPDATA%\Notepad++\plugins\config\PythonScript\scripts\mygrid\
   ```

### Step 3: Restart Notepad++

Close and reopen Notepad++ to load the new scripts.

### Step 4: Start my-grid Server

```bash
# Linux/WSL
python mygrid.py --server

# Or with custom port
python mygrid.py --server --port 9000
```

## Usage

### Quick Send

The fastest way to send text to the canvas:

1. Select text in Notepad++ (or leave empty for entire document)
2. Go to `Plugins > PythonScript > Scripts > mygrid > commands > send_to_mygrid`
3. Text appears on the my-grid canvas at the current cursor position

### Interactive Menu

For more options:

1. Go to `Plugins > PythonScript > Scripts > mygrid > mygrid_menu`
2. A dialog appears with options:

| Choice | Action                                |
| ------ | ------------------------------------- |
| 1      | Send text to canvas at cursor         |
| 2      | Send text at specific X,Y coordinates |
| 3      | Send text wrapped in ASCII art box    |
| 4      | Create a new zone with the text       |
| 5      | Check connection to my-grid           |

### Keyboard Shortcuts

To assign keyboard shortcuts for quick access:

1. Go to `Plugins > PythonScript > Configuration`
2. Under "Menu items", click **Add** and select the script
3. Click **OK** and restart Notepad++
4. Go to `Settings > Shortcut Mapper`
5. Select the **Plugin commands** tab
6. Find your script and double-click to assign a shortcut

**Recommended shortcuts:**

| Shortcut       | Script           | Action             |
| -------------- | ---------------- | ------------------ |
| `Ctrl+Shift+G` | `send_to_mygrid` | Quick send to grid |
| `Ctrl+Shift+M` | `mygrid_menu`    | Open command menu  |

## Scripts Reference

### mygrid_send.py

Basic send functionality with console output.

```python
# Functions available:
send_to_mygrid(command)  # Send raw command
get_text()               # Get selection or document
send_text()              # Main send function
check_connection()       # Test connectivity
```

### mygrid_menu.py

Full-featured integration with interactive menu.

```python
# Available commands:
cmd_send_text()       # Send selection/document
cmd_send_at_coords()  # Send at specific position
cmd_send_as_box()     # Send as ASCII box
cmd_create_zone()     # Create zone with content
cmd_check_status()    # Show my-grid status
cmd_show_menu()       # Interactive menu
```

### commands/send_to_mygrid.py

Minimal script optimized for keyboard shortcuts. No dependencies on other scripts.

## Configuration

Edit the scripts to customize:

```python
# At the top of each script
MYGRID_HOST = 'localhost'  # my-grid server host
MYGRID_PORT = 8765         # my-grid server port
TIMEOUT = 2.0              # Connection timeout (seconds)
```

### Custom Port

If running my-grid on a different port:

1. Start my-grid: `python mygrid.py --server --port 9000`
2. Edit scripts to change `MYGRID_PORT = 9000`

## Examples

### Send Code Snippet

1. Select a code block in Notepad++
2. Press `Ctrl+Shift+G` (if shortcut configured)
3. Code appears on canvas

### Create Documentation Zone

1. Select documentation text
2. Run `mygrid_menu` > Choose **4** (Create zone)
3. Enter: `DOCS 60 30`
4. A 60x30 zone named "DOCS" is created at cursor

### Send to Specific Location

1. Select text
2. Run `mygrid_menu` > Choose **2** (Send at coordinates)
3. Enter: `100 50`
4. Text appears at position (100, 50)

## Troubleshooting

### "Connection refused" error

**Cause:** my-grid server is not running

**Solution:**

```bash
# Make sure my-grid is running with --server
python mygrid.py --server

# Verify it's listening
netstat -an | grep 8765
```

### "Nothing to send"

**Cause:** No text selected and document is empty

**Solution:** Select some text or ensure document has content

### Scripts not appearing in menu

**Cause:** Scripts not in correct folder or Notepad++ needs restart

**Solution:**

1. Verify scripts are in `%APPDATA%\Notepad++\plugins\config\PythonScript\scripts\`
2. Restart Notepad++
3. Check PythonScript console: `Plugins > PythonScript > Show Console`

### Timeout errors

**Cause:** Network latency or my-grid is busy

**Solution:**

1. Increase `TIMEOUT` value in scripts
2. Check if my-grid is responsive via direct command:
   ```bash
   echo ":status" | nc localhost 8765
   ```

## WSL Integration

If running my-grid in WSL and Notepad++ on Windows:

- TCP connections work seamlessly across the WSL boundary
- Use `localhost` as the host (not the WSL IP)
- Port 8765 is accessible from Windows when my-grid runs in WSL

```
Windows Notepad++  ──TCP:8765──>  WSL my-grid
     (client)                      (server)
```

## Advanced: Extending the Scripts

### Add Custom Command

Edit `mygrid_menu.py` to add new commands:

```python
def cmd_my_custom():
    """My custom command."""
    text, _ = get_selection_or_document()
    # Process text...
    result = client.send(':my_command ' + text)
    show_result(result, "Custom action")

# Add to menu in cmd_show_menu():
commands = {
    ...
    '6': cmd_my_custom,
}
```

### Batch Operations

Send multiple commands in sequence:

```python
def cmd_create_dashboard():
    """Create a dashboard layout."""
    client.goto(0, 0)
    client.send(':zone watch CPU 30 10 5s "top -bn1 | head -5"')
    client.goto(35, 0)
    client.send(':zone watch MEM 30 10 5s "free -h"')
    console.write("[my-grid] Dashboard created\n")
```

## See Also

- [API Scripting Guide](api-scripting.md) - Full API documentation
- [Zones Documentation](../README.md#zones-spatial-workspace) - Zone types and commands
- [Claude Code Integration](../README.md#claude-code-integration) - Other integration patterns
