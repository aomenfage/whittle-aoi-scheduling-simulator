from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import build_demo_env, build_scheduler
from utils.metrics import compute_run_metrics, save_history_csv, save_summary_csv
from utils.plotter import (
    plot_aoi_trajectories,
    plot_average_aoi_by_source,
    plot_average_weighted_aoi,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline strategy comparison experiments.")
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=["round_robin", "periodic", "greedy", "random"],
        choices=["round_robin", "periodic", "greedy", "random"],
        help="Strategies to compare in one experiment run.",
    )
    parser.add_argument("--horizon", type=int, default=1000, help="Number of time slots.")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed.")
    parser.add_argument(
        "--high-weight-threshold",
        type=float,
        default=2.0,
        help="Threshold for defining high-weight services.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "results" / "exp_compare"),
        help="Directory for CSV results and figures.",
    )
    return parser.parse_args()


def run_experiment(
    strategies: List[str],
    horizon: int,
    seed: int,
    high_weight_threshold: float,
    output_dir: Path,
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    trajectory_dir = output_dir / "trajectories"
    figure_dir = output_dir / "figures"
    trajectory_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    source_ids = None

    for strategy_name in strategies:
        env = build_demo_env(seed=seed)
        scheduler = build_scheduler(strategy_name=strategy_name, env=env)
        history_df = env.run(policy=scheduler, horizon=horizon)
        source_ids = [source.source_id for source in env.sources]

        metrics = compute_run_metrics(
            history_df=history_df,
            sources=env.sources,
            strategy_name=strategy_name,
            high_weight_threshold=high_weight_threshold,
        )
        summary_rows.append(metrics)

        save_history_csv(history_df, trajectory_dir / f"{strategy_name}_trajectory.csv")
        plot_aoi_trajectories(
            history_df=history_df,
            source_ids=source_ids,
            strategy_name=strategy_name,
            output_path=figure_dir / f"{strategy_name}_aoi_trajectory.png",
        )

    summary_df = pd.DataFrame(summary_rows).sort_values(by="average_weighted_aoi", ascending=True)
    save_summary_csv(summary_df, output_dir / "summary_metrics.csv")
    plot_average_weighted_aoi(summary_df, figure_dir / "average_weighted_aoi_bar.png")
    plot_average_aoi_by_source(summary_df, source_ids=source_ids or [], output_path=figure_dir / "average_aoi_by_source.png")
    return summary_df


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)

    summary_df = run_experiment(
        strategies=args.strategies,
        horizon=args.horizon,
        seed=args.seed,
        high_weight_threshold=args.high_weight_threshold,
        output_dir=output_dir,
    )

    print("=" * 70)
    print("AoI Baseline Experiment Summary")
    print("=" * 70)
    print(summary_df.to_string(index=False))
    print("-" * 70)
    print(f"Summary CSV : {output_dir / 'summary_metrics.csv'}")
    print(f"Trajectory CSV dir: {output_dir / 'trajectories'}")
    print(f"Figure dir   : {output_dir / 'figures'}")


if __name__ == "__main__":
    main()
