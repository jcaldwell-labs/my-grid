#!/usr/bin/env python3
"""Tests for command_queue module."""

import sys
import time
import threading
from pathlib import Path
from queue import Queue

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from command_queue import CommandQueue, ExternalCommand, CommandResponse, send_response


class TestCommandQueue:
    """Tests for CommandQueue class."""

    def test_put_and_get(self):
        """Test basic put and get operations."""
        q = CommandQueue()
        q.put(":rect 10 5")

        cmd = q.get_nowait()
        assert cmd is not None
        assert cmd.command == ":rect 10 5"
        assert cmd.response_queue is None
        assert cmd.source == "unknown"

    def test_put_with_response_queue(self):
        """Test put with response queue."""
        q = CommandQueue()
        response_q = Queue()
        q.put(":text Hello", response_queue=response_q, source="tcp")

        cmd = q.get_nowait()
        assert cmd is not None
        assert cmd.command == ":text Hello"
        assert cmd.response_queue is response_q
        assert cmd.source == "tcp"

    def test_get_nowait_empty(self):
        """Test get_nowait on empty queue."""
        q = CommandQueue()
        assert q.get_nowait() is None

    def test_get_blocking(self):
        """Test blocking get with timeout."""
        q = CommandQueue()

        # Should timeout on empty queue
        start = time.time()
        result = q.get(timeout=0.1)
        elapsed = time.time() - start

        assert result is None
        assert elapsed >= 0.1

    def test_pending_count(self):
        """Test pending_count property."""
        q = CommandQueue()
        assert q.pending_count == 0

        q.put(":cmd1")
        assert q.pending_count == 1

        q.put(":cmd2")
        assert q.pending_count == 2

        q.get_nowait()
        assert q.pending_count == 1

    def test_is_empty(self):
        """Test is_empty property."""
        q = CommandQueue()
        assert q.is_empty

        q.put(":cmd")
        assert not q.is_empty

        q.get_nowait()
        assert q.is_empty

    def test_clear(self):
        """Test clear method."""
        q = CommandQueue()
        q.put(":cmd1")
        q.put(":cmd2")
        q.put(":cmd3")

        cleared = q.clear()
        assert cleared == 3
        assert q.is_empty

    def test_stats(self):
        """Test stats property."""
        q = CommandQueue()

        stats = q.stats
        assert stats["pending"] == 0
        assert stats["total_received"] == 0
        assert stats["total_processed"] == 0
        assert stats["total_dropped"] == 0

        q.put(":cmd1")
        q.put(":cmd2")
        stats = q.stats
        assert stats["total_received"] == 2

        q.get_nowait()
        stats = q.stats
        assert stats["total_processed"] == 1

    def test_max_size(self):
        """Test queue max size limit."""
        q = CommandQueue(max_size=3)

        assert q.put(":cmd1") is True
        assert q.put(":cmd2") is True
        assert q.put(":cmd3") is True
        assert q.put(":cmd4", block=False) is False  # Should fail

        stats = q.stats
        assert stats["total_dropped"] == 1

    def test_command_stripping(self):
        """Test that commands are stripped of whitespace."""
        q = CommandQueue()
        q.put("  :rect 10 5  \n")

        cmd = q.get_nowait()
        assert cmd.command == ":rect 10 5"

    def test_timestamp(self):
        """Test that commands have timestamps."""
        q = CommandQueue()
        before = time.time()
        q.put(":cmd")
        after = time.time()

        cmd = q.get_nowait()
        assert before <= cmd.timestamp <= after

    def test_thread_safety(self):
        """Test thread-safe access to queue."""
        q = CommandQueue()
        num_threads = 10
        commands_per_thread = 100

        def producer(thread_id):
            for i in range(commands_per_thread):
                q.put(f":cmd_{thread_id}_{i}")

        threads = [threading.Thread(target=producer, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All commands should be in queue
        assert q.pending_count == num_threads * commands_per_thread


class TestExternalCommand:
    """Tests for ExternalCommand dataclass."""

    def test_creation(self):
        """Test ExternalCommand creation."""
        cmd = ExternalCommand(command=":rect 10 5")
        assert cmd.command == ":rect 10 5"
        assert cmd.response_queue is None
        assert cmd.source == "unknown"

    def test_with_all_fields(self):
        """Test ExternalCommand with all fields."""
        response_q = Queue()
        cmd = ExternalCommand(
            command=":text Hello",
            response_queue=response_q,
            timestamp=12345.0,
            source="tcp"
        )
        assert cmd.command == ":text Hello"
        assert cmd.response_queue is response_q
        assert cmd.timestamp == 12345.0
        assert cmd.source == "tcp"


class TestCommandResponse:
    """Tests for CommandResponse dataclass."""

    def test_ok_response(self):
        """Test OK response."""
        resp = CommandResponse(status="ok", message="Drew 10x5 rectangle")
        assert resp.status == "ok"
        assert resp.message == "Drew 10x5 rectangle"
        assert resp.data is None

    def test_error_response(self):
        """Test error response."""
        resp = CommandResponse(status="error", message="Invalid command")
        assert resp.status == "error"
        assert resp.message == "Invalid command"

    def test_with_data(self):
        """Test response with data."""
        resp = CommandResponse(
            status="ok",
            message="Status retrieved",
            data={"cursor": {"x": 10, "y": 5}}
        )
        assert resp.data == {"cursor": {"x": 10, "y": 5}}

    def test_to_dict(self):
        """Test to_dict conversion."""
        resp = CommandResponse(status="ok", message="OK")
        d = resp.to_dict()
        assert d == {"status": "ok", "message": "OK"}

    def test_to_dict_with_data(self):
        """Test to_dict with data."""
        resp = CommandResponse(
            status="ok",
            message="OK",
            data={"key": "value"}
        )
        d = resp.to_dict()
        assert d == {"status": "ok", "message": "OK", "data": {"key": "value"}}


class TestSendResponse:
    """Tests for send_response function."""

    def test_send_response(self):
        """Test sending response to command."""
        response_q = Queue()
        cmd = ExternalCommand(command=":test", response_queue=response_q)
        resp = CommandResponse(status="ok", message="Success")

        send_response(cmd, resp)

        received = response_q.get_nowait()
        assert received.status == "ok"
        assert received.message == "Success"

    def test_send_response_no_queue(self):
        """Test sending response with no response queue."""
        cmd = ExternalCommand(command=":test")
        resp = CommandResponse(status="ok", message="Success")

        # Should not raise
        send_response(cmd, resp)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
