"""Game state, input handling, validation, and win checking for KenKen."""

import json
import os
from puzzle import Cage


class GameState:
    def __init__(self, size: int, cages: list[Cage], save_path: str = ""):
        self.size = size
        self.cages = cages
        self.grid: list[list[int]] = [[0] * size for _ in range(size)]
        self.cursor_row = 0
        self.cursor_col = 0
        self.save_path = save_path
        # Build cell-to-cage lookup
        self.cell_cage: dict[tuple[int, int], Cage] = {}
        for cage in cages:
            for cell in cage.cells:
                self.cell_cage[cell] = cage
        self.conflicts: set[tuple[int, int]] = set()

    def move_cursor(self, dr: int, dc: int):
        self.cursor_row = max(0, min(self.size - 1, self.cursor_row + dr))
        self.cursor_col = max(0, min(self.size - 1, self.cursor_col + dc))

    def place_number(self, num: int):
        """Place a number (1-size) at the cursor, or 0 to clear."""
        if 0 <= num <= self.size:
            self.grid[self.cursor_row][self.cursor_col] = num
            self._update_conflicts()
            self.save()

    def clear_cell(self):
        self.grid[self.cursor_row][self.cursor_col] = 0
        self._update_conflicts()
        self.save()

    def reset(self):
        for r in range(self.size):
            for c in range(self.size):
                self.grid[r][c] = 0
        self.conflicts.clear()
        self.save()

    def save(self):
        """Auto-save grid state to disk."""
        if not self.save_path:
            return
        data = {
            "grid": self.grid,
            "cursor_row": self.cursor_row,
            "cursor_col": self.cursor_col,
        }
        try:
            with open(self.save_path, "w") as f:
                json.dump(data, f)
        except OSError:
            pass

    def load_save(self):
        """Load saved grid state from disk if it exists."""
        if not self.save_path or not os.path.exists(self.save_path):
            return False
        try:
            with open(self.save_path) as f:
                data = json.load(f)
            grid = data["grid"]
            if len(grid) == self.size and all(len(row) == self.size for row in grid):
                self.grid = grid
                self.cursor_row = data.get("cursor_row", 0)
                self.cursor_col = data.get("cursor_col", 0)
                self._update_conflicts()
                return True
        except (OSError, json.JSONDecodeError, KeyError):
            pass
        return False

    def _update_conflicts(self):
        """Find all cells involved in row/column duplicate conflicts."""
        self.conflicts.clear()
        for i in range(self.size):
            # Check row i
            seen: dict[int, list[int]] = {}
            for c in range(self.size):
                v = self.grid[i][c]
                if v != 0:
                    seen.setdefault(v, []).append(c)
            for v, cols in seen.items():
                if len(cols) > 1:
                    for c in cols:
                        self.conflicts.add((i, c))
            # Check column i
            seen = {}
            for r in range(self.size):
                v = self.grid[r][i]
                if v != 0:
                    seen.setdefault(v, []).append(r)
            for v, rows in seen.items():
                if len(rows) > 1:
                    for r in rows:
                        self.conflicts.add((r, i))

    def _check_cage(self, cage: Cage) -> bool:
        """Check if a cage's arithmetic constraint is satisfied."""
        values = [self.grid[r][c] for r, c in cage.cells]
        if any(v == 0 for v in values):
            return False

        if cage.op == "":
            return values[0] == cage.target
        elif cage.op == "+":
            return sum(values) == cage.target
        elif cage.op == "*":
            product = 1
            for v in values:
                product *= v
            return product == cage.target
        elif cage.op == "-":
            return abs(values[0] - values[1]) == cage.target
        elif cage.op == "/":
            a, b = max(values), min(values)
            return b != 0 and a % b == 0 and a // b == cage.target
        return False

    def is_won(self) -> bool:
        """Check if the puzzle is solved: all filled, no conflicts, all cages valid."""
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 0:
                    return False
        if self.conflicts:
            return False
        return all(self._check_cage(cage) for cage in self.cages)
