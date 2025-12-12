#!/usr/bin/env python3
"""Tests for server module."""

import json
import socket
import sys
import threading
import time
from pathlib import Path
from queue import Queue

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from command_queue import CommandQueue, CommandResponse
from server import APIServer, ServerConfig, ServerStatus


class TestServerConfig:
    """Tests for ServerConfig dataclass."""

    def test_defaults(self):
        """Test default configuration."""
        config = ServerConfig()
        assert config.tcp_enabled is True
        assert config.tcp_port == 8765
        assert config.tcp_host == "127.0.0.1"
        assert config.fifo_path == "/tmp/mygrid.fifo"

    def test_custom_port(self):
        """Test custom port configuration."""
        config = ServerConfig(tcp_port=9000)
        assert config.tcp_port == 9000

    def test_disable_tcp(self):
        """Test disabling TCP."""
        config = ServerConfig(tcp_enabled=False)
        assert config.tcp_enabled is False


class TestServerStatus:
    """Tests for ServerStatus dataclass."""

    def test_defaults(self):
        """Test default status."""
        status = ServerStatus()
        assert status.running is False
        assert status.tcp_active is False
        assert status.tcp_port is None
        assert status.fifo_active is False
        assert status.connections_handled == 0
        assert status.errors == []


class TestAPIServer:
    """Tests for APIServer class."""

    def test_creation(self):
        """Test server creation."""
        q = CommandQueue()
        server = APIServer(q)
        assert server.command_queue is q
        assert server.config is None  # Not started yet

    def test_start_stop(self):
        """Test server start and stop."""
        q = CommandQueue()
        server = APIServer(q)

        # Use a random high port to avoid conflicts
        config = ServerConfig(tcp_port=19876, fifo_enabled=False)
        server.start(config)

        # Give server time to start
        time.sleep(0.2)

        status = server.status
        assert status.running is True

        server.stop()
        assert server.status.running is False

    def test_tcp_connection(self):
        """Test TCP connection and command sending."""
        q = CommandQueue()
        server = APIServer(q)

        # Use a random high port to avoid conflicts
        port = 19877
        config = ServerConfig(tcp_port=port, fifo_enabled=False)
        server.start(config)

        # Wait for server to start
        time.sleep(0.3)

        # Start a thread to consume commands and send responses
        def command_processor():
            while True:
                cmd = q.get(timeout=1.0)
                if cmd is None:
                    break
                if cmd.response_queue:
                    resp = CommandResponse(status="ok", message=f"Received: {cmd.command}")
                    cmd.response_queue.put(resp)

        processor = threading.Thread(target=command_processor, daemon=True)
        processor.start()

        try:
            # Connect and send command
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(("127.0.0.1", port))
                s.sendall(b":rect 10 5\n")
                s.shutdown(socket.SHUT_WR)

                # Read response
                response = s.recv(4096).decode('utf-8')
                assert "ok" in response
                assert "Received" in response

        finally:
            server.stop()

    def test_multiple_commands(self):
        """Test sending multiple commands."""
        q = CommandQueue()
        server = APIServer(q)

        port = 19878
        config = ServerConfig(tcp_port=port, fifo_enabled=False)
        server.start(config)
        time.sleep(0.3)

        # Command processor
        def command_processor():
            for _ in range(3):
                cmd = q.get(timeout=2.0)
                if cmd and cmd.response_queue:
                    resp = CommandResponse(status="ok", message="OK")
                    cmd.response_queue.put(resp)

        processor = threading.Thread(target=command_processor, daemon=True)
        processor.start()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(("127.0.0.1", port))
                s.sendall(b":cmd1\n:cmd2\n:cmd3\n")
                s.shutdown(socket.SHUT_WR)

                response = s.recv(4096).decode('utf-8')
                # Should have 3 JSON responses
                lines = [l for l in response.strip().split('\n') if l]
                assert len(lines) == 3

        finally:
            server.stop()

    def test_status_updates(self):
        """Test that status is updated correctly."""
        q = CommandQueue()
        server = APIServer(q)

        port = 19879
        config = ServerConfig(tcp_port=port, fifo_enabled=False)
        server.start(config)
        time.sleep(0.3)

        status = server.status
        assert status.tcp_active is True
        assert status.tcp_port == port

        server.stop()
        status = server.status
        assert status.running is False


class TestTCPProtocol:
    """Tests for TCP protocol implementation."""

    def test_json_response_format(self):
        """Test that responses are valid JSON."""
        q = CommandQueue()
        server = APIServer(q)

        port = 19880
        config = ServerConfig(tcp_port=port, fifo_enabled=False)
        server.start(config)
        time.sleep(0.3)

        def command_processor():
            cmd = q.get(timeout=2.0)
            if cmd and cmd.response_queue:
                resp = CommandResponse(
                    status="ok",
                    message="Test message",
                    data={"key": "value"}
                )
                cmd.response_queue.put(resp)

        processor = threading.Thread(target=command_processor, daemon=True)
        processor.start()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(("127.0.0.1", port))
                s.sendall(b":test\n")
                s.shutdown(socket.SHUT_WR)

                response = s.recv(4096).decode('utf-8').strip()
                data = json.loads(response)

                assert data["status"] == "ok"
                assert data["message"] == "Test message"

        finally:
            server.stop()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
