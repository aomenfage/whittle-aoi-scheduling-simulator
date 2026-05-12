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
    parser = argparse.ArgumentParser(description="Peak AoI stress experiment.")
    parser.add_argument("--output-dir", type=str, default=str(PROJECT_ROOT / "results" / "final_peak_aoi"))
    parser.add_argument("--horizon", type=int, default=5000)
    parser.add_argument("--num-runs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def build_peak_scenarios() -> list[ScenarioConfig]:
    return [
        ScenarioConfig(
            name="baseline",
            n=5,
            weights=[1.0, 1.5, 2.0, 3.0, 5.0],
            sampling_rates=[0.95, 0.92, 0.88, 0.84, 0.80],
            channel_success_probs=[0.92, 0.88, 0.84, 0.78, 0.70],
        ),
        ScenarioConfig(
            name="poor_links",
            n=5,
            weights=[1.0, 1.5, 2.0, 3.0, 5.0],
            sampling_rates=[0.95, 0.90, 0.85, 0.80, 0.75],
            channel_success_probs=[0.80, 0.74, 0.68, 0.60, 0.52],
        ),
        ScenarioConfig(
            name="extreme_aging",
            n=5,
            weights=[1.0, 1.5, 2.0, 3.0, 5.0],
            sampling_rates=[0.85, 0.80, 0.75, 0.70, 0.65],
            channel_success_probs=[0.72, 0.66, 0.60, 0.52, 0.45],
        ),
    ]


def write_conclusion_template(output_dir: Path) -> None:
    template = """Peak AoI Conclusion Template
1. Under stressed conditions, the peak AoI of baseline strategies [increases substantially / becomes unstable], indicating higher risk of stale information.
2. Whittle maintains [lower / better controlled] system peak AoI and peak weighted AoI, showing stronger protection against extreme information aging.
3. These results indicate that the proposed policy is advantageous not only in average performance but also in worst-case freshness control.
"""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "conclusion_template.txt").write_text(template, encoding="utf-8")


def run_default_experiment(output_dir: Path, horizon: int, num_runs: int, seed: int):
    scenarios = build_peak_scenarios()
    _, summary_df = run_repeated_experiment(
        experiment_name="peak_aoi",
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
        metric_mean_col="system_peak_aoi_mean",
        metric_std_col="system_peak_aoi_std",
        output_path=output_dir / "figures" / "system_peak_aoi_by_scenario.png",
        title="System Peak AoI under Stress Scenarios",
        ylabel="System Peak AoI",
    )
    plot_grouped_metric_with_errorbars(
        summary_df=summary_df,
        scenario_order=scenario_order,
        strategy_order=strategy_order,
        metric_mean_col="peak_weighted_aoi_mean",
        metric_std_col="peak_weighted_aoi_std",
        output_path=output_dir / "figures" / "peak_weighted_aoi_by_scenario.png",
        title="Peak Weighted AoI under Stress Scenarios",
        ylabel="Peak Weighted AoI",
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
    print("Peak AoI Experiment Finished")
    print("=" * 72)
    print(summary_df[["scenario_name", "strategy", "system_peak_aoi_mean", "peak_weighted_aoi_mean"]].to_string(index=False))
    print(f"Output dir: {output_dir}")


if __name__ == "__main__":
    main()
