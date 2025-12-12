#!/usr/bin/env python3
"""
API server for my-grid external command interface.

Provides multiple protocols for external processes to send commands:
- TCP socket (cross-platform, default port 8765)
- Unix FIFO / named pipe (Linux/macOS/WSL)
- Windows named pipe (optional, requires pywin32)
"""

import json
import logging
import os
import socket
import stat
import threading
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from typing import Callable

from command_queue import CommandQueue, CommandResponse

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for the API server."""

    # TCP settings
    tcp_enabled: bool = True
    tcp_port: int = 8765
    tcp_host: str = "127.0.0.1"  # Local only by default

    # FIFO settings (Unix only)
    fifo_enabled: bool = True
    fifo_path: str = "/tmp/mygrid.fifo"

    # Windows named pipe (requires pywin32)
    pipe_enabled: bool = False
    pipe_name: str = r"\\.\pipe\mygrid"

    # Timeouts
    tcp_timeout: float = 1.0  # Socket accept timeout
    response_timeout: float = 5.0  # Wait for command response

    def __post_init__(self):
        # Auto-disable FIFO on Windows
        if os.name == 'nt':
            self.fifo_enabled = False


@dataclass
class ServerStatus:
    """Current status of the API server."""
    running: bool = False
    tcp_active: bool = False
    tcp_port: int | None = None
    fifo_active: bool = False
    fifo_path: str | None = None
    pipe_active: bool = False
    connections_handled: int = 0
    errors: list[str] = field(default_factory=list)


class APIServer:
    """
    Multi-protocol API server for external command interface.

    Runs listener threads for each enabled protocol.
    Commands are queued for processing by the main event loop.
    """

    def __init__(self, command_queue: CommandQueue):
        """
        Initialize the API server.

        Args:
            command_queue: Queue for sending commands to main loop
        """
        self.command_queue = command_queue
        self.config: ServerConfig | None = None
        self._running = False
        self._threads: list[threading.Thread] = []
        self._status = ServerStatus()
        self._lock = threading.Lock()

    def start(self, config: ServerConfig | None = None) -> None:
        """
        Start the API server with given configuration.

        Args:
            config: Server configuration (uses defaults if None)
        """
        if self._running:
            logger.warning("Server already running")
            return

        self.config = config or ServerConfig()
        self._running = True
        self._status.running = True

        # Start TCP listener
        if self.config.tcp_enabled:
            thread = threading.Thread(
                target=self._tcp_listener,
                name="mygrid-tcp",
                daemon=True
            )
            thread.start()
            self._threads.append(thread)

        # Start FIFO listener (Unix only)
        if self.config.fifo_enabled and os.name != 'nt':
            thread = threading.Thread(
                target=self._fifo_listener,
                name="mygrid-fifo",
                daemon=True
            )
            thread.start()
            self._threads.append(thread)

        # Start Windows named pipe (if pywin32 available)
        if self.config.pipe_enabled and os.name == 'nt':
            try:
                import win32pipe  # noqa: F401
                thread = threading.Thread(
                    target=self._pipe_listener,
                    name="mygrid-pipe",
                    daemon=True
                )
                thread.start()
                self._threads.append(thread)
            except ImportError:
                logger.warning("pywin32 not installed, Windows pipe disabled")
                self._status.errors.append("pywin32 not installed")

        logger.info(f"API server started: TCP={self.config.tcp_enabled}, "
                   f"FIFO={self.config.fifo_enabled and os.name != 'nt'}")

    def stop(self) -> None:
        """Stop the API server and all listener threads."""
        self._running = False
        self._status.running = False

        # Clean up FIFO
        if self.config and self.config.fifo_enabled:
            try:
                fifo_path = Path(self.config.fifo_path)
                if fifo_path.exists():
                    fifo_path.unlink()
            except OSError:
                pass

        # Threads are daemons, they'll stop when main exits
        self._threads.clear()
        logger.info("API server stopped")

    @property
    def status(self) -> ServerStatus:
        """Get current server status."""
        with self._lock:
            return self._status

    def _tcp_listener(self) -> None:
        """TCP socket listener thread."""
        config = self.config
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((config.tcp_host, config.tcp_port))
                server.listen(5)
                server.settimeout(config.tcp_timeout)

                with self._lock:
                    self._status.tcp_active = True
                    self._status.tcp_port = config.tcp_port

                logger.info(f"TCP listener started on {config.tcp_host}:{config.tcp_port}")

                while self._running:
                    try:
                        conn, addr = server.accept()
                        self._handle_tcp_connection(conn, addr)
                    except socket.timeout:
                        continue
                    except OSError as e:
                        if self._running:
                            logger.error(f"TCP accept error: {e}")

        except Exception as e:
            logger.error(f"TCP listener failed: {e}")
            with self._lock:
                self._status.errors.append(f"TCP: {e}")
        finally:
            with self._lock:
                self._status.tcp_active = False

    def _handle_tcp_connection(self, conn: socket.socket, addr: tuple) -> None:
        """Handle a single TCP connection."""
        try:
            conn.settimeout(5.0)
            data = b""

            # Read until connection closed or newline
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b'\n' in data or len(data) > 65536:
                    break

            if not data:
                return

            # Parse and execute commands
            commands = data.decode('utf-8', errors='replace').strip().split('\n')
            responses = []

            for cmd in commands:
                cmd = cmd.strip()
                if not cmd:
                    continue

                # Create response queue for synchronous execution
                response_queue: Queue[CommandResponse] = Queue()
                self.command_queue.put(cmd, response_queue=response_queue, source="tcp")

                # Wait for response
                try:
                    response = response_queue.get(timeout=self.config.response_timeout)
                    responses.append(response.to_dict())
                except Exception:
                    responses.append({"status": "error", "message": "Command timeout"})

            # Send responses
            response_data = '\n'.join(json.dumps(r) for r in responses) + '\n'
            conn.sendall(response_data.encode('utf-8'))

            with self._lock:
                self._status.connections_handled += 1

        except Exception as e:
            logger.debug(f"TCP connection error: {e}")
        finally:
            conn.close()

    def _fifo_listener(self) -> None:
        """Unix FIFO listener thread."""
        config = self.config
        fifo_path = Path(config.fifo_path)

        try:
            # Create FIFO if it doesn't exist
            if fifo_path.exists():
                if not stat.S_ISFIFO(fifo_path.stat().st_mode):
                    fifo_path.unlink()
                    os.mkfifo(str(fifo_path), mode=0o600)
            else:
                os.mkfifo(str(fifo_path), mode=0o600)

            with self._lock:
                self._status.fifo_active = True
                self._status.fifo_path = str(fifo_path)

            logger.info(f"FIFO listener started on {fifo_path}")

            while self._running:
                try:
                    # Open blocks until a writer connects
                    with open(fifo_path, 'r') as fifo:
                        for line in fifo:
                            if not self._running:
                                break
                            cmd = line.strip()
                            if cmd:
                                # FIFO is fire-and-forget, no response
                                self.command_queue.put(cmd, source="fifo")
                except OSError as e:
                    if self._running:
                        logger.debug(f"FIFO read error: {e}")

        except Exception as e:
            logger.error(f"FIFO listener failed: {e}")
            with self._lock:
                self._status.errors.append(f"FIFO: {e}")
        finally:
            with self._lock:
                self._status.fifo_active = False
            # Clean up FIFO
            try:
                if fifo_path.exists():
                    fifo_path.unlink()
            except OSError:
                pass

    def _pipe_listener(self) -> None:
        """Windows named pipe listener thread."""
        try:
            import win32pipe
            import win32file
            import pywintypes
        except ImportError:
            logger.error("pywin32 required for Windows named pipes")
            return

        config = self.config
        pipe_name = config.pipe_name

        try:
            with self._lock:
                self._status.pipe_active = True

            logger.info(f"Windows pipe listener started on {pipe_name}")

            while self._running:
                try:
                    # Create pipe instance
                    pipe = win32pipe.CreateNamedPipe(
                        pipe_name,
                        win32pipe.PIPE_ACCESS_DUPLEX,
                        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                        1,  # Max instances
                        65536,  # Out buffer
                        65536,  # In buffer
                        0,  # Timeout
                        None  # Security
                    )

                    # Wait for client
                    win32pipe.ConnectNamedPipe(pipe, None)

                    # Read command
                    result, data = win32file.ReadFile(pipe, 65536)
                    commands = data.decode('utf-8', errors='replace').strip().split('\n')
                    responses = []

                    for cmd in commands:
                        cmd = cmd.strip()
                        if not cmd:
                            continue

                        response_queue: Queue[CommandResponse] = Queue()
                        self.command_queue.put(cmd, response_queue=response_queue, source="pipe")

                        try:
                            response = response_queue.get(timeout=self.config.response_timeout)
                            responses.append(response.to_dict())
                        except Exception:
                            responses.append({"status": "error", "message": "Command timeout"})

                    # Send response
                    response_data = '\n'.join(json.dumps(r) for r in responses) + '\n'
                    win32file.WriteFile(pipe, response_data.encode('utf-8'))

                    win32file.CloseHandle(pipe)

                    with self._lock:
                        self._status.connections_handled += 1

                except pywintypes.error as e:
                    if self._running:
                        logger.debug(f"Pipe error: {e}")

        except Exception as e:
            logger.error(f"Pipe listener failed: {e}")
            with self._lock:
                self._status.errors.append(f"Pipe: {e}")
        finally:
            with self._lock:
                self._status.pipe_active = False
