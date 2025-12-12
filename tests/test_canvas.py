"""Tests for sparse canvas data structure."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from canvas import Canvas, BoundingBox


def test_empty_canvas():
    canvas = Canvas()
    assert canvas.cell_count == 0
    assert canvas.bounding_box() is None
    assert canvas.get_char(0, 0) == ' '
    assert canvas.is_empty_at(0, 0)


def test_set_and_get():
    canvas = Canvas()
    canvas.set(5, 10, 'X')

    assert canvas.get_char(5, 10) == 'X'
    assert canvas.cell_count == 1
    assert not canvas.is_empty_at(5, 10)


def test_negative_coordinates():
    canvas = Canvas()
    canvas.set(-100, -200, 'N')
    canvas.set(100, 200, 'P')

    assert canvas.get_char(-100, -200) == 'N'
    assert canvas.get_char(100, 200) == 'P'
    assert canvas.cell_count == 2


def test_clear_cell():
    canvas = Canvas()
    canvas.set(0, 0, 'X')
    canvas.clear(0, 0)

    assert canvas.is_empty_at(0, 0)
    assert canvas.cell_count == 0


def test_set_space_clears():
    canvas = Canvas()
    canvas.set(0, 0, 'X')
    canvas.set(0, 0, ' ')

    assert canvas.is_empty_at(0, 0)
    assert canvas.cell_count == 0


def test_bounding_box():
    canvas = Canvas()
    canvas.set(-5, -3, 'A')
    canvas.set(10, 20, 'B')

    bb = canvas.bounding_box()
    assert bb.min_x == -5
    assert bb.min_y == -3
    assert bb.max_x == 10
    assert bb.max_y == 20
    assert bb.width == 16
    assert bb.height == 24


def test_cells_iteration():
    canvas = Canvas()
    canvas.set(0, 0, 'A')
    canvas.set(1, 1, 'B')

    cells = list(canvas.cells())
    assert len(cells) == 2

    chars = {cell.char for _, _, cell in cells}
    assert chars == {'A', 'B'}


def test_cells_in_rect():
    canvas = Canvas()
    canvas.set(1, 1, 'X')

    cells = list(canvas.cells_in_rect(0, 0, 3, 3))
    assert len(cells) == 9  # 3x3 grid

    # Find the X
    x_cells = [(x, y, c) for x, y, c in cells if c.char == 'X']
    assert len(x_cells) == 1
    assert x_cells[0][0] == 1
    assert x_cells[0][1] == 1


def test_serialize_deserialize():
    canvas = Canvas()
    canvas.set(0, 0, 'A')
    canvas.set(5, 5, 'B')
    canvas.set(-3, 2, 'C')

    data = canvas.to_dict()
    restored = Canvas.from_dict(data)

    assert restored.get_char(0, 0) == 'A'
    assert restored.get_char(5, 5) == 'B'
    assert restored.get_char(-3, 2) == 'C'
    assert restored.cell_count == 3


def test_draw_line_horizontal():
    canvas = Canvas()
    canvas.draw_line(0, 0, 5, 0, '-')

    for x in range(6):
        assert canvas.get_char(x, 0) == '-'


def test_draw_line_vertical():
    canvas = Canvas()
    canvas.draw_line(0, 0, 0, 5, '|')

    for y in range(6):
        assert canvas.get_char(0, y) == '|'


def test_draw_rect():
    canvas = Canvas()
    canvas.draw_rect(0, 0, 5, 3)

    # Corners
    assert canvas.get_char(0, 0) == '+'
    assert canvas.get_char(4, 0) == '+'
    assert canvas.get_char(0, 2) == '+'
    assert canvas.get_char(4, 2) == '+'

    # Horizontal edges
    assert canvas.get_char(2, 0) == '-'
    assert canvas.get_char(2, 2) == '-'

    # Vertical edges
    assert canvas.get_char(0, 1) == '|'
    assert canvas.get_char(4, 1) == '|'


def test_write_text():
    canvas = Canvas()
    canvas.write_text(0, 0, "Hello")

    assert canvas.get_char(0, 0) == 'H'
    assert canvas.get_char(1, 0) == 'e'
    assert canvas.get_char(2, 0) == 'l'
    assert canvas.get_char(3, 0) == 'l'
    assert canvas.get_char(4, 0) == 'o'


def test_large_coordinates():
    """Test that sparse storage handles large coordinates efficiently."""
    canvas = Canvas()
    canvas.set(1_000_000, 1_000_000, 'X')
    canvas.set(-1_000_000, -1_000_000, 'Y')

    assert canvas.cell_count == 2
    assert canvas.get_char(1_000_000, 1_000_000) == 'X'
    assert canvas.get_char(-1_000_000, -1_000_000) == 'Y'


if __name__ == "__main__":
    # Run all tests
    test_empty_canvas()
    test_set_and_get()
    test_negative_coordinates()
    test_clear_cell()
    test_set_space_clears()
    test_bounding_box()
    test_cells_iteration()
    test_cells_in_rect()
    test_serialize_deserialize()
    test_draw_line_horizontal()
    test_draw_line_vertical()
    test_draw_rect()
    test_write_text()
    test_large_coordinates()
    print("All tests passed!")
