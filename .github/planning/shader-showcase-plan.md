# Shader Integration Showcase Plan

## The Story

**"Live Parametric Shader Control in Spatial Canvas Zones"**

This integration brings together three powerful concepts:
1. **Spatial Computing** (my-grid's infinite 2D canvas)
2. **Parametric Visualization** (atari-style's animated shaders)
3. **AI Integration** (Claude Code auto-capture)

Result: A terminal-based development workspace where you can control live shaders like a musical instrument while AI responses stream in automatically.

---

## Content Plan

### 1. Hero Demo Video (60-90 seconds)

**Script:**

**[0:00-0:10] Opening Shot**
- Full ai-dev-studio layout visible
- All 6 zones active: DOCS, SHELL, GIT, CLAUDE, PLASMA, LISSAJOUS
- Title overlay: "Spatial AI Workspace + Live Shader Control"

**[0:10-0:25] Introduce the Workspace**
- Zoom/pan to show each zone briefly
- Narration: "my-grid creates a spatial development workspace..."
- Highlight: CLAUDE zone showing AI responses with auto-scroll
- Highlight: PLASMA and LISSAJOUS zones animating in color

**[0:25-0:50] Live Parameter Control Demo**
- Type commands in SHELL zone:
  ```
  :shader LISSAJOUS param freq_x 1.0
  :shader LISSAJOUS param freq_y 1.0
  ```
- Watch curve morph to circle (LIVE)
- Continue with sequence:
  ```
  :shader LISSAJOUS param freq_y 2.0  # Figure-eight
  :shader LISSAJOUS param freq_x 5.0  # Flower
  :shader LISSAJOUS param freq_y 6.0  # Dense mesh
  ```
- Watch transformation in real-time
- Narration: "Change parameters live... watch the shader respond instantly..."

**[0:50-1:05] Show PLASMA Control**
- Switch to plasma:
  ```
  :shader PLASMA param freq_x 0.05   # Slow waves
  :shader PLASMA param freq_x 0.2    # Fast turbulence
  :shader PLASMA param freq_diag 0.15 # Diagonal flow
  ```
- Show colorful gradients morphing

**[1:05-1:20] Navigation & Integration**
- Quick bookmark navigation: `'c` `'p` `'l` `'s`
- Show Claude response appearing in CLAUDE zone (hook firing)
- Show git status updating
- Narration: "Navigate in 2D space... AI responses auto-capture... live system monitoring..."

**[1:20-1:30] Closing**
- Pull back to show full workspace
- Text overlay:
  ```
  my-grid + atari-style + Claude Code
  Spatial AI Development Workspace
  github.com/jcaldwell-labs/my-grid
  ```

---

### 2. Technical Deep Dive Video (5-7 minutes)

**Sections:**

**Part 1: Architecture (1:30)**
- Show the 3-layer communication:
  - Port 9999: Claude responses (socket zone)
  - Port 9998/9997: Shader control (control sockets)
  - PTY zones: Visual output (ANSI frames)
- Diagram on screen
- Code walkthrough

**Part 2: Zone Types (2:00)**
- SOCKET zones (Claude integration)
- PTY zones (shaders, terminals)
- PAGER zones (documentation with colors)
- WATCH zones (git status)
- STATIC zones (notes)
- Show each with examples

**Part 3: Live Control Protocol (1:30)**
- Show JSON command structure
- Explain bidirectional communication
- Demo via API: `echo '...' | nc localhost 9998`
- Show :shader command syntax

**Part 4: Building Your Own (2:00)**
- How to create custom layouts
- How to add new shader types
- How to integrate with other tools
- Configuration files walkthrough

---

### 3. Quick Start Guide (Written + GIF)

**File:** `QUICK-START-SHADER-INTEGRATION.md`

**Sections:**
1. Prerequisites (my-grid, atari-style repos)
2. 5-Minute Setup
   - Clone repos
   - Install dependencies
   - Start workspace: `python3 mygrid.py --layout ai-dev-studio --server`
3. First Commands
   - Navigate: `'c` `'p` `'l`
   - Control shader: `:shader LISSAJOUS param freq_x 7.0`
4. Animated GIF showing the full flow

---

### 4. Screenshot Gallery

**Captures needed:**

1. **Full workspace overview**
   - All 6 zones visible
   - Shaders animating in color
   - Claude responses in CLAUDE zone

2. **Plasma shader close-up**
   - Colorful gradient waves
   - Show the beauty of the plasma effect

3. **Lissajous curves**
   - Different ratios (1:1, 1:2, 3:4, 5:6, 7:6)
   - Show the variety of patterns

4. **Live control in action**
   - Terminal showing `:shader` command
   - Shader zone showing the result

5. **Multi-zone navigation**
   - Show bookmark navigation (`'c` jumps to CLAUDE, etc.)

6. **Claude integration**
   - Hook firing, response appearing with timestamp
   - Separator lines visible

---

### 5. README Updates

**For my-grid README:**

Add new section: **"Shader Integration Example"**
```markdown
## Live Shader Control

Integrate parametric visualizations with real-time control:

![Shader Integration Demo](docs/images/shader-demo.gif)

See [SHADER-INTEGRATION-COMPLETE.md](SHADER-INTEGRATION-COMPLETE.md) for details.
```

**For atari-style README:**

Add new section: **"Zone Mode - Embedding in Other Tools"**
```markdown
## Zone Mode

Run animations in headless mode for embedding in other applications:

bash
python -m atari_style.zone_mode plasma --width 80 --height 40 --fps 20 --control-port 9997


Live parameter control via TCP socket. See integration examples in my-grid.
```

---

### 6. Social Media Content

**Twitter/X Thread (6 tweets):**

1. 🎸 Built something wild: Terminal-based spatial AI workspace with LIVE shader control

   Watch Lissajous curves morph in real-time as I adjust parameters - like playing a visual instrument

   [Video or GIF]

2. The stack:
   - my-grid: ASCII canvas with zones (infinite 2D space)
   - atari-style: Parametric shaders (plasma, curves, etc.)
   - Claude Code: AI responses auto-streaming

   All in the terminal. All composable via sockets/pipes.

3. Type a command, watch the shader transform instantly:

   :shader LISSAJOUS param freq_x 7.0

   No restart. No lag. Just pure parametric beauty responding at 20 FPS.

   [GIF of transformation]

4. The architecture is clean:
   - Socket zones for AI output (port 9999)
   - PTY zones for shader display
   - Control sockets for parameter updates (9997/9998)
   - Hook system auto-captures Claude responses

5. Why it matters:
   - Spatial computing in the terminal
   - Live-programmable visuals
   - AI-assisted development with persistent context
   - All Unix-composable (pipes, sockets, text streams)

6. Open source and ready to build on:
   - github.com/jcaldwell-labs/my-grid
   - github.com/jcaldwell-labs/atari-style

   Phase 3 ideas: MIDI control, preset system, composite modulation

   Go big or go home 🚀

**LinkedIn Post:**

Professional version highlighting:
- Technical achievement (bidirectional PTY control)
- AI integration patterns
- Terminal as a serious development medium
- Link to repos and demo video

**Dev.to/Hashnode Article:**

**Title:** "Building a Spatial AI Workspace: Live Shader Control in Terminal Zones"

Sections:
- The Vision (spatial computing meets parametric art)
- Architecture (technical deep dive)
- Implementation (code walkthrough)
- Results (demo + screenshots)
- What's Next (Phase 3 features)

---

### 7. Video Recording Tools

**Use VHS (tape files):**

Create tapes for:
- `hero-demo.tape` - 60-90 second showcase
- `parameter-control.tape` - Focus on live control
- `claude-integration.tape` - AI response capture demo
- `navigation.tape` - Zone navigation and bookmarks

**Location:** `~/projects/jcaldwell-labs/media/tapes/my-grid-shader-integration/`

---

### 8. Documentation Artifacts

**Files to create:**

1. `SHADER-INTEGRATION-TUTORIAL.md` - Step-by-step tutorial
2. `PARAMETER-REFERENCE.md` - All shader parameters documented
3. `LAYOUT-GUIDE.md` - How to create custom layouts
4. `INTEGRATION-PATTERNS.md` - General patterns for tool integration
5. `TROUBLESHOOTING.md` - Common issues and solutions

---

## Priority Order

**Immediate (Tonight):**
1. ✅ Commit color support (DONE)
2. 🎥 Record hero demo video (60-90s)
3. 📸 Capture screenshot gallery
4. 📝 Write quick-start guide

**This Weekend:**
1. Technical deep-dive video
2. Dev.to article
3. Social media thread
4. README updates

**Next Week:**
1. Documentation artifacts
2. More demo videos (specific features)
3. Tutorial series
4. Share widely

---

## Recording Setup

**For VHS tapes:**
```bash
cd ~/projects/jcaldwell-labs/media/tapes
mkdir -p my-grid-shader-integration
cd my-grid-shader-integration

# Create hero-demo.tape
# Include:
# - Layout load
# - Zone navigation
# - Shader parameter changes
# - Claude integration demo
```

**For screenshots:**
- Use terminal with good color support
- Max dimensions for visibility
- Clean, uncluttered examples

---

## Success Metrics

**Community Engagement:**
- [ ] 100+ stars on my-grid repo
- [ ] 50+ stars on atari-style repo
- [ ] Shared by terminal/CLI enthusiasts
- [ ] Featured in newsletters (Terminal Trove, Console, etc.)

**Technical Impact:**
- [ ] Other projects adopt zone mode pattern
- [ ] Contributions from community
- [ ] Integration examples from users
- [ ] Phase 3 features implemented with community input

---

**This is genuinely innovative work - spatial computing + live shader control + AI integration, all in the terminal. Let's get it the attention it deserves!** 🎸🚀

Next: Record the hero demo video?
