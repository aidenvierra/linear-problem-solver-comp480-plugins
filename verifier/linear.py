"""Checks for each tool's calls and for the solve-system submission, against the pinned system."""

import re
from fractions import Fraction

from .checks import gave_up_verdict, result

PUZZLE_ID = re.compile(r"^lin-\d{2}$")
NUMBER = re.compile(r"^-?\d+(/[1-9]\d*)?$")


def square_problem(matrix):
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        return "the matrix must be square, with at least one row"
    return None


def reduce(matrix, rhs):
    """Rank of A, rank of [A | b], and the solution when the rank is full, by exact Gauss-Jordan elimination."""
    n = len(matrix)
    rows = [[Fraction(v) for v in row] + [Fraction(b)] for row, b in zip(matrix, rhs)]
    rank = 0
    for col in range(n):
        pivot = next((r for r in range(rank, n) if rows[r][col] != 0), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        lead = rows[rank][col]
        rows[rank] = [v / lead for v in rows[rank]]
        for r in range(n):
            if r != rank and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[rank])]
        rank += 1
    augmented = rank + sum(1 for row in rows[rank:] if row[-1] != 0)
    solution = [rows[i][-1] for i in range(n)] if rank == n else None
    return rank, augmented, solution


def determinant(matrix):
    rank, _, _ = reduce(matrix, [0] * len(matrix))
    if rank < len(matrix):
        return Fraction(0)
    # Recompute with the product of pivots: elimination with row swaps tracked.
    rows = [[Fraction(v) for v in row] for row in matrix]
    n, value = len(rows), Fraction(1)
    for col in range(n):
        pivot = next(r for r in range(col, n) if rows[r][col] != 0)
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            value = -value
        value *= rows[col][col]
        for r in range(col + 1, n):
            factor = rows[r][col] / rows[col][col]
            rows[r] = [a - factor * b for a, b in zip(rows[r], rows[col])]
    return value


def parse(values):
    """The values as fractions, or None if any is not an integer or a fraction like -7/3."""
    cleaned = [value.strip() for value in values]
    if any(not NUMBER.fullmatch(value) for value in cleaned):
        return None
    return [Fraction(value) for value in cleaned]


def _puzzle_input(value):
    if not PUZZLE_ID.fullmatch(value.puzzle_id):
        return result(False, f"puzzle_id {value.puzzle_id!r} is not of the form lin-NN")
    return result(True, "input is valid")


class GetSystem:
    verify_input = staticmethod(_puzzle_input)

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        if output_value.puzzle_id != input_value.puzzle_id:
            return result(False, "the system is for a different id")
        problem = square_problem(output_value.matrix)
        if problem:
            return result(False, problem)
        if not len(output_value.rhs) == output_value.size == len(output_value.matrix):
            return result(False, "size, matrix and rhs do not agree")
        return result(True, "system returned")


class Determinant:
    @staticmethod
    def verify_input(value):
        problem = square_problem(value.matrix)
        return result(False, problem) if problem else result(True, "input is valid")

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        if output_value.determinant != determinant(input_value.matrix):
            return result(False, "the determinant is wrong")
        return result(True, "determinant is right")


def verify_get_system(arguments, output, reference, workspace):
    return GetSystem.verify_output(arguments, output, workspace)


def _judge(arguments, output, reference, workspace):
    """Status by the ranks of A and [A | b]; a unique solution must equal the verifier's exactly, and a
    solution of an infinite system must satisfy Ax = b. Score: 0.4 for the status, 0.6 for the values."""
    if reference is None or square_problem(reference.matrix) or len(reference.rhs) != len(reference.matrix):
        return result(False, "no usable system was pinned, so the submission cannot be judged")
    matrix, rhs = reference.matrix, reference.rhs
    rank, augmented, truth = reduce(matrix, rhs)
    status = "unique" if truth is not None else "none" if augmented > rank else "infinite"
    details = {"true_status": status, "rank": rank, "augmented_rank": augmented}
    if output.status.value != status:
        return result(False, f"wrong status: the system has {status} solution(s)", score=0.0, **details)
    if status == "none":
        if output.solution:
            return result(False, "a system with no solution needs an empty solution", score=0.4, **details)
        return result(True, "correct: the system has no solution", **details)
    if len(output.solution) != len(matrix):
        return result(False, f"the solution needs exactly {len(matrix)} values", score=0.4, **details)
    values = parse(output.solution)
    if values is None:
        return result(False, "each value must be an exact integer or fraction such as -7/3", score=0.4, **details)
    if status == "unique":
        right = sum(1 for a, b in zip(values, truth) if a == b)
        if right != len(truth):
            score = round(0.4 + 0.6 * right / len(truth), 4)
            return result(False, f"{len(truth) - right} of {len(truth)} values are wrong", score=score, **details)
        return result(True, "correct: the one solution, exactly", **details)
    residual = [sum(a * x for a, x in zip(row, values)) - b for row, b in zip(matrix, rhs)]
    if any(residual):
        return result(False, "the values do not satisfy Ax = b", score=0.4, **details)
    return result(True, "correct: infinitely many solutions, and the values satisfy Ax = b", **details)


def verify_solve(arguments, output, reference, workspace):
    return gave_up_verdict(_judge(arguments, output, reference, workspace), output)
