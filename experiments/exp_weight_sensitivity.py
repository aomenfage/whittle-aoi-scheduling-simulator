from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.experiment_utils import ScenarioConfig, default_strategy_list, run_repeated_experiment
from utils.metrics import save_summary_csv
from utils.plotter import plot_metric_vs_parameter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weight sensitivity experiment for high-priority services.")
    parser.add_argument("--output-dir", type=str, default=str(PROJECT_ROOT / "results" / "final_weight_sensitivity"))
    parser.add_argument("--horizon", type=int, default=3000)
    parser.add_argument("--num-runs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def build_weight_scenarios() -> list[ScenarioConfig]:
    scenarios = []
    for high_weight in [2.0, 4.0, 6.0, 8.0, 10.0]:
        scenarios.append(
            ScenarioConfig(
                name=f"high_w_{int(high_weight)}",
                n=5,
                weights=[1.0, 1.0, 1.0, 1.0, high_weight],
                sampling_rates=[0.95, 0.92, 0.88, 0.84, 0.80],
                channel_success_probs=[0.92, 0.88, 0.84, 0.80, 0.76],
            )
        )
    return scenarios


def write_conclusion_template(output_dir: Path) -> None:
    template = """Weight Sensitivity Conclusion Template
1. As the high-priority weight increases, the average AoI of the critical source under Whittle [decreases / remains lower than baselines].
2. Compared with Greedy and periodic baselines, Whittle provides [better / more stable] protection for critical monitoring traffic.
3. The weighted AoI results suggest that the proposed policy is more robust when system priorities become highly skewed.
"""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "conclusion_template.txt").write_text(template, encoding="utf-8")


def run_default_experiment(output_dir: Path, horizon: int, num_runs: int, seed: int):
    scenarios = build_weight_scenarios()
    _, summary_df = run_repeated_experiment(
        experiment_name="weight_sensitivity",
        scenarios=scenarios,
        strategies=default_strategy_list(),
        horizon=horizon,
        num_runs=num_runs,
        base_seed=seed,
        output_dir=output_dir,
        high_weight_threshold=2.0,
        whittle_a_max=25,
    )

    weight_map = {scenario.name: scenario.weights[-1] for scenario in scenarios}
    summary_df["high_priority_weight"] = summary_df["scenario_name"].map(weight_map)
    save_summary_csv(summary_df, output_dir / "summary_with_weight.csv")

    strategy_order = default_strategy_list()
    plot_metric_vs_parameter(
        summary_df=summary_df,
        parameter_col="high_priority_weight",
        strategy_order=strategy_order,
        metric_mean_col="high_weight_avg_aoi_mean",
        metric_std_col="high_weight_avg_aoi_std",
        output_path=output_dir / "figures" / "high_priority_aoi_vs_weight.png",
        title="High-Priority Average AoI vs Critical Weight",
        xlabel="High-priority weight",
        ylabel="High-priority average AoI",
    )
    plot_metric_vs_parameter(
        summary_df=summary_df,
        parameter_col="high_priority_weight",
        strategy_order=strategy_order,
        metric_mean_col="average_weighted_aoi_mean",
        metric_std_col="average_weighted_aoi_std",
        output_path=output_dir / "figures" / "avg_weighted_aoi_vs_weight.png",
        title="Average Weighted AoI vs Critical Weight",
        xlabel="High-priority weight",
        ylabel="Average Weighted AoI",
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
    print("Weight Sensitivity Experiment Finished")
    print("=" * 72)
    print(summary_df[["scenario_name", "strategy", "high_priority_weight", "high_weight_avg_aoi_mean", "average_weighted_aoi_mean"]].to_string(index=False))
    print(f"Output dir: {output_dir}")


if __name__ == "__main__":
    main()
