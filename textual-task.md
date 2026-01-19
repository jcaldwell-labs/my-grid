# Task: Create Textual CanvasWidget Prototype for my-grid

## Context
You are in the my-grid project - an ASCII canvas editor currently using Python curses.
We want to prototype migrating to Textual for web support via textual-web.

## Current State
- Branch: feature/textual-web-prototype (already created)
- Venv: .venv with textual installed
- Existing code in src/: canvas.py, viewport.py, modes.py (reusable)

## Your Task
Create a minimal Textual prototype that:

1. Create textual_prototype/ directory with:
   - __init__.py
   - canvas_widget.py - Widget that renders Canvas using Rich Text
   - app.py - Minimal MyGridApp with navigation

2. The CanvasWidget should:
   - Import and use existing src/canvas.py Canvas class
   - Import and use existing src/viewport.py Viewport class  
   - Render cells as Rich Text with proper styling
   - Show cursor (reverse video), origin marker (yellow +)
   - Handle basic colors from Cell.fg/bg

3. The app.py should:
   - Create MyGridApp(App) with CanvasWidget
   - Add keybindings: wasd/arrows for nav, q to quit, g for grid toggle
   - Show a status bar with cursor position

4. Add a run script run_textual.py at project root that:
   - Can be run with: source .venv/bin/activate && python run_textual.py

## Key Files to Reference
- src/canvas.py - Canvas and Cell classes (sparse dict storage)
- src/viewport.py - Viewport with screen_to_canvas(), cursor, origin
- src/renderer.py - Current curses renderer (for reference on styling logic)

## Testing
After creating files, run the prototype to verify it works:
source .venv/bin/activate
python run_textual.py

## Constraints
- Keep it minimal - this is a proof of concept
- Reuse existing Canvas/Viewport classes, don't rewrite them
- Use Rich Text styling, not curses attributes
