"""Declarative working memory: the chunks a subtraction problem is made of.

This is the ACT-R "chunk" side of the chunk/production split [Anderson &
Lebiere, 1998]. The rules in rules_correct.py / rules_buggy.py may read and
write *only* what lives here -- column digits, the borrow bookkeeping, and the
focus of attention. Forbidding rules from reaching outside these chunks is what
makes a bug expressible: a broken rule set can no longer quietly "do the right
thing," because the only way to compute is through this explicit state.

Columns are indexed right-to-left: column 0 is the units column. A problem is
laid out so that `top - bottom` is computed column by column from column 0
upward, exactly as the written algorithm is taught.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


def _digits_low_to_high(n: int, width: int) -> list[int]:
    """Return the decimal digits of `n`, units first, left-padded to `width`."""
    s = str(n)
    digs = [int(c) for c in reversed(s)]
    digs += [0] * (width - len(digs))
    return digs


@dataclass
class Column:
    """One column of the problem -- a single declarative chunk.

    `top` and `bottom` are the two digits; `answer` is the digit written
    underneath, or None until a rule fills it in. `top` is mutated in place by
    borrowing (add-10 on this column, decrement on a column to the left), which
    is precisely how the written procedure records a borrow.
    """

    index: int
    top: int
    bottom: int
    answer: Optional[int] = None


@dataclass
class State:
    """Complete working-memory state for one subtraction problem."""

    columns: list[Column] = field(default_factory=list)
    # Focus of attention: index of the column currently being processed.
    focus: int = 0
    # Borrow bookkeeping: index of a column whose top digit still owes a
    # decrement of 1, or None when no borrow is pending.
    need_decrement: Optional[int] = None
    # Set True by the engine when no rule (and no repair) can fire.
    impasse: bool = False

    @classmethod
    def from_problem(cls, top: int, bottom: int) -> "State":
        """Build a state for `top - bottom` (both non-negative integers)."""
        if top < 0 or bottom < 0:
            raise ValueError("only non-negative integers are supported")
        width = max(len(str(top)), len(str(bottom)))
        t = _digits_low_to_high(top, width)
        b = _digits_low_to_high(bottom, width)
        cols = [Column(index=i, top=t[i], bottom=b[i]) for i in range(width)]
        return cls(columns=cols, focus=0, need_decrement=None)

    # --- convenience accessors used by rule conditions -----------------------

    @property
    def width(self) -> int:
        return len(self.columns)

    @property
    def current(self) -> Optional[Column]:
        """The column under focus, or None if focus has run off the end."""
        if 0 <= self.focus < self.width:
            return self.columns[self.focus]
        return None

    def is_goal(self) -> bool:
        """Goal reached when every column has an answer digit written."""
        return all(c.answer is not None for c in self.columns)

    # --- reading out the result ---------------------------------------------

    def result(self) -> int:
        """Integer value of the answer row (assumes the goal is reached)."""
        value = 0
        for c in reversed(self.columns):  # high-order column first
            value = value * 10 + (c.answer or 0)
        return value

    def result_str(self) -> str:
        """Answer digits high-order to low-order, '?' where still blank."""
        return "".join(
            ("?" if c.answer is None else str(c.answer))
            for c in reversed(self.columns)
        )

    def snapshot(self) -> dict:
        """A structured, copyable picture of working memory for one trace row.

        Loose print statements cannot pinpoint *which* column a procedure broke
        in; a per-cycle snapshot can. This is the diagnostic payoff of the tool.
        """
        return {
            "focus": self.focus,
            "need_decrement": self.need_decrement,
            "impasse": self.impasse,
            "top": [c.top for c in reversed(self.columns)],
            "bottom": [c.bottom for c in reversed(self.columns)],
            "answer": [c.answer for c in reversed(self.columns)],
            "answer_str": self.result_str(),
        }
