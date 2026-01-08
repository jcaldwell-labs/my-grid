# -*- coding: utf-8 -*-
"""
my-grid Integration for Notepad++ (PythonScript plugin)

Sends selected text or current document to a my-grid canvas.

Installation:
1. Install PythonScript plugin in Notepad++ (Plugins > Plugins Admin)
2. Copy this file to: %APPDATA%\Notepad++\plugins\config\PythonScript\scripts\
3. Restart Notepad++
4. Access via: Plugins > PythonScript > Scripts > mygrid_send

Usage:
- Select text and run script to send selection
- Run with no selection to send entire document
- my-grid must be running with --server flag (port 8765)
"""

import socket

# Configuration
MYGRID_HOST = 'localhost'
MYGRID_PORT = 8765
TIMEOUT = 2.0  # seconds


def send_to_mygrid(command):
    """Send a command to my-grid and return response."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((MYGRID_HOST, MYGRID_PORT))
        sock.sendall((command + '\n').encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')
        sock.close()
        return response
    except socket.timeout:
        return '{"status": "error", "message": "Connection timeout"}'
    except ConnectionRefusedError:
        return '{"status": "error", "message": "my-grid not running (start with --server)"}'
    except Exception as e:
        return '{"status": "error", "message": "' + str(e) + '"}'


def get_text():
    """Get selected text or entire document."""
    selected = editor.getSelText()
    if selected:
        return selected, "selection"
    return editor.getText(), "document"


def send_text():
    """Send text to my-grid at current canvas cursor."""
    text, source = get_text()
    if not text.strip():
        console.write("Nothing to send (empty {})\n".format(source))
        return

    # Escape for command - replace newlines with literal \n for multi-line
    # For single line, send as :text command
    lines = text.split('\n')

    if len(lines) == 1:
        # Single line - simple text command
        response = send_to_mygrid(':text ' + text)
        console.write("Sent {} to my-grid: {}\n".format(source, response))
    else:
        # Multi-line - send line by line, moving cursor down
        console.write("Sending {} lines to my-grid...\n".format(len(lines)))
        for i, line in enumerate(lines):
            if line:  # Skip empty lines or send them?
                send_to_mygrid(':text ' + line)
            send_to_mygrid(':goto +0 +1')  # Move down one line (relative)
        console.write("Done! Sent {} lines.\n".format(len(lines)))


def send_to_zone(zone_name):
    """Send text as content for a static zone."""
    text, source = get_text()
    if not text.strip():
        console.write("Nothing to send (empty {})\n".format(source))
        return

    # This would require my-grid to support setting zone content via API
    # For now, we can create a pipe zone that echoes the content
    console.write("Zone content setting not yet implemented\n")


def send_as_box():
    """Send text wrapped in an ASCII box."""
    text, source = get_text()
    if not text.strip():
        console.write("Nothing to send (empty {})\n".format(source))
        return

    # Use my-grid's box command (requires 'boxes' tool)
    response = send_to_mygrid(':box ' + text.replace('\n', ' '))
    console.write("Sent {} as box: {}\n".format(source, response))


def check_connection():
    """Check if my-grid is running and responding."""
    response = send_to_mygrid(':status')
    console.write("my-grid status: {}\n".format(response))


# Main execution - run when script is executed
if __name__ == '__main__':
    send_text()
