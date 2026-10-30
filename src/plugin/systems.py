from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from contract import DeterminantOutput, MatrixInput, PuzzleInput, SystemOutput

# Fixed systems Ax = b: lin-01..04 have one solution (lin-03 and lin-04 in fractions), lin-05 has none
# (row 2 is twice row 1 but b is not), lin-06 has infinitely many (rows 3 and 4 are row 1 +/- row 2).
SYSTEMS = {
    "lin-01": ([[2, 3], [1, -1]], [8, -1]),
    "lin-02": ([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]], [8, -11, -3]),
    "lin-03": ([[4, -2, 1], [3, 6, -4], [2, 1, 8]], [11, -20, 30]),
    "lin-04": ([[2, -1, 0, 3], [1, 4, -2, 0], [0, 3, 5, -1], [-2, 1, 1, 4]], [7, -3, 10, 5]),
    "lin-05": ([[1, 2, 3], [2, 4, 6], [1, 1, 1]], [6, 13, 3]),
    "lin-06": ([[1, 2, -1, 3], [2, -1, 4, 1], [3, 1, 3, 4], [-1, 3, -5, 2]], [4, 7, 11, -3]),
}


def get_system(given: PuzzleInput, workspace: Path) -> SystemOutput:
    if given.puzzle_id not in SYSTEMS:
        raise ValueError(f"unknown puzzle {given.puzzle_id!r}: the systems are {', '.join(SYSTEMS)}")
    matrix, rhs = SYSTEMS[given.puzzle_id]
    return SystemOutput(puzzle_id=given.puzzle_id, matrix=[list(row) for row in matrix], rhs=list(rhs), size=len(rhs))


def system_record(given: PuzzleInput, workspace: Path) -> SystemOutput:
    return get_system(given, workspace)


def determinant(given: MatrixInput, workspace: Path) -> DeterminantOutput:
    """By exact elimination over fractions; the result of an integer matrix is an integer."""
    n = len(given.matrix)
    if n == 0 or any(len(row) != n for row in given.matrix):
        raise ValueError("the matrix must be square, with at least one row")
    rows = [[Fraction(value) for value in row] for row in given.matrix]
    result = Fraction(1)
    for col in range(n):
        pivot = next((r for r in range(col, n) if rows[r][col] != 0), None)
        if pivot is None:
            return DeterminantOutput(determinant=0)
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            result = -result
        result *= rows[col][col]
        for r in range(col + 1, n):
            factor = rows[r][col] / rows[col][col]
            rows[r] = [a - factor * b for a, b in zip(rows[r], rows[col])]
    return DeterminantOutput(determinant=int(result))
