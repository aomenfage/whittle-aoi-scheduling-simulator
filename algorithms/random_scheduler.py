from __future__ import annotations

from typing import List, Optional

from algorithms.base import SchedulerBase


class RandomScheduler(SchedulerBase):
    """Random scheduler selecting one source uniformly each slot."""

    def __init__(self, source_ids: List[int]) -> None:
        super().__init__(name="random")
        if not source_ids:
            raise ValueError("source_ids must not be empty.")
        self.source_ids = list(source_ids)

    def select_action(self, env) -> Optional[int]:
        index = int(env.rng.integers(low=0, high=len(self.source_ids)))
        return self.source_ids[index]
