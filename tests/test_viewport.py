"""Tests for viewport coordinate transforms and navigation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from viewport import Viewport, Cursor, Origin, YAxisDirection


def test_default_viewport():
    vp = Viewport()
    assert vp.x == 0
    assert vp.y == 0
    assert vp.width == 80
    assert vp.height == 24
    assert vp.cursor.x == 0
    assert vp.cursor.y == 0


def test_canvas_to_screen_basic():
    vp = Viewport(x=0, y=0, width=80, height=24)

    # Origin should map to screen origin
    assert vp.canvas_to_screen(0, 0) == (0, 0)

    # Point at (5, 10) should be at screen (5, 10)
    assert vp.canvas_to_screen(5, 10) == (5, 10)

    # Point outside viewport should return None
    assert vp.canvas_to_screen(100, 0) is None
    assert vp.canvas_to_screen(0, 100) is None
    assert vp.canvas_to_screen(-1, 0) is None


def test_canvas_to_screen_panned():
    vp = Viewport(x=10, y=20, width=80, height=24)

    # Canvas (10, 20) is now screen (0, 0)
    assert vp.canvas_to_screen(10, 20) == (0, 0)

    # Canvas (15, 25) is screen (5, 5)
    assert vp.canvas_to_screen(15, 25) == (5, 5)

    # Canvas (0, 0) is now off-screen
    assert vp.canvas_to_screen(0, 0) is None


def test_screen_to_canvas():
    vp = Viewport(x=10, y=20, width=80, height=24)

    # Screen (0, 0) maps to canvas (10, 20)
    assert vp.screen_to_canvas(0, 0) == (10, 20)

    # Screen (5, 5) maps to canvas (15, 25)
    assert vp.screen_to_canvas(5, 5) == (15, 25)


def test_y_up_direction():
    vp = Viewport(x=0, y=0, width=80, height=24, y_direction=YAxisDirection.UP)

    # With Y-up, canvas y=0 should still map to screen top
    # but canvas y=1 should be higher on screen (lower screen y)
    pos = vp.canvas_to_screen(0, 0)
    assert pos == (0, 0)

    # Y=1 in canvas (up) should map to screen Y=-1 (off-screen in this case)
    pos = vp.canvas_to_screen(0, 1)
    assert pos is None  # Above viewport

    # Y=-1 in canvas should map to screen Y=1
    pos = vp.canvas_to_screen(0, -1)
    assert pos == (0, 1)


def test_pan():
    vp = Viewport(x=0, y=0, width=80, height=24)

    vp.pan(10, 5)
    assert vp.x == 10
    assert vp.y == 5

    vp.pan(-20, -10)
    assert vp.x == -10
    assert vp.y == -5


def test_center_on():
    vp = Viewport(x=0, y=0, width=80, height=24)

    vp.center_on(100, 100)

    # Viewport should be centered on (100, 100)
    assert vp.x == 100 - 40  # 100 - width/2
    assert vp.y == 100 - 12  # 100 - height/2


def test_cursor_movement():
    vp = Viewport()

    vp.move_cursor(5, 3)
    assert vp.cursor.x == 5
    assert vp.cursor.y == 3

    vp.move_cursor(-2, -1)
    assert vp.cursor.x == 3
    assert vp.cursor.y == 2


def test_cursor_screen_pos():
    vp = Viewport(x=0, y=0, width=80, height=24)
    vp.cursor.set(10, 5)

    pos = vp.cursor_screen_pos()
    assert pos == (10, 5)

    # Pan viewport so cursor is off-screen
    vp.pan(100, 100)
    assert vp.cursor_screen_pos() is None


def test_ensure_cursor_visible():
    vp = Viewport(x=0, y=0, width=80, height=24)

    # Move cursor off-screen to the right
    vp.cursor.set(100, 10)
    vp.ensure_cursor_visible()

    # Viewport should have scrolled
    assert vp.is_visible(100, 10)
    assert vp.cursor_screen_pos() is not None


def test_ensure_cursor_visible_with_margin():
    vp = Viewport(x=0, y=0, width=80, height=24)

    # Move cursor to edge
    vp.cursor.set(79, 0)
    vp.ensure_cursor_visible(margin=5)

    # Viewport should scroll to keep margin
    screen_pos = vp.cursor_screen_pos()
    assert screen_pos is not None
    assert screen_pos[0] <= vp.width - 5 - 1


def test_center_on_cursor():
    vp = Viewport(x=0, y=0, width=80, height=24)
    vp.cursor.set(500, 300)

    vp.center_on_cursor()

    screen_pos = vp.cursor_screen_pos()
    assert screen_pos is not None
    # Should be near center
    assert abs(screen_pos[0] - 40) <= 1
    assert abs(screen_pos[1] - 12) <= 1


def test_visible_range():
    vp = Viewport(x=10, y=20, width=80, height=24)

    min_x, min_y, max_x, max_y = vp.visible_range()

    assert min_x == 10
    assert min_y == 20
    assert max_x == 89  # 10 + 80 - 1
    assert max_y == 43  # 20 + 24 - 1


def test_resize():
    vp = Viewport(width=80, height=24)

    vp.resize(120, 40)
    assert vp.width == 120
    assert vp.height == 40

    # Minimum size should be 1x1
    vp.resize(0, 0)
    assert vp.width == 1
    assert vp.height == 1


def test_origin():
    vp = Viewport()

    vp.origin.set(50, 50)
    assert vp.origin.x == 50
    assert vp.origin.y == 50

    vp.origin.move(-10, 10)
    assert vp.origin.x == 40
    assert vp.origin.y == 60


def test_origin_screen_pos():
    vp = Viewport(x=0, y=0, width=80, height=24)
    vp.origin.set(10, 5)

    pos = vp.origin_screen_pos()
    assert pos == (10, 5)


def test_center_on_origin():
    vp = Viewport(x=0, y=0, width=80, height=24)
    vp.origin.set(100, 100)

    vp.center_on_origin()

    origin_pos = vp.origin_screen_pos()
    assert origin_pos is not None
    assert abs(origin_pos[0] - 40) <= 1
    assert abs(origin_pos[1] - 12) <= 1


def test_serialize_deserialize():
    vp = Viewport(x=10, y=20, width=100, height=50)
    vp.cursor.set(30, 40)
    vp.origin.set(5, 5)
    vp.y_direction = YAxisDirection.UP

    data = vp.to_dict()
    restored = Viewport.from_dict(data)

    assert restored.x == 10
    assert restored.y == 20
    assert restored.width == 100
    assert restored.height == 50
    assert restored.cursor.x == 30
    assert restored.cursor.y == 40
    assert restored.origin.x == 5
    assert restored.origin.y == 5
    assert restored.y_direction == YAxisDirection.UP


def test_is_visible():
    vp = Viewport(x=10, y=10, width=20, height=10)

    assert vp.is_visible(10, 10)  # Top-left
    assert vp.is_visible(29, 19)  # Bottom-right
    assert vp.is_visible(20, 15)  # Middle

    assert not vp.is_visible(9, 10)   # Just left
    assert not vp.is_visible(30, 10)  # Just right
    assert not vp.is_visible(10, 9)   # Just above
    assert not vp.is_visible(10, 20)  # Just below


def test_negative_coordinates():
    vp = Viewport(x=-50, y=-50, width=80, height=24)

    # Canvas (-50, -50) should be screen (0, 0)
    assert vp.canvas_to_screen(-50, -50) == (0, 0)

    # Canvas (0, 0) should be screen (50, 50) - but that's outside viewport
    assert vp.canvas_to_screen(0, 0) is None

    # Canvas (-40, -40) should be screen (10, 10)
    assert vp.canvas_to_screen(-40, -40) == (10, 10)


if __name__ == "__main__":
    test_default_viewport()
    test_canvas_to_screen_basic()
    test_canvas_to_screen_panned()
    test_screen_to_canvas()
    test_y_up_direction()
    test_pan()
    test_center_on()
    test_cursor_movement()
    test_cursor_screen_pos()
    test_ensure_cursor_visible()
    test_ensure_cursor_visible_with_margin()
    test_center_on_cursor()
    test_visible_range()
    test_resize()
    test_origin()
    test_origin_screen_pos()
    test_center_on_origin()
    test_serialize_deserialize()
    test_is_visible()
    test_negative_coordinates()
    print("All viewport tests passed!")
