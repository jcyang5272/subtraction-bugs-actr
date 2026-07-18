"""Each bug must reproduce its documented wrong answer -- exactly.

These assertions are the "bug catalog kept honest": a rule set counts as
modeling a bug only if it produces that specific human-like error, not merely
*an* error. Expected values are hand-derived from the rule edits in
rules_buggy.py and the bug taxonomy [Brown & Burton, 1978; VanLehn, 1990].
"""

import pytest

from subtraction import solve


# (bug, top, bottom, expected_wrong_answer, correct_answer)
BUG_CASES = [
    # Smaller-from-larger: never borrow, subtract small from large per column.
    ("smaller_from_larger", 81, 38, 57, 43),
    ("smaller_from_larger", 50, 23, 33, 27),
    ("smaller_from_larger", 305, 9, 304, 296),

    # Borrow-no-decrement: add 10 but never pay the borrow back.
    ("borrow_no_decrement", 81, 38, 53, 43),
    ("borrow_no_decrement", 50, 23, 37, 27),
    ("borrow_no_decrement", 305, 9, 306, 296),

    # Borrow-across-zero: 0 becomes 9 but the borrow dies, next col untouched.
    ("borrow_across_zero", 305, 9, 396, 296),
    ("borrow_across_zero", 4002, 5, 4097, 3997),

    # Stops-borrow-at-zero: skip the 0, decrement the next non-zero column.
    ("stops_borrow_at_zero", 305, 9, 206, 296),
]


@pytest.mark.parametrize("bug, top, bottom, wrong, correct", BUG_CASES)
def test_bug_reproduces_documented_answer(bug, top, bottom, wrong, correct):
    state, _ = solve(top, bottom, bug=bug)
    assert state.is_goal()
    assert state.result() == wrong
    # a real bug is wrong on this problem, not accidentally correct
    assert state.result() != correct
    assert correct == top - bottom


def test_bug_81_38_53_is_no_decrement_not_smaller_from_larger():
    """The 81-38=53 error is the borrow-no-decrement bug; smaller-from-larger
    on the same problem gives 57. (Documenting the distinction explicitly.)"""
    nd, _ = solve(81, 38, bug="borrow_no_decrement")
    sfl, _ = solve(81, 38, bug="smaller_from_larger")
    assert nd.result() == 53
    assert sfl.result() == 57
