"""Tests for zone management."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from zones import Zone, ZoneManager


class TestZone:
    """Tests for Zone class."""

    def test_create_zone(self):
        zone = Zone("test", 10, 20, 100, 50)
        assert zone.name == "test"
        assert zone.x == 10
        assert zone.y == 20
        assert zone.width == 100
        assert zone.height == 50

    def test_contains(self):
        zone = Zone("test", 10, 20, 100, 50)
        # Inside
        assert zone.contains(10, 20)
        assert zone.contains(50, 40)
        assert zone.contains(109, 69)
        # Outside
        assert not zone.contains(9, 20)
        assert not zone.contains(10, 19)
        assert not zone.contains(110, 20)
        assert not zone.contains(10, 70)

    def test_center(self):
        zone = Zone("test", 10, 20, 100, 50)
        cx, cy = zone.center()
        assert cx == 60  # 10 + 100/2
        assert cy == 45  # 20 + 50/2

    def test_distance_to_inside(self):
        zone = Zone("test", 10, 20, 100, 50)
        assert zone.distance_to(50, 40) == 0.0

    def test_distance_to_outside(self):
        zone = Zone("test", 10, 20, 100, 50)
        # Directly left
        assert zone.distance_to(0, 40) == 10.0
        # Directly above
        assert zone.distance_to(50, 10) == 10.0

    def test_direction_from(self):
        zone = Zone("test", 100, 100, 50, 50)
        # Center is at (125, 125)
        # From far left
        assert zone.direction_from(0, 125) == '→'
        # From far right
        assert zone.direction_from(300, 125) == '←'
        # From above
        assert zone.direction_from(125, 0) == '↓'
        # From below
        assert zone.direction_from(125, 300) == '↑'

    def test_to_dict(self):
        zone = Zone("test", 10, 20, 100, 50, description="A test zone", bookmark="t")
        d = zone.to_dict()
        assert d["name"] == "test"
        assert d["x"] == 10
        assert d["y"] == 20
        assert d["width"] == 100
        assert d["height"] == 50
        assert d["description"] == "A test zone"
        assert d["bookmark"] == "t"

    def test_from_dict(self):
        d = {"name": "test", "x": 10, "y": 20, "width": 100, "height": 50}
        zone = Zone.from_dict(d)
        assert zone.name == "test"
        assert zone.x == 10
        assert zone.contains(50, 40)


class TestZoneManager:
    """Tests for ZoneManager class."""

    def test_create_zone(self):
        manager = ZoneManager()
        zone = manager.create("workspace", 0, 0, 100, 50)
        assert zone.name == "workspace"
        assert len(manager) == 1

    def test_create_duplicate_raises(self):
        manager = ZoneManager()
        manager.create("workspace", 0, 0, 100, 50)
        with pytest.raises(ValueError):
            manager.create("workspace", 100, 0, 100, 50)

    def test_get_case_insensitive(self):
        manager = ZoneManager()
        manager.create("WorkSpace", 0, 0, 100, 50)
        assert manager.get("workspace") is not None
        assert manager.get("WORKSPACE") is not None

    def test_delete(self):
        manager = ZoneManager()
        manager.create("test", 0, 0, 100, 50)
        assert manager.delete("test")
        assert len(manager) == 0
        assert not manager.delete("nonexistent")

    def test_find_at(self):
        manager = ZoneManager()
        zone1 = manager.create("zone1", 0, 0, 100, 50)
        zone2 = manager.create("zone2", 200, 0, 100, 50)

        assert manager.find_at(50, 25) is zone1
        assert manager.find_at(250, 25) is zone2
        assert manager.find_at(150, 25) is None

    def test_nearest(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 50, 50)
        manager.create("zone2", 200, 0, 50, 50)

        # From middle, zone1 is closer
        result = manager.nearest(100, 25)
        assert result is not None
        zone, dist, direction = result
        assert zone.name == "zone1"

    def test_rename(self):
        manager = ZoneManager()
        manager.create("old", 0, 0, 100, 50)
        assert manager.rename("old", "new")
        assert manager.get("new") is not None
        assert manager.get("old") is None

    def test_clear(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 100, 50)
        manager.create("zone2", 200, 0, 100, 50)
        manager.clear()
        assert len(manager) == 0

    def test_to_dict_from_dict(self):
        manager = ZoneManager()
        manager.create("zone1", 0, 0, 100, 50, bookmark="1")
        manager.create("zone2", 200, 0, 100, 50, bookmark="2")

        d = manager.to_dict()
        assert "zones" in d
        assert len(d["zones"]) == 2

        # Restore
        manager2 = ZoneManager.from_dict(d)
        assert len(manager2) == 2
        assert manager2.get("zone1") is not None
        assert manager2.get("zone2") is not None

    def test_iter(self):
        manager = ZoneManager()
        manager.create("a", 0, 0, 10, 10)
        manager.create("b", 20, 0, 10, 10)

        names = [z.name for z in manager]
        assert "a" in names
        assert "b" in names

    def test_contains(self):
        manager = ZoneManager()
        manager.create("test", 0, 0, 100, 50)
        assert "test" in manager
        assert "TEST" in manager  # case insensitive
        assert "other" not in manager


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
