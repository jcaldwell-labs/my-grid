# my-grid Coordinate System Guide

## Three Different Measurements

### 1. Terminal Size (Physical Screen)
**Your current terminal:** 80 columns × 24 lines

This is the **physical screen** dimensions. Check with:
```bash
echo "Columns: $(tput cols), Lines: $(tput lines)"
```

---

### 2. Viewport Size (Visible Canvas Area)
**Size:** Same as terminal minus status bar

**Calculation:**
```
Terminal: 80 × 24
Status bar: 1 line
Viewport: 80 × 23 characters
```

The viewport is a "window" that shows part of the canvas.

**Status line shows:**
```
NAV │ X: 464 Y: -321 │ · │ KEY_E │ ↖203 [7] │ Untitled │ 4186 cells
      ^^^^^^^^^^^^                  ^^^^
      Cursor position               Arrow + distance to center
```

---

### 3. Canvas Coordinates (Unlimited Sparse Space)
**Size:** Unlimited! Can be any integer.

**Your music keys circle:**
- Radius: 600 units from origin
- Range: X: -660 to +660, Y: -660 to +660
- Total "canvas size": ~1320 × 1320 units

**Canvas is sparse:**
- Only stores cells with content
- Empty areas consume no memory
- Can have coordinates like (1000000, -5000)

---

## Viewport = Window into Canvas

```
Canvas (unlimited):
    -660 ─────────────────────────────── +660
     │                                    │
     │    Music Key Zones (12 areas)     │
     │                                    │
     │         [Viewport Window]          │
     │         80 × 23 view              │
     │         Shows small portion        │
     │                                    │
    -660 ─────────────────────────────── +660

Viewport position: (X, Y) in canvas space
Viewport size: 80 × 23 characters (fixed to terminal)
```

**Example:**

If viewport is at position (0, 0):
- Top-left corner of viewport = canvas (0, 0)
- Bottom-right = canvas (79, 22)
- You see canvas coordinates 0-79 in X, 0-22 in Y

If you pan to position (400, 500):
- Top-left = canvas (400, 500)
- Bottom-right = canvas (479, 522)
- You see coordinates 400-479 in X, 500-522 in Y

---

## Visible Canvas Units

**Formula:**
```
Visible X range: [viewport.x, viewport.x + viewport.width - 1]
Visible Y range: [viewport.y, viewport.y + viewport.height - 1]
```

**Your terminal (80 × 24):**
- Viewport width: 80 characters
- Viewport height: 23 (24 - status bar)
- **Visible canvas area: 80 × 23 units at any time**

**You can pan to see different 80×23 windows** of the unlimited canvas.

---

## What You See in Status Line

```
NAV │ X:  464 Y: -321 │   · │ KEY_E │ ↖203 [7] │ Untitled │ 4186 cells
```

**Breakdown:**
- `X: 464 Y: -321` - **Cursor position** in canvas coordinates
- `KEY_E` - Current zone name
- `↖203` - Direction and distance from cursor to viewport center
- `[7]` - Zone count
- `4186 cells` - Total non-empty cells on canvas

The status line does **NOT** show viewport size - that's always your terminal size.

---

## Planning Large Canvases

### Music Keys Circle (What You Built):
```
Canvas span: -660 to +660 (1320 × 1320 total area)
Zone count: 12
Zone size: 120 × 50 each
Spacing: 600 unit radius
```

**Viewport sees:** 80 × 23 at a time
**Navigation:** Use bookmarks ('1-'9, 'a-'c) to jump between zones

### How Much Can You See at Once?

**Maximum visible area:** Your terminal size
- Width: 80 canvas units
- Height: 23 canvas units

**To see more:**
- Pan around (p key, then wasd)
- Use bookmarks to jump
- Use :goto to teleport

---

## For Planning Your Next Large Canvas

**Terminal: 80 × 24** (physical screen)
**Viewport: 80 × 23** (minus status bar)
**Visible canvas: 80 × 23 units** at any moment

**Canvas can be:** Unlimited!
- You've already used -660 to +660 (1320 units)
- Could go -10000 to +10000 if needed
- Only occupied cells use memory

**Zone sizing:**
- 120 × 50 zones work well (current music keys)
- Can see ~60% of zone width at once (80/120)
- Can see ~46% of zone height at once (23/50)

**Spacing for large layouts:**
- 300-600 units between zones (music circle)
- Gives room to work without seeing other zones
- Bookmarks make navigation instant

---

## Quick Reference

| Measurement | Your Value | What It Means |
|-------------|------------|---------------|
| Terminal width | 80 | Physical screen columns |
| Terminal height | 24 | Physical screen lines |
| Viewport width | 80 | Canvas units visible horizontally |
| Viewport height | 23 | Canvas units visible vertically (24-1 status) |
| Canvas span | Unlimited | Can be -∞ to +∞ |
| Current canvas | -660 to +660 | Music keys circle range |
| Zone size | 120 × 50 | Each key signature area |

**You see 80×23 canvas units** at any time, but can navigate an unlimited canvas!
