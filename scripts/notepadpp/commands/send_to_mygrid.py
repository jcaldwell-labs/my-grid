# -*- coding: utf-8 -*-
"""Send selected text (or document) to my-grid canvas."""
import socket


def send(cmd):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("localhost", 8765))
        s.sendall((cmd + "\n").encode("utf-8"))
        r = s.recv(1024).decode("utf-8")
        s.close()
        return r
    except Exception as e:
        return str(e)


text = editor.getSelText() or editor.getText()
if text.strip():
    lines = text.rstrip("\n").split("\n")
    for line in lines:
        send(":text " + line)
        send(":goto +0 +1")
    console.write("[my-grid] Sent {} lines\n".format(len(lines)))
else:
    console.write("[my-grid] Nothing to send\n")
