"""Puzzle loading, parsing, and validation for KenKen."""

import json
from collections import deque


class Cage:
    __slots__ = ("cells", "target", "op")

    def __init__(self, cells: list[tuple[int, int]], target: int, op: str):
        self.cells = cells
        self.target = target
        self.op = op

    def __repr__(self):
        return f"Cage(cells={self.cells}, target={self.target}, op={self.op!r})"


def parse_coord(coord: str, size: int) -> tuple[int, int]:
    """Convert chess-style coordinate like 'B3' to 0-indexed (row, col).

    Row 1 is the bottom row (index size-1), matching chess convention.
    """
    if len(coord) < 2:
        raise ValueError(f"Invalid coordinate: {coord!r}")
    col_char = coord[0].upper()
    row_str = coord[1:]
    if not col_char.isalpha() or not row_str.isdigit():
        raise ValueError(f"Invalid coordinate: {coord!r}")
    col = ord(col_char) - ord("A")
    row = size - int(row_str)
    return (row, col)


def _cells_contiguous(cells: list[tuple[int, int]]) -> bool:
    """Check that a set of cells forms a contiguous group (4-connected)."""
    if len(cells) <= 1:
        return True
    cell_set = set(cells)
    visited: set[tuple[int, int]] = set()
    queue = deque([cells[0]])
    visited.add(cells[0])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nb = (r + dr, c + dc)
            if nb in cell_set and nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return len(visited) == len(cell_set)


def load_puzzle(path: str) -> tuple[int, list[Cage]]:
    """Load and validate a puzzle JSON file. Returns (size, cages)."""
    with open(path) as f:
        data = json.load(f)

    # Validate top-level structure
    if "size" not in data or "cages" not in data:
        raise ValueError("Puzzle JSON must contain 'size' and 'cages' keys")

    size = data["size"]
    if not isinstance(size, int) or size < 2 or size > 9:
        raise ValueError(f"Puzzle size must be an integer between 2 and 9, got {size}")

    covered: set[tuple[int, int]] = set()
    cages: list[Cage] = []

    for i, cage_data in enumerate(data["cages"]):
        if "cells" not in cage_data or "target" not in cage_data:
            raise ValueError(f"Cage {i}: must have 'cells' and 'target'")

        raw_cells = cage_data["cells"]
        if not isinstance(raw_cells, list) or len(raw_cells) == 0:
            raise ValueError(f"Cage {i}: 'cells' must be a non-empty list")

        cells: list[tuple[int, int]] = []
        for coord in raw_cells:
            r, c = parse_coord(coord, size)
            if r < 0 or r >= size or c < 0 or c >= size:
                raise ValueError(f"Cage {i}: coordinate {coord!r} out of bounds for size {size}")
            if (r, c) in covered:
                raise ValueError(f"Cage {i}: cell {coord!r} already belongs to another cage")
            covered.add((r, c))
            cells.append((r, c))

        target = cage_data["target"]
        if not isinstance(target, (int, float)):
            raise ValueError(f"Cage {i}: 'target' must be a number")

        op = cage_data.get("op", "")
        if len(cells) == 1:
            if op and op != "":
                raise ValueError(f"Cage {i}: single-cell cage should not have an op")
            op = ""
        else:
            if op not in ("+", "-", "*", "/"):
                raise ValueError(f"Cage {i}: invalid op {op!r}")
            if op in ("-", "/") and len(cells) != 2:
                raise ValueError(f"Cage {i}: '{op}' requires exactly 2 cells")

        if not _cells_contiguous(cells):
            raise ValueError(f"Cage {i}: cells are not contiguous")

        cages.append(Cage(cells, int(target), op))

    # Check all cells covered
    expected = {(r, c) for r in range(size) for c in range(size)}
    if covered != expected:
        missing = expected - covered
        raise ValueError(f"Not all cells covered. Missing: {missing}")

    return size, cages
