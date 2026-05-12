from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.experiment_utils import ScenarioConfig, default_strategy_list, run_repeated_experiment
from utils.plotter import plot_grouped_metric_with_errorbars


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Channel heterogeneity sensitivity experiment.")
    parser.add_argument("--output-dir", type=str, default=str(PROJECT_ROOT / "results" / "final_channel_sensitivity"))
    parser.add_argument("--horizon", type=int, default=3000)
    parser.add_argument("--num-runs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def build_channel_scenarios() -> list[ScenarioConfig]:
    return [
        ScenarioConfig(
            name="uniform",
            n=5,
            weights=[1.0, 1.5, 2.0, 3.0, 5.0],
            sampling_rates=[0.95, 0.92, 0.88, 0.84, 0.80],
            channel_success_probs=[0.85, 0.85, 0.85, 0.85, 0.85],
        ),
        ScenarioConfig(
            name="mild_hetero",
            n=5,
            weights=[1.0, 1.5, 2.0, 3.0, 5.0],
            sampling_rates=[0.95, 0.92, 0.88, 0.84, 0.80],
            channel_success_probs=[0.92, 0.88, 0.84, 0.78, 0.72],
        ),
        ScenarioConfig(
            name="strong_hetero",
            n=5,
            weights=[1.0, 1.5, 2.0, 3.0, 5.0],
            sampling_rates=[0.95, 0.92, 0.88, 0.84, 0.80],
            channel_success_probs=[0.95, 0.88, 0.76, 0.62, 0.48],
        ),
    ]


def write_conclusion_template(output_dir: Path) -> None:
    template = """Channel Heterogeneity Conclusion Template
1. As link heterogeneity becomes stronger, the weighted AoI of all strategies [increases / degrades], but Whittle remains [the best / competitive].
2. The proposed policy better captures source-dependent success probabilities, resulting in [lower / more stable] AoI under heterogeneous links.
3. The results support the robustness of Whittle scheduling in realistic railway monitoring networks with non-uniform transmission reliability.
"""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "conclusion_template.txt").write_text(template, encoding="utf-8")


def run_default_experiment(output_dir: Path, horizon: int, num_runs: int, seed: int):
    scenarios = build_channel_scenarios()
    _, summary_df = run_repeated_experiment(
        experiment_name="channel_sensitivity",
        scenarios=scenarios,
        strategies=default_strategy_list(),
        horizon=horizon,
        num_runs=num_runs,
        base_seed=seed,
        output_dir=output_dir,
        high_weight_threshold=2.0,
        whittle_a_max=25,
    )

    scenario_order = [scenario.name for scenario in scenarios]
    strategy_order = default_strategy_list()
    plot_grouped_metric_with_errorbars(
        summary_df=summary_df,
        scenario_order=scenario_order,
        strategy_order=strategy_order,
        metric_mean_col="average_weighted_aoi_mean",
        metric_std_col="average_weighted_aoi_std",
        output_path=output_dir / "figures" / "avg_weighted_aoi_by_channel_profile.png",
        title="Average Weighted AoI under Different Channel Profiles",
        ylabel="Average Weighted AoI",
    )
    plot_grouped_metric_with_errorbars(
        summary_df=summary_df,
        scenario_order=scenario_order,
        strategy_order=strategy_order,
        metric_mean_col="high_weight_avg_aoi_mean",
        metric_std_col="high_weight_avg_aoi_std",
        output_path=output_dir / "figures" / "high_priority_aoi_by_channel_profile.png",
        title="High-Priority Average AoI under Different Channel Profiles",
        ylabel="High-Priority Average AoI",
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
    print("Channel Heterogeneity Experiment Finished")
    print("=" * 72)
    print(summary_df[["scenario_name", "strategy", "average_weighted_aoi_mean", "high_weight_avg_aoi_mean"]].to_string(index=False))
    print(f"Output dir: {output_dir}")


if __name__ == "__main__":
    main()
