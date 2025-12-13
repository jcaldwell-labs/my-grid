# VHS Recording Guide for my-grid

## The Problem

When trying to record a demo of my-grid using VHS, the `educational_demo.py` approach captured the **wrong thing**:
- It sends API commands to a headless server via `mygrid-ctl`
- VHS records the **terminal running the commands** (server logs, command output)
- The **actual canvas is not visible** because the server is headless

Result: VHS recording shows command output instead of the visual canvas.

## The Solution

Create a **visual auto-demo module** that:
1. **Runs the actual curses UI** (visual terminal display)
2. **Programmatically feeds actions** instead of waiting for keyboard input
3. **VHS records the visual canvas** as it animates

This pattern comes from the **jcaldwell-labs-media** skill, proven to work with VHS.

## Architecture Comparison

### ❌ Wrong Approach (API Demo)
```
Terminal 1: python src/main.py --server  (headless, no visual)
Terminal 2: python demo/educational_demo.py  (sends API commands)
VHS records: Terminal 2 (command output only)
Result: No canvas visible
```

### ✅ Correct Approach (Visual Auto-Demo)
```
Terminal: python demo/visual_auto_demo.py
VHS records: Actual curses canvas rendering
Result: Full visual demo
```

## Files Created

| File | Description |
|------|-------------|
| `demo/visual_auto_demo.py` | Auto-demo module that runs curses UI with programmed actions |
| `demo/visual-auto-demo.tape` | VHS recording script |
| `demo/run-demo.sh` | Updated with `visual` option |

## Usage

### Test the Visual Demo (No Recording)

```bash
# Run visual demo for 75 seconds
python demo/visual_auto_demo.py 75

# Or use the demo runner
./demo/run-demo.sh visual 75
```

You should see the actual curses UI with:
- Animated panning across the canvas
- Text and shapes appearing
- Smooth transitions between zones
- All happening automatically without keyboard input

### Record with VHS

```bash
# Make sure VHS is installed
export PATH="$HOME/go/bin:$PATH"

# Record the demo
vhs demo/visual-auto-demo.tape

# Output appears at:
# demo/output/my-grid-visual-demo.mp4
```

## Key Implementation Details

Based on jcaldwell-labs-media skill patterns:

### 1. Single Fullscreen Session
```python
# CORRECT: Enter once, stay until done
try:
    while elapsed < total_duration:
        # ... all segments
finally:
    # Exit once at end
```

### 2. 20 FPS for VHS Reliability
```python
FRAME_DELAY = 0.05  # 20 FPS proven reliable for VHS
time.sleep(FRAME_DELAY)
```

### 3. Time-Based Segment Switching
```python
# Single while loop with time boundaries
segments = [
    (0, 8, segment_welcome),    # 0-8s
    (8, 10, segment_drawing),   # 8-18s
    (18, 8, segment_nav),       # 18-26s
]

# Switch based on elapsed time
for i, (boundary, duration, fn, desc) in enumerate(segments):
    if elapsed >= boundary:
        current_segment = i
```

### 4. Smooth Parametric Panning
```python
def _smooth_interpolate(self, t):
    """Smoothstep ease-in-out."""
    return t * t * (3 - 2 * t)

# Apply to viewport movement
t = self._smooth_interpolate(progress)
x = start_x + (target_x - start_x) * t
```

## Demo Segments

The visual auto-demo shows 8 zones across 75 seconds:

| Time | Segment | Description |
|------|---------|-------------|
| 0-8s | Welcome | Giant banner with panning |
| 8-18s | Drawing | Rectangles, lines, text |
| 18-26s | Navigation | Bookmarks and movement |
| 26-34s | Modes | NAV, EDIT, PAN, COMMAND |
| 34-44s | Architecture | System diagram |
| 44-52s | Productivity | TODO lists, notes |
| 52-60s | API | External control features |
| 60-65s | Easter Egg | The answer (42) |

## Customization

### Adjust Duration

```bash
# Shorter demo (quick test)
python demo/visual_auto_demo.py 30

# Longer demo (detailed)
python demo/visual_auto_demo.py 120
```

### Modify Segments

Edit `demo/visual_auto_demo.py`:

```python
def _define_segments(self):
    return [
        (0, 10, self._segment_welcome, "Welcome"),
        (10, 15, self._segment_custom, "Custom content"),
        # Add your segments here
    ]

def _segment_custom(self, segment_time, dt):
    """Your custom segment."""
    if segment_time < 0.5:
        self._execute_command("goto 100 100")
        self._execute_command("text Custom content here")
```

### Change VHS Settings

Edit `demo/visual-auto-demo.tape`:

```tape
Set FontSize 18         # Larger font
Set Width 2560          # 2K resolution
Set Height 1440
Set Framerate 60        # Higher framerate
Set Theme "Monokai"     # Different theme
```

## Troubleshooting

### Issue: Video freezes around 10-20 seconds

**Cause**: Nested loops or multiple fullscreen enter/exit calls
**Fix**: Use single while loop pattern (already implemented)

### Issue: VHS records too fast/too slow

**Cause**: Frame rate mismatch
**Fix**: Stick to 20 FPS (`FRAME_DELAY = 0.05`)

### Issue: Commands execute but nothing appears

**Cause**: Viewport not positioned correctly
**Fix**: Add `_pan_to()` calls before drawing

### Issue: VHS tape parser errors

**Cause**: Complex inline Python with escaped quotes
**Fix**: Use dedicated Python module (already done)

## Next Steps

### Option 1: Record Now

```bash
vhs demo/visual-auto-demo.tape
```

### Option 2: Test First

```bash
# Run the visual demo manually to preview
python demo/visual_auto_demo.py 75

# If it looks good, record it
vhs demo/visual-auto-demo.tape
```

### Option 3: Customize Then Record

1. Edit `demo/visual_auto_demo.py` - modify segments
2. Test: `python demo/visual_auto_demo.py 75`
3. Record: `vhs demo/visual-auto-demo.tape`

## Reference

- **Skill**: `~/.claude/skills/jcaldwell-labs-media`
- **Pattern**: Auto-demo module with programmed actions
- **Examples**: `atari-style/demos/screensaver_demo.py`

## Key Takeaway

**VHS needs visual terminal output to record.**

- API demos send commands → VHS sees command output (wrong)
- Visual auto-demos run curses UI → VHS sees canvas (correct)

The visual auto-demo pattern ensures VHS captures what you actually want to show: the canvas in action!
