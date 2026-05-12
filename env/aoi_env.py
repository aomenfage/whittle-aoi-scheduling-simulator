from __future__ import annotations

from typing import Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from env.channel import Channel
from env.source import Source

PolicyLike = Union[Callable[["AoIEnv"], Optional[int]], object]


class AoIEnv:
    """Discrete-time AoI simulation environment.

    State transition used in this first-round core:

    For each source ``i`` at slot ``t``:
    - if source ``i`` is scheduled, has a fresh sample, and the channel succeeds,
      then ``A_i(t + 1) = 1``
    - otherwise ``A_i(t + 1) = A_i(t) + 1``

    Instantaneous weighted AoI cost:
    ``C(t) = sum_i w_i * A_i(t)``
    """

    def __init__(self, sources: List[Source], channel: Channel, seed: Optional[int] = None) -> None:
        if not sources:
            raise ValueError("sources must not be empty.")
        self.sources = sources
        self.channel = channel
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.slot = 0
        self.history: List[Dict[str, float]] = []

    def reset(self) -> Dict[str, object]:
        self.slot = 0
        self.history = []
        self.rng = np.random.default_rng(self.seed)
        for source in self.sources:
            source.reset()
        return self.get_observation()

    def get_observation(self) -> Dict[str, object]:
        return {
            "slot": self.slot,
            "aois": {source.source_id: source.aoi for source in self.sources},
        }

    def step(self, action: Optional[int]) -> Dict[str, object]:
        """Advance one slot.

        Args:
            action: scheduled source id. ``None`` means idle.
        """
        valid_source_ids = {source.source_id for source in self.sources}
        if action is not None and action not in valid_source_ids:
            raise ValueError(f"invalid action {action}, expected one of {sorted(valid_source_ids)}.")

        scheduled_sample_ready = False
        scheduled_channel_success = False

        for source in self.sources:
            if source.source_id == action:
                scheduled_sample_ready = source.sample_ready(self.rng)
                scheduled_channel_success = False

                if scheduled_sample_ready:
                    scheduled_channel_success = self.channel.transmit(source.source_id, self.rng)

                if scheduled_sample_ready and scheduled_channel_success:
                    source.apply_success()
                else:
                    source.apply_failure_or_idle(counted_attempt=True)
            else:
                source.apply_failure_or_idle(counted_attempt=False)

        self.slot += 1
        weighted_aoi = self.compute_weighted_aoi()

        record: Dict[str, float] = {
            "slot": self.slot,
            "action": -1 if action is None else action,
            "sample_ready": int(scheduled_sample_ready),
            "channel_success": int(scheduled_channel_success),
            "weighted_aoi": weighted_aoi,
        }
        for source in self.sources:
            record[f"aoi_{source.source_id}"] = source.aoi

        self.history.append(record)
        return {
            "slot": self.slot,
            "action": action,
            "weighted_aoi": weighted_aoi,
            "done": False,
            "info": record,
        }

    def _resolve_action(self, policy: PolicyLike) -> Optional[int]:
        if hasattr(policy, "select_action"):
            return policy.select_action(self)
        if callable(policy):
            return policy(self)
        raise TypeError("policy must be a callable or a scheduler with select_action(env).")

    def run(self, policy: PolicyLike, horizon: int) -> pd.DataFrame:
        if horizon <= 0:
            raise ValueError("horizon must be positive.")

        self.reset()
        if hasattr(policy, "reset"):
            policy.reset()
        for _ in range(horizon):
            action = self._resolve_action(policy)
            self.step(action)
        return self.get_history_df()

    def compute_weighted_aoi(self) -> float:
        return float(sum(source.weight * source.aoi for source in self.sources))

    def get_history_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.history)

    def summary(self) -> Dict[str, object]:
        if not self.history:
            raise RuntimeError("no simulation history found, call run() first.")

        history_df = self.get_history_df()
        final_aois = {source.source_id: source.aoi for source in self.sources}
        average_aoi = {
            source.source_id: float(history_df[f"aoi_{source.source_id}"].mean())
            for source in self.sources
        }

        return {
            "slots": self.slot,
            "final_aois": final_aois,
            "average_aoi": average_aoi,
            "average_weighted_aoi": float(history_df["weighted_aoi"].mean()),
            "history": history_df,
        }
