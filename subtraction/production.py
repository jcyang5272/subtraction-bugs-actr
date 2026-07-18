"""Production-rule abstraction.

A production is a single IF -> THEN rule: a `condition` predicate over the
current working-memory state and an `action` that mutates that state. This is
the procedural-knowledge unit of an ACT-R-style architecture [Anderson &
Lebiere, 1998]: knowing *how* is stored as separate condition->action pairs,
kept apart from the declarative chunks they read and write (see state.py).

`specificity` drives conflict resolution: when several productions match in one
recognize-act cycle, the engine fires the most specific one (mirroring ACT-R's
preference for more specific productions). `is_repair` flags a production that
should fire only at an impasse -- the mechanism behind Repair Theory [Brown &
VanLehn, 1980].
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .state import State


@dataclass(frozen=True)
class Production:
    name: str
    condition: Callable[["State"], bool]
    action: Callable[["State"], None]
    specificity: int = 1
    is_repair: bool = False
    description: str = ""

    def matches(self, state: "State") -> bool:
        """True iff this rule's IF-part is satisfied by the current state."""
        return self.condition(state)

    def fire(self, state: "State") -> None:
        """Apply this rule's THEN-part, mutating working memory in place."""
        self.action(state)
