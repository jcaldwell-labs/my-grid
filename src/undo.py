"""
Undo/Redo system for canvas operations.

Uses the Command pattern to track reversible operations on the canvas.
Each operation stores the before/after state of affected cells.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from canvas import Canvas


@dataclass
class CellSnapshot:
    """Snapshot of a single cell's state."""

    x: int
    y: int
    char: str
    fg: int
    bg: int
    existed: bool  # Whether cell existed in canvas (vs empty default)


class UndoableOperation(ABC):
    """Base class for undoable operations."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the operation."""
        pass

    @abstractmethod
    def undo(self, canvas: "Canvas") -> None:
        """Reverse this operation."""
        pass

    @abstractmethod
    def redo(self, canvas: "Canvas") -> None:
        """Re-apply this operation."""
        pass


@dataclass
class CellOperation(UndoableOperation):
    """Operation affecting one or more cells."""

    before: list[CellSnapshot] = field(default_factory=list)
    after: list[CellSnapshot] = field(default_factory=list)
    _description: str = "Edit"

    @property
    def description(self) -> str:
        count = len(self.before)
        if count == 1:
            return self._description
        return f"{self._description} ({count} cells)"

    def undo(self, canvas: "Canvas") -> None:
        """Restore cells to their before state."""
        for snap in self.before:
            if snap.existed:
                canvas.set(snap.x, snap.y, snap.char, snap.fg, snap.bg)
            else:
                canvas.clear(snap.x, snap.y)

    def redo(self, canvas: "Canvas") -> None:
        """Restore cells to their after state."""
        for snap in self.after:
            if snap.existed:
                canvas.set(snap.x, snap.y, snap.char, snap.fg, snap.bg)
            else:
                canvas.clear(snap.x, snap.y)


class UndoManager:
    """
    Manages undo/redo history for canvas operations.

    Uses a standard undo stack with redo stack that clears on new operations.
    """

    def __init__(self, max_history: int = 100):
        self._undo_stack: list[UndoableOperation] = []
        self._redo_stack: list[UndoableOperation] = []
        self._max_history = max_history
        self._current_operation: CellOperation | None = None

    @property
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    @property
    def undo_count(self) -> int:
        """Number of operations that can be undone."""
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
        """Number of operations that can be redone."""
        return len(self._redo_stack)

    def begin_operation(self, description: str = "Edit") -> None:
        """
        Begin a new undoable operation.

        Call this before making canvas changes that should be grouped together.
        """
        self._current_operation = CellOperation(_description=description)

    def record_cell_before(self, canvas: "Canvas", x: int, y: int) -> None:
        """
        Record a cell's state before modification.

        Call this for each cell that will be changed.
        """
        if self._current_operation is None:
            return

        cell = canvas.get(x, y)
        existed = not canvas.is_empty_at(x, y)
        snap = CellSnapshot(
            x=x, y=y, char=cell.char, fg=cell.fg, bg=cell.bg, existed=existed
        )
        self._current_operation.before.append(snap)

    def record_cell_after(self, canvas: "Canvas", x: int, y: int) -> None:
        """
        Record a cell's state after modification.

        Call this for each cell after it's been changed.
        """
        if self._current_operation is None:
            return

        cell = canvas.get(x, y)
        existed = not canvas.is_empty_at(x, y)
        snap = CellSnapshot(
            x=x, y=y, char=cell.char, fg=cell.fg, bg=cell.bg, existed=existed
        )
        self._current_operation.after.append(snap)

    def end_operation(self) -> bool:
        """
        Finish the current operation and add to history.

        Returns True if operation was recorded, False if empty/cancelled.
        """
        if self._current_operation is None:
            return False

        op = self._current_operation
        self._current_operation = None

        # Only record if there were actual changes
        if not op.before and not op.after:
            return False

        # Add to undo stack
        self._undo_stack.append(op)

        # Clear redo stack (new branch of history)
        self._redo_stack.clear()

        # Enforce history limit
        while len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)

        return True

    def cancel_operation(self) -> None:
        """Cancel the current operation without recording."""
        self._current_operation = None

    def undo(self, canvas: "Canvas") -> str | None:
        """
        Undo the last operation.

        Returns the operation description, or None if nothing to undo.
        """
        if not self._undo_stack:
            return None

        op = self._undo_stack.pop()
        op.undo(canvas)
        self._redo_stack.append(op)

        return op.description

    def redo(self, canvas: "Canvas") -> str | None:
        """
        Redo the last undone operation.

        Returns the operation description, or None if nothing to redo.
        """
        if not self._redo_stack:
            return None

        op = self._redo_stack.pop()
        op.redo(canvas)
        self._undo_stack.append(op)

        return op.description

    def get_history(self, limit: int = 10) -> list[tuple[int, str]]:
        """
        Get recent operation history.

        Returns list of (index, description) tuples, most recent first.
        Index 0 is the most recent (next to undo).
        """
        result = []
        for i, op in enumerate(reversed(self._undo_stack[-limit:])):
            result.append((i, op.description))
        return result

    def clear(self) -> None:
        """Clear all history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._current_operation = None


def snapshot_cell(canvas: "Canvas", x: int, y: int) -> CellSnapshot:
    """Helper to create a cell snapshot."""
    cell = canvas.get(x, y)
    existed = not canvas.is_empty_at(x, y)
    return CellSnapshot(
        x=x, y=y, char=cell.char, fg=cell.fg, bg=cell.bg, existed=existed
    )


def snapshot_region(
    canvas: "Canvas", x: int, y: int, width: int, height: int
) -> list[CellSnapshot]:
    """Helper to snapshot a rectangular region."""
    snapshots = []
    for cy in range(y, y + height):
        for cx in range(x, x + width):
            snapshots.append(snapshot_cell(canvas, cx, cy))
    return snapshots
