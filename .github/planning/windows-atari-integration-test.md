# Windows Git Bash - Atari-Style Integration Testing Guide

## Overview

Test the my-grid + atari-style shader integration on Windows using Git Bash.

**What we're testing:**
- Zone mode animations running in my-grid zones
- ANSI color output in Windows terminal
- Socket zones for Claude Code integration
- Live shader visualizations (plasma, lissajous, etc.)

---

## Prerequisites

### 1. Install Python (Windows)
```bash
# Check if Python is installed
python --version  # Should be 3.8+

# If not installed, download from:
# https://www.python.org/downloads/
```

### 2. Clone Repositories

```bash
# Navigate to your projects directory
cd ~/projects  # or wherever you keep projects

# Clone my-grid
git clone <my-grid-repo-url> my-grid
cd my-grid

# Clone atari-style
cd ~/projects
git clone <atari-style-repo-url> atari-style
```

### 3. Setup atari-style

```bash
cd ~/projects/atari-style

# Create virtual environment (Windows)
python -m venv venv

# Activate venv (Git Bash)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Test zone mode works
python -m atari_style.zone_mode plasma --width 40 --height 20 --fps 5
# Press Ctrl+C to stop after you see colorful output
```

### 4. Setup my-grid

```bash
cd ~/projects/my-grid

# Install dependencies
pip install -r requirements.txt

# Test my-grid works
python mygrid.py
# Press 'q' to quit
```

---

## Windows-Specific Shader Scripts

Create shader wrapper scripts for Windows:

### Create: `~/.config/mygrid/shaders/plasma.sh`
```bash
#!/bin/bash
cd /c/Users/<YOUR_USERNAME>/projects/atari-style
exec ./venv/Scripts/python -m atari_style.zone_mode plasma --width 83 --height 43 --fps 20
```

### Create: `~/.config/mygrid/shaders/lissajous.sh`
```bash
#!/bin/bash
cd /c/Users/<YOUR_USERNAME>/projects/atari-style
exec ./venv/Scripts/python -m atari_style.zone_mode lissajous --width 83 --height 43 --fps 20
```

**Make them executable:**
```bash
chmod +x ~/.config/mygrid/shaders/*.sh
```

---

## Testing Plan

### Test 1: Zone Mode Standalone

Test that zone mode outputs ANSI frames correctly:

```bash
cd ~/projects/atari-style
source venv/Scripts/activate

# Test plasma (should show colorful animated plasma)
python -m atari_style.zone_mode plasma --width 60 --height 20 --fps 10

# Test lissajous (should show animated curves)
python -m atari_style.zone_mode lissajous --width 60 --height 20 --fps 10

# Test other animations
python -m atari_style.zone_mode spiral --width 60 --height 20 --fps 10
python -m atari_style.zone_mode waves --width 60 --height 20 --fps 10
```

**Expected:** You should see ANSI-colored animated frames outputting to the terminal.

---

### Test 2: Socket Zone (Claude Integration)

**Step 1:** Start my-grid with server mode
```bash
cd ~/projects/my-grid
python mygrid.py --server --port 8765
```

**Step 2:** In another Git Bash terminal, test the API:
```bash
# Send a test command
echo ":text Hello from Windows!" | nc localhost 8765
```

**Step 3:** Test socket zone for Claude responses:
```bash
# In my-grid, create socket zone
:zone socket CLAUDE 100 40 9999

# In another terminal, send test message
echo "Test message from Git Bash" | nc localhost 9999
```

**Expected:** Message should appear in the CLAUDE zone.

---

### Test 3: Shader Zones (Critical Test)

**Important Note:** PTY zones may not work on native Windows. We have two approaches:

#### Approach A: Try PTY (May Work in Git Bash)

```bash
# In my-grid:
:zone pty PLASMA 80 40 /c/Users/<YOUR_USERNAME>/.config/mygrid/shaders/plasma.sh
```

**If this doesn't work** (shows error or blank), PTY is not supported. Try Approach B.

#### Approach B: PIPE Zones (Windows Fallback)

PTY zones don't work well on Windows. Instead, we can use a continuously running script with PIPE zones:

**Create: `~/projects/my-grid/shaders/plasma-loop.sh`**
```bash
#!/bin/bash
cd /c/Users/<YOUR_USERNAME>/projects/atari-style
source venv/Scripts/activate

while true; do
    python -m atari_style.zone_mode plasma --width 78 --height 38 --fps 10
    sleep 0.1
done
```

**In my-grid:**
```bash
# Make executable
chmod +x ~/projects/my-grid/shaders/plasma-loop.sh

# Create PIPE zone
:zone pipe PLASMA 80 40 bash ~/projects/my-grid/shaders/plasma-loop.sh
```

---

### Test 4: Full Layout

**Create: `~/.config/mygrid/layouts/windows-dev.yaml`**
```yaml
name: windows-dev
description: Windows development workspace with shaders

cursor:
  x: 10
  y: 5

zones:
  # Left: Documentation
  - name: DOCS
    type: pager
    x: 0
    y: 0
    width: 80
    height: 40
    file_path: ./README.md
    renderer: auto
    bookmark: d

  # Middle: Claude responses
  - name: CLAUDE
    type: socket
    x: 85
    y: 0
    width: 80
    height: 40
    port: 9999
    bookmark: c

  # Right: Shader (create manually after loading)
  # Use :zone pipe PLASMA 80 40 bash ~/projects/my-grid/shaders/plasma-loop.sh

  # Bottom: Shell
  - name: SHELL
    type: pty
    x: 0
    y: 45
    width: 160
    height: 30
    bookmark: s
```

**Load it:**
```bash
python mygrid.py --layout windows-dev --server
```

---

## Expected Results Checklist

- [ ] Zone mode outputs colorful ANSI frames
- [ ] Socket zone receives messages from nc
- [ ] Shader animations display in zones (PTY or PIPE)
- [ ] Claude Code hook integration works (if testing with Claude Code)
- [ ] Layout loads without zone overlaps
- [ ] Navigation bookmarks work (`'c`, `'d`, etc.)
- [ ] Server API responds to commands

---

## Troubleshooting

### Issue: "No module named 'blessed'"
```bash
cd ~/projects/atari-style
source venv/Scripts/activate
pip install -r requirements.txt
```

### Issue: "nc command not found"
Git Bash should include nc. If not:
```bash
# Use Python alternative
echo "test" | python -c "import socket; s=socket.socket(); s.connect(('localhost', 9999)); s.send(b'test\n')"
```

### Issue: PTY zones show error
Windows doesn't fully support PTY. Use PIPE zones instead (Approach B above).

### Issue: Shaders don't animate
- Check venv activation: `source venv/Scripts/activate`
- Test zone mode standalone first
- Check Windows paths (use `/c/Users/...` format in Git Bash)
- Try reducing FPS: `--fps 5` instead of `--fps 20`

### Issue: Colors don't display
- Check Windows Terminal supports ANSI colors
- Try Windows Terminal instead of Git Bash default
- Test: `echo -e "\033[31mRed Text\033[0m"`

---

## Success Criteria

✅ **Minimum Success:**
- Zone mode runs and outputs ANSI frames
- Socket zones receive messages
- Basic layout loads

✅ **Full Success:**
- Live shader animations in zones
- Claude Code integration working
- Multiple zones with proper spacing
- All 4 shader types working (plasma, lissajous, spiral, waves)

---

## Reporting Results

After testing, report:
1. Which tests passed/failed
2. Windows version
3. Git Bash version (`bash --version`)
4. Python version (`python --version`)
5. Screenshots of working shaders (if successful)
6. Any error messages encountered

---

## Next Steps After Testing

If successful:
- Document Windows-specific setup in main README
- Create Windows-optimized layouts
- Add Windows CI testing
- Create `.bat` wrapper scripts for easier Windows usage

If issues found:
- Identify specific Windows limitations
- Create fallback approaches (PIPE vs PTY)
- Document workarounds
- Consider Windows-specific zone types
