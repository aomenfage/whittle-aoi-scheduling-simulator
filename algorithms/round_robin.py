from __future__ import annotations

from typing import List, Optional

from algorithms.base import SchedulerBase


class RoundRobinScheduler(SchedulerBase):
    """Round-robin scheduler that selects sources in a fixed cyclic order."""

    def __init__(self, source_ids: List[int]) -> None:
        super().__init__(name="round_robin")
        if not source_ids:
            raise ValueError("source_ids must not be empty.")
        self.source_ids = list(source_ids)
        self.pointer = 0

    def reset(self) -> None:
        self.pointer = 0

    def select_action(self, env=None) -> Optional[int]:
        action = self.source_ids[self.pointer]
        self.pointer = (self.pointer + 1) % len(self.source_ids)
        return action
