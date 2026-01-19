# Task: Add Zone System to Textual Prototype (Phase 3)

## Context
You are continuing the my-grid Textual prototype. Phases 1-2 complete (canvas rendering, modes).
Now add the zone system for dynamic content regions.

## Current State
- Branch: feature/textual-web-prototype
- textual_prototype/app.py - Has NAV, EDIT, COMMAND, VISUAL modes
- textual_prototype/canvas_widget.py - Renders canvas with selection
- src/zones.py - Existing zone implementation (reference)

## Your Task
Add zone support to the Textual prototype:

### 1. Create zones.py in textual_prototype/
Port the core zone concepts:
- Zone dataclass (name, x, y, width, height, zone_type, content)
- ZoneType enum: STATIC, PIPE, WATCH
- ZoneManager class to track zones

### 2. Update CanvasWidget
- Add zone_manager attribute
- Render zone borders with type indicators [S], [P], [W]
- Zone content overlays canvas content in zone region

### 3. Update app.py
Add zone commands:
- :zone create NAME X Y W H - create static zone
- :zone pipe NAME W H CMD - create pipe zone (run command, show output)
- :zone watch NAME W H INTERVAL CMD - create watch zone (refresh periodically)
- :zones - list all zones
- :zone delete NAME - delete zone
- :zone goto NAME - jump cursor to zone

### 4. Implement PIPE zones
- Run subprocess, capture output
- Display output in zone region (truncate/wrap to fit)

### 5. Implement WATCH zones
- Use Textual's set_interval for periodic refresh
- Re-run command and update zone content

## Testing
After implementation:
1. :zone create TEST 5 5 20 10 - creates bordered region
2. :zone pipe LS 30 10 ls -la - shows directory listing
3. :zone watch TIME 60 5 5s date - shows updating time

When all zone types work, output: <promise>PHASE3_COMPLETE</promise>
