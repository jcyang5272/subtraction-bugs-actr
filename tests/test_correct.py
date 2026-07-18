"""The intact procedure must compute correct differences on any problem."""

import random

import pytest

from subtraction import solve


CORRECT_CASES = [
    (81, 38, 43),
    (50, 23, 27),
    (305, 9, 296),      # borrow across a single zero
    (4002, 5, 3997),    # borrow across two zeros
    (100, 1, 99),
    (7, 3, 4),
    (90, 90, 0),
    (1000, 999, 1),     # cascade of borrows across zeros
]


@pytest.mark.parametrize("top, bottom, expected", CORRECT_CASES)
def test_correct_procedure(top, bottom, expected):
    state, _ = solve(top, bottom)
    assert state.is_goal()
    assert state.result() == expected
    assert state.result() == top - bottom


def test_correct_matches_python_on_random_problems():
    rng = random.Random(6795)
    for _ in range(500):
        top = rng.randint(0, 99999)
        bottom = rng.randint(0, top)  # keep it non-negative
        state, _ = solve(top, bottom)
        assert state.result() == top - bottom, (top, bottom)


def test_trace_is_recorded_per_cycle():
    _, tracer = solve(305, 9)
    assert len(tracer.entries) > 0
    # every entry carries a structured snapshot, not just a string
    for e in tracer.entries:
        assert "answer_str" in e.snapshot
        assert "focus" in e.snapshot
