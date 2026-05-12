from __future__ import annotations

from typing import List, Optional

from algorithms.base import SchedulerBase


class PeriodicScheduler(SchedulerBase):
    """Periodic scheduler based on a predefined repeating pattern."""

    def __init__(self, pattern: List[int]) -> None:
        super().__init__(name="periodic")
        if not pattern:
            raise ValueError("pattern must not be empty.")
        self.pattern = list(pattern)
        self.pointer = 0

    def reset(self) -> None:
        self.pointer = 0

    def select_action(self, env=None) -> Optional[int]:
        action = self.pattern[self.pointer]
        self.pointer = (self.pointer + 1) % len(self.pattern)
        return action
