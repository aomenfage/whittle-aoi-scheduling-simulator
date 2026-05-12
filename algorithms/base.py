from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class SchedulerBase(ABC):
    """Unified scheduler interface for all baseline and future policies."""

    def __init__(self, name: str) -> None:
        self.name = name

    def reset(self) -> None:
        """Reset internal state before a new simulation run."""

    @abstractmethod
    def select_action(self, env) -> Optional[int]:
        """Return the source id to schedule in the current slot."""
