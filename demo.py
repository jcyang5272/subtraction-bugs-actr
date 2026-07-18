"""Proof-of-concept demo: run the correct procedure and all four bugs, with
annotated traces, on canonical problems.

    python demo.py            # full traces for a couple of problems + summary
    python demo.py --summary  # just the one-line correct-vs-bug summary table
"""

from __future__ import annotations

import sys

from subtraction import solve, ImpasseError
from subtraction.rules_buggy import BUGS


BUG_TITLES = {
    "smaller_from_larger": "Smaller-from-larger (impasse + repair)",
    "borrow_no_decrement": "Borrow, no decrement",
    "borrow_across_zero": "Borrow across zero (borrow dies)",
    "stops_borrow_at_zero": "Stops-borrow-at-zero (skip the 0)",
}


def show_trace(top: int, bottom: int, bug=None) -> None:
    title = BUG_TITLES.get(bug, "Correct procedure")
    print(f"\n{'=' * 64}")
    print(f"{title}:  {top} - {bottom}")
    print("=" * 64)
    state, tracer = solve(top, bottom, bug=bug)
    print(tracer.render())
    print(f"--> answer: {state.result()}   (correct = {top - bottom})")


def summary() -> None:
    print(f"\n{'bug':<24} {'81-38':>8} {'50-23':>8} {'305-9':>8} {'4002-5':>8}")
    print("-" * 60)
    probs = [(81, 38), (50, 23), (305, 9), (4002, 5)]

    def cell(bug, t, b):
        try:
            st, _ = solve(t, b, bug=bug)
            return str(st.result())
        except ImpasseError:
            return "impasse"

    row = "correct"
    print(f"{row:<24} " + " ".join(f"{t - b:>8}" for t, b in probs))
    for bug in BUGS:
        print(f"{bug:<24} " + " ".join(f"{cell(bug, t, b):>8}" for t, b in probs))


def main(argv) -> None:
    if "--summary" in argv:
        summary()
        return
    # A few full traces that exercise borrowing and zeros...
    show_trace(305, 9)                              # correct, across a zero
    show_trace(81, 38, bug="smaller_from_larger")   # repair-driven bug
    show_trace(81, 38, bug="borrow_no_decrement")   # the real 81-38=53 bug
    show_trace(305, 9, bug="borrow_across_zero")
    show_trace(305, 9, bug="stops_borrow_at_zero")
    summary()


if __name__ == "__main__":
    main(sys.argv[1:])
