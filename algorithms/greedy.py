from __future__ import annotations

from typing import Optional

from algorithms.base import SchedulerBase


class GreedyScheduler(SchedulerBase):
    """Myopic scheduler selecting the source with the largest current w_i * A_i."""

    def __init__(self) -> None:
        super().__init__(name="greedy")

    def select_action(self, env) -> Optional[int]:
        best_source = max(
            env.sources,
            key=lambda source: (source.weight * source.aoi, source.weight, source.source_id),
        )
        return best_source.source_id
