from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import numpy as np

from algorithms.base import SchedulerBase
from solver.dp_solver import SingleSourceMDPConfig, SingleSourceMDPSolver
from solver.lagrangian import effective_update_success_prob


@dataclass
class WhittleArmInfo:
    source_id: int
    weight: float
    success_prob: float
    a_max: int
    index_table: np.ndarray


class WhittleIndexCalculator:
    """Numerically compute Whittle indices via subsidy bisection.

    For a fixed AoI state a, define the state-action gap under passive subsidy:

        gap(lambda; a) = Q_active(a; lambda) - Q_passive(a; lambda)

    - gap < 0: active is better
    - gap > 0: passive is better
    - gap = 0: active and passive are indifferent

    The Whittle index is the subsidy lambda that makes gap(lambda; a) = 0.
    """

    def __init__(
        self,
        weight: float,
        success_prob: float,
        a_max: int,
        subsidy_lower: float = -100.0,
        subsidy_upper: float = 100.0,
        subsidy_tolerance: float = 1e-5,
        max_binary_iterations: int = 40,
        mdp_tolerance: float = 1e-8,
        mdp_max_iterations: int = 5000,
    ) -> None:
        self.weight = float(weight)
        self.success_prob = float(success_prob)
        self.a_max = int(a_max)
        self.subsidy_lower = float(subsidy_lower)
        self.subsidy_upper = float(subsidy_upper)
        self.subsidy_tolerance = float(subsidy_tolerance)
        self.max_binary_iterations = int(max_binary_iterations)
        self.mdp_tolerance = float(mdp_tolerance)
        self.mdp_max_iterations = int(mdp_max_iterations)
        self._solve_cache: Dict[float, object] = {}

    def _solve_relaxed_problem(self, subsidy: float):
        cache_key = round(float(subsidy), 8)
        if cache_key not in self._solve_cache:
            config = SingleSourceMDPConfig(
                weight=self.weight,
                success_prob=self.success_prob,
                lambda_value=float(subsidy),
                a_max=self.a_max,
                lambda_mode="passive_subsidy",
                tolerance=self.mdp_tolerance,
                max_iterations=self.mdp_max_iterations,
            )
            self._solve_cache[cache_key] = SingleSourceMDPSolver(config).solve()
        return self._solve_cache[cache_key]

    def evaluate_gap(self, state: int, subsidy: float) -> float:
        state = int(min(max(state, 1), self.a_max))
        result = self._solve_relaxed_problem(subsidy)
        state_index = state - 1
        return float(result.q_active[state_index] - result.q_passive[state_index])

    def _find_bracket(self, state: int) -> tuple[float, float]:
        low = self.subsidy_lower
        high = self.subsidy_upper
        gap_low = self.evaluate_gap(state, low)
        gap_high = self.evaluate_gap(state, high)

        expand_count = 0
        while gap_low > 0 and expand_count < 30:
            low *= 2.0
            gap_low = self.evaluate_gap(state, low)
            expand_count += 1

        expand_count = 0
        while gap_high < 0 and expand_count < 30:
            high *= 2.0
            gap_high = self.evaluate_gap(state, high)
            expand_count += 1

        if gap_low > 0 or gap_high < 0:
            raise RuntimeError(
                "failed to bracket the Whittle index. Try enlarging subsidy bounds or A_max."
            )
        return low, high

    def compute_index(self, state: int) -> float:
        """Return the Whittle index for one AoI state."""
        state = int(min(max(state, 1), self.a_max))
        low, high = self._find_bracket(state)

        for _ in range(self.max_binary_iterations):
            mid = 0.5 * (low + high)
            gap_mid = self.evaluate_gap(state, mid)
            if abs(gap_mid) < self.subsidy_tolerance:
                return float(mid)
            if gap_mid < 0:
                low = mid
            else:
                high = mid
        return float(0.5 * (low + high))

    def compute_index_table(self) -> np.ndarray:
        return np.array([self.compute_index(state) for state in range(1, self.a_max + 1)], dtype=float)


class WhittleScheduler(SchedulerBase):
    """Online scheduler selecting the source with the largest Whittle index."""

    def __init__(
        self,
        sources: Iterable,
        channel,
        a_max: int = 25,
        subsidy_lower: float = -100.0,
        subsidy_upper: float = 100.0,
        subsidy_tolerance: float = 1e-5,
        max_binary_iterations: int = 40,
    ) -> None:
        super().__init__(name="whittle")
        self.a_max = a_max
        self.arm_info: Dict[int, WhittleArmInfo] = {}

        for source in sources:
            channel_success_prob = channel.get_success_prob(source.source_id)
            success_prob = effective_update_success_prob(source.sampling_rate, channel_success_prob)
            calculator = WhittleIndexCalculator(
                weight=source.weight,
                success_prob=success_prob,
                a_max=a_max,
                subsidy_lower=subsidy_lower,
                subsidy_upper=subsidy_upper,
                subsidy_tolerance=subsidy_tolerance,
                max_binary_iterations=max_binary_iterations,
            )
            self.arm_info[source.source_id] = WhittleArmInfo(
                source_id=source.source_id,
                weight=source.weight,
                success_prob=success_prob,
                a_max=a_max,
                index_table=calculator.compute_index_table(),
            )

    def get_index(self, source_id: int, aoi: int) -> float:
        arm = self.arm_info[source_id]
        state = min(max(int(aoi), 1), arm.a_max)
        return float(arm.index_table[state - 1])

    def get_indices_from_state_map(self, state_map: Dict[int, int]) -> Dict[int, float]:
        return {source_id: self.get_index(source_id, aoi) for source_id, aoi in state_map.items()}

    def select_action_from_state_map(self, state_map: Dict[int, int]) -> Optional[int]:
        indices = self.get_indices_from_state_map(state_map)
        return max(
            indices,
            key=lambda source_id: (
                indices[source_id],
                self.arm_info[source_id].weight * state_map[source_id],
                -source_id,
            ),
        )

    def select_action(self, env) -> Optional[int]:
        state_map = {source.source_id: source.aoi for source in env.sources}
        return self.select_action_from_state_map(state_map)
