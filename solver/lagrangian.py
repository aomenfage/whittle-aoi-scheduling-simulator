from __future__ import annotations

from dataclasses import dataclass


def effective_update_success_prob(sampling_rate: float, channel_success_prob: float) -> float:
    """Return the effective success probability of one scheduled update.

    In the current environment, a successful reset needs:
    1. a fresh sample is generated
    2. the channel transmission succeeds
    """
    if not 0.0 <= sampling_rate <= 1.0:
        raise ValueError("sampling_rate must be in [0, 1].")
    if not 0.0 <= channel_success_prob <= 1.0:
        raise ValueError("channel_success_prob must be in [0, 1].")
    return float(sampling_rate * channel_success_prob)


@dataclass
class RelaxedArmDescription:
    """Single-arm problem obtained by Lagrangian relaxation.

    Original coupled constraint:
        sum_i u_i(t) <= 1

    After relaxation, each arm is solved independently with passive subsidy
    lambda. For one arm with state a and action u in {0, 1}:

        u = 0 -> passive
        u = 1 -> active

    Stage cost under passive subsidy:
        c_lambda(a, passive) = w * a - lambda
        c_lambda(a, active)  = w * a

    The Whittle index at state a is the subsidy value lambda that makes
    passive and active equally desirable.
    """

    weight: float
    success_prob: float

    def passive_cost(self, aoi: int, subsidy: float) -> float:
        return self.weight * aoi - subsidy

    def active_cost(self, aoi: int) -> float:
        return self.weight * aoi
