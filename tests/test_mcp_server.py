#!/usr/bin/env python3
"""
Tests for MCP server module.

Tests the MCP server tool definitions and client connection logic.
"""

import pytest
from unittest.mock import MagicMock, patch
import json


class TestMCPServerImports:
    """Test that MCP server module imports correctly."""

    def test_import_mcp_server(self):
        """Test that mcp_server module can be imported."""
        from src.mcp_server import mcp, client, MyGridClient, MyGridConnection

        assert mcp is not None
        assert client is not None
        assert MyGridClient is not None
        assert MyGridConnection is not None

    def test_mcp_server_name(self):
        """Test MCP server has correct name."""
        from src.mcp_server import mcp

        assert mcp.name == "my-grid"

    def test_mcp_server_has_instructions(self):
        """Test MCP server has instructions."""
        from src.mcp_server import mcp

        assert mcp.instructions is not None
        assert "my-grid" in mcp.instructions.lower()


class TestMCPTools:
    """Test MCP tool registrations."""

    def test_all_tools_registered(self):
        """Test that all expected tools are registered."""
        from src.mcp_server import mcp

        tools = list(mcp._tool_manager._tools.keys())

        # Canvas tools
        assert "canvas_text" in tools
        assert "canvas_rect" in tools
        assert "canvas_line" in tools
        assert "canvas_clear" in tools
        assert "canvas_fill" in tools
        assert "canvas_box" in tools
        assert "canvas_figlet" in tools

        # Navigation tools
        assert "canvas_goto" in tools
        assert "canvas_status" in tools
        assert "canvas_origin" in tools

        # Zone tools
        assert "zone_create" in tools
        assert "zone_pipe" in tools
        assert "zone_watch" in tools
        assert "zone_http" in tools
        assert "zone_pty" in tools
        assert "zone_delete" in tools
        assert "zone_goto" in tools
        assert "zone_list" in tools
        assert "zone_info" in tools
        assert "zone_refresh" in tools
        assert "zone_send" in tools

        # Bookmark tools
        assert "bookmark_set" in tools
        assert "bookmark_jump" in tools
        assert "bookmark_list" in tools
        assert "bookmark_delete" in tools

        # Layout tools
        assert "layout_load" in tools
        assert "layout_save" in tools
        assert "layout_list" in tools

        # Project tools
        assert "project_save" in tools
        assert "project_export" in tools
        assert "execute_command" in tools
        assert "check_connection" in tools

    def test_tool_count(self):
        """Test total number of registered tools."""
        from src.mcp_server import mcp

        tools = list(mcp._tool_manager._tools.keys())
        assert len(tools) == 32


class TestMyGridConnection:
    """Test MyGridConnection configuration."""

    def test_default_config(self):
        """Test default connection configuration."""
        from src.mcp_server import MyGridConnection

        config = MyGridConnection()
        assert config.host == "127.0.0.1"
        assert config.port == 8765
        assert config.timeout == 5.0

    def test_custom_config(self):
        """Test custom connection configuration."""
        from src.mcp_server import MyGridConnection

        config = MyGridConnection(host="192.168.1.1", port=9999, timeout=10.0)
        assert config.host == "192.168.1.1"
        assert config.port == 9999
        assert config.timeout == 10.0


class TestMyGridClient:
    """Test MyGridClient functionality."""

    def test_client_default_config(self):
        """Test client uses default config."""
        from src.mcp_server import MyGridClient

        client = MyGridClient()
        assert client.config.host == "127.0.0.1"
        assert client.config.port == 8765

    def test_client_custom_config(self):
        """Test client with custom config."""
        from src.mcp_server import MyGridClient, MyGridConnection

        config = MyGridConnection(port=9999)
        client = MyGridClient(config)
        assert client.config.port == 9999

    @patch("socket.socket")
    def test_send_command_success(self, mock_socket_class):
        """Test successful command sending."""
        from src.mcp_server import MyGridClient

        # Setup mock socket
        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock response
        response_data = json.dumps({"status": "ok", "message": "Test passed"})
        mock_socket.recv.side_effect = [response_data.encode("utf-8") + b"\n", b""]

        client = MyGridClient()
        result = client.send_command(":test")

        assert result["status"] == "ok"
        assert result["message"] == "Test passed"

    @patch("socket.socket")
    def test_send_command_connection_refused(self, mock_socket_class):
        """Test connection refused handling."""
        from src.mcp_server import MyGridClient

        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_socket.connect.side_effect = ConnectionRefusedError()

        client = MyGridClient()
        with pytest.raises(ConnectionError) as excinfo:
            client.send_command(":test")

        assert "Cannot connect to my-grid" in str(excinfo.value)

    @patch("socket.socket")
    def test_is_connected_true(self, mock_socket_class):
        """Test is_connected when server is reachable."""
        from src.mcp_server import MyGridClient

        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        client = MyGridClient()
        assert client.is_connected() is True

    @patch("socket.socket")
    def test_is_connected_false(self, mock_socket_class):
        """Test is_connected when server is unreachable."""
        from src.mcp_server import MyGridClient

        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_socket.connect.side_effect = ConnectionRefusedError()

        client = MyGridClient()
        assert client.is_connected() is False


class TestToolFunctions:
    """Test individual tool function behavior."""

    @patch("src.mcp_server.client")
    def test_canvas_text_simple(self, mock_client):
        """Test canvas_text with just text."""
        from src.mcp_server import canvas_text

        mock_client.send_command.return_value = {
            "status": "ok",
            "message": "Text written",
        }

        result = canvas_text("Hello World")

        mock_client.send_command.assert_called_with(":text Hello World")
        assert "Text written" in result

    @patch("src.mcp_server.client")
    def test_canvas_text_with_coords(self, mock_client):
        """Test canvas_text with coordinates."""
        from src.mcp_server import canvas_text

        mock_client.send_command.return_value = {"status": "ok", "message": "OK"}

        canvas_text("Hello", x=10, y=20)

        # Should call goto first
        calls = mock_client.send_command.call_args_list
        assert any(":goto 10 20" in str(call) for call in calls)

    @patch("src.mcp_server.client")
    def test_zone_create_at_cursor(self, mock_client):
        """Test zone_create without coordinates uses cursor position."""
        from src.mcp_server import zone_create

        mock_client.send_command.return_value = {
            "status": "ok",
            "message": "Zone created",
        }

        zone_create("TEST", 40, 20)

        mock_client.send_command.assert_called_with(":zone create TEST here 40 20")

    @patch("src.mcp_server.client")
    def test_zone_create_with_coords(self, mock_client):
        """Test zone_create with specific coordinates."""
        from src.mcp_server import zone_create

        mock_client.send_command.return_value = {
            "status": "ok",
            "message": "Zone created",
        }

        zone_create("TEST", 40, 20, x=100, y=50)

        mock_client.send_command.assert_called_with(":zone create TEST 100 50 40 20")

    @patch("src.mcp_server.client")
    def test_execute_command(self, mock_client):
        """Test execute_command passes through commands."""
        from src.mcp_server import execute_command

        mock_client.send_command.return_value = {"status": "ok", "message": "Done"}

        result = execute_command(":custom command here")

        mock_client.send_command.assert_called_with(":custom command here")
        assert "Done" in result

    @patch("src.mcp_server.client")
    def test_check_connection_connected(self, mock_client):
        """Test check_connection when connected."""
        from src.mcp_server import check_connection

        mock_client.is_connected.return_value = True
        mock_client.config.host = "127.0.0.1"
        mock_client.config.port = 8765

        result = check_connection()

        assert "Connected" in result

    @patch("src.mcp_server.client")
    def test_check_connection_not_connected(self, mock_client):
        """Test check_connection when not connected."""
        from src.mcp_server import check_connection

        mock_client.is_connected.return_value = False
        mock_client.config.host = "127.0.0.1"
        mock_client.config.port = 8765

        result = check_connection()

        assert "Cannot connect" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
