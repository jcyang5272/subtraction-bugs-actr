"""Engine-level guarantees: impasse handling and conflict resolution."""

import pytest

from subtraction import Engine, State, ImpasseError, solve
from subtraction.rules_correct import correct_rules
from subtraction.rules_buggy import (
    _without,
    smaller_from_larger,
    stops_borrow_at_zero,
    stops_borrow_at_zero_repaired,
)


def test_naive_deletion_causes_impasse_not_a_wrong_answer():
    """Deleting borrow-init with NO repair stalls the procedure.

    This is the check-in's central lesson: you cannot get a human-like wrong
    answer by naive corruption -- it crashes/stalls. A human-like error needs a
    principled repair (see the next test).
    """
    rules = _without(correct_rules(), "borrow-init")  # no repair supplied
    state = State.from_problem(81, 38)  # units column needs a borrow
    with pytest.raises(ImpasseError):
        Engine(rules, repairs=[]).run(state)
    assert state.impasse is True


def test_repair_turns_impasse_into_human_like_error():
    """Same deletion, but with the smaller-from-larger repair, yields 57."""
    rules, repairs = smaller_from_larger()
    state = State.from_problem(81, 38)
    Engine(rules, repairs).run(state)
    assert state.result() == 57
    assert state.impasse is False


def test_conflict_resolution_prefers_specificity():
    """When borrow-decrement (spec 2) and diff (spec 1) both match, the more
    specific decrement fires first, so the borrow is paid before differencing."""
    _, tracer = _run_traced(305, 9)
    fired = tracer.fired_rules()
    # the first decrement-family rule must precede the first diff
    first_diff = next(i for i, r in enumerate(fired) if r == "diff")
    first_borrow_pay = next(
        i for i, r in enumerate(fired)
        if r in ("borrow-decrement", "borrow-across-zero")
    )
    assert first_borrow_pay < first_diff


def test_stops_borrow_at_zero_hits_a_second_impasse():
    """The bare stops-borrow-at-zero bug cascades into a SECOND impasse when a
    borrow chains through an already-zeroed column and runs off the high end.
    10303 - 7338 is the smallest such case found by the robustness sweep."""
    rules, repairs = stops_borrow_at_zero()  # no repair for the off-end impasse
    state = State.from_problem(10303, 7338)
    with pytest.raises(ImpasseError):
        Engine(rules, repairs).run(state)
    assert state.impasse is True


def test_second_stage_repair_closes_the_cascade():
    """Attaching the borrow-off-end repair turns that second impasse into a
    systematic wrong answer, while leaving the already-passing 305-9=206 case
    unchanged. This is Repair Theory's 'impasses cascade, repairs resolve them'
    made executable a second time."""
    rules, repairs = stops_borrow_at_zero_repaired()

    st = State.from_problem(10303, 7338)
    Engine(rules, repairs).run(st)          # no longer raises
    assert st.impasse is False
    assert st.result() == 3875              # a specific, deterministic error

    # the repair only fires at the off-end impasse; the base bug is untouched
    st206 = State.from_problem(305, 9)
    Engine(rules, repairs).run(st206)
    assert st206.result() == 206
    # sanity: the canonical bug (via solve) still stalls on the cascade case
    with pytest.raises(ImpasseError):
        solve(10303, 7338, bug="stops_borrow_at_zero")


def test_runaway_is_bounded():
    rules = correct_rules()
    state = State.from_problem(5, 5)
    with pytest.raises(RuntimeError):
        # max_cycles=0 forces the guard to trip immediately
        Engine(rules, max_cycles=0).run(state)


def _run_traced(top, bottom):
    from subtraction import solve
    return solve(top, bottom)
