# -*- coding: utf-8 -*-
"""
my-grid Menu Integration for Notepad++ (PythonScript plugin)

Provides multiple commands for sending text to my-grid canvas.
Registers menu items under Plugins > PythonScript > Scripts.

Installation:
1. Install PythonScript plugin in Notepad++ (Plugins > Plugins Admin)
2. Copy this file to: %APPDATA%\Notepad++\plugins\config\PythonScript\scripts\
3. Restart Notepad++

Commands (run via Plugins > PythonScript > Scripts > mygrid_menu):
- Send Selection/Document to canvas
- Send as ASCII box
- Send to specific coordinates
- Create a zone with content
- Check my-grid connection
"""

import socket
import json

# Configuration - change these if needed
MYGRID_HOST = 'localhost'
MYGRID_PORT = 8765
TIMEOUT = 2.0


class MyGridClient:
    """Simple client for my-grid API."""

    def __init__(self, host=MYGRID_HOST, port=MYGRID_PORT):
        self.host = host
        self.port = port

    def send(self, command):
        """Send command and return parsed response."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT)
            sock.connect((self.host, self.port))
            sock.sendall((command.strip() + '\n').encode('utf-8'))
            response = sock.recv(4096).decode('utf-8')
            sock.close()
            try:
                return json.loads(response)
            except:
                return {"status": "ok", "message": response}
        except socket.timeout:
            return {"status": "error", "message": "Connection timeout"}
        except ConnectionRefusedError:
            return {"status": "error", "message": "my-grid not running. Start with: python mygrid.py --server"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def text(self, text):
        """Write text at current cursor position."""
        return self.send(':text ' + text)

    def goto(self, x, y):
        """Move cursor to coordinates."""
        return self.send(':goto {} {}'.format(x, y))

    def rect(self, w, h, char=None):
        """Draw rectangle."""
        cmd = ':rect {} {}'.format(w, h)
        if char:
            cmd += ' ' + char
        return self.send(cmd)

    def status(self):
        """Get my-grid status."""
        return self.send(':status')

    def box(self, text):
        """Draw text in ASCII box (requires 'boxes' tool)."""
        return self.send(':box ' + text)


# Global client instance
client = MyGridClient()


def get_selection_or_document():
    """Get selected text, or entire document if nothing selected."""
    sel = editor.getSelText()
    if sel:
        return sel, True
    return editor.getText(), False


def show_result(result, action=""):
    """Display result in console."""
    if result.get('status') == 'ok':
        msg = result.get('message', 'OK')
        console.write("[my-grid] {}: {}\n".format(action, msg))
    else:
        console.write("[my-grid] ERROR: {}\n".format(result.get('message', 'Unknown error')))


# ============================================
# COMMANDS - Each can be run as a script
# ============================================

def cmd_send_text():
    """Send selection or document as text at cursor."""
    text, is_selection = get_selection_or_document()
    if not text.strip():
        console.write("[my-grid] Nothing to send\n")
        return

    lines = text.rstrip('\n').split('\n')
    source = "selection" if is_selection else "document"

    if len(lines) == 1:
        result = client.text(lines[0])
        show_result(result, "Sent {} ({} chars)".format(source, len(lines[0])))
    else:
        # Multi-line: send each line and move down
        console.write("[my-grid] Sending {} lines...\n".format(len(lines)))
        for line in lines:
            client.text(line)
            client.send(':goto +0 +1')
        console.write("[my-grid] Done! Sent {} lines.\n".format(len(lines)))


def cmd_send_at_coords():
    """Send text at specific coordinates (prompts for X,Y)."""
    text, is_selection = get_selection_or_document()
    if not text.strip():
        console.write("[my-grid] Nothing to send\n")
        return

    # Simple prompt via notepad
    coords = notepad.prompt("Enter coordinates (X Y):", "my-grid: Send at Position", "0 0")
    if coords is None:
        return

    try:
        parts = coords.strip().split()
        x, y = int(parts[0]), int(parts[1])
    except:
        console.write("[my-grid] Invalid coordinates. Use: X Y (e.g., 10 20)\n")
        return

    client.goto(x, y)
    lines = text.rstrip('\n').split('\n')
    for line in lines:
        client.text(line)
        client.send(':goto {} {}'.format(x, y + 1))
        y += 1
    console.write("[my-grid] Sent {} lines at ({}, {})\n".format(len(lines), parts[0], parts[1]))


def cmd_send_as_box():
    """Send selection wrapped in ASCII box."""
    text, _ = get_selection_or_document()
    if not text.strip():
        console.write("[my-grid] Nothing to send\n")
        return

    # Flatten to single line for box command
    flat = ' '.join(text.split())
    result = client.box(flat)
    show_result(result, "Sent as box")


def cmd_create_zone():
    """Create a static zone with the selected text."""
    text, _ = get_selection_or_document()

    # Get zone parameters
    params = notepad.prompt(
        "Zone name and size (NAME WIDTH HEIGHT):",
        "my-grid: Create Zone",
        "NOTES 40 20"
    )
    if params is None:
        return

    try:
        parts = params.strip().split()
        name = parts[0]
        w, h = int(parts[1]), int(parts[2])
    except:
        console.write("[my-grid] Invalid params. Use: NAME WIDTH HEIGHT\n")
        return

    # Create zone at current cursor position
    result = client.send(':zone create {} here {} {}'.format(name, w, h))
    show_result(result, "Created zone '{}'".format(name))

    # TODO: Could send text content to zone if my-grid supported it


def cmd_check_status():
    """Check if my-grid is running and show status."""
    result = client.status()
    if result.get('status') == 'ok':
        try:
            info = json.loads(result.get('message', '{}'))
            console.write("[my-grid] Connected!\n")
            console.write("  Cursor: ({}, {})\n".format(info.get('cursor', {}).get('x'), info.get('cursor', {}).get('y')))
            console.write("  Mode: {}\n".format(info.get('mode', '?')))
            console.write("  Cells: {}\n".format(info.get('cells', '?')))
            console.write("  File: {}\n".format(info.get('file', '?')))
        except:
            console.write("[my-grid] Connected: {}\n".format(result.get('message')))
    else:
        show_result(result, "Status")


def cmd_show_menu():
    """Show interactive menu of commands."""
    menu = """
my-grid Commands:
1. Send text to canvas
2. Send at coordinates
3. Send as ASCII box
4. Create zone
5. Check connection

Enter choice (1-5):"""

    choice = notepad.prompt(menu, "my-grid Menu", "1")
    if choice is None:
        return

    commands = {
        '1': cmd_send_text,
        '2': cmd_send_at_coords,
        '3': cmd_send_as_box,
        '4': cmd_create_zone,
        '5': cmd_check_status,
    }

    cmd = commands.get(choice.strip())
    if cmd:
        cmd()
    else:
        console.write("[my-grid] Invalid choice\n")


# Main entry point
if __name__ == '__main__':
    cmd_show_menu()
