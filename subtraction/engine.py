"""The recognize-act cycle: a minimal ACT-R-style production-system engine.

Each cycle does exactly four things [Anderson et al., 2004; Ritter et al.,
2019]:

    match all -> conflict-resolve by specificity -> fire one -> log

and repeats until the goal state is reached or an impasse is detected. An
impasse is when no ordinary production matches and the goal is not yet met
[VanLehn, 1990]. At an impasse the engine looks for a *repair* production; if
one applies it fires (Repair Theory [Brown & VanLehn, 1980]), otherwise the run
halts with an ImpasseError. That halt is the point: naively deleting a rule does
not yield a human-like wrong answer, it stalls the procedure -- a human-like
error requires a principled, rule-shaped repair.
"""

from __future__ import annotations

from typing import Optional

from .production import Production
from .state import State
from .trace import Tracer


class ImpasseError(RuntimeError):
    """Raised when the procedure stalls with no rule and no repair to apply."""

    def __init__(self, state: State, cycle: int):
        self.state = state
        self.cycle = cycle
        super().__init__(
            f"impasse at cycle {cycle}: focus column {state.focus}, "
            f"no production matches and goal not reached"
        )


class Engine:
    def __init__(
        self,
        rules: list[Production],
        repairs: Optional[list[Production]] = None,
        max_cycles: int = 1000,
    ):
        self.rules = list(rules)
        self.repairs = list(repairs or [])
        self.max_cycles = max_cycles

    # --- conflict resolution -------------------------------------------------

    @staticmethod
    def _resolve(matched: list[Production]) -> Production:
        """Pick one rule from those that matched, most specific first.

        Specificity-based selection mirrors ACT-R conflict resolution: a more
        specific production (more conditions satisfied) wins over a general one.
        This is where bugs live -- a *missing specific* rule lets a more
        *general*, wrong rule win the cycle. Ties keep registration order so
        runs are deterministic.
        """
        best = max(r.specificity for r in matched)
        for r in matched:  # registration order among the top-specificity rules
            if r.specificity == best:
                return r
        raise AssertionError("unreachable")

    # --- the cycle -----------------------------------------------------------

    def run(self, state: State, tracer: Optional[Tracer] = None) -> Tracer:
        tracer = tracer or Tracer()
        cycle = 0
        while not state.is_goal():
            cycle += 1
            if cycle > self.max_cycles:
                raise RuntimeError(
                    f"non-termination: exceeded {self.max_cycles} cycles"
                )

            matched = [r for r in self.rules if r.matches(state)]
            if matched:
                rule = self._resolve(matched)
                rule.fire(state)
                tracer.record(cycle, rule.name, state.snapshot())
                continue

            # No ordinary rule fits -> impasse. Try a repair.
            repair = self._find_repair(state)
            if repair is None:
                state.impasse = True
                tracer.record(
                    cycle, "(impasse)", state.snapshot(), note="no repair"
                )
                raise ImpasseError(state, cycle)
            repair.fire(state)
            tracer.record(
                cycle, repair.name, state.snapshot(), repaired=True,
                note="repair",
            )
        return tracer

    def _find_repair(self, state: State) -> Optional[Production]:
        for r in self.repairs:
            if r.matches(state):
                return r
        return None
