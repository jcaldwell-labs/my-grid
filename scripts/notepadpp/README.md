# Notepad++ Integration for my-grid

Send text from Notepad++ directly to your my-grid canvas using the PythonScript plugin.

## Requirements

- **Notepad++** (Windows)
- **PythonScript plugin** - Install via `Plugins > Plugins Admin > PythonScript`
- **my-grid** running with `--server` flag

## Installation

1. **Install PythonScript plugin:**
   - Open Notepad++
   - Go to `Plugins > Plugins Admin`
   - Search for "PythonScript"
   - Check the box and click Install

2. **Copy scripts to Notepad++:**

   ```
   Copy contents of this folder to:
   %APPDATA%\Notepad++\plugins\config\PythonScript\scripts\
   ```

   Or in PowerShell:

   ```powershell
   Copy-Item -Path ".\*" -Destination "$env:APPDATA\Notepad++\plugins\config\PythonScript\scripts\mygrid\" -Recurse
   ```

3. **Restart Notepad++**

4. **Start my-grid with server:**
   ```bash
   python mygrid.py --server
   ```

## Usage

### Quick Send (Recommended)

1. Select text in Notepad++ (or leave empty for entire document)
2. Go to `Plugins > PythonScript > Scripts > commands > send_to_mygrid`
3. Text appears on my-grid canvas!

### Interactive Menu

1. Go to `Plugins > PythonScript > Scripts > mygrid_menu`
2. Choose from:
   - **1** - Send text to canvas
   - **2** - Send at specific coordinates
   - **3** - Send as ASCII box
   - **4** - Create a zone
   - **5** - Check connection

## Keyboard Shortcuts

To bind a script to a keyboard shortcut:

1. Go to `Plugins > PythonScript > Configuration`
2. Under "Menu items", add the script you want
3. Restart Notepad++
4. Go to `Settings > Shortcut Mapper > Plugin commands`
5. Find your script and assign a shortcut (e.g., `Ctrl+Shift+G`)

### Suggested Shortcuts

| Shortcut       | Script         | Action                 |
| -------------- | -------------- | ---------------------- |
| `Ctrl+Shift+G` | send_to_mygrid | Send selection to grid |
| `Ctrl+Shift+M` | mygrid_menu    | Open command menu      |

## Scripts Included

| Script                       | Description                             |
| ---------------------------- | --------------------------------------- |
| `mygrid_send.py`             | Basic send functionality                |
| `mygrid_menu.py`             | Interactive menu with multiple commands |
| `commands/send_to_mygrid.py` | Minimal script for quick sending        |

## Configuration

Edit the scripts to change:

- `MYGRID_HOST` - default: `localhost`
- `MYGRID_PORT` - default: `8765`
- `TIMEOUT` - connection timeout in seconds

## Troubleshooting

**"Connection refused" error:**

- Make sure my-grid is running with `--server` flag
- Check the port matches (default: 8765)

**"Nothing to send":**

- Select some text, or ensure document isn't empty

**Scripts not appearing:**

- Verify scripts are in the correct folder
- Restart Notepad++
- Check PythonScript console for errors (`Plugins > PythonScript > Show Console`)

## WSL/Linux Note

If running my-grid in WSL and Notepad++ on Windows, the TCP connection works across the WSL boundary - just use `localhost:8765`.
