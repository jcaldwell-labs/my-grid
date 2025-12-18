#!/usr/bin/env python3
"""Generate mathematically-inspired patterns for my-grid canvas."""
import json
import math
from datetime import datetime

# Unicode box drawing characters
H = "─"  # horizontal
V = "│"  # vertical
TL = "┌"  # top-left
TR = "┐"  # top-right
BL = "└"  # bottom-left
BR = "┘"  # bottom-right
CROSS = "┼"
TEE_D = "┬"  # T down
TEE_U = "┴"  # T up
TEE_R = "├"  # T right
TEE_L = "┤"  # T left

# Colors
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = 0, 1, 2, 3, 4, 5, 6, 7

cells = []

def put(x, y, char, fg=-1, bg=-1):
    """Add a cell to the canvas."""
    cells.append({"x": x, "y": y, "char": char, "fg": fg, "bg": bg})

def hline(x1, x2, y, fg=-1):
    """Draw horizontal line."""
    for x in range(x1, x2 + 1):
        put(x, y, H, fg)

def vline(x, y1, y2, fg=-1):
    """Draw vertical line."""
    for y in range(y1, y2 + 1):
        put(x, y, V, fg)

def box(x, y, w, h, fg=-1):
    """Draw a box."""
    put(x, y, TL, fg)
    put(x + w - 1, y, TR, fg)
    put(x, y + h - 1, BL, fg)
    put(x + w - 1, y + h - 1, BR, fg)
    for i in range(1, w - 1):
        put(x + i, y, H, fg)
        put(x + i, y + h - 1, H, fg)
    for i in range(1, h - 1):
        put(x, y + i, V, fg)
        put(x + w - 1, y + i, V, fg)

def spiral(cx, cy, turns, fg=-1):
    """Draw a rectangular spiral."""
    x, y = cx, cy
    size = 1
    for t in range(turns):
        # Right
        for _ in range(size):
            put(x, y, H, fg)
            x += 1
        put(x - 1, y, TR if t < turns - 1 else H, fg)
        # Down
        for _ in range(size):
            put(x, y, V, fg)
            y += 1
        put(x, y - 1, BR if t < turns - 1 else V, fg)
        size += 1
        # Left
        for _ in range(size):
            put(x, y, H, fg)
            x -= 1
        put(x + 1, y, BL if t < turns - 1 else H, fg)
        # Up
        for _ in range(size):
            put(x, y, V, fg)
            y -= 1
        put(x, y + 1, TL if t < turns - 1 else V, fg)
        size += 1

def maze_pattern(x0, y0, w, h):
    """Generate a simple maze-like pattern."""
    import random
    random.seed(42)  # Reproducible

    # Draw outer border
    box(x0, y0, w, h, CYAN)

    # Add internal walls
    for i in range(2, w - 2, 4):
        gap = random.randint(1, h - 4)
        for y in range(1, h - 1):
            if abs(y - gap) > 1:
                put(x0 + i, y0 + y, V, CYAN)

    for j in range(2, h - 2, 3):
        gap = random.randint(1, w - 4)
        for x in range(1, w - 1):
            if abs(x - gap) > 1:
                put(x0 + x, y0 + j, H, CYAN)

def diamond(cx, cy, size, fg=-1):
    """Draw a diamond shape."""
    for i in range(size):
        put(cx - i, cy - size + i, "╲", fg)
        put(cx + i, cy - size + i, "╱", fg)
        put(cx - i, cy + size - i, "╱", fg)
        put(cx + i, cy + size - i, "╲", fg)

def nested_boxes(x, y, count, fg_start=RED):
    """Draw nested boxes with cycling colors."""
    colors = [RED, YELLOW, GREEN, CYAN, BLUE, MAGENTA]
    for i in range(count):
        size = (count - i) * 4 + 2
        offset = i * 2
        box(x + offset, y + offset, size, size // 2 + 1, colors[i % len(colors)])

def greek_key(x0, y0, width, fg=YELLOW):
    """Draw Greek key / meander pattern."""
    unit = 3
    for i in range(0, width, unit * 2):
        x = x0 + i
        # Down stroke
        vline(x, y0, y0 + unit, fg)
        put(x, y0 + unit, BL, fg)
        # Right
        hline(x + 1, x + unit, y0 + unit, fg)
        put(x + unit, y0 + unit, BR, fg)
        # Up
        vline(x + unit, y0 + 1, y0 + unit - 1, fg)
        put(x + unit, y0 + 1, TR, fg)
        # Left partial
        hline(x + 2, x + unit - 1, y0 + 1, fg)
        put(x + 2, y0 + 1, TL, fg)
        # Down partial
        vline(x + 2, y0 + 2, y0 + unit - 1, fg)
        # Connect to next
        if i + unit * 2 < width:
            hline(x + unit + 1, x + unit * 2, y0, fg)

def celtic_knot(x0, y0, size, fg=GREEN):
    """Draw a simple celtic knot pattern."""
    # Outer ring
    for i in range(size):
        angle = 2 * math.pi * i / size
        x = int(x0 + size * math.cos(angle))
        y = int(y0 + size * 0.5 * math.sin(angle))
        put(x, y, "●", fg)

    # Inner pattern - interlocking loops
    for i in range(-size//2, size//2 + 1):
        for j in range(-size//4, size//4 + 1):
            if (i + j) % 2 == 0:
                put(x0 + i, y0 + j, CROSS, fg)

def rug_pattern(x0, y0, w, h):
    """Draw a rug/textile inspired pattern."""
    colors = [RED, YELLOW, RED, YELLOW]

    # Border
    box(x0, y0, w, h, RED)
    box(x0 + 1, y0 + 1, w - 2, h - 2, YELLOW)

    # Inner diamond grid
    for dy in range(3, h - 3, 4):
        for dx in range(3, w - 3, 6):
            x, y = x0 + dx, y0 + dy
            color = colors[(dx // 6 + dy // 4) % len(colors)]
            # Small diamond
            put(x, y - 1, "╱", color)
            put(x + 1, y - 1, "╲", color)
            put(x - 1, y, H, color)
            put(x + 2, y, H, color)
            put(x, y + 1, "╲", color)
            put(x + 1, y + 1, "╱", color)

def sierpinski_lines(x0, y0, size, depth, fg=MAGENTA):
    """Draw Sierpinski-triangle inspired line pattern."""
    if depth == 0 or size < 2:
        return

    # Draw triangle outline
    half = size // 2
    # Top
    hline(x0, x0 + size, y0, fg)
    # Left side
    for i in range(half):
        put(x0 + i, y0 + i + 1, "╲", fg)
        put(x0 + size - i, y0 + i + 1, "╱", fg)
    # Bottom
    hline(x0 + half - half//2, x0 + half + half//2, y0 + half, fg)

    # Recurse on smaller triangles
    sierpinski_lines(x0, y0, half, depth - 1, fg)
    sierpinski_lines(x0 + half, y0, half, depth - 1, fg)

def text_at(x, y, text, fg=-1):
    """Write text at position."""
    for i, ch in enumerate(text):
        put(x + i, y, ch, fg)

# === BUILD THE CANVAS ===

# Title
text_at(5, 1, "═══ MATHEMATICAL PATTERNS ═══", CYAN)

# Section 1: Nested boxes (top-left)
text_at(2, 3, "Nested Boxes", YELLOW)
nested_boxes(2, 5, 5)

# Section 2: Spiral (top-center)
text_at(35, 3, "Rectangular Spiral", GREEN)
spiral(45, 12, 4, GREEN)

# Section 3: Greek Key pattern
text_at(70, 3, "Greek Meander", YELLOW)
greek_key(70, 5, 30, YELLOW)

# Section 4: Maze (middle-left)
text_at(2, 20, "Labyrinth", CYAN)
maze_pattern(2, 22, 30, 15)

# Section 5: Rug pattern (middle-center)
text_at(40, 20, "Rug Pattern", RED)
rug_pattern(38, 22, 26, 14)

# Section 6: Sierpinski-inspired (middle-right)
text_at(75, 20, "Fractal Lines", MAGENTA)
sierpinski_lines(72, 22, 24, 3, MAGENTA)

# Section 7: Grid of crosses (bottom)
text_at(2, 40, "Infinite Grid", BLUE)
for dy in range(5):
    for dx in range(20):
        x, y = 2 + dx * 3, 42 + dy * 2
        color = [BLUE, CYAN][(dx + dy) % 2]
        put(x, y, CROSS, color)
        if dx < 19:
            put(x + 1, y, H, color)
            put(x + 2, y, H, color)
        if dy < 4:
            put(x, y + 1, V, color)

# Section 8: Concentric pattern
text_at(70, 40, "Concentric", MAGENTA)
for i in range(6):
    color = [RED, YELLOW, GREEN, CYAN, BLUE, MAGENTA][i]
    box(70 + i, 42 + i // 2, 20 - i * 2, 10 - i, color)

# === SAVE PROJECT ===

project = {
    "version": "1.0",
    "metadata": {
        "name": "Mathematical Patterns",
        "created": datetime.now().isoformat(),
        "modified": datetime.now().isoformat()
    },
    "canvas": {
        "cells": cells
    },
    "viewport": {
        "x": 0, "y": 0,
        "cursor": {"x": 0, "y": 0},
        "origin": {"x": 0, "y": 0}
    },
    "grid": {
        "show_origin": True,
        "major_interval": 10
    },
    "bookmarks": {},
    "zones": {"zones": []}
}

with open("patterns-demo.json", "w", encoding="utf-8") as f:
    json.dump(project, f, indent=2, ensure_ascii=False)

print(f"Created patterns-demo.json with {len(cells)} cells")
print("Open with: python mygrid.py patterns-demo.json")
