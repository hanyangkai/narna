from __future__ import annotations

from enum import Enum


class RunState(str, Enum):
    CREATED = "Created"
    STARTING = "Starting"
    RUNNING = "Running"
    AWAITING_INPUT = "AwaitingInput"
    COMPLETING = "Completing"
    COMPLETED = "Completed"
    FAILING = "Failing"
    FAILED = "Failed"
    ABORTING = "Aborting"
    ABORTED = "Aborted"


TERMINAL = {RunState.COMPLETED, RunState.FAILED, RunState.ABORTED}

TRANSITIONS: dict[RunState, set[RunState]] = {
    RunState.CREATED: {RunState.STARTING},
    RunState.STARTING: {RunState.RUNNING, RunState.FAILING},
    RunState.RUNNING: {
        RunState.AWAITING_INPUT,
        RunState.COMPLETING,
        RunState.FAILING,
        RunState.ABORTING,
    },
    RunState.AWAITING_INPUT: {RunState.RUNNING, RunState.FAILING, RunState.ABORTING},
    RunState.COMPLETING: {RunState.COMPLETED, RunState.FAILING},
    RunState.FAILING: {RunState.FAILED},
    RunState.ABORTING: {RunState.ABORTED},
    RunState.COMPLETED: set(),
    RunState.FAILED: set(),
    RunState.ABORTED: set(),
}


def transition(current: RunState, nxt: RunState) -> RunState:
    allowed = TRANSITIONS.get(current, set())
    if nxt not in allowed:
        raise ValueError(f"invalid transition {current.value} -> {nxt.value}")
    return nxt
