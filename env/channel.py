from __future__ import annotations

from typing import Dict, Union


class Channel:
    """Single-hop channel with configurable transmission success probability."""

    def __init__(self, success_prob: Union[float, Dict[int, float]]) -> None:
        self.success_prob = success_prob
        self._validate()

    def _validate(self) -> None:
        if isinstance(self.success_prob, dict):
            for source_id, prob in self.success_prob.items():
                if not 0.0 <= prob <= 1.0:
                    raise ValueError(
                        f"success probability for source {source_id} must be in [0, 1]."
                    )
        else:
            if not 0.0 <= float(self.success_prob) <= 1.0:
                raise ValueError("success probability must be in [0, 1].")

    def get_success_prob(self, source_id: int) -> float:
        if isinstance(self.success_prob, dict):
            return float(self.success_prob.get(source_id, 1.0))
        return float(self.success_prob)

    def transmit(self, source_id: int, rng) -> bool:
        """Return whether the scheduled transmission succeeds."""
        prob = self.get_success_prob(source_id)
        return float(rng.random()) < prob
