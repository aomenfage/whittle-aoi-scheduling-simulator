from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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


@dataclass
class ScenarioConfig:
    name: str
    n: int
    weights: List[float]
    channel_success_probs: List[float]
    sampling_rates: Optional[List[float]] = None

    def validate(self) -> None:
        if self.n <= 0:
            raise ValueError("n must be positive.")
        if len(self.weights) != self.n:
            raise ValueError("weights must have length n.")
        if len(self.channel_success_probs) != self.n:
            raise ValueError("channel_success_probs must have length n.")
        if self.sampling_rates is None:
            self.sampling_rates = [1.0] * self.n
        if len(self.sampling_rates) != self.n:
            raise ValueError("sampling_rates must have length n.")


class TimedSchedulerWrapper:
    """Wrap any scheduler and record per-slot decision time."""

    def __init__(self, scheduler) -> None:
        self.scheduler = scheduler
        self.name = getattr(scheduler, "name", scheduler.__class__.__name__.lower())
        self.decision_times_ns: List[int] = []

    def reset(self) -> None:
        self.decision_times_ns = []
        if hasattr(self.scheduler, "reset"):
            self.scheduler.reset()

    def select_action(self, env):
        start_ns = time.perf_counter_ns()
        action = self.scheduler.select_action(env)
        elapsed_ns = time.perf_counter_ns() - start_ns
        self.decision_times_ns.append(int(elapsed_ns))
        return action

    def avg_decision_time_ms(self) -> float:
        if not self.decision_times_ns:
            return 0.0
        return float(np.mean(self.decision_times_ns) / 1e6)


def _format_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remain = seconds - 60 * minutes
    return f"{minutes}m {remain:.1f}s"


def _print_progress(
    experiment_name: str,
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
        "[{exp}] {cur}/{tot} ({pct:.1f}%) | scenario={scenario} | run={run}/{runs} | "
        "strategy={strategy} | elapsed={elapsed}".format(
            exp=experiment_name,
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
    scenario.validate()
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


def build_scheduler(strategy_name: str, env: AoIEnv, whittle_a_max: int = 15):
    source_ids = [source.source_id for source in env.sources]
    if strategy_name == "whittle":
        return WhittleScheduler(sources=env.sources, channel=env.channel, a_max=whittle_a_max)
    if strategy_name == "round_robin":
        return RoundRobinScheduler(source_ids=source_ids)
    if strategy_name == "periodic":
        min_weight = min(source.weight for source in env.sources)
        pattern: List[int] = []
        for source in env.sources:
            repeat_count = max(1, int(round(source.weight / min_weight)))
            pattern.extend([source.source_id] * repeat_count)
        return PeriodicScheduler(pattern=pattern)
    if strategy_name == "greedy":
        return GreedyScheduler()
    if strategy_name == "random":
        return RandomScheduler(source_ids=source_ids)
    raise ValueError(f"unsupported strategy: {strategy_name}")


def run_timed_strategy(
    scenario: ScenarioConfig,
    strategy_name: str,
    horizon: int,
    run_seed: int,
    high_weight_threshold: Optional[float] = None,
    whittle_a_max: int = 15,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    env = build_env_from_scenario(scenario=scenario, seed=run_seed)
    base_scheduler = build_scheduler(strategy_name=strategy_name, env=env, whittle_a_max=whittle_a_max)
    timed_scheduler = TimedSchedulerWrapper(base_scheduler)

    run_start = time.perf_counter()
    history_df = env.run(policy=timed_scheduler, horizon=horizon)
    total_runtime_s = float(time.perf_counter() - run_start)

    metrics = compute_run_metrics(
        history_df=history_df,
        sources=env.sources,
        strategy_name=strategy_name,
        high_weight_threshold=high_weight_threshold,
    )
    metrics["avg_decision_time_ms"] = timed_scheduler.avg_decision_time_ms()
    metrics["total_runtime_s"] = total_runtime_s
    return history_df, metrics


def run_repeated_experiment(
    experiment_name: str,
    scenarios: List[ScenarioConfig],
    strategies: List[str],
    horizon: int,
    num_runs: int,
    base_seed: int,
    output_dir: Path,
    high_weight_threshold: Optional[float] = None,
    save_trajectories: bool = False,
    whittle_a_max: int = 15,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if save_trajectories:
        (output_dir / "trajectories").mkdir(parents=True, exist_ok=True)

    run_rows: List[Dict[str, float]] = []
    scenario_rows: List[Dict[str, object]] = []
    total_jobs = len(scenarios) * num_runs * len(strategies)
    completed_jobs = 0
    experiment_start_time = time.perf_counter()

    print(
        f"[{experiment_name}] start | scenarios={len(scenarios)} | runs={num_runs} | "
        f"strategies={len(strategies)} | total_jobs={total_jobs} | output={output_dir}",
        flush=True,
    )

    for scenario_index, scenario in enumerate(scenarios):
        scenario.validate()
        scenario_rows.append(
            {
                "experiment_name": experiment_name,
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
                _print_progress(
                    experiment_name=experiment_name,
                    current_job=completed_jobs,
                    total_jobs=total_jobs,
                    scenario_name=scenario.name,
                    run_id=run_id,
                    num_runs=num_runs,
                    strategy_name=strategy_name,
                    start_time=experiment_start_time,
                )
                history_df, metrics = run_timed_strategy(
                    scenario=scenario,
                    strategy_name=strategy_name,
                    horizon=horizon,
                    run_seed=run_seed,
                    high_weight_threshold=high_weight_threshold,
                    whittle_a_max=whittle_a_max,
                )
                run_rows.append(
                    {
                        "experiment_name": experiment_name,
                        "scenario_name": scenario.name,
                        "run_id": run_id,
                        **metrics,
                    }
                )
                if save_trajectories:
                    save_history_csv(
                        history_df,
                        output_dir / "trajectories" / f"{scenario.name}__{strategy_name}__run{run_id}.csv",
                    )

    run_metrics_df = pd.DataFrame(run_rows)
    summary_df = aggregate_run_metrics(run_metrics_df)

    save_summary_csv(run_metrics_df, output_dir / "run_metrics.csv")
    save_summary_csv(summary_df, output_dir / "summary_aggregated.csv")
    save_summary_csv(pd.DataFrame(scenario_rows), output_dir / "scenario_table.csv")
    print(
        f"[{experiment_name}] done | output={output_dir} | total_elapsed="
        f"{_format_seconds(time.perf_counter() - experiment_start_time)}",
        flush=True,
    )
    return run_metrics_df, summary_df


def default_strategy_list() -> List[str]:
    return ["whittle", "round_robin", "periodic", "greedy", "random"]


def linear_profile(start: float, end: float, n: int) -> List[float]:
    return [float(x) for x in np.linspace(start, end, n)]


def high_priority_weight_profile(n: int, base_weight: float, high_priority_weight: float) -> List[float]:
    weights = [float(base_weight)] * n
    weights[-1] = float(high_priority_weight)
    return weights
