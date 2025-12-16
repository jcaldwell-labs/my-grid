"""
Project save/load for ASCII canvas editor.

Handles JSON project files with canvas data, viewport state, and settings.
Also supports plain text export/import.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from canvas import Canvas
    from viewport import Viewport
    from renderer import GridSettings
    from modes import ModeConfig, BookmarkManager
    from zones import ZoneManager


# Project file version for format compatibility
PROJECT_VERSION = "1.0"


@dataclass
class ProjectMetadata:
    """Project metadata."""
    name: str = "Untitled"
    created: str = ""
    modified: str = ""
    version: str = PROJECT_VERSION
    description: str = ""

    def touch(self) -> None:
        """Update modified timestamp."""
        self.modified = datetime.now().isoformat()

    @classmethod
    def new(cls, name: str = "Untitled") -> "ProjectMetadata":
        """Create new metadata with timestamps."""
        now = datetime.now().isoformat()
        return cls(name=name, created=now, modified=now)


@dataclass
class Project:
    """
    Manages project state and file operations.

    A project contains:
    - Canvas data (sparse cell storage)
    - Viewport state (position, cursor, origin)
    - Grid settings
    - Metadata (name, timestamps)
    """
    filepath: Path | None = None
    metadata: ProjectMetadata = field(default_factory=ProjectMetadata.new)
    _dirty: bool = False

    @property
    def dirty(self) -> bool:
        """True if project has unsaved changes."""
        return self._dirty

    @property
    def filename(self) -> str:
        """Get filename or 'Untitled'."""
        if self.filepath:
            return self.filepath.name
        return "Untitled"

    @property
    def display_name(self) -> str:
        """Get display name with dirty indicator."""
        name = self.filename
        if self._dirty:
            name = f"*{name}"
        return name

    def mark_dirty(self) -> None:
        """Mark project as having unsaved changes."""
        self._dirty = True

    def mark_clean(self) -> None:
        """Mark project as saved."""
        self._dirty = False

    def save(
        self,
        canvas: "Canvas",
        viewport: "Viewport",
        grid_settings: "GridSettings | None" = None,
        bookmarks: "BookmarkManager | None" = None,
        zones: "ZoneManager | None" = None,
        filepath: Path | str | None = None
    ) -> Path:
        """
        Save project to JSON file.

        Args:
            canvas: Canvas to save
            viewport: Viewport state to save
            grid_settings: Optional grid settings to save
            bookmarks: Optional bookmarks to save
            zones: Optional zone manager to save
            filepath: Path to save to (uses self.filepath if None)

        Returns:
            Path where file was saved

        Raises:
            ValueError: If no filepath specified and none set
        """
        if filepath:
            self.filepath = Path(filepath)
        elif not self.filepath:
            raise ValueError("No filepath specified for save")

        self.metadata.touch()

        data = {
            "version": PROJECT_VERSION,
            "metadata": {
                "name": self.metadata.name,
                "created": self.metadata.created,
                "modified": self.metadata.modified,
                "description": self.metadata.description,
            },
            "canvas": canvas.to_dict(),
            "viewport": viewport.to_dict(),
        }

        if grid_settings:
            data["grid"] = {
                "show_origin": grid_settings.show_origin,
                "show_major_lines": grid_settings.show_major_lines,
                "show_minor_lines": grid_settings.show_minor_lines,
                "major_interval": grid_settings.major_interval,
                "minor_interval": grid_settings.minor_interval,
            }

        if bookmarks:
            data["bookmarks"] = bookmarks.to_dict()

        if zones and len(zones) > 0:
            data["zones"] = zones.to_dict()

        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        self.mark_clean()
        return self.filepath

    @classmethod
    def load(
        cls,
        filepath: Path | str,
        canvas: "Canvas",
        viewport: "Viewport",
        grid_settings: "GridSettings | None" = None,
        bookmarks: "BookmarkManager | None" = None,
        zones: "ZoneManager | None" = None
    ) -> "Project":
        """
        Load project from JSON file.

        Args:
            filepath: Path to load from
            canvas: Canvas to populate
            viewport: Viewport to restore
            grid_settings: Optional grid settings to restore
            bookmarks: Optional bookmark manager to restore
            zones: Optional zone manager to restore

        Returns:
            Project instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        filepath = Path(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Version check
        version = data.get("version", "0.0")
        if not version.startswith("1."):
            raise ValueError(f"Unsupported project version: {version}")

        # Load metadata
        meta_data = data.get("metadata", {})
        metadata = ProjectMetadata(
            name=meta_data.get("name", filepath.stem),
            created=meta_data.get("created", ""),
            modified=meta_data.get("modified", ""),
            version=version,
            description=meta_data.get("description", ""),
        )

        # Load canvas
        canvas.clear_all()
        canvas_data = data.get("canvas", {})
        for cell in canvas_data.get("cells", []):
            canvas.set(cell["x"], cell["y"], cell["char"])

        # Load viewport
        vp_data = data.get("viewport", {})
        viewport.x = vp_data.get("x", 0)
        viewport.y = vp_data.get("y", 0)

        if "cursor" in vp_data:
            viewport.cursor.x = vp_data["cursor"].get("x", 0)
            viewport.cursor.y = vp_data["cursor"].get("y", 0)

        if "origin" in vp_data:
            viewport.origin.x = vp_data["origin"].get("x", 0)
            viewport.origin.y = vp_data["origin"].get("y", 0)

        if "y_direction" in vp_data:
            from viewport import YAxisDirection
            viewport.y_direction = YAxisDirection[vp_data["y_direction"]]

        # Load grid settings
        if grid_settings and "grid" in data:
            grid_data = data["grid"]
            grid_settings.show_origin = grid_data.get("show_origin", True)
            grid_settings.show_major_lines = grid_data.get("show_major_lines", False)
            grid_settings.show_minor_lines = grid_data.get("show_minor_lines", False)
            grid_settings.major_interval = grid_data.get("major_interval", 10)
            grid_settings.minor_interval = grid_data.get("minor_interval", 5)

        # Load bookmarks
        if bookmarks and "bookmarks" in data:
            from modes import BookmarkManager
            bm_data = data["bookmarks"]
            for key, bm in bm_data.items():
                bookmarks.set(key, bm.get("x", 0), bm.get("y", 0), bm.get("name", ""))

        # Load zones
        if zones and "zones" in data:
            from zones import ZoneManager
            zones.clear()
            loaded_zones = ZoneManager.from_dict(data["zones"])
            for zone in loaded_zones:
                zones._zones[zone.name.lower()] = zone

        project = cls(filepath=filepath, metadata=metadata)
        project.mark_clean()
        return project

    def export_text(
        self,
        canvas: "Canvas",
        filepath: Path | str | None = None,
        include_empty_lines: bool = True
    ) -> Path:
        """
        Export canvas as plain text file.

        Args:
            canvas: Canvas to export
            filepath: Path to export to (defaults to .txt version of project file)
            include_empty_lines: Include lines that are entirely spaces

        Returns:
            Path where file was saved
        """
        if filepath:
            export_path = Path(filepath)
        elif self.filepath:
            export_path = self.filepath.with_suffix('.txt')
        else:
            export_path = Path("export.txt")

        bbox = canvas.bounding_box()
        if not bbox:
            # Empty canvas
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("")
            return export_path

        lines = []
        for y in range(bbox.min_y, bbox.max_y + 1):
            line_chars = []
            for x in range(bbox.min_x, bbox.max_x + 1):
                line_chars.append(canvas.get_char(x, y))
            line = ''.join(line_chars).rstrip()  # Remove trailing spaces

            if include_empty_lines or line:
                lines.append(line)

        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        with open(export_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            if lines:
                f.write('\n')  # Final newline

        return export_path

    @classmethod
    def import_text(
        cls,
        filepath: Path | str,
        canvas: "Canvas",
        viewport: "Viewport",
        start_x: int = 0,
        start_y: int = 0
    ) -> "Project":
        """
        Import plain text file into canvas.

        Args:
            filepath: Path to text file
            canvas: Canvas to populate
            viewport: Viewport to reset
            start_x: X offset for imported content
            start_y: Y offset for imported content

        Returns:
            Project instance
        """
        filepath = Path(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        canvas.clear_all()

        y = start_y
        for line in content.splitlines():
            for x, char in enumerate(line):
                if char != ' ':
                    canvas.set(start_x + x, y, char)
            y += 1

        # Reset viewport
        viewport.x = 0
        viewport.y = 0
        viewport.cursor.set(start_x, start_y)

        metadata = ProjectMetadata.new(name=filepath.stem)
        project = cls(filepath=None, metadata=metadata)  # No filepath - needs Save As
        project.mark_dirty()  # Imported content is "unsaved"
        return project


def get_recent_projects(max_count: int = 10) -> list[Path]:
    """
    Get list of recently opened project files.

    Reads from ~/.mygrid/recent.json if it exists.
    """
    config_dir = Path.home() / ".mygrid"
    recent_file = config_dir / "recent.json"

    if not recent_file.exists():
        return []

    try:
        with open(recent_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        paths = [Path(p) for p in data.get("recent", [])]
        # Filter to existing files only
        return [p for p in paths if p.exists()][:max_count]
    except (json.JSONDecodeError, KeyError):
        return []


def add_recent_project(filepath: Path | str, max_count: int = 10) -> None:
    """
    Add a project to the recent files list.
    """
    filepath = Path(filepath).resolve()
    config_dir = Path.home() / ".mygrid"
    config_dir.mkdir(exist_ok=True)
    recent_file = config_dir / "recent.json"

    # Load existing
    recent = []
    if recent_file.exists():
        try:
            with open(recent_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            recent = data.get("recent", [])
        except (json.JSONDecodeError, KeyError):
            pass

    # Add to front, remove duplicates
    filepath_str = str(filepath)
    if filepath_str in recent:
        recent.remove(filepath_str)
    recent.insert(0, filepath_str)
    recent = recent[:max_count]

    # Save
    with open(recent_file, 'w', encoding='utf-8') as f:
        json.dump({"recent": recent}, f, indent=2)


def suggest_filename(canvas: "Canvas", base: str = "canvas") -> str:
    """
    Suggest a filename based on canvas content.

    Uses first line of text if available, otherwise base name.
    """
    bbox = canvas.bounding_box()
    if not bbox:
        return f"{base}.json"

    # Try to get first non-empty line as name
    for y in range(bbox.min_y, min(bbox.min_y + 5, bbox.max_y + 1)):
        line_chars = []
        for x in range(bbox.min_x, min(bbox.min_x + 30, bbox.max_x + 1)):
            char = canvas.get_char(x, y)
            if char.isalnum() or char in ' -_':
                line_chars.append(char)
        line = ''.join(line_chars).strip()
        if line:
            # Clean up for filename
            safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in line)
            safe_name = safe_name.strip('_')[:30]
            if safe_name:
                return f"{safe_name}.json"

    return f"{base}.json"


class SessionManager:
    """
    Manages auto-save and session recovery.

    Sessions are saved to ~/.mygrid/sessions/ with timestamps.
    Supports recovery from crashes and session history browsing.
    """

    def __init__(self, interval_seconds: int = 30, max_sessions: int = 20):
        """
        Initialize session manager.

        Args:
            interval_seconds: Auto-save interval (default 30s)
            max_sessions: Maximum sessions to keep in history
        """
        self.interval_seconds = interval_seconds
        self.max_sessions = max_sessions
        self._last_save_time: float = 0
        self._session_id: str = ""
        self._enabled = True

        # Ensure session directory exists
        self._session_dir = Path.home() / ".mygrid" / "sessions"
        self._session_dir.mkdir(parents=True, exist_ok=True)

        # Generate session ID for this run
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    @property
    def session_dir(self) -> Path:
        """Get the sessions directory."""
        return self._session_dir

    @property
    def enabled(self) -> bool:
        """Whether auto-save is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable auto-save."""
        self._enabled = value

    def get_session_file(self, suffix: str = "") -> Path:
        """Get the path for current session file."""
        name = f"session_{self._session_id}"
        if suffix:
            name = f"{name}_{suffix}"
        return self._session_dir / f"{name}.json"

    def should_save(self) -> bool:
        """Check if it's time for auto-save."""
        if not self._enabled:
            return False

        import time
        current_time = time.time()
        if current_time - self._last_save_time >= self.interval_seconds:
            return True
        return False

    def auto_save(
        self,
        canvas: "Canvas",
        viewport: "Viewport",
        grid_settings: "GridSettings | None" = None,
        bookmarks: "BookmarkManager | None" = None,
        zones: "ZoneManager | None" = None
    ) -> Path | None:
        """
        Perform auto-save if interval has elapsed.

        Returns:
            Path where session was saved, or None if not saved
        """
        if not self.should_save():
            return None

        import time
        self._last_save_time = time.time()

        # Save to session file
        session_path = self.get_session_file()

        try:
            data = {
                "version": PROJECT_VERSION,
                "session_id": self._session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "name": "Auto-save Session",
                    "created": datetime.now().isoformat(),
                    "modified": datetime.now().isoformat(),
                },
                "canvas": canvas.to_dict(),
                "viewport": viewport.to_dict(),
            }

            if grid_settings:
                data["grid"] = {
                    "show_origin": grid_settings.show_origin,
                    "show_major_lines": grid_settings.show_major_lines,
                    "show_minor_lines": grid_settings.show_minor_lines,
                    "major_interval": grid_settings.major_interval,
                    "minor_interval": grid_settings.minor_interval,
                }

            if bookmarks:
                data["bookmarks"] = bookmarks.to_dict()

            if zones and len(zones) > 0:
                data["zones"] = zones.to_dict()

            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Cleanup old sessions
            self._cleanup_old_sessions()

            return session_path
        except Exception:
            return None

    def _cleanup_old_sessions(self) -> None:
        """Remove old session files beyond max_sessions limit."""
        try:
            sessions = sorted(
                self._session_dir.glob("session_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Keep only the most recent sessions
            for old_session in sessions[self.max_sessions:]:
                old_session.unlink()
        except Exception:
            pass  # Ignore cleanup errors

    def list_sessions(self) -> list[dict]:
        """
        List available sessions with metadata.

        Returns:
            List of session info dicts with id, timestamp, path
        """
        sessions = []

        try:
            for session_file in sorted(
                self._session_dir.glob("session_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            ):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    sessions.append({
                        "id": data.get("session_id", session_file.stem),
                        "timestamp": data.get("timestamp", "Unknown"),
                        "path": session_file,
                        "name": data.get("metadata", {}).get("name", "Session"),
                    })
                except (json.JSONDecodeError, KeyError):
                    # Include file even if we can't read metadata
                    sessions.append({
                        "id": session_file.stem,
                        "timestamp": datetime.fromtimestamp(
                            session_file.stat().st_mtime
                        ).isoformat(),
                        "path": session_file,
                        "name": "Unknown",
                    })
        except Exception:
            pass

        return sessions

    def get_latest_session(self) -> Path | None:
        """Get the most recent session file."""
        sessions = self.list_sessions()
        if sessions:
            return sessions[0]["path"]
        return None

    def restore_session(
        self,
        session_path: Path,
        canvas: "Canvas",
        viewport: "Viewport",
        grid_settings: "GridSettings | None" = None,
        bookmarks: "BookmarkManager | None" = None,
        zones: "ZoneManager | None" = None
    ) -> bool:
        """
        Restore a session from file.

        Args:
            session_path: Path to session file
            canvas: Canvas to restore to
            viewport: Viewport to restore
            grid_settings: Optional grid settings
            bookmarks: Optional bookmark manager
            zones: Optional zone manager

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load canvas
            canvas.clear_all()
            canvas_data = data.get("canvas", {})
            for cell in canvas_data.get("cells", []):
                canvas.set(cell["x"], cell["y"], cell["char"])

            # Load viewport
            vp_data = data.get("viewport", {})
            viewport.x = vp_data.get("x", 0)
            viewport.y = vp_data.get("y", 0)

            if "cursor" in vp_data:
                viewport.cursor.x = vp_data["cursor"].get("x", 0)
                viewport.cursor.y = vp_data["cursor"].get("y", 0)

            if "origin" in vp_data:
                viewport.origin.x = vp_data["origin"].get("x", 0)
                viewport.origin.y = vp_data["origin"].get("y", 0)

            if "y_direction" in vp_data:
                from viewport import YAxisDirection
                viewport.y_direction = YAxisDirection[vp_data["y_direction"]]

            # Load grid settings
            if grid_settings and "grid" in data:
                grid_data = data["grid"]
                grid_settings.show_origin = grid_data.get("show_origin", True)
                grid_settings.show_major_lines = grid_data.get("show_major_lines", False)
                grid_settings.show_minor_lines = grid_data.get("show_minor_lines", False)
                grid_settings.major_interval = grid_data.get("major_interval", 10)
                grid_settings.minor_interval = grid_data.get("minor_interval", 5)

            # Load bookmarks
            if bookmarks and "bookmarks" in data:
                bm_data = data["bookmarks"]
                for key, bm in bm_data.items():
                    bookmarks.set(key, bm.get("x", 0), bm.get("y", 0), bm.get("name", ""))

            # Load zones
            if zones and "zones" in data:
                from zones import ZoneManager
                zones.clear()
                loaded_zones = ZoneManager.from_dict(data["zones"])
                for zone in loaded_zones:
                    zones._zones[zone.name.lower()] = zone

            return True
        except Exception:
            return False

    def clear_current_session(self) -> None:
        """Clear the current session file (for clean exit)."""
        session_path = self.get_session_file()
        if session_path.exists():
            try:
                session_path.unlink()
            except Exception:
                pass

    def check_for_recovery(self) -> Path | None:
        """
        Check if there's a session from a previous crash to recover.

        Returns:
            Path to recovery file if found, None otherwise
        """
        # Look for sessions older than current one but not too old (within 24h)
        latest = self.get_latest_session()
        if not latest:
            return None

        try:
            # Check if session is from a different run (not current session)
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)

            session_id = data.get("session_id", "")
            if session_id != self._session_id:
                # Found a session from previous run
                timestamp_str = data.get("timestamp", "")
                if timestamp_str:
                    session_time = datetime.fromisoformat(timestamp_str)
                    age = datetime.now() - session_time
                    # Only offer recovery for sessions less than 24 hours old
                    if age.total_seconds() < 86400:
                        return latest
        except Exception:
            pass

        return None
