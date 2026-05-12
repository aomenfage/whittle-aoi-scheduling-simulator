from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.greedy import GreedyScheduler
from algorithms.periodic import PeriodicScheduler
from algorithms.random_scheduler import RandomScheduler
from algorithms.round_robin import RoundRobinScheduler
from algorithms.whittle import WhittleScheduler
from env.aoi_env import AoIEnv
from env.channel import Channel
from env.source import Source
from utils.metrics import aggregate_run_metrics, compute_run_metrics, save_history_csv, save_summary_csv
from utils.plotter import plot_average_aoi_by_source, plot_grouped_metric_with_errorbars


@dataclass
class ScenarioConfig:
    name: str
    n: int
    weights: List[float]
    sampling_rates: Optional[List[float]]
    channel_success_probs: List[float]

    def validate(self) -> None:
        if self.n <= 0:
            raise ValueError("N must be positive.")
        if len(self.weights) != self.n or len(self.channel_success_probs) != self.n:
            raise ValueError("weights and channel_success_probs must have length N.")
        if self.sampling_rates is None:
            self.sampling_rates = [1.0] * self.n
        if len(self.sampling_rates) != self.n:
            raise ValueError("sampling_rates must have length N.")


def _format_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remain = seconds - 60 * minutes
    return f"{minutes}m {remain:.1f}s"


def _print_standard_progress(
    current_job: int,
    total_jobs: int,
    scenario_name: str,
    run_id: int,
    num_runs: int,
    strategy_name: str,
    start_time: float,
) -> None:
    elapsed = time.perf_counter() - start_time
    percentage = 100.0 * current_job / max(total_jobs, 1)
    print(
        "[standard] {cur}/{tot} ({pct:.1f}%) | scenario={scenario} | run={run}/{runs} | "
        "strategy={strategy} | elapsed={elapsed}".format(
            cur=current_job,
            tot=total_jobs,
            pct=percentage,
            scenario=scenario_name,
            run=run_id + 1,
            runs=num_runs,
            strategy=strategy_name,
            elapsed=_format_seconds(elapsed),
        ),
        flush=True,
    )


def build_env_from_scenario(scenario: ScenarioConfig, seed: int) -> AoIEnv:
    sources = [
        Source(
            source_id=i,
            weight=float(scenario.weights[i]),
            sampling_rate=float(scenario.sampling_rates[i]),
            initial_aoi=1,
        )
        for i in range(scenario.n)
    ]
    channel = Channel(success_prob={i: float(scenario.channel_success_probs[i]) for i in range(scenario.n)})
    return AoIEnv(sources=sources, channel=channel, seed=seed)


def build_scheduler(strategy_name: str, env: AoIEnv):
    source_ids = [source.source_id for source in env.sources]
    if strategy_name == "whittle":
        return WhittleScheduler(sources=env.sources, channel=env.channel, a_max=20)
    if strategy_name == "round_robin":
        return RoundRobinScheduler(source_ids=source_ids)
    if strategy_name == "periodic":
        min_weight = min(source.weight for source in env.sources)
        pattern = []
        for source in env.sources:
            repeat_count = max(1, int(round(source.weight / min_weight)))
            pattern.extend([source.source_id] * repeat_count)
        return PeriodicScheduler(pattern=pattern)
    if strategy_name == "greedy":
        return GreedyScheduler()
    if strategy_name == "random":
        return RandomScheduler(source_ids=source_ids)
    raise ValueError(f"unsupported strategy: {strategy_name}")


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_one(strategy_name: str, scenario: ScenarioConfig, run_seed: int, horizon: int, high_weight_threshold: float):
    env = build_env_from_scenario(scenario=scenario, seed=run_seed)
    scheduler = build_scheduler(strategy_name=strategy_name, env=env)
    history_df = env.run(policy=scheduler, horizon=horizon)
    metrics = compute_run_metrics(
        history_df=history_df,
        sources=env.sources,
        strategy_name=strategy_name,
        high_weight_threshold=high_weight_threshold,
    )
    return history_df, metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paper-style AoI comparison experiment runner.")
    parser.add_argument(
        "--suite",
        type=str,
        default="standard",
        choices=["standard", "extended"],
        help="Run the standard comparison suite or the extended sensitivity suite.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(PROJECT_ROOT / "config" / "runner_default.json"),
        help="Path to experiment config JSON.",
    )
    parser.add_argument(
        "--save-trajectories",
        action="store_true",
        help="Save per-slot AoI trajectories for each run (may be large).",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default=str(PROJECT_ROOT / "results" / "extended_suite"),
        help="Root directory for the extended sensitivity suite outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.suite == "extended":
        from experiments.exp_channel_sensitivity import run_default_experiment as run_channel_experiment
        from experiments.exp_peak_aoi import run_default_experiment as run_peak_experiment
        from experiments.exp_scalability import run_default_experiment as run_scalability_experiment
        from experiments.exp_weight_sensitivity import run_default_experiment as run_weight_experiment

        output_root = Path(args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        print("[runner] extended suite start", flush=True)
        print(f"[runner] output_root={output_root}", flush=True)

        print("[runner] running scalability experiment", flush=True)
        run_scalability_experiment(output_root / "exp_scalability", horizon=2000, num_runs=5, seed=2026)
        print("[runner] running weight sensitivity experiment", flush=True)
        run_weight_experiment(output_root / "exp_weight_sensitivity", horizon=3000, num_runs=10, seed=2026)
        print("[runner] running channel sensitivity experiment", flush=True)
        run_channel_experiment(output_root / "exp_channel_sensitivity", horizon=3000, num_runs=10, seed=2026)
        print("[runner] running peak AoI experiment", flush=True)
        run_peak_experiment(output_root / "exp_peak_aoi", horizon=5000, num_runs=10, seed=2026)

        print("=" * 72)
        print("Extended Sensitivity Suite Finished")
        print("=" * 72)
        print(f"Output root: {output_root}")
        print(f"- scalability        : {output_root / 'exp_scalability'}")
        print(f"- weight sensitivity : {output_root / 'exp_weight_sensitivity'}")
        print(f"- channel sensitivity: {output_root / 'exp_channel_sensitivity'}")
        print(f"- peak AoI           : {output_root / 'exp_peak_aoi'}")
        return

    config_path = Path(args.config)
    config = load_config(config_path)
    print("[runner] standard suite start", flush=True)
    print(f"[runner] config={config_path}", flush=True)

    output_dir = PROJECT_ROOT / str(config.get("output_dir", "results/runner"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "trajectories").mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(parents=True, exist_ok=True)

    num_runs = int(config.get("num_runs", 5))
    horizon = int(config.get("T", 1000))
    base_seed = int(config.get("seed", 2026))
    strategies = list(config.get("strategies", ["whittle", "round_robin", "periodic", "greedy", "random"]))
    scenarios_raw = list(config.get("scenarios", []))
    high_weight_threshold = float(config.get("high_weight_threshold", 2.0))

    scenario_configs = []
    for item in scenarios_raw:
        scenario = ScenarioConfig(
            name=str(item["name"]),
            n=int(item["N"]),
            weights=list(item["weights"]),
            sampling_rates=list(item["sampling_rates"]) if "sampling_rates" in item else None,
            channel_success_probs=list(item["channel_success_probs"]),
        )
        scenario.validate()
        scenario_configs.append(scenario)

    run_rows: List[Dict[str, float]] = []

    scenario_meta_rows = []
    total_jobs = len(scenario_configs) * num_runs * len(strategies)
    completed_jobs = 0
    standard_start_time = time.perf_counter()
    print(
        f"[standard] total_jobs={total_jobs} | scenarios={len(scenario_configs)} | "
        f"runs={num_runs} | strategies={len(strategies)} | output={output_dir}",
        flush=True,
    )

    for scenario_index, scenario in enumerate(scenario_configs):
        scenario_meta_rows.append(
            {
                "scenario_name": scenario.name,
                "N": scenario.n,
                "T": horizon,
                "num_runs": num_runs,
                "weights": json.dumps(scenario.weights),
                "sampling_rates": json.dumps(scenario.sampling_rates),
                "channel_success_probs": json.dumps(scenario.channel_success_probs),
            }
        )
        for run_id in range(num_runs):
            run_seed = int(base_seed + 1000 * run_id + 100 * scenario_index)
            for strategy_name in strategies:
                completed_jobs += 1
                _print_standard_progress(
                    current_job=completed_jobs,
                    total_jobs=total_jobs,
                    scenario_name=scenario.name,
                    run_id=run_id,
                    num_runs=num_runs,
                    strategy_name=strategy_name,
                    start_time=standard_start_time,
                )
                history_df, metrics = run_one(
                    strategy_name=strategy_name,
                    scenario=scenario,
                    run_seed=run_seed,
                    horizon=horizon,
                    high_weight_threshold=high_weight_threshold,
                )

                row: Dict[str, float] = {
                    "scenario_name": scenario.name,
                    "run_id": run_id,
                    **metrics,
                }
                run_rows.append(row)

                if args.save_trajectories:
                    save_history_csv(
                        history_df,
                        output_dir / "trajectories" / f"{scenario.name}__{strategy_name}__run{run_id}.csv",
                    )

    run_metrics_df = pd.DataFrame(run_rows)
    save_summary_csv(run_metrics_df, output_dir / "run_metrics.csv")
    save_summary_csv(pd.DataFrame(scenario_meta_rows), output_dir / "scenario_config_table.csv")

    aggregated_df = aggregate_run_metrics(run_metrics_df)
    save_summary_csv(aggregated_df, output_dir / "summary_aggregated.csv")

    scenario_order = [scenario.name for scenario in scenario_configs]
    strategy_order = strategies

    plot_grouped_metric_with_errorbars(
        summary_df=aggregated_df,
        scenario_order=scenario_order,
        strategy_order=strategy_order,
        metric_mean_col="average_weighted_aoi_mean",
        metric_std_col="average_weighted_aoi_std",
        output_path=output_dir / "figures" / "avg_weighted_aoi_mean_std.png",
        title="Average Weighted AoI (mean ± std)",
        ylabel="Average Weighted AoI",
    )

    plot_grouped_metric_with_errorbars(
        summary_df=aggregated_df,
        scenario_order=scenario_order,
        strategy_order=strategy_order,
        metric_mean_col="high_weight_avg_aoi_mean",
        metric_std_col="high_weight_avg_aoi_std",
        output_path=output_dir / "figures" / "high_weight_avg_aoi_mean_std.png",
        title="High-Priority Average AoI (mean ± std)",
        ylabel="High-Priority Average AoI",
    )

    for scenario in scenario_configs:
        scenario_df = aggregated_df[aggregated_df["scenario_name"] == scenario.name].copy()
        per_source_plot_df = pd.DataFrame({"strategy": scenario_df["strategy"].tolist()})
        for source_id in range(scenario.n):
            per_source_plot_df[f"avg_aoi_{source_id}"] = scenario_df[f"avg_aoi_{source_id}_mean"].tolist()

        plot_average_aoi_by_source(
            summary_df=per_source_plot_df,
            source_ids=list(range(scenario.n)),
            output_path=output_dir / "figures" / f"{scenario.name}_avg_aoi_by_source.png",
        )

    print("=" * 72)
    print("Runner Finished")
    print("=" * 72)
    print(f"Config         : {config_path}")
    print(f"Output dir     : {output_dir}")
    print(f"Run metrics    : {output_dir / 'run_metrics.csv'}")
    print(f"Aggregated CSV : {output_dir / 'summary_aggregated.csv'}")
    print(f"Figures dir    : {output_dir / 'figures'}")
    print(f"Total elapsed  : {_format_seconds(time.perf_counter() - standard_start_time)}")
    print("-" * 72)
    print(aggregated_df.sort_values(by=['scenario_name', 'average_weighted_aoi_mean']).to_string(index=False))


if __name__ == "__main__":
    main()
