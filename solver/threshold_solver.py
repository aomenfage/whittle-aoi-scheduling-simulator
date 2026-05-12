from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from solver.dp_solver import SingleSourceMDPResult


@dataclass
class ThresholdAnalysisResult:
    has_threshold_structure: bool
    threshold_state: Optional[int]
    passive_prefix_length: int
    action_switch_count: int

    def to_dict(self) -> dict:
        return {
            "has_threshold_structure": self.has_threshold_structure,
            "threshold_state": self.threshold_state,
            "passive_prefix_length": self.passive_prefix_length,
            "action_switch_count": self.action_switch_count,
        }


def analyze_threshold_structure(actions: np.ndarray, states: np.ndarray) -> ThresholdAnalysisResult:
    """Check whether the optimal action is threshold-type.

    Convention:
    - 0 means passive
    - 1 means active
    Threshold structure means there exists theta such that
    passive for a < theta and active for a >= theta.
    """

    if len(actions) != len(states):
        raise ValueError("actions and states must have the same length.")

    switch_count = int(np.sum(actions[1:] != actions[:-1]))
    is_monotone_binary = bool(np.all(actions[1:] >= actions[:-1]))

    if np.all(actions == 0):
        return ThresholdAnalysisResult(
            has_threshold_structure=True,
            threshold_state=None,
            passive_prefix_length=len(actions),
            action_switch_count=switch_count,
        )

    first_active_index = int(np.argmax(actions == 1))
    threshold_state = int(states[first_active_index])

    has_threshold = is_monotone_binary and bool(np.all(actions[first_active_index:] == 1))
    return ThresholdAnalysisResult(
        has_threshold_structure=has_threshold,
        threshold_state=threshold_state if has_threshold else None,
        passive_prefix_length=first_active_index,
        action_switch_count=switch_count,
    )


def build_threshold_report(result: SingleSourceMDPResult) -> pd.DataFrame:
    analysis = analyze_threshold_structure(result.actions, result.states)
    report = result.to_action_table().copy()
    report["is_threshold_policy"] = int(analysis.has_threshold_structure)
    report["threshold_state"] = analysis.threshold_state
    return report
