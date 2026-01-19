# Task: Add Mode System to Textual Prototype (Phase 2)

## Context
You are continuing work on the my-grid Textual prototype in feature/textual-web-prototype branch.
Phase 1 (basic canvas rendering with navigation) is complete.

## Current Files
- textual_prototype/canvas_widget.py - CanvasWidget rendering
- textual_prototype/app.py - MyGridApp with NAV mode bindings
- src/modes.py - Existing mode state machine (reference)

## Your Task
Extend the prototype to support multiple modes:

### 1. Edit Mode
- Press 'i' to enter edit mode from NAV
- In edit mode, typing characters writes to canvas at cursor
- Cursor advances right after each character
- Backspace deletes and moves cursor left
- Escape returns to NAV mode
- Show mode in status bar: [NAV] vs [EDIT]

### 2. Command Mode  
- Press ':' to enter command mode
- Show command input at bottom of screen (replace or overlay status bar)
- Support basic commands: quit, goto X Y, clear, rect W H
- Enter executes command, Escape cancels
- After command, return to NAV mode

### 3. Visual Selection Mode
- Press 'v' to enter visual mode
- Moving cursor extends selection from anchor point
- Selection should be highlighted (use different style)
- 'y' yanks selection to clipboard (store in app)
- 'd' deletes selection
- Escape cancels selection

### Implementation Notes
- Use Textual's mode system OR manage state manually (your choice)
- Update StatusBar to show current mode
- The CanvasWidget needs a way to highlight selection region
- For command mode, consider using Textual's Input widget

### Files to Modify
- textual_prototype/app.py - Add mode handling, command input
- textual_prototype/canvas_widget.py - Add selection highlighting, set_char method

### Testing
After changes, verify:
1. Can enter edit mode with 'i', type characters, escape back
2. Can enter command mode with ':', type ':goto 10 10', execute
3. Can select region with 'v', move to extend, 'y' to yank

Keep it functional but minimal - this is still a prototype.
