# Live Shader Control Tutorial

Learn to control parametric shaders in real-time using my-grid + atari-style integration.

## What You'll Build

A spatial development workspace where you can:
- **Control shaders like a musical instrument** - adjust parameters and watch instant visual feedback
- **Capture AI responses automatically** - Claude Code streams into a dedicated zone
- **Navigate in 2D space** - bookmarks let you jump between zones instantly
- **Compose tools freely** - everything connects via sockets and pipes

## 5-Minute Quick Start

### 1. Clone Repositories

```bash
cd ~/projects
git clone https://github.com/jcaldwell-labs/my-grid.git
git clone https://github.com/jcaldwell-labs/atari-style.git
```

### 2. Setup atari-style

```bash
cd ~/projects/atari-style
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Setup my-grid

```bash
cd ~/projects/my-grid
pip install -r requirements.txt
```

### 4. Launch the Workspace

```bash
python3 mygrid.py --layout ai-dev-studio --server
```

You should see a 3×2 grid of zones load:
- **DOCS** (top-left) - README viewer
- **SHELL** (top-middle) - Terminal
- **PLASMA** (top-right) - Animated plasma shader in color!
- **CONTEXT** (bottom-left) - CLAUDE.md viewer
- **CLAUDE** (bottom-middle) - AI response capture
- **LISSAJOUS** (bottom-right) - Animated curves in rainbow colors!

---

## Your First Shader Control

### Navigate to Lissajous

Press `'l` (single-quote then L) to jump to the LISSAJOUS zone.

You should see flowing rainbow curves - a **3:4 frequency ratio Lissajous curve**.

### Change to a Circle

Press `:` to enter command mode, then type:

```
shader LISSAJOUS param freq_x 1.0
```

Press Enter. **Watch the curve morph!**

Now type:
```
shader LISSAJOUS param freq_y 1.0
```

**The curve becomes a perfect circle!** (1:1 frequency ratio)

### Create a Figure-Eight

```
shader LISSAJOUS param freq_y 2.0
```

**The circle stretches into a figure-eight!** (1:2 ratio)

### Make it Complex

```
shader LISSAJOUS param freq_x 5.0
shader LISSAJOUS param freq_y 6.0
```

**Dense mesh pattern!** (5:6 ratio)

---

## Understanding Parameters

### Lissajous Curve Parameters

**freq_x** (1.0-10.0)
- Controls X-axis oscillation frequency
- Higher = more loops horizontally

**freq_y** (1.0-10.0)
- Controls Y-axis oscillation frequency
- Higher = more loops vertically

**phase** (0.0-6.28 radians)
- Phase offset between X and Y
- 0.0 = symmetric
- 1.57 (π/2) = quarter rotation
- 3.14 (π) = mirror flip

**points** (100-1000)
- Number of points to draw
- Higher = smoother curve
- Lower = faster rendering

### Classic Frequency Ratios

Try these beautiful patterns:

```
# Simple patterns
1:1 → :shader LISSAJOUS param freq_x 1.0 && param freq_y 1.0  # Circle
1:2 → freq_x 1.0, freq_y 2.0  # Figure-eight
2:3 → freq_x 2.0, freq_y 3.0  # Gentle wave

# Complex patterns
3:4 → freq_x 3.0, freq_y 4.0  # Classic beauty (default)
5:4 → freq_x 5.0, freq_y 4.0  # Five-pointed star
7:6 → freq_x 7.0, freq_y 6.0  # Dense mesh
8:9 → freq_x 8.0, freq_y 9.0  # Very complex
```

### Plasma Parameters

**freq_x** (0.01-0.3)
- Horizontal wave frequency
- Higher = tighter horizontal bands

**freq_y** (0.01-0.3)
- Vertical wave frequency
- Higher = tighter vertical bands

**freq_diag** (0.01-0.3)
- Diagonal pattern frequency
- Creates cross-hatching

**freq_radial** (0.01-0.3)
- Radial wave frequency from center
- Creates ripple effects

### Plasma Presets

```bash
# Slow, gentle waves
:shader PLASMA param freq_x 0.05
:shader PLASMA param freq_y 0.05

# Fast turbulence
:shader PLASMA param freq_x 0.2
:shader PLASMA param freq_y 0.2

# Horizontal stripes
:shader PLASMA param freq_x 0.05
:shader PLASMA param freq_y 0.2

# Radial burst
:shader PLASMA param freq_radial 0.2
```

---

## Navigation Shortcuts

**Bookmarks** (press single-quote `'` then letter):
- `'d` - Jump to DOCS
- `'r` - Jump to CONTEXT (CLAUDE.md)
- `'c` - Jump to CLAUDE (AI responses)
- `'s` - Jump to SHELL
- `'g` - Jump to GIT status
- `'p` - Jump to PLASMA shader
- `'l` - Jump to LISSAJOUS shader

**Other keys:**
- `wasd` or arrows - Move cursor
- `i` - Enter edit mode (draw on canvas)
- `:` - Enter command mode
- `Esc` - Exit current mode
- `q` - Quit (from NAV mode)

---

## Advanced Usage

### Via my-grid API

Control shaders from another terminal:

```bash
# Send shader commands
echo ":shader LISSAJOUS param freq_x 7.0" | nc localhost 8765

# Navigate zones
echo ":zone goto PLASMA" | nc localhost 8765

# Send text to canvas
echo ":text Hello World" | nc localhost 8765
```

### Direct to Control Socket

Bypass my-grid and talk directly to shader:

```bash
# Lissajous control (port 9998)
echo '{"command":"set_param","param":"freq_x","value":8.0}' | nc localhost 9998

# Plasma control (port 9997)
echo '{"command":"set_param","param":"freq_diag","value":0.15}' | nc localhost 9997
```

### Custom Layouts

Create your own layout in `~/.config/mygrid/layouts/my-layout.yaml`:

```yaml
name: my-layout
description: My custom workspace

zones:
  - name: SHADER1
    type: pty
    x: 0
    y: 0
    width: 100
    height: 50
    shell: ~/.config/mygrid/shaders/plasma.sh
    bookmark: p

  - name: SHELL
    type: pty
    x: 110
    y: 0
    width: 80
    height: 50
    bookmark: s
```

Load with: `python3 mygrid.py --layout my-layout --server`

---

## Parameter Performance Ideas

### "Instrument Mode" - Play Live

Create a sequence of parameter changes and perform them:

```bash
# Start
:shader LISSAJOUS param freq_x 1.0
:shader LISSAJOUS param freq_y 1.0

# Build complexity
:shader LISSAJOUS param freq_y 2.0
:shader LISSAJOUS param freq_x 3.0
:shader LISSAJOUS param freq_y 4.0

# Add phase movement
:shader LISSAJOUS param phase 0.0
:shader LISSAJOUS param phase 1.57
:shader LISSAJOUS param phase 3.14

# Peak complexity
:shader LISSAJOUS param freq_x 7.0
:shader LISSAJOUS param freq_y 6.0

# Resolve
:shader LISSAJOUS param freq_x 3.0
:shader LISSAJOUS param freq_y 4.0
:shader LISSAJOUS param phase 1.57
```

### Complementary Shaders

Run both shaders with complementary parameters:

```bash
# Lissajous: Simple, slow
:shader LISSAJOUS param freq_x 1.0
:shader LISSAJOUS param freq_y 2.0

# Plasma: Complex, fast
:shader PLASMA param freq_x 0.2
:shader PLASMA param freq_y 0.18
:shader PLASMA param freq_diag 0.15
```

---

## Troubleshooting

### Shaders not showing colors

**Problem:** PTY zones show monochrome instead of colors

**Solution:** Restart my-grid to load ANSI color support:
```bash
# Latest my-grid has color support
git pull
python3 mygrid.py --layout ai-dev-studio --server
```

### Parameter changes not working

**Problem:** `:shader` commands don't change the visual

**Check:**
1. Is the shader running with `--control-port`? (Check shell scripts in `~/.config/mygrid/shaders/`)
2. Are the ports listening? `netstat -ln | grep 999`
3. Try direct socket test: `echo '{"command":"set_param","param":"freq_x","value":5.0}' | nc localhost 9998`

### Shader zones empty or showing errors

**Problem:** PTY zone is blank or shows Python errors

**Solutions:**
1. Check paths in shader scripts (must use absolute paths)
2. Verify atari-style venv is activated in scripts
3. Check `cd` to atari-style directory in scripts
4. Look for errors in the zone (navigate to it and scroll)

### Claude zone not receiving responses

**Problem:** Hook not firing or CLAUDE zone empty

**Check:**
1. Settings: `~/.claude/settings.json` has Stop hook configured
2. Hook script: `ls -la ~/.claude/hooks/send-to-mygrid.py` (should be executable)
3. Port 9999 listening: `netstat -ln | grep 9999`
4. Test manually: `echo "Test" | nc localhost 9999`

---

## What's Next?

After mastering the basics:

**Explore:**
- Create custom layouts for your workflow
- Add more shader types (spiral, waves)
- Build integrations with your own tools
- Contribute new features!

**Phase 3 Ideas:**
- MIDI controller support (physical knobs for parameters!)
- Preset system (save/load shader configurations)
- Macro system (record parameter sequences)
- Composite shaders (one shader modulates another)

**Share:**
- Record your own demos
- Show off your custom layouts
- Build integrations we haven't thought of
- Contribute back to the projects!

---

## Resources

- **my-grid repo:** https://github.com/jcaldwell-labs/my-grid
- **atari-style repo:** https://github.com/jcaldwell-labs/atari-style
- **Demo video:** [Coming soon]
- **Technical deep-dive:** See SHADER-INTEGRATION-COMPLETE.md

**Questions?** Open an issue or discussion on GitHub!

---

**Go big or go home!** 🎸🚀
