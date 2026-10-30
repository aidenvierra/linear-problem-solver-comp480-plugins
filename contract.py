"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    GET_SYSTEM = "get_system"
    DETERMINANT = "determinant"
    SYSTEM_RECORD = "system_record"


class Task(Enum):
    GET_SYSTEM = "get-system"
    SOLVE_SYSTEM = "solve-system"


class Status(Enum):
    UNIQUE = "unique"
    NONE = "none"
    INFINITE = "infinite"


GAVE_UP = (
    "True only if you could not solve it: then submit your best partial attempt, or empty values."
    " False when you believe your answer is right"
)


@dataclass
class PuzzleInput(Output):
    puzzle_id: Annotated[str, "The system's id, e.g. lin-01"]


@dataclass
class SystemOutput(Output):
    puzzle_id: Annotated[str, "The system's id, as given"]
    matrix: Annotated[list[list[int]], "The coefficient matrix A, one row per equation"]
    rhs: Annotated[list[int], "The right-hand side b, one value per equation"]
    size: Annotated[int, "The number of equations and of unknowns x1..xn"]


@dataclass
class MatrixInput(Output):
    matrix: Annotated[list[list[int]], "A square matrix of integers, one row per list"]


@dataclass
class DeterminantOutput(Output):
    determinant: Annotated[int, "The matrix's determinant"]


@dataclass
class SolutionOutput(Output):
    status: Annotated[Status, "Whether Ax = b has exactly one solution, none, or infinitely many"]
    solution: Annotated[
        list[str],
        "x1..xn as exact integers or fractions such as -7/3, never decimals: the solution when unique, any one"
        " solution when there are infinitely many, empty when there is none",
    ]
    gave_up: Annotated[bool, GAVE_UP]


TOOLS = {
    Tool.GET_SYSTEM: (PuzzleInput, SystemOutput),
    Tool.DETERMINANT: (MatrixInput, DeterminantOutput),
    Tool.SYSTEM_RECORD: (PuzzleInput, SystemOutput),
}
TASKS = {
    Task.GET_SYSTEM: (PuzzleInput, SystemOutput),
    Task.SOLVE_SYSTEM: (PuzzleInput, SolutionOutput),
}
