"""Buggy rule sets: four documented procedural bugs, each a principled edit.

A bug is never random corruption. Each rule set below is the correct procedure
with one rule-shaped change -- a deletion that forces an impasse and a repair, or
a single malformed production swapped in for a correct one. That is the whole
claim, made runnable: human error has structure, and you reproduce it by
breaking the *procedure*, not by perturbing the output [Brown & Burton, 1978;
Brown & VanLehn, 1980; VanLehn, 1990].

Each builder returns `(rules, repairs)` ready for Engine(rules, repairs).

  smaller_from_larger    delete borrow-init -> impasse -> "subtract small from
                         large" repair (a Repair-Theory bug).   81-38 -> 57
  borrow_no_decrement    borrow adds 10 but the decrement never happens.
                                                                81-38 -> 53
  borrow_across_zero     borrow into a 0 makes it 9 but the borrow dies there,
                         never reaching the next column.        305-9 -> 396
  stops_borrow_at_zero   refuse to borrow from a 0: skip it, decrement the next
                         non-zero column, leave the 0 alone.    305-9 -> 206
"""

from __future__ import annotations

from .production import Production
from .state import State
from .rules_correct import (
    correct_rules,
    cond_borrow_init,
    cond_diff,
    act_diff,
)


def _without(rules: list[Production], *names: str) -> list[Production]:
    return [r for r in rules if r.name not in names]


# --- 1. Smaller-from-larger (a Repair-Theory bug) ----------------------------
# Delete the borrow-init rule. A column with top < bottom now matches nothing:
# an impasse. The learner repairs it locally -- "you can't take big from small,
# so take small from big" -- and proceeds. The repair *is* the bug.


def cond_repair_sfl(s: State) -> bool:
    c = s.current
    return (
        s.need_decrement is None
        and c is not None
        and c.answer is None
        and c.top < c.bottom
    )


def act_repair_sfl(s: State) -> None:
    c = s.current
    c.answer = c.bottom - c.top   # smaller subtracted from larger
    s.focus += 1


def smaller_from_larger() -> tuple[list[Production], list[Production]]:
    rules = _without(correct_rules(), "borrow-init")
    repair = Production(
        "repair:smaller-from-larger", cond_repair_sfl, act_repair_sfl,
        is_repair=True,
        description="impasse repair: write |top-bottom| and move on",
    )
    return rules, [repair]


# --- 2. Borrow, no decrement -------------------------------------------------
# The add-10 half of borrowing survives; the decrement half is gone. We swap the
# two decrement rules for one that simply clears the debt without touching any
# digit, so 10 is added but nothing is ever paid back.


def cond_borrow_forget(s: State) -> bool:
    return s.need_decrement is not None


def act_borrow_forget(s: State) -> None:
    s.need_decrement = None  # debt forgotten; no column is decremented


def borrow_no_decrement() -> tuple[list[Production], list[Production]]:
    rules = _without(correct_rules(), "borrow-decrement", "borrow-across-zero")
    rules.append(
        Production(
            "borrow-no-decrement", cond_borrow_forget, act_borrow_forget,
            specificity=2,
            description="malformed: clear the borrow without decrementing",
        )
    )
    return rules, []


# --- 3. Borrow across zero (borrow dies at the zero) -------------------------
# Correct across-zero makes the 0 a 9 *and* carries the borrow one column left.
# This malformed version makes the 0 a 9 but stops there: the next column is
# never decremented.


def cond_across_zero(s: State) -> bool:
    i = s.need_decrement
    return i is not None and i < s.width and s.columns[i].top == 0


def act_across_zero_dies(s: State) -> None:
    i = s.need_decrement
    s.columns[i].top = 9
    s.need_decrement = None  # borrow does not propagate


def borrow_across_zero() -> tuple[list[Production], list[Production]]:
    rules = _without(correct_rules(), "borrow-across-zero")
    rules.append(
        Production(
            "borrow-across-zero-bug", cond_across_zero, act_across_zero_dies,
            specificity=2,
            description="malformed: 0 becomes 9 but the borrow stops there",
        )
    )
    return rules, []


# --- 4. Stops-borrow-at-zero (skip the zero) ---------------------------------
# Refuse to borrow from a 0 at all: leave the 0 untouched and pass the borrow on
# to the next column to the left, which is decremented normally.


def act_skip_zero(s: State) -> None:
    i = s.need_decrement
    s.need_decrement = i + 1  # leave the 0 as-is, owe the column to its left


def stops_borrow_at_zero() -> tuple[list[Production], list[Production]]:
    rules = _without(correct_rules(), "borrow-across-zero")
    rules.append(
        Production(
            "stops-borrow-at-zero", cond_across_zero, act_skip_zero,
            specificity=2,
            description="malformed: skip the 0, borrow from the next column",
        )
    )
    return rules, []


# --- 4b. Stops-borrow-at-zero, with a second-stage repair ---------------------
# The bug above reaches a *second* impasse on ~1% of valid problems: when a
# borrow chains left through a column an earlier borrow already zeroed and then
# runs off the high-order end (need_decrement >= width), no rule matches and the
# procedure stalls. Repair Theory says the learner applies a local repair at that
# impasse [Brown & VanLehn, 1980; VanLehn, 1990]. The most faithful one for "no
# column is left to borrow from" is to abandon the unpayable borrow: clear the
# debt and let the initiating column difference itself with the 10 it already
# received. Adding this repair closes the cascade -- the completed model returns
# a systematic wrong answer everywhere instead of stalling on those inputs.


def cond_repair_borrow_off_end(s: State) -> bool:
    return s.need_decrement is not None and s.need_decrement >= s.width


def act_repair_borrow_off_end(s: State) -> None:
    s.need_decrement = None  # the borrow ran off the end; drop the unpayable debt


def stops_borrow_at_zero_repaired() -> tuple[list[Production], list[Production]]:
    rules, _ = stops_borrow_at_zero()
    repair = Production(
        "repair:borrow-off-end",
        cond_repair_borrow_off_end,
        act_repair_borrow_off_end,
        is_repair=True,
        description="impasse repair: borrow ran off the high end -> drop the debt",
    )
    return rules, [repair]


# Registry for demos/tests. The four canonical bugs; the repaired variant is an
# extension kept out of the catalog so the base four stay stable.
BUGS = {
    "smaller_from_larger": smaller_from_larger,
    "borrow_no_decrement": borrow_no_decrement,
    "borrow_across_zero": borrow_across_zero,
    "stops_borrow_at_zero": stops_borrow_at_zero,
}
