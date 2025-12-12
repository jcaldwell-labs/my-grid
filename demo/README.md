# my-grid Demo System

Professional demos showcasing my-grid as a terminal-based productivity canvas tool.

**Two Modes Available:**

1. **VHS Recording** - Video demos (MP4/GIF) for showcases and social media
2. **Headless Generation** - Text tutorials (Markdown/TXT) for documentation

## Quick Start

### Headless Mode (Documentation)

```bash
# Generate tutorial documentation (no terminal needed!)
demo/generate-tutorial.sh

# Output: demo/output/tutorial.md and demo/output/tutorial.txt
```

**Best for:** README files, documentation sites, CI/CD pipelines, email distribution

**See:** [HEADLESS-DEMO.md](HEADLESS-DEMO.md) for complete guide

---

### VHS Mode (Video Recording)

Test the live demo:

```bash
cd ~/projects/active/my-grid

# Run 10-second quick test
python -c 'import sys; sys.path.insert(0, "src"); from demo import run_demo; run_demo(10)'

# Run full 75-second demo
python -c 'import sys; sys.path.insert(0, "src"); from demo import run_demo; run_demo(75)'
```

Press `q` or `Ctrl+C` to exit early.

### Record with VHS

```bash
cd ~/projects/active/my-grid

# Ensure VHS is in PATH
export PATH="$HOME/go/bin:$PATH"

# Record productivity demo (1920x1080, ~85s total)
vhs demo/my-grid-productivity-demo.tape

# Output: demo/output/my-grid-productivity-demo.mp4
```

### View the Recording

```bash
# Play with VLC or mpv
mpv demo/output/my-grid-productivity-demo.mp4

# Or copy to Windows for viewing
cp demo/output/*.mp4 /mnt/c/Users/YourName/Videos/
```

## Demo Scenarios

### 1. Productivity Demo (Current)
- **Duration**: 75s
- **Content**: System architecture diagram (Frontend → API → Database)
- **Features**: Boxes, arrows, labels, bookmarks, grid, pan
- **Use Case**: Showcases my-grid as Miro/Lucidchart alternative

### 2. Flow Chart Demo (TODO)
- **Duration**: 60s
- **Content**: Decision tree workflow
- **Features**: Diamond shapes, yes/no branches, annotations

### 3. Mind Map Demo (TODO)
- **Duration**: 45s
- **Content**: Radial idea organization
- **Features**: Central topic, branches, bookmarks for navigation

### 4. Sprint Planning Board (TODO)
- **Duration**: 90s
- **Content**: Kanban-style board (To Do, In Progress, Done)
- **Features**: Cards, swim lanes, labels

## Demo Module API

```python
from demo import MyGridDemo, run_demo

# Standalone entry point
run_demo(duration=75)  # 75 second demo

# Custom usage
import curses

def custom_demo(stdscr):
    demo = MyGridDemo(stdscr)
    demo.run_demo(duration=60)

curses.wrapper(custom_demo)
```

## VHS Recording Tips

From jcaldwell-labs-media skill guidelines:

### Critical VHS Patterns

1. **Single While Loop**: Avoid nested loops (causes freeze at ~10-20s)
2. **20 FPS**: Use `time.sleep(0.05)` for reliable VHS capture
3. **Single Fullscreen Session**: Don't re-enter/exit fullscreen between segments
4. **Time-Based Switching**: Use elapsed time, not segment loops

### Proven Working Pattern

The `demo.py` module follows the VHS-compatible pattern:

```python
# Single continuous loop
while time.time() - start_time < duration:
    elapsed = time.time() - start_time

    # Time-based segment switching
    new_segment = calculate_segment(elapsed)
    if new_segment != current_segment:
        execute_segment_actions(new_segment)

    render_frame()
    time.sleep(0.05)  # 20 FPS
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Video freezes at 10-20s | Switch to single while loop pattern |
| Choppy rendering | Reduce to 20 FPS (`sleep(0.05)`) |
| Freeze at transitions | Remove nested loops, use time-based switching |
| VHS parser errors | Move Python code to dedicated module, not inline |

## Customizing the Demo

### Timing Adjustments

Edit `src/demo.py` segment boundaries:

```python
segments = [
    (0, "Title"),
    (3, "Draw Frontend Box"),   # Starts at 3s
    (9, "Draw API Box"),         # Starts at 9s
    # ... adjust times as needed
]
```

### Visual Customization

Modify drawing parameters in `_execute_segment()`:

```python
# Larger boxes
self.draw_box(10, 10, 30, 7, "Frontend")  # was 20x5

# Different arrow style
self.canvas.draw_line(x1, y1, x2, y2, '═')  # Unicode box drawing

# Add colors (if terminal supports)
# Note: Current version uses monochrome ASCII
```

### Adding New Segments

```python
segments = [
    # ... existing segments
    (75, "Save Project"),
]

# In _execute_segment():
elif description == "Save Project":
    self.project.save(
        self.canvas, self.viewport,
        filepath=Path("demo-architecture.json")
    )
```

## Directory Structure

```
demo/
├── README.md                           # This file
├── my-grid-productivity-demo.tape      # Main VHS script
├── output/
│   └── my-grid-productivity-demo.mp4   # Generated video
└── templates/
    └── vhs-template.tape               # Template for new demos
```

## Future Demo Ideas

### Terminal Workflow Integration

Show my-grid in a real development workflow:

```tape
# Split tmux panes
Type "tmux new-session -d -s demo"
Type "tmux split-window -h"

# Left pane: my-grid with architecture diagram
Type "tmux send-keys -t demo:0.0 'python mygrid.py' Enter"

# Right pane: code editor referencing the diagram
Type "tmux send-keys -t demo:0.1 'vim api-service.py' Enter"

Type "tmux attach -t demo"
```

### Export Workflow

Demonstrate the full create → edit → export → use cycle:

1. Create diagram in my-grid
2. Export to text file (`:export diagram.txt`)
3. Include in documentation (Markdown code block)
4. Version control with git

### Multi-User Collaboration

Show how my-grid projects can be shared:

```bash
# Create diagram
python mygrid.py architecture.json

# Commit to git
git add architecture.json
git commit -m "Add system architecture diagram"

# Team member loads and extends
python mygrid.py architecture.json
# ... add deployment layer ...
```

## Resources

- **my-grid Repository**: github.com/yourusername/my-grid
- **VHS Documentation**: github.com/charmbracelet/vhs
- **jcaldwell-labs-media Skill**: ~/.claude/skills/jcaldwell-labs-media/

## Credits

Demo creation guided by the jcaldwell-labs-media skill, following proven VHS-compatible patterns for terminal recording.
