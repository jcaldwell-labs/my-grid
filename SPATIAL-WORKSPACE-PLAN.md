# Spatial Workspace Enhancement Plan

## Vision

Transform my-grid from an ASCII canvas editor into a **spatial document workspace** - a 2D text space where different regions serve different purposes, connected by instant bookmark jumps.

Think of it as a virtual desktop with infinite space where each "window" is a text zone you can scroll between or warp to instantly.

---

## Phase 1: Enhanced Grid System

### 1.1 Grid Line Modes

**Current**: Intersection markers only (`+` at major, `·` at minor)

**New Options**:
```
GridLineMode:
  - MARKERS     # Current behavior - dots at intersections
  - LINES       # Full grid lines (─ │ for minor, ═ ║ for major)
  - DOTS        # Dots along both axes at intervals
  - OFF         # No grid display
```

**Implementation** (`renderer.py`):
```python
class GridLineMode(Enum):
    OFF = auto()
    MARKERS = auto()
    LINES = auto()
    DOTS = auto()

@dataclass
class GridSettings:
    # ... existing fields ...
    line_mode: GridLineMode = GridLineMode.MARKERS
    show_rulers: bool = False        # Edge rulers with coordinates
    show_labels: bool = False        # Coordinate labels at intervals
    label_interval: int = 50         # How often to show coordinate labels
```

### 1.2 Ruler Display

Show coordinates along top and left edges:
```
     0    10    20    30    40    50
     │     │     │     │     │     │
   ──┼─────┼─────┼─────┼─────┼─────┼──────
  0 ─┤
    ─┤     Canvas content here...
 10 ─┤
    ─┤
 20 ─┤
```

### 1.3 New Commands

```
:grid lines|markers|dots|off    # Set grid line mode
:grid rulers on|off             # Toggle edge rulers
:grid labels on|off             # Toggle coordinate labels at intervals
:grid interval MAJOR [MINOR]    # Set grid intervals (e.g., :grid interval 50 10)
```

### Files to Modify
- `src/renderer.py`: Add GridLineMode, ruler rendering, label rendering
- `src/main.py`: Extend `_cmd_grid()` for new subcommands

---

## Phase 2: Named Zones

### 2.1 Zone Data Structure

```python
@dataclass
class Zone:
    """A named region on the canvas."""
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str = ""
    border_style: str | None = None  # boxes style name
    bookmark: str | None = None      # Associated bookmark key (a-z, 0-9)

    def contains(self, cx: int, cy: int) -> bool:
        """Check if canvas coordinate is within this zone."""
        return (self.x <= cx < self.x + self.width and
                self.y <= cy < self.y + self.height)

    def center(self) -> tuple[int, int]:
        """Get center coordinates."""
        return (self.x + self.width // 2, self.y + self.height // 2)
```

### 2.2 Zone Manager

```python
class ZoneManager:
    """Manages named zones on the canvas."""

    def __init__(self):
        self.zones: dict[str, Zone] = {}

    def create(self, name: str, x: int, y: int, w: int, h: int, **kwargs) -> Zone
    def delete(self, name: str) -> bool
    def get(self, name: str) -> Zone | None
    def find_at(self, x: int, y: int) -> Zone | None  # Zone containing point
    def list_all(self) -> list[Zone]
    def nearest(self, x: int, y: int) -> tuple[Zone, int, str] | None  # (zone, distance, direction)

    def to_dict(self) -> dict  # For JSON serialization
    @classmethod
    def from_dict(cls, data: dict) -> "ZoneManager"
```

### 2.3 Zone Commands

```
:zone create NAME X Y W H [desc]   # Create zone at coordinates
:zone create NAME here W H [desc]  # Create zone at cursor
:zone delete NAME                  # Delete zone
:zone list                         # List all zones
:zone goto NAME                    # Jump to zone center
:zone info [NAME]                  # Show zone info (current zone if no name)
:zone rename OLD NEW               # Rename zone
:zone resize NAME W H              # Resize zone
:zone border NAME [style]          # Draw/update border (uses boxes styles)
:zone link NAME BOOKMARK           # Associate zone with bookmark key
```

### 2.4 Zone Visualization

When cursor enters a zone, status bar shows zone name.
Optional: highlight zone boundaries when near edge.

### Files to Create
- `src/zones.py`: Zone, ZoneManager classes

### Files to Modify
- `src/main.py`: Add zone commands, integrate ZoneManager
- `src/project.py`: Save/load zones in project JSON
- `src/renderer.py`: Optional zone boundary highlighting

---

## Phase 3: Enhanced Status Bar

### 3.1 Multi-Segment Status

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ NAV │ X:  150 Y:   40 │ 'A' │ NOTES │ ←120 INBOX │ project.json [+] │ 847 cells │
└─────────────────────────────────────────────────────────────────────────────────┘
  │         │            │       │          │              │              │
  │         │            │       │          │              │              └─ Cell count
  │         │            │       │          │              └─ File + dirty indicator
  │         │            │       │          └─ Nearest bookmark with distance/direction
  │         │            │       └─ Current zone name (or "---" if none)
  │         │            └─ Character at cursor
  │         └─ Cursor coordinates
  └─ Current mode
```

### 3.2 Status Bar Configuration

```python
@dataclass
class StatusBarConfig:
    show_mode: bool = True
    show_coords: bool = True
    show_cell: bool = True
    show_zone: bool = True           # NEW
    show_nearest_bookmark: bool = True  # NEW
    show_file: bool = True
    show_cell_count: bool = True
    compact_mode: bool = False       # Shorter labels for narrow terminals
```

### 3.3 Nearest Bookmark Indicator

Calculate and display:
- Direction arrow: ← → ↑ ↓ ↖ ↗ ↙ ↘
- Distance (Manhattan or Euclidean)
- Bookmark name/key

```python
def nearest_bookmark(cursor_x: int, cursor_y: int, bookmarks: dict) -> tuple[str, int, str] | None:
    """Find nearest bookmark. Returns (key, distance, direction_arrow)."""
```

### Files to Modify
- `src/main.py`: `_get_status_line()` - major refactor
- `src/renderer.py`: Add `StatusBarConfig`

---

## Phase 4: Content Integration

### 4.1 Boxes Integration

```
:box STYLE [W H]              # Draw box at cursor with style
:box list                     # List available box styles
:box wrap STYLE               # Wrap text selection (future: visual mode)
```

Implementation approach:
- Shell out to `boxes` command
- Parse output and write to canvas
- Cache available styles on startup

```python
def get_box_styles() -> list[str]:
    """Get list of available boxes styles."""
    result = subprocess.run(['boxes', '-l'], capture_output=True, text=True)
    # Parse style names from output

def draw_box(style: str, content: str) -> list[str]:
    """Generate box around content."""
    result = subprocess.run(
        ['boxes', '-d', style],
        input=content,
        capture_output=True,
        text=True
    )
    return result.stdout.split('\n')
```

### 4.2 Figlet Integration

```
:figlet TEXT [font]           # Draw figlet text at cursor
:figlet list                  # List available fonts
```

### 4.3 Pipe/Import Commands

```
:pipe COMMAND                 # Execute command, write stdout to canvas
:pipe! COMMAND                # Same but clear region first
:import FILE                  # Import file content at cursor (existing)
:import-box FILE [style]      # Import with box frame
```

### 4.4 Region Operations (Future)

Visual selection mode for:
- Copy/paste regions
- Box wrapping
- Clear region
- Export region

### Files to Create
- `src/external.py`: Boxes, figlet, pipe integration

### Files to Modify
- `src/main.py`: Add new commands

---

## Phase 5: Demo Content

### 5.1 Spatial Layout

Create a demo project with 5-6 zones spread across the canvas:

```
Zone Layout (not to scale):

    (0,0)           (150,0)          (300,0)
      INBOX          WORKSPACE        REFERENCE
      [i]              [w]              [r]

          (75,80)            (225,80)
           SCRATCH            OUTPUT
             [s]                [o]

                  (150,160)
                   ARCHIVE
                     [a]
```

### 5.2 Demo Content per Zone

| Zone | Content Type | Example |
|------|-------------|---------|
| INBOX | TODO list, piped input | `todo.txt` styled list |
| WORKSPACE | Current diagrams | ASCII flowchart |
| REFERENCE | Documentation | Man page excerpt |
| SCRATCH | Temp notes | Quick calculations |
| OUTPUT | Command output | `ls`, `git status` |
| ARCHIVE | Completed work | Old diagrams |

### 5.3 Demo Script Updates

Update `visual_auto_demo.py` to:
1. Create zones with borders
2. Populate with realistic content
3. Demonstrate zone jumping
4. Show status bar zone indicator
5. Demo boxes/figlet integration

---

## Implementation Order

### Sprint 1: Grid Enhancements
1. Add `GridLineMode` enum
2. Implement full grid lines rendering
3. Add ruler display
4. Add coordinate labels
5. Extend `:grid` command

### Sprint 2: Zone System
1. Create `zones.py` with Zone, ZoneManager
2. Integrate into Application
3. Add zone commands
4. Save/load in project JSON
5. Status bar zone indicator

### Sprint 3: Status Bar
1. Add nearest bookmark calculation
2. Refactor `_get_status_line()`
3. Add `StatusBarConfig`
4. Display zone and bookmark info

### Sprint 4: Content Integration
1. Create `external.py`
2. Add `:box` command with boxes integration
3. Add `:figlet` command
4. Add `:pipe` command

### Sprint 5: Demo
1. Create demo project JSON with zones
2. Update visual_auto_demo.py
3. Record new demo video
4. Frame validation

---

## File Summary

### New Files
- `src/zones.py` - Zone management
- `src/external.py` - External tool integration (boxes, figlet)
- `demo/spatial-workspace-demo.json` - Demo project

### Modified Files
- `src/renderer.py` - Grid modes, rulers, labels
- `src/main.py` - New commands, zone integration, status bar
- `src/project.py` - Zone serialization
- `demo/visual_auto_demo.py` - New demo content

---

## Success Criteria

1. **Grid**: Can toggle between marker/line/dot modes, see rulers with coordinates
2. **Zones**: Can create named zones, jump between them, see current zone in status
3. **Status**: Status bar shows zone name and nearest bookmark with direction
4. **Content**: Can pipe command output and draw boxes-styled frames
5. **Demo**: 60-90 second video showing spatial workflow with multiple zones
