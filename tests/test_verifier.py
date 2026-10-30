from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, PuzzleInput, Task, Tool
from plugin import get_system, system_record

# Exact answers, found independently by elimination and by Cramer's rule.
UNIQUE = {
    "lin-01": ["1", "2"],
    "lin-02": ["2", "3", "-1"],
    "lin-03": ["292/263", "-382/263", "961/263"],
    "lin-04": ["569/399", "10/399", "43/19", "185/133"],
}


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def verify_input(tool: str, value: dict) -> dict:
    return verifier.verify_input(tool, build_output(value, TOOLS[Tool(tool)][0]))


def verify_output(tool: str, given: dict, made: dict, workspace: Path) -> dict:
    classes = TOOLS[Tool(tool)]
    return verifier.verify_output(tool, build_output(given, classes[0]), build_output(made, classes[1]), str(workspace))


def solve(workspace: Path, puzzle_id: str, output: dict, pin: bool = True) -> dict:
    given, made = TASKS[Task.SOLVE_SYSTEM]
    record = plain_output(system_record(PuzzleInput(puzzle_id=puzzle_id), workspace))
    pinned = build_output(record, TOOLS[Tool.SYSTEM_RECORD][1]) if pin else None
    return verifier.verify_task(
        "solve-system",
        build_output({"puzzle_id": puzzle_id}, given),
        build_output({"gave_up": False} | output, made),
        pinned,
        str(workspace),
    )


@pytest.mark.parametrize(("puzzle_id", "solution"), list(UNIQUE.items()))
def test_approves_each_exact_unique_solution(tmp_path: Path, puzzle_id: str, solution: list[str]) -> None:
    verdict = solve(tmp_path, puzzle_id, {"status": "unique", "solution": solution})
    assert verdict["valid"] is True and verdict["score"] == 1.0


def test_accepts_equal_fractions_in_any_form(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "lin-01", {"status": "unique", "solution": ["2/2", " 4/2"]})
    assert verdict["valid"] is True


def test_one_wrong_value_is_invalid_with_partial_credit(tmp_path: Path) -> None:
    wrong = ["292/263", "-382/263", "960/263"]
    verdict = solve(tmp_path, "lin-03", {"status": "unique", "solution": wrong})
    assert verdict["valid"] is False and verdict["score"] == round(0.4 + 0.6 * 2 / 3, 4)


def test_rounded_decimals_are_malformed(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "lin-03", {"status": "unique", "solution": ["1.1103", "-1.4525", "3.6540"]})
    assert verdict["valid"] is False and verdict["score"] == 0.4 and "fraction" in verdict["message"]


@pytest.mark.parametrize("solution", [[], ["1"], ["1", "2", "3"], ["1", "2/0"], ["1", "two"], ["1", "2/-3"]])
def test_malformed_or_wrong_length_solutions(tmp_path: Path, solution: list[str]) -> None:
    verdict = solve(tmp_path, "lin-01", {"status": "unique", "solution": solution})
    assert verdict["valid"] is False and verdict["score"] == 0.4


def test_no_solution_system(tmp_path: Path) -> None:
    assert solve(tmp_path, "lin-05", {"status": "none", "solution": []})["valid"] is True
    verdict = solve(tmp_path, "lin-05", {"status": "infinite", "solution": ["1", "1", "1"]})
    assert verdict["valid"] is False and verdict["score"] == 0.0 and "none" in verdict["message"]
    verdict = solve(tmp_path, "lin-05", {"status": "none", "solution": ["1", "1", "1"]})
    assert verdict["valid"] is False and "empty" in verdict["message"]


def test_infinite_system_accepts_any_particular_solution(tmp_path: Path) -> None:
    for particular in (["18/5", "1/5", "0", "0"], ["4", "0", "0", "0"]):
        verdict = solve(tmp_path, "lin-06", {"status": "infinite", "solution": particular})
        assert verdict["valid"] is (particular[0] == "18/5")
    verdict = solve(tmp_path, "lin-06", {"status": "unique", "solution": ["18/5", "1/5", "0", "0"]})
    assert verdict["valid"] is False and verdict["score"] == 0.0


def test_calling_a_unique_system_singular_is_invalid(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "lin-01", {"status": "none", "solution": []})
    assert verdict["valid"] is False and verdict["score"] == 0.0


def test_refuses_to_judge_without_the_system(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "lin-01", {"status": "unique", "solution": ["1", "2"]}, pin=False)
    assert verdict["valid"] is False and "system" in verdict["message"]


def test_tool_task_and_tool_checks(tmp_path: Path) -> None:
    given = {"puzzle_id": "lin-01"}
    made = plain_output(get_system(PuzzleInput(**given), tmp_path))
    task_given, task_made = TASKS[Task.GET_SYSTEM]
    verdict = verifier.verify_task(
        "get-system", build_output(given, task_given), build_output(made, task_made), None, ""
    )
    assert verdict["valid"] is True
    assert verify_output("get_system", given, made | {"size": 3}, tmp_path)["valid"] is False
    assert verify_input("determinant", {"matrix": [[1, 2], [3, 4]]})["valid"] is True
    assert verify_input("determinant", {"matrix": [[1, 2], [3]]})["valid"] is False
    assert verify_output("determinant", {"matrix": [[1, 2], [3, 4]]}, {"determinant": -2}, tmp_path)["valid"] is True
    assert verify_output("determinant", {"matrix": [[1, 2], [3, 4]]}, {"determinant": 2}, tmp_path)["valid"] is False


def test_giving_up_is_a_failure_with_the_attempt_kept_in_details(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "lin-01", {"status": "unique", "solution": ["1", "2"], "gave_up": True})
    assert verdict["valid"] is False and verdict["score"] == 0.0 and "gave up" in verdict["message"]
    assert verdict["details"]["attempt_score"] == 1.0
    verdict = solve(tmp_path, "lin-01", {"status": "none", "solution": [], "gave_up": True})
    assert verdict["valid"] is False and verdict["score"] == 0.0 and verdict["details"]["gave_up"] is True
