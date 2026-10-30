"""The deterministic verifier: each tool's checks live in its own class, on contract instances."""

from contract import Task, Tool

from .linear import Determinant, GetSystem, verify_get_system, verify_solve

TOOLS = {
    Tool.GET_SYSTEM: GetSystem,
    Tool.DETERMINANT: Determinant,
    Tool.SYSTEM_RECORD: GetSystem,
}
# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {
    Task.GET_SYSTEM: verify_get_system,
    Task.SOLVE_SYSTEM: verify_solve,
}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
