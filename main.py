from __future__ import annotations

import argparse

import pandas as pd

from algorithms.greedy import GreedyScheduler
from algorithms.periodic import PeriodicScheduler
from algorithms.random_scheduler import RandomScheduler
from algorithms.round_robin import RoundRobinScheduler
from algorithms.whittle import WhittleScheduler
from env.aoi_env import AoIEnv
from env.channel import Channel
from env.source import Source
from utils.metrics import compute_run_metrics


def build_demo_env(seed: int = 2026) -> AoIEnv:
    """Build a minimal runnable AoI simulation scenario."""
    sources = [
        Source(source_id=0, weight=1.0, sampling_rate=0.95, initial_aoi=1),
        Source(source_id=1, weight=2.0, sampling_rate=0.85, initial_aoi=1),
        Source(source_id=2, weight=3.0, sampling_rate=0.75, initial_aoi=1),
    ]

    channel = Channel(
        success_prob={
            0: 0.90,
            1: 0.80,
            2: 0.70,
        }
    )
    return AoIEnv(sources=sources, channel=channel, seed=seed)


def build_scheduler(strategy_name: str, env: AoIEnv):
    source_ids = [source.source_id for source in env.sources]
    if strategy_name == "round_robin":
        return RoundRobinScheduler(source_ids=source_ids)
    if strategy_name == "periodic":
        return PeriodicScheduler(pattern=[0, 1, 2, 1])
    if strategy_name == "greedy":
        return GreedyScheduler()
    if strategy_name == "random":
        return RandomScheduler(source_ids=source_ids)
    if strategy_name == "whittle":
        return WhittleScheduler(sources=env.sources, channel=env.channel, a_max=25)
    raise ValueError(f"unsupported strategy: {strategy_name}")


def run_single_strategy(strategy_name: str, horizon: int, seed: int) -> tuple[AoIEnv, object, pd.DataFrame, dict]:
    env = build_demo_env(seed=seed)
    scheduler = build_scheduler(strategy_name=strategy_name, env=env)
    history_df = env.run(policy=scheduler, horizon=horizon)
    summary = compute_run_metrics(
        history_df=history_df,
        sources=env.sources,
        strategy_name=strategy_name,
        high_weight_threshold=2.0,
    )
    return env, scheduler, history_df, summary


def print_single_strategy_result(
    strategy_name: str,
    env: AoIEnv,
    history_df: pd.DataFrame,
    summary: dict,
) -> None:
    print("=" * 60)
    print(f"High-Speed Railway MEC Weighted AoI Simulation: {strategy_name}")
    print("=" * 60)
    print(f"Simulated slots: {summary['slots']}")
    print(f"Recorded rows  : {len(history_df)}")
    print("-" * 60)
    print("Average / Peak AoI for each source:")
    for source in env.sources:
        print(
            "  Source {sid}: avg_aoi={avg_aoi:.3f}, peak_aoi={peak_aoi:.1f}, "
            "weight={weight:.2f}, sampling_rate={sampling_rate:.2f}, "
            "success_prob={success_prob:.2f}".format(
                sid=source.source_id,
                avg_aoi=summary[f"avg_aoi_{source.source_id}"],
                peak_aoi=summary[f"peak_aoi_{source.source_id}"],
                weight=source.weight,
                sampling_rate=source.sampling_rate,
                success_prob=env.channel.get_success_prob(source.source_id),
            )
        )
    print("-" * 60)
    print(f"System average weighted AoI: {summary['average_weighted_aoi']:.3f}")
    print(f"System peak weighted AoI   : {summary['peak_weighted_aoi']:.3f}")
    print(f"System peak AoI            : {summary['system_peak_aoi']:.3f}")
    print(f"High-weight average AoI    : {summary['high_weight_avg_aoi']:.3f}")
    print("-" * 60)
    print("Last 5 slots of history:")
    print(history_df.tail(5).to_string(index=False))


def compare_all_strategies(horizon: int, seed: int) -> pd.DataFrame:
    strategy_names = ["round_robin", "periodic", "greedy", "random", "whittle"]
    rows = []
    for strategy_name in strategy_names:
        env, _, _, summary = run_single_strategy(strategy_name=strategy_name, horizon=horizon, seed=seed)
        rows.append(
            {
                "strategy": strategy_name,
                "average_weighted_aoi": summary["average_weighted_aoi"],
                "peak_weighted_aoi": summary["peak_weighted_aoi"],
                "high_weight_avg_aoi": summary["high_weight_avg_aoi"],
                "avg_aoi_0": summary["avg_aoi_0"],
                "avg_aoi_1": summary["avg_aoi_1"],
                "avg_aoi_2": summary["avg_aoi_2"],
            }
        )
    result_df = pd.DataFrame(rows).sort_values(by="average_weighted_aoi", ascending=True)
    return result_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weighted AoI baseline scheduler comparison.")
    parser.add_argument(
        "--strategy",
        type=str,
        default="all",
        choices=["all", "round_robin", "periodic", "greedy", "random", "whittle"],
        help="Scheduling strategy to run.",
    )
    parser.add_argument("--horizon", type=int, default=1000, help="Number of time slots.")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed for reproducibility.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.strategy == "all":
        result_df = compare_all_strategies(horizon=args.horizon, seed=args.seed)
        print("=" * 60)
        print("High-Speed Railway MEC Weighted AoI Baseline Comparison")
        print("=" * 60)
        print(result_df.to_string(index=False))
        return

    env, _, history_df, summary = run_single_strategy(
        strategy_name=args.strategy,
        horizon=args.horizon,
        seed=args.seed,
    )

    print_single_strategy_result(
        strategy_name=args.strategy,
        env=env,
        history_df=history_df,
        summary=summary,
    )


if __name__ == "__main__":
    main()
