from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

import numpy as np
import pandas as pd

ActionName = Literal["passive", "active"]
LambdaMode = Literal["passive_subsidy", "active_cost"]


@dataclass
class SingleSourceMDPConfig:
    """Configuration of the single-source average-cost MDP.

    State:
        AoI a in {1, 2, ..., A_max}

    Action:
        passive: do not schedule update
        active : schedule update

    Transition:
        passive:
            A' = min(a + 1, A_max)
        active:
            with probability p, A' = 1
            with probability 1 - p, A' = min(a + 1, A_max)

    Stage cost:
        base AoI cost is w * a
        if lambda_mode == "passive_subsidy":
            passive cost = w * a - lambda_value
            active cost  = w * a
        if lambda_mode == "active_cost":
            passive cost = w * a
            active cost  = w * a + lambda_value
    """

    weight: float
    success_prob: float
    lambda_value: float
    a_max: int
    lambda_mode: LambdaMode = "passive_subsidy"
    tolerance: float = 1e-10
    max_iterations: int = 10000
    reference_state: int = 1

    def validate(self) -> None:
        if self.weight <= 0:
            raise ValueError("weight must be positive.")
        if not 0.0 <= self.success_prob <= 1.0:
            raise ValueError("success_prob must be in [0, 1].")
        if self.a_max < 2:
            raise ValueError("a_max must be at least 2.")
        if not 1 <= self.reference_state <= self.a_max:
            raise ValueError("reference_state must be within [1, a_max].")
        if self.tolerance <= 0:
            raise ValueError("tolerance must be positive.")
        if self.max_iterations <= 0:
            raise ValueError("max_iterations must be positive.")


@dataclass
class SingleSourceMDPResult:
    config: SingleSourceMDPConfig
    states: np.ndarray
    value_function: np.ndarray
    actions: np.ndarray
    q_passive: np.ndarray
    q_active: np.ndarray
    average_cost: float
    iterations: int
    converged: bool

    def to_action_table(self) -> pd.DataFrame:
        action_labels = np.where(self.actions == 1, "active", "passive")
        return pd.DataFrame(
            {
                "state": self.states,
                "optimal_action": action_labels,
                "value_function": self.value_function,
                "q_passive": self.q_passive,
                "q_active": self.q_active,
            }
        )

    def to_summary_dict(self) -> Dict[str, float]:
        return {
            "weight": self.config.weight,
            "success_prob": self.config.success_prob,
            "lambda_value": self.config.lambda_value,
            "a_max": self.config.a_max,
            "average_cost": self.average_cost,
            "iterations": self.iterations,
            "converged": int(self.converged),
        }


class SingleSourceMDPSolver:
    """Solve the single-source average-cost MDP by relative value iteration."""

    def __init__(self, config: SingleSourceMDPConfig) -> None:
        config.validate()
        self.config = config
        self.states = np.arange(1, config.a_max + 1, dtype=int)

    def _next_aoi(self, aoi: int) -> int:
        return min(aoi + 1, self.config.a_max)

    def _passive_cost(self, aoi: int) -> float:
        base_cost = self.config.weight * aoi
        if self.config.lambda_mode == "passive_subsidy":
            return base_cost - self.config.lambda_value
        return base_cost

    def _active_cost(self, aoi: int) -> float:
        base_cost = self.config.weight * aoi
        if self.config.lambda_mode == "active_cost":
            return base_cost + self.config.lambda_value
        return base_cost

    def _compute_q_values(self, bias: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        q_passive = np.zeros(self.config.a_max, dtype=float)
        q_active = np.zeros(self.config.a_max, dtype=float)

        success_index = 0
        p = self.config.success_prob

        for idx, aoi in enumerate(self.states):
            next_index = self._next_aoi(aoi) - 1

            # Bellman branch for passive:
            # Q(a, passive) = c_passive(a) + h(min(a + 1, A_max))
            q_passive[idx] = self._passive_cost(aoi) + bias[next_index]

            # Bellman branch for active:
            # Q(a, active) = c_active(a) + p * h(1) + (1-p) * h(min(a + 1, A_max))
            q_active[idx] = (
                self._active_cost(aoi)
                + p * bias[success_index]
                + (1.0 - p) * bias[next_index]
            )

        return q_passive, q_active

    def solve(self) -> SingleSourceMDPResult:
        bias = np.zeros(self.config.a_max, dtype=float)
        q_passive = np.zeros_like(bias)
        q_active = np.zeros_like(bias)
        actions = np.zeros(self.config.a_max, dtype=int)
        reference_index = self.config.reference_state - 1
        converged = False
        average_cost = 0.0

        for iteration in range(1, self.config.max_iterations + 1):
            q_passive, q_active = self._compute_q_values(bias)
            value_candidate = np.minimum(q_passive, q_active)
            actions = (q_active < q_passive).astype(int)

            average_cost = float(value_candidate[reference_index])
            normalized_value = value_candidate - value_candidate[reference_index]

            delta = float(np.max(np.abs(normalized_value - bias)))
            bias = normalized_value

            if delta < self.config.tolerance:
                converged = True
                break

        return SingleSourceMDPResult(
            config=self.config,
            states=self.states.copy(),
            value_function=bias.copy(),
            actions=actions.copy(),
            q_passive=q_passive.copy(),
            q_active=q_active.copy(),
            average_cost=average_cost,
            iterations=iteration,
            converged=converged,
        )
