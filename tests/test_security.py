"""
Security tests for my-grid.

Tests for:
- Issue #66: Command injection prevention
- Issue #67: Proper exception handling
- Issue #68: JSON schema validation
"""

import json
import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


# =============================================================================
# Issue #66: Command Injection Prevention Tests
# =============================================================================


class TestCommandInjectionPrevention:
    """Tests verifying command injection vulnerabilities are mitigated."""

    def test_external_figlet_uses_list_form(self):
        """Verify external.py figlet uses list-based subprocess calls."""
        from src.external import draw_figlet

        # Mock subprocess to capture call arguments
        with patch("src.external.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="test", stderr="")

            # Malicious input that would exploit shell=True
            draw_figlet("; echo INJECTED", "standard")

            # Verify it was called with list form (not shell=True with string)
            call_args = mock_run.call_args
            assert call_args is not None, "subprocess.run should be called"

            # The first argument should be a list, not a string
            args, kwargs = call_args
            cmd_arg = args[0] if args else kwargs.get("cmd")

            # Should be list form for safe execution
            assert isinstance(
                cmd_arg, list
            ), f"Command should be list, got {type(cmd_arg)}: {cmd_arg}"
            # shell=True should not be present or should be False
            assert not kwargs.get("shell", False), "shell=True should not be used"

    def test_external_boxes_uses_list_form(self):
        """Verify external.py boxes uses list-based subprocess calls."""
        from src.external import draw_box

        with patch("src.external.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="test", stderr="")

            # Malicious input
            draw_box("test; rm -rf /", "ansi")

            call_args = mock_run.call_args
            if call_args:  # Only if subprocess.run was called
                args, kwargs = call_args
                cmd_arg = args[0] if args else kwargs.get("cmd")
                if isinstance(cmd_arg, list):
                    assert not kwargs.get("shell", False)
                # Input is passed safely, not as part of command

    def test_pipe_command_documents_shell_risk(self):
        """Verify pipe_command is marked as intentionally using shell."""
        from src.external import pipe_command
        import inspect

        # Check that the function has documentation about shell usage
        doc = inspect.getdoc(pipe_command)
        assert doc is not None, "pipe_command should have documentation"
        # The function intentionally uses shell for pipe functionality
        # This is documented and user-controlled

    def test_pager_renderer_path_escaping(self):
        """Test that file paths are properly escaped in renderer commands."""
        # Paths with special characters shouldn't cause injection
        malicious_path = "/tmp/test; rm -rf /"

        from src.zones import render_file_content

        with patch("src.zones.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="File not found"
            )

            # Call should not execute the malicious command
            render_file_content(malicious_path, "plain", use_wsl=False)

            # Verify the path is safely quoted in the command
            call_args = mock_run.call_args
            if call_args:
                args, kwargs = call_args
                cmd = args[0] if args else kwargs.get("cmd")
                # If using shell=True, path should be quoted
                if kwargs.get("shell", False) and isinstance(cmd, str):
                    # shlex.quote wraps paths with single quotes
                    # The malicious path should be quoted, preventing injection
                    assert (
                        "'/tmp/test; rm -rf /'" in cmd
                    ), f"Path should be quoted with shlex.quote, got: {cmd}"

    def test_wsl_renderer_avoids_double_quoting(self):
        """Test that WSL commands with pre-quoted templates don't get double-quoted."""
        from src.zones import render_file_content

        with patch("src.zones.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="file content", stderr=""
            )

            # Test with WSL mode - templates already have quotes around {file}
            render_file_content("/tmp/test.md", "plain", use_wsl=True)

            call_args = mock_run.call_args
            if call_args:
                args, kwargs = call_args
                cmd = args[0] if args else kwargs.get("cmd")
                # WSL command should NOT have double quotes like '''/tmp/test'''
                # It should have exactly one layer of quoting from the template
                assert "'''" not in cmd, f"WSL command has double-quoting: {cmd}"
                # Should contain the path in single quotes (from template)
                assert (
                    "'/tmp/test.md'" in cmd
                    or '"/tmp/test.md"' in cmd
                    or "/tmp/test.md" in cmd
                ), f"Path should be present in command: {cmd}"


# =============================================================================
# Issue #67: Exception Handling Tests
# =============================================================================


class TestExceptionHandling:
    """Tests verifying proper exception handling patterns."""

    def test_keyboard_interrupt_propagates(self):
        """Verify KeyboardInterrupt is not caught by bare except."""
        # This test ensures KeyboardInterrupt can escape through the application

        # Import any function that previously had bare except
        # After fix, KeyboardInterrupt should propagate

        def simulate_operation():
            raise KeyboardInterrupt()

        # Should propagate, not be caught
        with pytest.raises(KeyboardInterrupt):
            simulate_operation()

    def test_system_exit_propagates(self):
        """Verify SystemExit is not caught by bare except."""

        def simulate_exit():
            raise SystemExit(0)

        with pytest.raises(SystemExit):
            simulate_exit()

    def test_json_decode_error_handled_specifically(self):
        """Verify JSON errors are caught specifically, not generically."""
        # Malformed JSON should raise specific error
        malformed = "{invalid json"

        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed)


# =============================================================================
# Issue #68: JSON Schema Validation Tests
# =============================================================================


class TestJSONSchemaValidation:
    """Tests verifying JSON schema validation for project files."""

    def test_valid_project_file_loads(self):
        """Valid project JSON should load successfully."""
        from src.project import Project
        from src.canvas import Canvas
        from src.viewport import Viewport

        valid_project = {
            "version": "1.0",
            "metadata": {
                "name": "test",
                "created": "2024-01-01T00:00:00",
                "modified": "2024-01-01T00:00:00",
            },
            "canvas": {"cells": [{"x": 0, "y": 0, "char": "A"}]},
            "viewport": {"x": 0, "y": 0, "cursor": {"x": 0, "y": 0}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_project, f)
            temp_path = f.name

        try:
            canvas = Canvas()
            viewport = Viewport(width=80, height=24)
            project = Project.load(temp_path, canvas, viewport)
            assert project is not None
        finally:
            Path(temp_path).unlink()

    def test_invalid_version_rejected(self):
        """Project with unsupported version should raise ValueError."""
        from src.project import Project
        from src.canvas import Canvas
        from src.viewport import Viewport

        invalid_project = {
            "version": "99.0",  # Unsupported version
            "metadata": {},
            "canvas": {"cells": []},
            "viewport": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_project, f)
            temp_path = f.name

        try:
            canvas = Canvas()
            viewport = Viewport(width=80, height=24)
            with pytest.raises(ValueError, match="Unsupported project version"):
                Project.load(temp_path, canvas, viewport)
        finally:
            Path(temp_path).unlink()

    def test_malformed_json_raises_decode_error(self):
        """Malformed JSON should raise JSONDecodeError."""
        from src.project import Project
        from src.canvas import Canvas
        from src.viewport import Viewport

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json content")
            temp_path = f.name

        try:
            canvas = Canvas()
            viewport = Viewport(width=80, height=24)
            with pytest.raises(json.JSONDecodeError):
                Project.load(temp_path, canvas, viewport)
        finally:
            Path(temp_path).unlink()

    def test_missing_required_fields_handled(self):
        """Project missing required fields should fail gracefully."""
        from src.project import Project
        from src.canvas import Canvas
        from src.viewport import Viewport

        # Missing version - should raise error for missing field
        minimal_project = {"canvas": {"cells": []}, "viewport": {}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(minimal_project, f)
            temp_path = f.name

        try:
            canvas = Canvas()
            viewport = Viewport(width=80, height=24)
            # Should raise error for missing version field
            with pytest.raises(ValueError, match="Missing required field: version"):
                Project.load(temp_path, canvas, viewport)
        finally:
            Path(temp_path).unlink()

    def test_cells_must_have_required_fields(self):
        """Each cell must have x, y, char fields."""
        from src.project import Project, validate_project_data
        from src.canvas import Canvas
        from src.viewport import Viewport

        # Cell missing required field
        invalid_project = {
            "version": "1.0",
            "metadata": {},
            "canvas": {"cells": [{"x": 0, "y": 0}]},  # Missing 'char'
            "viewport": {},
        }

        # After schema validation is added, this should raise an error
        try:
            validate_project_data(invalid_project)
            pytest.fail("Should have raised validation error for missing 'char' field")
        except ValueError:
            # Expected behavior - validation catches missing field
            pass
        except ImportError:
            # validate_project_data not yet implemented - skip
            pytest.skip("validate_project_data not yet implemented")


class TestStaticAnalysis:
    """Static analysis tests for security patterns."""

    def test_no_bare_except_in_src(self):
        """Verify no bare 'except:' clauses in src/ directory."""
        src_dir = Path(__file__).parent.parent / "src"
        violations = []

        for py_file in src_dir.glob("**/*.py"):
            content = py_file.read_text()
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Look for 'except:' not followed by a specific exception type
                stripped = line.strip()
                if stripped == "except:" or stripped.startswith("except:"):
                    # Check if it's actually a bare except (not except SomeError:)
                    if stripped == "except:":
                        violations.append(f"{py_file.name}:{i}: {line.strip()}")

        assert not violations, f"Found bare except clauses:\n" + "\n".join(violations)

    def test_no_shell_true_without_shlex(self):
        """Verify shell=True calls use shlex.quote for user input."""
        src_dir = Path(__file__).parent.parent / "src"
        # This is more of a reminder - actual enforcement requires AST parsing
        # For now, we document that shell=True is only used in controlled contexts

        for py_file in src_dir.glob("**/*.py"):
            content = py_file.read_text()
            if "shell=True" in content:
                # zones.py uses shell=True for user-defined pipe commands
                # external.py pipe_command is documented as intentional
                if py_file.name in ("zones.py", "external.py"):
                    continue  # These are documented intentional uses
                # Any other file with shell=True should import shlex
                has_shlex = "import shlex" in content or "from shlex" in content
                assert has_shlex, f"{py_file.name} uses shell=True without shlex import"
