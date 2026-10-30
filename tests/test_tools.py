from __future__ import annotations

from pathlib import Path

import pytest

from contract import MatrixInput, PuzzleInput, Tool
from plugin import determinant, get_system, system_record
from plugin.budget import Budget, BudgetSpent
from plugin.systems import SYSTEMS


def test_get_system_returns_matrix_and_rhs(tmp_path: Path) -> None:
    system = get_system(PuzzleInput(puzzle_id="lin-01"), tmp_path)
    assert (system.matrix, system.rhs, system.size) == ([[2, 3], [1, -1]], [8, -1], 2)
    assert system_record(PuzzleInput(puzzle_id="lin-01"), tmp_path) == system
    with pytest.raises(ValueError, match="unknown puzzle"):
        get_system(PuzzleInput(puzzle_id="lin-99"), tmp_path)


def test_bank_is_square_systems_of_two_to_four() -> None:
    assert len(SYSTEMS) == 6
    for matrix, rhs in SYSTEMS.values():
        assert 2 <= len(matrix) <= 4 and all(len(row) == len(matrix) for row in matrix) and len(rhs) == len(matrix)


@pytest.mark.parametrize(
    ("matrix", "value"),
    [
        ([[5]], 5),
        ([[2, 3], [1, -1]], -5),
        ([[4, -2, 1], [3, 6, -4], [2, 1, 8]], 263),
        ([[1, 2, 3], [2, 4, 6], [1, 1, 1]], 0),
        ([[2, -1, 0, 3], [1, 4, -2, 0], [0, 3, 5, -1], [-2, 1, 1, 4]], 399),
    ],
)
def test_determinant(tmp_path: Path, matrix: list[list[int]], value: int) -> None:
    assert determinant(MatrixInput(matrix=matrix), tmp_path).determinant == value


def test_determinant_needs_a_square_matrix(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="square"):
        determinant(MatrixInput(matrix=[[1, 2], [3]]), tmp_path)
    with pytest.raises(ValueError, match="square"):
        determinant(MatrixInput(matrix=[]), tmp_path)


def test_budget_allows_twelve_calls_per_system() -> None:
    budget = Budget(limit=12)
    budget.charge(Tool.GET_SYSTEM, {"puzzle_id": "lin-01"})
    for _ in range(11):
        budget.charge(Tool.DETERMINANT, {})
    with pytest.raises(BudgetSpent, match="submit your best answer now, or set gave_up"):
        budget.charge(Tool.DETERMINANT, {})
    budget.charge(Tool.SYSTEM_RECORD, {})
    budget.charge(Tool.GET_SYSTEM, {"puzzle_id": "lin-02"})
    assert budget.used == 1
