# my-grid Demo Package - Summary

Complete demo production system for showcasing my-grid as a terminal-based productivity tool.

## 📦 What's Included

### 1. Auto-Demo Module (`src/demo.py`)

VHS-compatible Python module that creates an automated system architecture diagram demo:

**Features:**
- ✅ Single while loop pattern (VHS-compatible, no freeze issues)
- ✅ Time-based segment switching (smooth transitions)
- ✅ 20 FPS rendering (reliable VHS capture)
- ✅ 75-second demo showing: boxes, arrows, labels, bookmarks, grid, pan

**Run standalone:**
```bash
python -c 'import sys; sys.path.insert(0, "src"); from demo import run_demo; run_demo(75)'
```

### 2. VHS Recording Scripts

**Production demo:**
- `demo/my-grid-productivity-demo.tape` - 75s system architecture showcase

**Quick test:**
- `demo/quick-test.tape` - 10s rapid test for development

**Template:**
- `demo/templates/vhs-template.tape` - Starter for new demos

### 3. Convenience Tools

**Recording script:**
```bash
demo/record.sh quick        # 10s test
demo/record.sh full         # 75s demo
demo/record.sh list         # Show available tapes
demo/record.sh view         # List recordings
demo/record.sh clean        # Remove outputs
```

### 4. Documentation

- **`demo/README.md`** - Quick start guide
- **`demo/PRODUCTION-GUIDE.md`** - Complete technical guide with VHS patterns
- **`demo/SUMMARY.md`** - This file

### 5. Presentation

**Patat slide deck:**
- `demo/presentation/my-grid-intro.md` - Live presentation for talks

Run with:
```bash
patat demo/presentation/my-grid-intro.md
```

## 🎯 Use Cases

### 1. GitHub README / Project Page

Record demo video and embed in README:

```bash
# Record
demo/record.sh full

# Upload to GitHub releases or host elsewhere
# Embed in README.md
![my-grid demo](https://user-content.../demo.mp4)
```

### 2. YouTube / Social Media

```bash
# Record full demo
vhs demo/my-grid-productivity-demo.tape

# Output: 1920x1080 MP4 suitable for YouTube
# Upload to YouTube with:
# - Title: "my-grid: Terminal-Based Productivity Canvas"
# - Tags: terminal, productivity, ascii-art, vim, diagrams
```

### 3. Live Demos / Talks

Option A - Run automated demo:
```bash
python -c 'import sys; sys.path.insert(0, "src"); from demo import run_demo; run_demo(75)'
```

Option B - Presentation slides with patat:
```bash
patat demo/presentation/my-grid-intro.md
```

Option C - Interactive live coding:
```bash
# Just run my-grid and create diagram live
python mygrid.py
```

### 4. Documentation

Embed demo in project wiki, docs site, or documentation repository.

## 🚀 Quick Start

### First-Time Setup

```bash
# 1. Ensure VHS is installed
go install github.com/charmbracelet/vhs@latest
export PATH="$HOME/go/bin:$PATH"

# 2. Test the demo module works
cd ~/projects/active/my-grid
python -c 'import sys; sys.path.insert(0, "src"); from demo import run_demo; run_demo(10)'

# 3. Record quick test
demo/record.sh quick

# 4. View output
mpv demo/output/quick-test.mp4
```

### Record Production Demo

```bash
# Full 75-second demo
demo/record.sh full

# Output: demo/output/my-grid-productivity-demo.mp4
# Duration: ~85s (includes intro/outro)
# Resolution: 1920x1080
# Format: MP4
```

## 📋 Demo Content

### Timeline (75 seconds)

| Time | Segment | Content |
|------|---------|---------|
| 0-3s | Title | "my-grid: System Architecture Demo" |
| 3-9s | Draw Component 1 | Frontend box with label |
| 9-15s | Draw Component 2 | API box with label |
| 15-21s | Draw Component 3 | Database box with label |
| 21-27s | Connect | Frontend → API arrow |
| 27-33s | Connect | API → Database arrow |
| 33-39s | Annotate | "HTTP" label |
| 39-45s | Annotate | "SQL" label |
| 45-50s | Bookmark | Set 'f' at Frontend |
| 50-55s | Bookmark | Set 'd' at Database |
| 55-60s | Navigate | Jump to Database |
| 60-65s | Navigate | Jump to Frontend |
| 65-70s | Visualize | Toggle grid overlay |
| 70-75s | Overview | Pan to show full diagram |

### Visual Output

```
my-grid: System Architecture Demo

┌──────────────────┐              ┌────────────────┐              ┌──────────────────┐
│                  │    HTTP      │                │     SQL      │                  │
│    Frontend      │─────────────>│      API       │─────────────>│    Database      │
│                  │              │                │              │                  │
└──────────────────┘              └────────────────┘              └──────────────────┘
        ^                                 ^                               ^
        |                                 |                               |
   Bookmark 'f'                           |                          Bookmark 'd'
```

## 🔧 Customization

### Adjust Timing

Edit `src/demo.py`, segments array:

```python
segments = [
    (0, "Title"),
    (5, "Draw Frontend Box"),    # Change from 3s to 5s
    (12, "Draw API Box"),         # Change from 9s to 12s
    # ... adjust as needed
]
```

### Change Visual Style

Modify drawing helpers:

```python
# Larger boxes
def draw_box(self, x, y, width, height, label):
    self.canvas.draw_rect(x, y, width + 10, height + 2)  # Bigger

# Different arrow character
def draw_arrow(self, x1, y1, x2, y2):
    self.canvas.draw_line(x1, y1, x2, y2, '═')  # Unicode
```

### Create New Demo Scenario

```bash
# 1. Copy template
cp demo/templates/vhs-template.tape demo/my-new-demo.tape

# 2. Edit src/demo.py - add new method
def run_flowchart_demo(self, duration: int = 60):
    # New segment definitions
    segments = [...]

# 3. Update tape file
# Change: run_demo(75)
# To: run_flowchart_demo(60)

# 4. Record
vhs demo/my-new-demo.tape
```

## 🎓 Technical Details

### VHS Compatibility Patterns

The demo follows proven VHS-compatible patterns:

1. **Single While Loop** - No nested loops that cause freezes
2. **Time-Based Switching** - Elapsed time determines segment, not counters
3. **20 FPS** - `time.sleep(0.05)` for reliable VHS capture
4. **Single Fullscreen Session** - Enter once, exit once

See `demo/PRODUCTION-GUIDE.md` for complete technical details.

### Why These Patterns Matter

VHS (terminal recorder) has specific limitations:

- **Can't handle nested loops** → Video freezes at 10-20s
- **Lags behind at 60 FPS** → Dropped frames, desync
- **Breaks on fullscreen transitions** → Black frames

The demo module is specifically designed around these constraints.

## 📚 Learn More

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Quick start and usage |
| `PRODUCTION-GUIDE.md` | Complete technical reference |
| `SUMMARY.md` | This overview |

### External Resources

- **jcaldwell-labs-media skill**: `~/.claude/skills/jcaldwell-labs-media/`
  - Reference patterns and examples
  - VHS troubleshooting guide
  - GPU direct rendering (advanced)

- **VHS Documentation**: https://github.com/charmbracelet/vhs
  - Official tape script syntax
  - Configuration options
  - Examples and gallery

## ✅ Checklist

### Before Recording

- [ ] VHS installed and in PATH
- [ ] Demo module tested (`run_demo(10)`)
- [ ] Timing feels right
- [ ] Terminal size adequate (1920x1080 ≈ 240x54 chars)

### After Recording

- [ ] Video plays without freezing
- [ ] Content is visible and clear
- [ ] Timing matches expectations
- [ ] File size reasonable (<50MB for 75s)

### Before Publishing

- [ ] Video quality acceptable
- [ ] Duration appropriate for platform
- [ ] Thumbnail captured (if needed)
- [ ] Description/title prepared
- [ ] Tags/keywords identified

## 🎬 Next Steps

### Immediate (Production Ready)

✅ Auto-demo module created
✅ VHS tape scripts ready
✅ Documentation complete
✅ Recording tools ready

### To Record:

```bash
# Quick test (verify everything works)
demo/record.sh quick
mpv demo/output/quick-test.mp4

# Production recording
demo/record.sh full
mpv demo/output/my-grid-productivity-demo.mp4
```

### Future Enhancements

- [ ] Flowchart demo (decision trees)
- [ ] Mind map demo (radial layout)
- [ ] Kanban board demo (sprint planning)
- [ ] Collaborative workflow demo (git integration)
- [ ] YouTube Shorts version (vertical 1080x1920)
- [ ] Thumbnail generation automation
- [ ] Multiple language versions (intro text)

## 🙏 Credits

Demo production system created using patterns from the **jcaldwell-labs-media** skill, which provides proven VHS-compatible recording techniques for terminal applications.

---

**Status**: ✅ Production Ready

**Last Updated**: 2025-12-12

**Tools Used**:
- VHS v0.10.0 (terminal recorder)
- Python 3.12+ (demo automation)
- Curses (terminal rendering)
- Patat (presentation mode)

**Compatible With**:
- WSL2 (tested)
- Linux (should work)
- macOS (should work)
