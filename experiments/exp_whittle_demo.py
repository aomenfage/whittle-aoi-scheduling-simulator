from __future__ import annotations

import itertools
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.greedy import GreedyScheduler
from algorithms.whittle import WhittleScheduler
from main import build_demo_env
from solver.lagrangian import effective_update_success_prob


def evaluate_decisions(max_test_aoi: int = 10) -> tuple[dict, pd.DataFrame, int, int]:
    env = build_demo_env(seed=2026)
    greedy = GreedyScheduler()
    whittle = WhittleScheduler(sources=env.sources, channel=env.channel, a_max=25)

    source_ids = [source.source_id for source in env.sources]
    chosen_state_map = None
    greedy_action = None
    whittle_action = None

    for aois in itertools.product(range(1, max_test_aoi + 1), repeat=len(source_ids)):
        state_map = {source_id: aoi for source_id, aoi in zip(source_ids, aois)}
        for source in env.sources:
            source.aoi = state_map[source.source_id]

        greedy_action = greedy.select_action(env)
        whittle_action = whittle.select_action_from_state_map(state_map)
        if greedy_action != whittle_action:
            chosen_state_map = state_map
            break

    if chosen_state_map is None:
        chosen_state_map = {source_id: max_test_aoi for source_id in source_ids}
        for source in env.sources:
            source.aoi = chosen_state_map[source.source_id]
        greedy_action = greedy.select_action(env)
        whittle_action = whittle.select_action_from_state_map(chosen_state_map)

    rows = []
    for source in env.sources:
        channel_prob = env.channel.get_success_prob(source.source_id)
        effective_prob = effective_update_success_prob(source.sampling_rate, channel_prob)
        aoi = chosen_state_map[source.source_id]
        rows.append(
            {
                "source_id": source.source_id,
                "aoi": aoi,
                "weight": source.weight,
                "sampling_rate": source.sampling_rate,
                "channel_success_prob": channel_prob,
                "effective_success_prob": effective_prob,
                "greedy_score": source.weight * aoi,
                "whittle_index": whittle.get_index(source.source_id, aoi),
            }
        )

    detail_df = pd.DataFrame(rows).sort_values(by="source_id")
    return chosen_state_map, detail_df, int(greedy_action), int(whittle_action)


def main() -> None:
    state_map, detail_df, greedy_action, whittle_action = evaluate_decisions(max_test_aoi=10)

    print("=" * 72)
    print("Whittle vs Greedy Decision Demo")
    print("=" * 72)
    print(f"Test state map : {state_map}")
    print(f"Greedy action  : source {greedy_action}")
    print(f"Whittle action : source {whittle_action}")
    print("-" * 72)
    print(detail_df.to_string(index=False))


if __name__ == "__main__":
    main()
