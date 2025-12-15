# my-grid Demo Production Guide

Complete guide for creating professional demo videos for my-grid.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Production Workflow](#production-workflow)
3. [Technical Architecture](#technical-architecture)
4. [VHS Recording Patterns](#vhs-recording-patterns)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Customization](#advanced-customization)

## Quick Start

### Prerequisites

```bash
# Install VHS (if not already installed)
go install github.com/charmbracelet/vhs@latest

# Ensure in PATH
export PATH="$HOME/go/bin:$PATH"

# Verify installation
vhs --version
```

### Record Your First Demo

```bash
cd ~/projects/active/my-grid

# Test demo module (10s preview)
python -c 'import sys; sys.path.insert(0, "src"); from demo import run_demo; run_demo(10)'

# Record quick test (10s)
vhs demo/quick-test.tape

# Record full productivity demo (75s)
vhs demo/my-grid-productivity-demo.tape

# View output
ls -lh demo/output/
```

## Production Workflow

### 1. Design Phase

**Define the Demo Scenario:**
- What feature/use case to showcase?
- Target audience (developers, product managers, users)?
- Duration (30s, 60s, 90s)?
- Key moments to highlight?

**Sketch the Flow:**
```
0-5s:   Title card
5-20s:  Create first component
20-40s: Create second component
40-55s: Connect components
55-65s: Navigate with bookmarks
65-75s: Final overview + save
```

### 2. Implementation Phase

**Create Auto-Demo Module:**

The demo module (`src/demo.py`) uses a VHS-compatible pattern:

```python
class MyGridDemo:
    def run_demo(self, duration: int = 75):
        """Single while loop pattern - VHS compatible."""
        segments = [
            (0, "Title"),
            (5, "Draw Component"),
            (15, "Connect Components"),
            # ... time-based boundaries
        ]

        start_time = time.time()
        current_segment = 0

        # Single continuous loop (CRITICAL for VHS)
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time

            # Find current segment by time
            new_segment = find_segment_by_time(elapsed, segments)

            # Execute actions on segment change
            if new_segment != current_segment:
                execute_segment_actions(new_segment)

            # Render frame
            render()

            # 20 FPS (VHS compatible)
            time.sleep(0.05)
```

**Key Principles:**

1. **Single While Loop**: Never nest loops for segments
2. **Time-Based Switching**: Use `elapsed >= boundary`, not counters
3. **20 FPS**: Use `sleep(0.05)` for reliable VHS capture
4. **Single Fullscreen Session**: Enter once, exit once

### 3. VHS Tape Creation

**Tape Structure:**

```tape
# Header: metadata
Output "path/to/output.mp4"
Set FontSize 14
Set Width 1920
Set Height 1080
Set Framerate 30
Set Theme "Dracula"

# Introduction (5-10s)
Type "# my-grid: Feature Description"
Enter
Sleep 1s

# Launch demo
Type "python -c 'from demo import run_demo; run_demo(75)'"
Enter

# Wait for completion (demo duration + 5s buffer)
Sleep 80s

# Closing (3-5s)
Type "# github.com/user/my-grid"
Enter
Sleep 2s
```

### 4. Recording Phase

```bash
# Record with VHS
vhs demo/my-grid-productivity-demo.tape

# VHS will:
# 1. Launch terminal
# 2. Execute commands
# 3. Capture frames
# 4. Encode to MP4
# 5. Save to output/
```

### 5. Review & Iteration

```bash
# View recording
mpv demo/output/my-grid-productivity-demo.mp4

# Common adjustments:
# - Timing too fast/slow → adjust segment boundaries
# - Content unclear → add status messages
# - Visual issues → adjust box sizes, spacing
# - Freeze/stutter → check VHS compatibility patterns
```

## Technical Architecture

### Component Interaction

```
VHS Tape Script
    │
    ├─→ Launches Terminal Session
    │
    └─→ Executes: python demo.py
            │
            ├─→ MyGridDemo class
            │       │
            │       ├─→ Canvas (drawing)
            │       ├─→ Viewport (navigation)
            │       ├─→ Renderer (display)
            │       └─→ ModeStateMachine (bookmarks)
            │
            └─→ run_demo(duration)
                    │
                    └─→ Single while loop
                            │
                            ├─→ Time-based segment switching
                            ├─→ Execute drawing actions
                            ├─→ Render frame (20 FPS)
                            └─→ Loop until duration
```

### Demo Module Structure

```python
# src/demo.py
class MyGridDemo:
    """Automated demo - no user input required."""

    def __init__(self, stdscr):
        # Initialize my-grid components
        self.canvas = Canvas()
        self.viewport = Viewport()
        self.renderer = Renderer(stdscr)
        # ...

    def run_demo(self, duration: int):
        """VHS-compatible main loop."""
        # Single while loop pattern
        # Time-based segment switching
        # 20 FPS rendering

    def _execute_segment(self, description: str):
        """Perform actions for each demo segment."""
        if description == "Draw Frontend Box":
            self.draw_box(10, 10, 20, 5, "Frontend")
        elif description == "Connect Components":
            self.draw_arrow(30, 12, 45, 12)
        # ...

    def draw_box(self, x, y, width, height, label):
        """Helper: draw labeled box."""

    def draw_arrow(self, x1, y1, x2, y2):
        """Helper: draw connecting arrow."""
```

## VHS Recording Patterns

### Pattern 1: Single While Loop (REQUIRED)

**WRONG - Causes freeze:**
```python
for segment in segments:
    start = time.time()
    while time.time() - start < segment_duration:  # Nested loop!
        render()
```

**CORRECT - VHS compatible:**
```python
segments = [(0, "A"), (10, "B"), (20, "C")]
start_time = time.time()

while time.time() - start_time < total_duration:
    elapsed = time.time() - start_time
    current_segment = find_segment(elapsed, segments)
    render()
```

### Pattern 2: Time-Based Switching (REQUIRED)

**WRONG - Counter-based:**
```python
for i, segment in enumerate(segments):
    execute_segment(i)  # Immediate execution
```

**CORRECT - Time-based:**
```python
segments = [
    (0, "Title"),       # Starts at 0s
    (5, "Draw"),        # Starts at 5s
    (15, "Connect"),    # Starts at 15s
]

# Find segment by elapsed time
for i, (boundary, desc) in enumerate(segments):
    if elapsed >= boundary:
        new_segment = i
```

### Pattern 3: 20 FPS (RECOMMENDED)

**Issue with 60 FPS:**
```python
time.sleep(1.0 / 60)  # VHS lags behind, causes desync
```

**Proven reliable:**
```python
time.sleep(0.05)  # 20 FPS - VHS keeps up
```

### Pattern 4: Single Fullscreen Session (REQUIRED)

**WRONG - Re-enter between segments:**
```python
for segment in segments:
    renderer.enter_fullscreen()  # Don't do this!
    # ... render segment ...
    renderer.exit_fullscreen()
```

**CORRECT - Single session:**
```python
renderer.enter_fullscreen()  # Once at start
try:
    while running:
        # ... all segments in one session ...
        render()
finally:
    renderer.exit_fullscreen()  # Once at end
```

## Troubleshooting

### Video Freezes at 10-20 Seconds

**Cause**: Nested loops or segment transitions

**Solution**: Convert to single while loop pattern

```python
# Before (nested loops):
for segment in segments:
    while time_in_segment < duration:
        render()

# After (single loop):
while total_elapsed < total_duration:
    current_segment = calculate_segment(total_elapsed)
    render()
```

### Choppy or Dropped Frames

**Cause**: Frame rate too high for VHS to capture

**Solution**: Reduce to 20 FPS

```python
# Before:
time.sleep(1.0 / 60)  # 60 FPS

# After:
time.sleep(0.05)  # 20 FPS
```

### VHS Hangs or Doesn't Complete

**Cause**: Demo doesn't exit cleanly

**Solution**: Ensure demo terminates after duration

```python
def run_demo(self, duration: int = 75):
    start_time = time.time()

    while self.running:
        elapsed = time.time() - start_time

        # CRITICAL: Check duration limit
        if elapsed >= duration:
            break

        render()
```

### Demo Actions Execute Too Fast/Slow

**Cause**: Segment timing doesn't match content density

**Solution**: Adjust time boundaries

```python
# Too fast - components drawn instantly
segments = [
    (0, "Draw All Components"),
]

# Better - spaced for visual clarity
segments = [
    (0, "Title"),
    (5, "Draw Frontend"),    # 5s for first component
    (12, "Draw API"),         # 7s spacing
    (20, "Draw Database"),    # 8s spacing
    (30, "Connect"),          # 10s for connections
]
```

### Terminal Size Issues

**Cause**: Demo designed for different terminal size

**Solution**: Test with VHS terminal size (1920x1080 = ~240x54 chars)

```python
# In demo module
height, width = self.renderer.get_terminal_size()
print(f"Terminal: {width}x{height} chars")

# Adjust drawing positions based on actual size
box_x = width // 4  # 1/4 from left
```

## Advanced Customization

### Creating New Demo Scenarios

1. **Copy template:**
   ```bash
   cp demo/templates/vhs-template.tape demo/my-new-demo.tape
   ```

2. **Design segment timeline:**
   ```python
   # In src/demo.py, create new method
   def run_flowchart_demo(self, duration: int = 60):
       segments = [
           (0, "Draw Decision Diamond"),
           (8, "Draw Yes Branch"),
           (16, "Draw No Branch"),
           # ...
       ]
   ```

3. **Update VHS tape:**
   ```tape
   Type "python -c 'from demo import run_flowchart_demo; run_flowchart_demo(60)'"
   ```

4. **Record and iterate:**
   ```bash
   vhs demo/my-new-demo.tape
   mpv demo/output/my-new-demo.mp4
   ```

### YouTube Shorts Format (Vertical)

For 1080x1920 vertical videos:

```tape
Set Width 1080
Set Height 1920
Set FontSize 18  # Larger for mobile viewing

# Adjust demo layout for vertical orientation
# Recommendation: Stack components vertically instead of horizontally
```

### Multi-Part Demo Series

```bash
# Part 1: Basics (30s)
vhs demo/part1-basics.tape

# Part 2: Advanced Features (45s)
vhs demo/part2-advanced.tape

# Part 3: Real Workflow (60s)
vhs demo/part3-workflow.tape
```

### Thumbnail Generation

```python
# Add to demo.py
def capture_thumbnail(output_path: str = "thumbnail.png"):
    """Capture single frame for video thumbnail."""
    import curses
    from PIL import Image
    import numpy as np

    def capture_main(stdscr):
        demo = MyGridDemo(stdscr)
        # Run to interesting moment
        demo.run_demo(duration=30)
        # Capture final frame
        # (Implementation depends on your rendering approach)

    curses.wrapper(capture_main)
```

## Performance Optimization

### Reduce Render Complexity

```python
# Disable expensive features during recording
if self.demo_mode:
    self.renderer.grid.show_minor_lines = False  # Less line drawing
    self.enable_animations = False               # Skip smooth transitions
```

### Pre-compute Drawing Operations

```python
# Instead of:
def _execute_segment(self, desc):
    if desc == "Draw Complex Shape":
        for i in range(100):
            self.canvas.set_cell(...)  # 100 operations per frame!

# Do:
def __init__(self):
    # Pre-compute once
    self.predrawn_shapes = {
        "complex_shape": self._generate_complex_shape()
    }

def _execute_segment(self, desc):
    if desc == "Draw Complex Shape":
        self._apply_predrawn("complex_shape")  # Single operation
```

## Resources

- **VHS Documentation**: https://github.com/charmbracelet/vhs
- **VHS Examples**: https://github.com/charmbracelet/vhs/tree/main/examples
- **jcaldwell-labs-media Skill**: `~/.claude/skills/jcaldwell-labs-media/`
- **Curses Programming**: https://docs.python.org/3/howto/curses.html

## Credits

Demo production patterns derived from the jcaldwell-labs-media skill, which provides proven VHS-compatible recording techniques for terminal applications.

---

**Last Updated**: 2025-12-12
**VHS Version**: v0.10.0
**Python Version**: 3.12+
