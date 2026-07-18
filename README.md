# Modeling Procedural Bugs in Multi-Digit Subtraction

A small, dependency-free production-rule interpreter that runs the correct
column-subtraction algorithm **and** reproduces four documented "buggy"
procedures children use — each as a principled, rule-shaped break in the
procedure, not as random corruption of the output.

This is the proof-of-concept tool for the CS 6795 project (Computational
Model/Tool track). Everything is plain Python 3 standard library; transparency
is the point, so every cognitive step is inspectable.

## Run it

```bash
cd assignment/project1/code

# Demo: annotated traces for the correct procedure and all four bugs
python demo.py
python demo.py --summary      # just the correct-vs-bug results table

# Tests (pytest). A venv with pytest already exists at code/.venv:
.venv/bin/python -m pytest -q
```

`demo.py` and the tests need `subtraction/` on the path; running from `code/`
(as above) or via the provided venv handles that automatically.

## Architecture: the recognize–act cycle is the theory

The design mirrors an ACT-R-style production system [Anderson & Lebiere, 1998;
Anderson et al., 2004; Ritter et al., 2019]. The split between *what is known*
(declarative chunks) and *how to act* (procedural productions) is enforced in
code, which is exactly what makes a bug expressible.

| Module | Responsibility | ACT-R mapping |
|---|---|---|
| `state.py` | Working memory: `Column` chunks (top, bottom, answer), focus of attention, borrow bookkeeping | Declarative chunks |
| `production.py` | A `Production` = `condition` + `action` + `specificity` | A procedural production rule |
| `engine.py` | The cycle: **match all → conflict-resolve by specificity → fire one → log**; impasse detection + repair | Recognize–act cycle, conflict resolution, impasse/repair |
| `trace.py` | Structured per-cycle state snapshots | Inspectable processing trace |
| `rules_correct.py` | The five productions of the intact procedure | The correct skill |
| `rules_buggy.py` | Each bug = the correct set with one rule-shaped edit | Mislearned / repaired skills |

The engine loop (`engine.py`):

```
while not goal:
    matched = [r for r in rules if r.matches(state)]
    if matched:
        fire the most specific matched rule        # conflict resolution
    elif a repair matches:
        fire the repair                            # Repair Theory
    else:
        impasse — halt                             # naive breakage just stalls
```

**Why specificity matters.** After `borrow-init` adds 10 to a column, two rules
match the same cycle: pay the owed borrow (`borrow-decrement`, specificity 2) or
difference the now-ready column (`diff`, specificity 1). The more specific
decrement wins, so the borrow is always paid before the column is differenced.
Bugs live here: a missing *specific* rule lets a more *general*, wrong rule take
the cycle.

## The bug catalog (with verified outputs)

Each bug is one edit away from the correct procedure. Outputs below are asserted
in `tests/test_bugs.py`.

| Bug | The rule-shaped break | 81−38 | 50−23 | 305−9 | 4002−5 |
|---|---|---|---|---|---|
| *correct* | — | 43 | 27 | 296 | 3997 |
| **smaller-from-larger** | delete `borrow-init` → impasse → "take small from large" **repair** | **57** | 33 | 304 | 4003 |
| **borrow-no-decrement** | add 10 but never decrement the next column | **53** | 37 | 306 | 4007 |
| **borrow-across-zero** | borrow into a 0 makes it 9, but the borrow dies there | 43 | 27 | **396** | 4097 |
| **stops-borrow-at-zero** | refuse to borrow from a 0: skip it, decrement the next column | 43 | 27 | **206** | 3007 |

Smaller-from-larger is modeled as a genuine **Repair-Theory** bug [Brown &
VanLehn, 1980]: deleting the borrow rule creates an *impasse* (no rule matches a
`top < bottom` column), and the model applies a local *repair* — subtract the
smaller digit from the larger — which is itself the observed error. The other
three are mislearned productions (a malformed rule swapped in), reflecting
VanLehn's point [VanLehn, 1990] that not every bug is a repair.

### Note on the "81 − 38 = 53" example

`81 − 38 = 53` is the **borrow-no-decrement** bug, *not* smaller-from-larger.
Smaller-from-larger on the same problem gives **57** (units |1−8|=7, tens
|8−3|=5). This is pinned down in
`tests/test_bugs.py::test_bug_81_38_53_is_no_decrement_not_smaller_from_larger`.
The pitch and check-in currently attribute `81 − 38 = 53` to the
smaller-from-larger rule — worth correcting in the final report.

## Testing results

`.venv/bin/python -m pytest -q` → **26 passed**. Coverage:

- **Correct procedure** (`test_correct.py`): 8 hand-picked cases plus 500
  random problems checked against Python's `-`, including cascades of borrows
  across zeros (e.g. 1000−999, 4002−5).
- **Bugs** (`test_bugs.py`): each bug reproduces its exact documented wrong
  answer and is verified to differ from the correct answer.
- **Engine** (`test_engine.py`): naive rule deletion raises `ImpasseError`
  (does *not* silently produce a wrong answer); the same deletion **with** a
  repair yields the human-like 57; specificity-based conflict resolution pays
  borrows before differencing; runaway cycles are bounded; the bare
  stops-borrow-at-zero bug hits a *second* impasse on ~1% of problems (e.g.
  10303−7338), which the `stops_borrow_at_zero_repaired` variant closes with a
  borrow-off-the-end repair (→ 3875) while leaving 305−9=206 untouched.

**Note — the second impasse.** A robustness sweep (20k correct + 10k/bug random
problems) found that stops-borrow-at-zero alone stalls when a borrow chains
through an already-zeroed column and runs off the high end. That is Repair
Theory's cascade: one mislearned rule breeds a further impasse needing a further
repair. `stops_borrow_at_zero_repaired()` in `rules_buggy.py` supplies that
second repair; it is kept out of the canonical four-bug `BUGS` catalog on
purpose.

## References

Brown & Burton (1978); Brown & VanLehn (1980); VanLehn (1990); Anderson &
Lebiere (1998); Anderson et al. (2004); Ritter, Tehranchi & Oury (2019). Full
IEEE citations are in `../check-in.md`.
