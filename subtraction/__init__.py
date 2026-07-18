"""An ACT-R-style production-rule model of multi-digit subtraction and its bugs.

Public API:

    from subtraction import solve, correct_rules, BUGS

    state, trace = solve(81, 38)                       # correct procedure
    state, trace = solve(81, 38, bug="borrow_no_decrement")
    print(state.result(), trace.render())
"""

from __future__ import annotations

from typing import Optional

from .production import Production
from .state import State, Column
from .trace import Tracer, TraceEntry
from .engine import Engine, ImpasseError
from .rules_correct import correct_rules, correct_repairs
from .rules_buggy import BUGS

__all__ = [
    "Production", "State", "Column", "Tracer", "TraceEntry",
    "Engine", "ImpasseError", "correct_rules", "correct_repairs",
    "BUGS", "solve",
]


def solve(top: int, bottom: int, bug: Optional[str] = None,
          max_cycles: int = 1000) -> tuple[State, Tracer]:
    """Run `top - bottom` with the correct procedure or a named bug.

    Returns the final State and the Tracer. Raises KeyError for an unknown bug
    name and ImpasseError if the procedure stalls with no applicable repair.
    """
    if bug is None:
        rules, repairs = correct_rules(), correct_repairs()
    else:
        rules, repairs = BUGS[bug]()
    state = State.from_problem(top, bottom)
    tracer = Engine(rules, repairs, max_cycles=max_cycles).run(state)
    return state, tracer
