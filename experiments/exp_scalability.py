from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.experiment_utils import (
    ScenarioConfig,
    default_strategy_list,
    linear_profile,
    run_repeated_experiment,
)
from utils.metrics import save_summary_csv
from utils.plotter import plot_metric_vs_parameter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scalability experiment for AoI schedulers.")
    parser.add_argument("--output-dir", type=str, default=str(PROJECT_ROOT / "results" / "final_scalability"))
    parser.add_argument("--horizon", type=int, default=2000)
    parser.add_argument("--num-runs", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def build_scalability_scenarios() -> list[ScenarioConfig]:
    scenarios = []
    for n in [5, 10, 20, 50]:
        scenarios.append(
            ScenarioConfig(
                name=f"N_{n}",
                n=n,
                weights=linear_profile(1.0, 5.0, n),
                sampling_rates=linear_profile(0.95, 0.75, n),
                channel_success_probs=linear_profile(0.95, 0.70, n),
            )
        )
    return scenarios


def write_conclusion_template(output_dir: Path) -> None:
    template = """Scalability Conclusion Template
1. As N increases from 5 to 10, 20, and 50, the average weighted AoI of each strategy [increases / remains stable / degrades slowly].
2. Whittle shows [the best / competitive] weighted AoI performance under all tested scales.
3. In terms of complexity, the average decision time of Whittle is [higher than / comparable to] simple baselines, but remains within [acceptable / practical] online scheduling latency.
4. The overall runtime trend indicates that the proposed method is [scalable / suitable] for larger source populations in the considered MEC monitoring system.
"""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "conclusion_template.txt").write_text(template, encoding="utf-8")


def run_default_experiment(output_dir: Path, horizon: int, num_runs: int, seed: int):
    scenarios = build_scalability_scenarios()
    _, summary_df = run_repeated_experiment(
        experiment_name="scalability",
        scenarios=scenarios,
        strategies=default_strategy_list(),
        horizon=horizon,
        num_runs=num_runs,
        base_seed=seed,
        output_dir=output_dir,
        high_weight_threshold=3.0,
        whittle_a_max=105,
    )

    n_map = {scenario.name: scenario.n for scenario in scenarios}
    summary_df["N"] = summary_df["scenario_name"].map(n_map)
    save_summary_csv(summary_df, output_dir / "summary_with_N.csv")

    strategy_order = default_strategy_list()
    plot_metric_vs_parameter(
        summary_df=summary_df,
        parameter_col="N",
        strategy_order=strategy_order,
        metric_mean_col="average_weighted_aoi_mean",
        metric_std_col="average_weighted_aoi_std",
        output_path=output_dir / "figures" / "avg_weighted_aoi_vs_N.png",
        title="Average Weighted AoI vs Number of Sources",
        xlabel="Number of sources N",
        ylabel="Average Weighted AoI",
    )
    plot_metric_vs_parameter(
        summary_df=summary_df,
        parameter_col="N",
        strategy_order=strategy_order,
        metric_mean_col="avg_decision_time_ms_mean",
        metric_std_col="avg_decision_time_ms_std",
        output_path=output_dir / "figures" / "decision_time_vs_N.png",
        title="Average Decision Time vs Number of Sources",
        xlabel="Number of sources N",
        ylabel="Average decision time (ms)",
    )
    plot_metric_vs_parameter(
        summary_df=summary_df,
        parameter_col="N",
        strategy_order=strategy_order,
        metric_mean_col="total_runtime_s_mean",
        metric_std_col="total_runtime_s_std",
        output_path=output_dir / "figures" / "runtime_vs_N.png",
        title="Total Runtime vs Number of Sources",
        xlabel="Number of sources N",
        ylabel="Total runtime (s)",
    )

    write_conclusion_template(output_dir)
    return summary_df


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    summary_df = run_default_experiment(
        output_dir=output_dir,
        horizon=args.horizon,
        num_runs=args.num_runs,
        seed=args.seed,
    )

    print("=" * 72)
    print("Scalability Experiment Finished")
    print("=" * 72)
    print(summary_df[["scenario_name", "strategy", "N", "average_weighted_aoi_mean", "avg_decision_time_ms_mean", "total_runtime_s_mean"]].to_string(index=False))
    print(f"Output dir: {output_dir}")


if __name__ == "__main__":
    main()
