"""Structured tracing of the recognize-act cycle.

The whole point of the tool is transparency: every cognitive step must be
inspectable. Rather than loose print output, each cycle is recorded as a
structured snapshot (which rule fired, whether it was a repair, and the full
state afterward). That lets us point at the exact column and cycle where a
procedure breaks -- the diagnostic payoff described in the check-in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TraceEntry:
    cycle: int
    rule: str
    repaired: bool
    snapshot: dict
    note: str = ""


@dataclass
class Tracer:
    entries: list[TraceEntry] = field(default_factory=list)

    def record(
        self,
        cycle: int,
        rule_name: str,
        snapshot: dict,
        repaired: bool = False,
        note: str = "",
    ) -> None:
        self.entries.append(
            TraceEntry(cycle, rule_name, repaired, snapshot, note)
        )

    def fired_rules(self) -> list[str]:
        return [e.rule for e in self.entries]

    def render(self) -> str:
        """Human-readable trace: one line per cycle, plus the answer so far."""
        lines = []
        header = f"{'cyc':>3}  {'rule':<22} {'foc':>3} {'borrow':>6}  answer"
        lines.append(header)
        lines.append("-" * len(header))
        for e in self.entries:
            tag = "*" if e.repaired else " "
            nd = e.snapshot.get("need_decrement")
            nd_s = "-" if nd is None else str(nd)
            lines.append(
                f"{e.cycle:>3}{tag} {e.rule:<22} "
                f"{e.snapshot['focus']:>3} {nd_s:>6}  "
                f"{e.snapshot['answer_str']}"
                + (f"   <- {e.note}" if e.note else "")
            )
        return "\n".join(lines)
