from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Source:
    """Single monitoring source in the slotted AoI system.

    The source keeps only the minimum state needed by the first-round
    simulation core:
    - ``aoi``: current Age of Information at the edge node
    - ``weight``: coefficient used in weighted AoI cost
    - ``sampling_rate``: Bernoulli probability that a fresh sample can be
      generated when this source is scheduled in the current slot
    """

    source_id: int
    weight: float
    sampling_rate: float
    initial_aoi: int = 1
    aoi: int = field(init=False)
    successful_updates: int = field(default=0, init=False)
    attempted_updates: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("weight must be positive.")
        if not 0.0 <= self.sampling_rate <= 1.0:
            raise ValueError("sampling_rate must be in [0, 1].")
        if self.initial_aoi < 1:
            raise ValueError("initial_aoi must be at least 1.")
        self.aoi = self.initial_aoi

    def reset(self) -> None:
        """Reset the source state before a new simulation run."""
        self.aoi = self.initial_aoi
        self.successful_updates = 0
        self.attempted_updates = 0

    def sample_ready(self, rng) -> bool:
        """Return whether a fresh sample is available in this slot."""
        return float(rng.random()) < self.sampling_rate

    def apply_success(self) -> None:
        """AoI reset after a successful fresh update delivery."""
        self.attempted_updates += 1
        self.successful_updates += 1
        self.aoi = 1

    def apply_failure_or_idle(self, counted_attempt: bool) -> None:
        """AoI grows by one slot when no successful update is delivered."""
        if counted_attempt:
            self.attempted_updates += 1
        self.aoi += 1
