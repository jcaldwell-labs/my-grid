"""Tests for undo/redo functionality."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from canvas import Canvas
from undo import UndoManager, CellSnapshot, CellOperation, snapshot_cell, snapshot_region


class TestCellSnapshot:
    """Tests for CellSnapshot dataclass."""

    def test_snapshot_existing_cell(self):
        canvas = Canvas()
        canvas.set(5, 10, 'X', fg=1, bg=2)

        snap = snapshot_cell(canvas, 5, 10)

        assert snap.x == 5
        assert snap.y == 10
        assert snap.char == 'X'
        assert snap.fg == 1
        assert snap.bg == 2
        assert snap.existed is True

    def test_snapshot_empty_cell(self):
        canvas = Canvas()

        snap = snapshot_cell(canvas, 5, 10)

        assert snap.x == 5
        assert snap.y == 10
        assert snap.char == ' '
        assert snap.fg == -1
        assert snap.bg == -1
        assert snap.existed is False


class TestSnapshotRegion:
    """Tests for snapshot_region helper."""

    def test_snapshot_empty_region(self):
        canvas = Canvas()
        snapshots = snapshot_region(canvas, 0, 0, 3, 3)

        assert len(snapshots) == 9
        for snap in snapshots:
            assert snap.existed is False

    def test_snapshot_region_with_content(self):
        canvas = Canvas()
        canvas.set(1, 1, 'X')

        snapshots = snapshot_region(canvas, 0, 0, 3, 3)

        assert len(snapshots) == 9
        existing = [s for s in snapshots if s.existed]
        assert len(existing) == 1
        assert existing[0].x == 1
        assert existing[0].y == 1
        assert existing[0].char == 'X'


class TestCellOperation:
    """Tests for CellOperation."""

    def test_undo_restores_cell(self):
        canvas = Canvas()
        canvas.set(5, 5, 'A')

        # Create operation: changing 'A' to 'B'
        before = [CellSnapshot(5, 5, 'A', -1, -1, True)]
        after = [CellSnapshot(5, 5, 'B', -1, -1, True)]
        op = CellOperation(before=before, after=after, _description="Edit")

        # Apply the change
        canvas.set(5, 5, 'B')
        assert canvas.get_char(5, 5) == 'B'

        # Undo should restore 'A'
        op.undo(canvas)
        assert canvas.get_char(5, 5) == 'A'

    def test_redo_reapplies_change(self):
        canvas = Canvas()
        canvas.set(5, 5, 'A')

        before = [CellSnapshot(5, 5, 'A', -1, -1, True)]
        after = [CellSnapshot(5, 5, 'B', -1, -1, True)]
        op = CellOperation(before=before, after=after, _description="Edit")

        # Redo should apply 'B'
        op.redo(canvas)
        assert canvas.get_char(5, 5) == 'B'

    def test_undo_clears_new_cell(self):
        canvas = Canvas()

        # Create operation: adding new cell
        before = [CellSnapshot(5, 5, ' ', -1, -1, False)]  # didn't exist
        after = [CellSnapshot(5, 5, 'X', -1, -1, True)]
        op = CellOperation(before=before, after=after, _description="Add")

        # Apply the change
        canvas.set(5, 5, 'X')
        assert not canvas.is_empty_at(5, 5)

        # Undo should clear the cell
        op.undo(canvas)
        assert canvas.is_empty_at(5, 5)

    def test_description_single_cell(self):
        before = [CellSnapshot(0, 0, 'A', -1, -1, True)]
        after = [CellSnapshot(0, 0, 'B', -1, -1, True)]
        op = CellOperation(before=before, after=after, _description="Type")

        assert op.description == "Type"

    def test_description_multiple_cells(self):
        before = [CellSnapshot(i, 0, ' ', -1, -1, False) for i in range(5)]
        after = [CellSnapshot(i, 0, 'X', -1, -1, True) for i in range(5)]
        op = CellOperation(before=before, after=after, _description="Fill")

        assert op.description == "Fill (5 cells)"


class TestUndoManager:
    """Tests for UndoManager."""

    def test_empty_history(self):
        manager = UndoManager()

        assert not manager.can_undo
        assert not manager.can_redo
        assert manager.undo_count == 0
        assert manager.redo_count == 0

    def test_basic_undo(self):
        canvas = Canvas()
        manager = UndoManager()

        # Record operation
        manager.begin_operation("Type")
        manager.record_cell_before(canvas, 0, 0)
        canvas.set(0, 0, 'X')
        manager.record_cell_after(canvas, 0, 0)
        manager.end_operation()

        assert manager.can_undo
        assert canvas.get_char(0, 0) == 'X'

        # Undo
        desc = manager.undo(canvas)
        assert desc == "Type"
        assert canvas.is_empty_at(0, 0)
        assert manager.can_redo

    def test_basic_redo(self):
        canvas = Canvas()
        manager = UndoManager()

        # Record and undo
        manager.begin_operation("Type")
        manager.record_cell_before(canvas, 0, 0)
        canvas.set(0, 0, 'X')
        manager.record_cell_after(canvas, 0, 0)
        manager.end_operation()

        manager.undo(canvas)
        assert canvas.is_empty_at(0, 0)

        # Redo
        desc = manager.redo(canvas)
        assert desc == "Type"
        assert canvas.get_char(0, 0) == 'X'

    def test_multiple_operations(self):
        canvas = Canvas()
        manager = UndoManager()

        # First operation
        manager.begin_operation("Type A")
        manager.record_cell_before(canvas, 0, 0)
        canvas.set(0, 0, 'A')
        manager.record_cell_after(canvas, 0, 0)
        manager.end_operation()

        # Second operation
        manager.begin_operation("Type B")
        manager.record_cell_before(canvas, 1, 0)
        canvas.set(1, 0, 'B')
        manager.record_cell_after(canvas, 1, 0)
        manager.end_operation()

        assert manager.undo_count == 2

        # Undo second
        manager.undo(canvas)
        assert canvas.get_char(0, 0) == 'A'
        assert canvas.is_empty_at(1, 0)

        # Undo first
        manager.undo(canvas)
        assert canvas.is_empty_at(0, 0)
        assert canvas.is_empty_at(1, 0)

    def test_redo_cleared_on_new_operation(self):
        canvas = Canvas()
        manager = UndoManager()

        # Record and undo
        manager.begin_operation("First")
        manager.record_cell_before(canvas, 0, 0)
        canvas.set(0, 0, 'A')
        manager.record_cell_after(canvas, 0, 0)
        manager.end_operation()

        manager.undo(canvas)
        assert manager.can_redo

        # New operation should clear redo stack
        manager.begin_operation("Second")
        manager.record_cell_before(canvas, 1, 0)
        canvas.set(1, 0, 'B')
        manager.record_cell_after(canvas, 1, 0)
        manager.end_operation()

        assert not manager.can_redo

    def test_max_history(self):
        canvas = Canvas()
        manager = UndoManager(max_history=5)

        # Add 10 operations
        for i in range(10):
            manager.begin_operation(f"Op {i}")
            manager.record_cell_before(canvas, i, 0)
            canvas.set(i, 0, str(i))
            manager.record_cell_after(canvas, i, 0)
            manager.end_operation()

        # Should only keep last 5
        assert manager.undo_count == 5

    def test_empty_operation_not_recorded(self):
        manager = UndoManager()

        # Begin and end without recording anything
        manager.begin_operation("Empty")
        result = manager.end_operation()

        assert result is False
        assert not manager.can_undo

    def test_cancel_operation(self):
        canvas = Canvas()
        manager = UndoManager()

        manager.begin_operation("Cancelled")
        manager.record_cell_before(canvas, 0, 0)
        canvas.set(0, 0, 'X')
        manager.record_cell_after(canvas, 0, 0)
        manager.cancel_operation()

        # Should not be recorded
        assert not manager.can_undo

    def test_clear_history(self):
        canvas = Canvas()
        manager = UndoManager()

        # Add operation
        manager.begin_operation("Test")
        manager.record_cell_before(canvas, 0, 0)
        canvas.set(0, 0, 'X')
        manager.record_cell_after(canvas, 0, 0)
        manager.end_operation()

        manager.clear()

        assert not manager.can_undo
        assert not manager.can_redo

    def test_get_history(self):
        canvas = Canvas()
        manager = UndoManager()

        for i in range(5):
            manager.begin_operation(f"Op {i}")
            manager.record_cell_before(canvas, i, 0)
            canvas.set(i, 0, 'X')
            manager.record_cell_after(canvas, i, 0)
            manager.end_operation()

        history = manager.get_history(3)

        assert len(history) == 3
        assert history[0] == (0, "Op 4")  # Most recent
        assert history[1] == (1, "Op 3")
        assert history[2] == (2, "Op 2")

    def test_undo_nothing_returns_none(self):
        canvas = Canvas()
        manager = UndoManager()

        result = manager.undo(canvas)
        assert result is None

    def test_redo_nothing_returns_none(self):
        canvas = Canvas()
        manager = UndoManager()

        result = manager.redo(canvas)
        assert result is None

    def test_multi_cell_operation(self):
        canvas = Canvas()
        manager = UndoManager()

        # Fill a 3x3 region
        manager.begin_operation("Fill")
        for y in range(3):
            for x in range(3):
                manager.record_cell_before(canvas, x, y)
                canvas.set(x, y, '#')
                manager.record_cell_after(canvas, x, y)
        manager.end_operation()

        assert canvas.cell_count == 9

        # Undo should clear all
        manager.undo(canvas)
        assert canvas.cell_count == 0

        # Redo should restore all
        manager.redo(canvas)
        assert canvas.cell_count == 9


class TestUndoWithColors:
    """Tests for undo/redo with colored cells."""

    def test_undo_restores_colors(self):
        canvas = Canvas()
        manager = UndoManager()

        canvas.set(0, 0, 'A', fg=1, bg=2)

        # Change character and color
        manager.begin_operation("Change")
        manager.record_cell_before(canvas, 0, 0)
        canvas.set(0, 0, 'B', fg=3, bg=4)
        manager.record_cell_after(canvas, 0, 0)
        manager.end_operation()

        # Undo
        manager.undo(canvas)
        cell = canvas.get(0, 0)
        assert cell.char == 'A'
        assert cell.fg == 1
        assert cell.bg == 2


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
