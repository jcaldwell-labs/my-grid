#!/usr/bin/env python3
"""Send stdin or argument to a TCP socket - netcat alternative for Windows."""
import socket
import sys

def send_to_socket(text: str, host: str = 'localhost', port: int = 9999):
    """Send text to TCP socket."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((host, port))
            s.sendall(text.encode('utf-8'))
        return True
    except ConnectionRefusedError:
        print(f"Error: Connection refused at {host}:{port}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    port = 9999

    # Parse port from args if provided
    args = sys.argv[1:]
    if args and args[0].isdigit():
        port = int(args.pop(0))

    # Get text from args or stdin
    if args:
        text = ' '.join(args)
    else:
        text = sys.stdin.read()

    if text:
        success = send_to_socket(text, port=port)
        sys.exit(0 if success else 1)
