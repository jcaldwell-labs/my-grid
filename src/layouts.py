"""
Layout system for workspace templates.

Layouts are YAML files that define zone configurations for quick workspace setup.
Stored in ~/.config/mygrid/layouts/ by default.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from zones import ZoneManager, ZoneExecutor, ZoneType, ZoneConfig


# Default layouts directory
def get_layouts_dir() -> Path:
    """Get the layouts directory, creating if needed."""
    if os.name == 'nt':
        # Windows: use APPDATA
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    else:
        # Unix: use XDG_CONFIG_HOME or ~/.config
        base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))

    layouts_dir = base / 'mygrid' / 'layouts'
    layouts_dir.mkdir(parents=True, exist_ok=True)
    return layouts_dir


@dataclass
class LayoutZone:
    """Zone definition within a layout."""
    name: str
    zone_type: str  # static, pipe, watch, pty
    x: int
    y: int
    width: int
    height: int
    command: str | None = None
    interval: float | None = None  # For watch zones
    shell: str | None = None  # For PTY zones
    bookmark: str | None = None
    description: str = ""

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        data = {
            "name": self.name,
            "type": self.zone_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
        if self.command:
            data["command"] = self.command
        if self.interval is not None:
            data["interval"] = self.interval
        if self.shell:
            data["shell"] = self.shell
        if self.bookmark:
            data["bookmark"] = self.bookmark
        if self.description:
            data["description"] = self.description
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "LayoutZone":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            zone_type=data.get("type", "static"),
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 40),
            height=data.get("height", 20),
            command=data.get("command"),
            interval=data.get("interval"),
            shell=data.get("shell"),
            bookmark=data.get("bookmark"),
            description=data.get("description", ""),
        )


@dataclass
class Layout:
    """A workspace layout configuration."""
    name: str
    description: str
    zones: list[LayoutZone]

    # Optional viewport settings
    cursor_x: int | None = None
    cursor_y: int | None = None
    viewport_x: int | None = None
    viewport_y: int | None = None

    def to_dict(self) -> dict:
        """Serialize to dictionary for YAML export."""
        data = {
            "name": self.name,
            "description": self.description,
            "zones": [z.to_dict() for z in self.zones],
        }
        if self.cursor_x is not None:
            data["cursor"] = {"x": self.cursor_x, "y": self.cursor_y}
        if self.viewport_x is not None:
            data["viewport"] = {"x": self.viewport_x, "y": self.viewport_y}
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Layout":
        """Deserialize from dictionary."""
        zones = [LayoutZone.from_dict(z) for z in data.get("zones", [])]
        cursor = data.get("cursor", {})
        viewport = data.get("viewport", {})
        return cls(
            name=data.get("name", "Unnamed"),
            description=data.get("description", ""),
            zones=zones,
            cursor_x=cursor.get("x"),
            cursor_y=cursor.get("y"),
            viewport_x=viewport.get("x"),
            viewport_y=viewport.get("y"),
        )

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "Layout":
        """Parse from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class LayoutManager:
    """
    Manages workspace layouts.

    Handles saving, loading, listing, and deleting layout files.
    """

    def __init__(self, layouts_dir: Path | None = None):
        self.layouts_dir = layouts_dir or get_layouts_dir()

    def _layout_path(self, name: str) -> Path:
        """Get path for a layout file."""
        # Sanitize name
        safe_name = "".join(c for c in name if c.isalnum() or c in '-_').lower()
        return self.layouts_dir / f"{safe_name}.yaml"

    def save(self, layout: Layout) -> Path:
        """
        Save a layout to file.

        Returns the path where it was saved.
        """
        path = self._layout_path(layout.name)
        path.write_text(layout.to_yaml(), encoding='utf-8')
        return path

    def load(self, name: str) -> Layout | None:
        """
        Load a layout by name.

        Returns None if not found.
        """
        path = self._layout_path(name)
        if not path.exists():
            return None

        try:
            yaml_str = path.read_text(encoding='utf-8')
            return Layout.from_yaml(yaml_str)
        except Exception:
            return None

    def delete(self, name: str) -> bool:
        """
        Delete a layout file.

        Returns True if deleted, False if not found.
        """
        path = self._layout_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_layouts(self) -> list[tuple[str, str]]:
        """
        List available layouts.

        Returns list of (name, description) tuples.
        """
        layouts = []
        for path in self.layouts_dir.glob("*.yaml"):
            try:
                yaml_str = path.read_text(encoding='utf-8')
                data = yaml.safe_load(yaml_str)
                name = data.get("name", path.stem)
                desc = data.get("description", "")
                layouts.append((name, desc))
            except Exception:
                # Skip invalid files
                continue
        return sorted(layouts, key=lambda x: x[0].lower())

    def exists(self, name: str) -> bool:
        """Check if a layout exists."""
        return self._layout_path(name).exists()

    def save_from_zones(
        self,
        name: str,
        description: str,
        zone_manager: ZoneManager,
        cursor: tuple[int, int] | None = None,
        viewport: tuple[int, int] | None = None,
    ) -> Path:
        """
        Save current zones as a layout.

        Args:
            name: Layout name
            description: Layout description
            zone_manager: ZoneManager with zones to save
            cursor: Optional cursor position (x, y)
            viewport: Optional viewport position (x, y)

        Returns path to saved file.
        """
        layout_zones = []

        for zone in zone_manager.list_all():
            lz = LayoutZone(
                name=zone.name,
                zone_type=zone.zone_type.value,
                x=zone.x,
                y=zone.y,
                width=zone.width,
                height=zone.height,
                command=zone.config.command,
                interval=zone.config.refresh_interval,
                shell=zone.config.shell if zone.config.shell != "/bin/bash" else None,
                bookmark=zone.bookmark,
                description=zone.description,
            )
            layout_zones.append(lz)

        layout = Layout(
            name=name,
            description=description,
            zones=layout_zones,
            cursor_x=cursor[0] if cursor else None,
            cursor_y=cursor[1] if cursor else None,
            viewport_x=viewport[0] if viewport else None,
            viewport_y=viewport[1] if viewport else None,
        )

        return self.save(layout)

    def apply_layout(
        self,
        layout: Layout,
        zone_manager: ZoneManager,
        zone_executor: ZoneExecutor,
        pty_handler: Any | None = None,
        clear_existing: bool = False,
    ) -> tuple[int, list[str]]:
        """
        Apply a layout by creating zones.

        Args:
            layout: Layout to apply
            zone_manager: ZoneManager to add zones to
            zone_executor: ZoneExecutor for starting watchers
            pty_handler: PTYHandler for starting PTY sessions
            clear_existing: If True, clear existing zones first

        Returns (zones_created, errors) tuple.
        """
        errors = []
        created = 0

        if clear_existing:
            zone_manager.clear()

        for lz in layout.zones:
            # Check for conflicts
            if lz.name.lower() in zone_manager:
                errors.append(f"Zone '{lz.name}' already exists, skipped")
                continue

            try:
                zone_type = ZoneType(lz.zone_type)
                config = ZoneConfig(zone_type=zone_type)

                if lz.command:
                    config.command = lz.command
                if lz.interval is not None:
                    config.refresh_interval = lz.interval
                if lz.shell:
                    config.shell = lz.shell

                zone = zone_manager.create(
                    name=lz.name,
                    x=lz.x,
                    y=lz.y,
                    width=lz.width,
                    height=lz.height,
                    description=lz.description,
                    bookmark=lz.bookmark,
                    config=config,
                )

                # Start dynamic zones
                if zone_type == ZoneType.PIPE:
                    zone_executor.execute_pipe(zone)
                elif zone_type == ZoneType.WATCH:
                    zone_executor.start_watch(zone)
                elif zone_type == ZoneType.PTY and pty_handler:
                    if not pty_handler.create_pty(zone):
                        errors.append(f"Failed to create PTY for '{lz.name}'")

                created += 1

            except Exception as e:
                errors.append(f"Error creating '{lz.name}': {e}")

        return created, errors


# =============================================================================
# DEFAULT LAYOUTS
# =============================================================================

DEFAULT_LAYOUTS = {
    "devops": Layout(
        name="devops",
        description="DevOps monitoring workspace",
        zones=[
            LayoutZone(
                name="LOGS",
                zone_type="watch",
                x=0, y=0, width=80, height=15,
                command="dmesg | tail -12",
                interval=10,
                bookmark="l",
                description="System logs"
            ),
            LayoutZone(
                name="PROCESSES",
                zone_type="watch",
                x=0, y=16, width=80, height=12,
                command="ps aux --sort=-%cpu | head -10",
                interval=5,
                bookmark="p",
                description="Top CPU processes"
            ),
            LayoutZone(
                name="DISK",
                zone_type="watch",
                x=85, y=0, width=45, height=10,
                command="df -h | head -8",
                interval=30,
                bookmark="d",
                description="Disk usage"
            ),
            LayoutZone(
                name="TERMINAL",
                zone_type="pty",
                x=85, y=11, width=60, height=18,
                bookmark="t",
                description="Interactive terminal"
            ),
        ],
    ),
    "development": Layout(
        name="development",
        description="Development workspace with git and tests",
        zones=[
            LayoutZone(
                name="GIT",
                zone_type="watch",
                x=0, y=0, width=50, height=12,
                command="git status --short 2>/dev/null || echo 'Not a git repo'",
                interval=5,
                bookmark="g",
                description="Git status"
            ),
            LayoutZone(
                name="FILES",
                zone_type="watch",
                x=0, y=13, width=50, height=15,
                command="ls -la | head -14",
                interval=10,
                bookmark="f",
                description="Directory listing"
            ),
            LayoutZone(
                name="EDITOR",
                zone_type="pty",
                x=55, y=0, width=80, height=28,
                bookmark="e",
                description="Editor terminal"
            ),
        ],
    ),
    "monitoring": Layout(
        name="monitoring",
        description="System monitoring dashboard",
        zones=[
            LayoutZone(
                name="CPU",
                zone_type="watch",
                x=0, y=0, width=40, height=8,
                command="uptime",
                interval=5,
                bookmark="c",
                description="CPU load"
            ),
            LayoutZone(
                name="MEMORY",
                zone_type="watch",
                x=0, y=9, width=40, height=8,
                command="free -h | head -3",
                interval=5,
                bookmark="m",
                description="Memory usage"
            ),
            LayoutZone(
                name="NETWORK",
                zone_type="watch",
                x=45, y=0, width=50, height=12,
                command="netstat -tuln 2>/dev/null | head -10 || ss -tuln | head -10",
                interval=10,
                bookmark="n",
                description="Network connections"
            ),
            LayoutZone(
                name="DISK",
                zone_type="watch",
                x=45, y=13, width=50, height=8,
                command="df -h | grep -E '^/dev' | head -5",
                interval=30,
                bookmark="d",
                description="Disk usage"
            ),
        ],
    ),
}


def install_default_layouts(layouts_dir: Path | None = None) -> int:
    """
    Install default layouts if they don't exist.

    Returns number of layouts installed.
    """
    manager = LayoutManager(layouts_dir)
    installed = 0

    for name, layout in DEFAULT_LAYOUTS.items():
        if not manager.exists(name):
            manager.save(layout)
            installed += 1

    return installed
