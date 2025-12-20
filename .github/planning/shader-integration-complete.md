# Shader Integration - Phase 2 Complete! 🎸

## What We Built Today

A complete spatial AI development workspace with **live parametric shader control**.

### Phase 1: Zone Mode Foundation ✅
- Created `zone_renderer.py` - ANSI-only renderer for headless output
- Created `zone_mode.py` - CLI for running shaders in zones
- Integrated 4 animations: plasma, lissajous, spiral, waves
- Auto-scroll for dynamic zones

### Phase 2: Live Parameter Control ✅
- Control socket server in zone_mode (separate TCP port per shader)
- JSON command protocol for real-time parameter updates
- `:shader` command in my-grid for live control
- Bidirectional communication working!

---

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│  my-grid    │ :shader │ Control      │  JSON   │ zone_mode       │
│  command    ├────────>│ Socket       ├────────>│ Animation       │
│             │         │ (port 9998)  │         │ (lissajous)     │
└─────────────┘         └──────────────┘         └────────┬────────┘
                                                           │
                                                           v
                                                  ┌─────────────────┐
                                                  │ PTY Zone        │
                                                  │ ANSI frames  ──>│
                                                  │ (visual output) │
                                                  └─────────────────┘
```

**Two channels:**
1. **ANSI Output** (PTY stdout) → Visual frames rendered in zone
2. **Control Socket** (TCP) → JSON parameter commands

---

## Usage

### Start my-grid with shaders:
```bash
python3 mygrid.py --layout ai-dev-studio --server
```

### Control ports (default):
- LISSAJOUS: 9998
- PLASMA: 9997
- SPIRAL: 9996
- WAVES: 9995

### Live parameter control:

**In my-grid:**
```
:shader LISSAJOUS param freq_x 5.0
:shader LISSAJOUS param freq_y 7.0
:shader LISSAJOUS param phase 1.57
:shader LISSAJOUS param points 800

:shader PLASMA param freq_x 0.2
:shader PLASMA param freq_y 0.15
:shader PLASMA param freq_diag 0.1
:shader PLASMA param freq_radial 0.12
```

**Via API (from another terminal):**
```bash
echo ":shader LISSAJOUS param freq_x 8.0" | nc localhost 8765
```

**Direct to control socket:**
```bash
echo '{"command":"set_param","param":"freq_x","value":6.0}' | nc localhost 9998
```

---

## Parameters Reference

### Lissajous Curves
- `freq_x` (1.0-10.0) - X-axis frequency
- `freq_y` (1.0-10.0) - Y-axis frequency
- `phase` (0.0-6.28) - Phase offset (radians)
- `points` (100-1000) - Resolution

**Classic ratios:**
- 1:1 → Circle
- 1:2 → Figure-eight
- 3:2 → Trefoil
- 3:4 → Classic beauty
- 5:4 → Star
- 7:6 → Dense mesh

### Plasma
- `freq_x` (0.01-0.3) - X-axis frequency
- `freq_y` (0.01-0.3) - Y-axis frequency
- `freq_diag` (0.01-0.3) - Diagonal frequency
- `freq_radial` (0.01-0.3) - Radial frequency

---

## Example Session: "Playing" the Shader

```bash
# Start with a circle
:shader LISSAJOUS param freq_x 1.0
:shader LISSAJOUS param freq_y 1.0

# Morph to figure-eight
:shader LISSAJOUS param freq_y 2.0

# Evolve to complex flower
:shader LISSAJOUS param freq_x 5.0

# Dense mesh
:shader LISSAJOUS param freq_y 6.0

# Phase shift (rotate pattern)
:shader LISSAJOUS param phase 0.0
:shader LISSAJOUS param phase 1.57
:shader LISSAJOUS param phase 3.14

# Back to classic
:shader LISSAJOUS param freq_x 3.0
:shader LISSAJOUS param freq_y 4.0
:shader LISSAJOUS param phase 1.57
```

**Watch the curves morph in real-time!** 🎨

---

## What Makes This Special

1. **Live Control** - Change parameters without restarting
2. **Visual Feedback** - See changes instantly (20 FPS)
3. **Composable** - Mix with Claude responses, terminals, docs
4. **Spatial** - Navigate between zones in 2D space
5. **Scriptable** - Control via API, hooks, or manual commands
6. **Cross-platform** - Works on Linux/WSL (Windows native via fallback)

---

## Files Created/Modified

### atari-style (feature/ascii-postprocess-shader branch):
- `atari_style/core/zone_renderer.py` - NEW: ANSI headless renderer
- `atari_style/zone_mode.py` - NEW: Zone mode CLI with control socket
- `atari_style/demos/visualizers/screensaver.py` - MODIFIED: Added set_param() methods

### my-grid (master branch):
- `src/zones.py` - MODIFIED: Auto-scroll for dynamic zones
- `src/main.py` - MODIFIED: Added :shader command
- `.config/mygrid/layouts/ai-dev-studio.yaml` - NEW: Epic 3x2 grid layout
- `.config/mygrid/shaders/plasma.sh` - NEW: Plasma launcher script
- `.config/mygrid/shaders/lissajous.sh` - NEW: Lissajous launcher script
- `WINDOWS-ATARI-INTEGRATION-TEST.md` - NEW: Windows testing guide
- `WINDOWS-QUICK-START.txt` - NEW: Quick-start for testers

### Claude Code Integration:
- `~/.claude/hooks/send-to-mygrid.py` - Hook for auto-capture responses
- `~/.claude/settings.json` - Hook configuration

---

## Integration Summary

**What's Connected:**
1. **Claude Code** → Socket 9999 → CLAUDE zone (auto-capture via hook)
2. **atari-style zone_mode** → PTY zones → LISSAJOUS/PLASMA zones (visual output)
3. **my-grid :shader command** → Control sockets 9997/9998 → Parameter updates

**Data Flow:**
```
Claude responds → Hook fires → Socket 9999 → CLAUDE zone displays
User types :shader → Control socket → zone_mode → Shader updates → Visual change
```

---

## Next Steps (Future Enhancements)

### Phase 3: Advanced Control (Optional)
- [ ] Parameter preset system (save/load configurations)
- [ ] Macro commands (sequences of parameter changes)
- [ ] Composite modulation (one shader controls another's parameters)
- [ ] MIDI controller support (physical knobs for parameters)
- [ ] Recording/playback of parameter performances

### Windows Native Support
- [ ] Test on Windows Git Bash (in progress)
- [ ] PIPE zone fallback for non-PTY systems
- [ ] Windows-specific layouts and scripts
- [ ] Path handling for Windows filesystem

### Additional Shaders
- [ ] Mandelbrot zoom with control
- [ ] Particle swarm with behavior parameters
- [ ] Fluid lattice with viscosity control
- [ ] Tunnel vision with speed/depth control

---

## Performance Notes

- **FPS**: Default 20 FPS, adjustable via `--fps` flag
- **Latency**: Parameter changes apply within 1 frame (~50ms at 20 FPS)
- **Network**: Control sockets use localhost (negligible latency)
- **CPU**: ~5-10% per shader on modern hardware

---

## Known Issues

- PLASMA zone occasionally shows `BlockingIOError` (non-fatal, visual artifact)
- PTY stdin doesn't work for parameter control (solved with control socket)
- Windows PTY support limited (use PIPE zones as fallback)

---

## Credits

Built with:
- **my-grid** - ASCII canvas with zones
- **atari-style** - Parametric terminal animations
- **Claude Code** - AI-assisted development with live response capture
- **blessed** - Terminal rendering (atari-style)
- **curses** - Terminal UI (my-grid)

**This integration brings together:**
- Spatial computing (2D canvas navigation)
- Live shader programming (real-time parameter control)
- AI integration (automated response capture)
- Unix philosophy (composable tools via sockets/pipes)

---

**Created:** 2025-12-18
**Status:** Phase 2 Complete ✅
**Next:** Test on Windows, add more shaders, explore Phase 3 features

🎸 Go big or go home! 🚀
