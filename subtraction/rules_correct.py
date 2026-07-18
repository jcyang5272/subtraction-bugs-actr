"""The correct multi-column subtraction procedure, as production rules.

The procedure (after VanLehn's "Sub" task analysis [VanLehn, 1990]) is: process
columns right-to-left; in each column, if the top digit is at least the bottom
digit, write the difference; otherwise borrow -- add 10 to this column's top and
decrement the next column to the left, recursing through any 0s on the way.

Each cognitive step is one production below. Specificity is set so that a pending
borrow is always resolved before the column that requested it is differenced:
the decrement rules (specificity 2) outrank the difference rule (specificity 1),
so when both match in the same cycle the decrement fires first.

    correct_rules():   the five productions of the intact procedure
    correct_repairs(): none -- a correct procedure never reaches an impasse
"""

from __future__ import annotations

from .production import Production
from .state import State

# --- conditions --------------------------------------------------------------


def _at_unfinished_column(s: State) -> bool:
    c = s.current
    return c is not None and c.answer is None


def cond_diff(s: State) -> bool:
    """Focus column is ready and needs no borrow (top >= bottom)."""
    if s.need_decrement is not None:
        return False
    c = s.current
    return _at_unfinished_column(s) and c.top >= c.bottom


def cond_borrow_init(s: State) -> bool:
    """Focus column needs a borrow (top < bottom) and none is pending yet."""
    if s.need_decrement is not None:
        return False
    c = s.current
    return _at_unfinished_column(s) and c.top < c.bottom


def cond_decrement(s: State) -> bool:
    """A borrow is owed by a non-zero column -> plain decrement."""
    i = s.need_decrement
    return i is not None and i < s.width and s.columns[i].top > 0


def cond_across_zero(s: State) -> bool:
    """A borrow is owed by a 0 column -> rewrite as 9 and carry the borrow on."""
    i = s.need_decrement
    return i is not None and i < s.width and s.columns[i].top == 0


# --- actions -----------------------------------------------------------------


def act_diff(s: State) -> None:
    c = s.current
    c.answer = c.top - c.bottom
    s.focus += 1


def act_borrow_init(s: State) -> None:
    c = s.current
    c.top += 10
    s.need_decrement = s.focus + 1  # the column to borrow from


def act_decrement(s: State) -> None:
    i = s.need_decrement
    s.columns[i].top -= 1
    s.need_decrement = None


def act_across_zero(s: State) -> None:
    i = s.need_decrement
    s.columns[i].top = 9        # 0 becomes 9...
    s.need_decrement = i + 1    # ...and the borrow propagates one column left


# --- rule set ----------------------------------------------------------------


def correct_rules() -> list[Production]:
    return [
        Production(
            "diff", cond_diff, act_diff, specificity=1,
            description="write top-bottom for a column needing no borrow",
        ),
        Production(
            "borrow-init", cond_borrow_init, act_borrow_init, specificity=1,
            description="top<bottom: add 10 here, owe a decrement to the left",
        ),
        Production(
            "borrow-decrement", cond_decrement, act_decrement, specificity=2,
            description="pay an owed borrow by decrementing a non-zero column",
        ),
        Production(
            "borrow-across-zero", cond_across_zero, act_across_zero,
            specificity=2,
            description="borrow owed by a 0: make it 9 and carry the borrow on",
        ),
    ]


def correct_repairs() -> list[Production]:
    return []
