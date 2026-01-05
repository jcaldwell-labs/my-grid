#!/usr/bin/env python3
"""
Thread-safe command queue for external API commands.

Allows external processes to queue commands for execution
by the main my-grid event loop.
"""

from dataclasses import dataclass, field
from queue import Queue, Empty, Full
from threading import Lock
import time


@dataclass
class ExternalCommand:
    """
    A command received from an external source.

    Attributes:
        command: The command string (e.g., ":rect 10 5" or "text Hello")
        response_queue: Optional queue to send response back to caller
        timestamp: When the command was received
        source: Identifier for the source (e.g., "tcp", "fifo", "pipe")
    """
    command: str
    response_queue: Queue | None = None
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"


@dataclass
class CommandResponse:
    """
    Response to an external command.

    Attributes:
        status: "ok" or "error"
        message: Human-readable result or error message
        data: Optional structured data (for queries like status)
    """
    status: str
    message: str
    data: dict | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"status": self.status, "message": self.message}
        if self.data:
            result["data"] = self.data
        return result


class CommandQueue:
    """
    Thread-safe queue for external commands.

    Commands are added by API server threads and consumed by the main loop.
    Supports optional response channels for synchronous command execution.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize the command queue.

        Args:
            max_size: Maximum number of pending commands (prevents memory exhaustion)
        """
        self._queue: Queue[ExternalCommand] = Queue(maxsize=max_size)
        self._stats_lock = Lock()
        self._total_received = 0
        self._total_processed = 0
        self._total_dropped = 0

    def put(
        self,
        command: str,
        response_queue: Queue | None = None,
        source: str = "unknown",
        block: bool = False,
        timeout: float | None = None
    ) -> bool:
        """
        Add a command to the queue.

        Args:
            command: The command string to execute
            response_queue: Optional queue for sending response back
            source: Identifier for command source
            block: If True, block until space available
            timeout: Timeout for blocking (None = infinite)

        Returns:
            True if command was queued, False if queue was full
        """
        ext_cmd = ExternalCommand(
            command=command.strip(),
            response_queue=response_queue,
            source=source
        )

        try:
            self._queue.put(ext_cmd, block=block, timeout=timeout)
            with self._stats_lock:
                self._total_received += 1
            return True
        except Full:
            with self._stats_lock:
                self._total_dropped += 1
            return False

    def get_nowait(self) -> ExternalCommand | None:
        """
        Get a command without blocking.

        Returns:
            ExternalCommand if available, None otherwise
        """
        try:
            cmd = self._queue.get_nowait()
            with self._stats_lock:
                self._total_processed += 1
            return cmd
        except Empty:
            return None

    def get(self, block: bool = True, timeout: float | None = None) -> ExternalCommand | None:
        """
        Get a command, optionally blocking.

        Args:
            block: If True, block until command available
            timeout: Timeout for blocking (None = infinite)

        Returns:
            ExternalCommand if available, None on timeout
        """
        try:
            cmd = self._queue.get(block=block, timeout=timeout)
            with self._stats_lock:
                self._total_processed += 1
            return cmd
        except Empty:
            return None

    def clear(self) -> int:
        """
        Clear all pending commands.

        Returns:
            Number of commands cleared
        """
        cleared = 0
        while True:
            try:
                self._queue.get_nowait()
                cleared += 1
            except Empty:
                break
        return cleared

    @property
    def pending_count(self) -> int:
        """Number of commands waiting to be processed."""
        return self._queue.qsize()

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    @property
    def stats(self) -> dict:
        """Get queue statistics."""
        with self._stats_lock:
            return {
                "pending": self._queue.qsize(),
                "total_received": self._total_received,
                "total_processed": self._total_processed,
                "total_dropped": self._total_dropped,
            }


def send_response(ext_cmd: ExternalCommand, response: CommandResponse) -> None:
    """
    Send a response back to the command source if a response queue exists.

    Args:
        ext_cmd: The original external command
        response: The response to send
    """
    if ext_cmd.response_queue:
        try:
            ext_cmd.response_queue.put_nowait(response)
        except Full:
            pass  # Response queue full, drop response
