from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from solver.dp_solver import SingleSourceMDPConfig, SingleSourceMDPSolver
from solver.threshold_solver import analyze_threshold_structure
from utils.plotter import plot_state_action_mapping, plot_value_function


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-source AoI MDP and threshold validation.")
    parser.add_argument("--weight", type=float, default=2.0, help="AoI weight w.")
    parser.add_argument("--success-prob", type=float, default=0.8, help="Update success probability p.")
    parser.add_argument(
        "--lambda-value",
        type=float,
        default=1.0,
        help="Passive subsidy or active scheduling cost lambda.",
    )
    parser.add_argument("--a-max", type=int, default=25, help="Maximum truncated AoI state.")
    parser.add_argument(
        "--lambda-mode",
        type=str,
        default="passive_subsidy",
        choices=["passive_subsidy", "active_cost"],
        help="Interpretation of lambda.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "results" / "single_arm_mdp"),
        help="Directory for tables and figures.",
    )
    return parser.parse_args()


def run_single_arm_experiment(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = SingleSourceMDPConfig(
        weight=args.weight,
        success_prob=args.success_prob,
        lambda_value=args.lambda_value,
        a_max=args.a_max,
        lambda_mode=args.lambda_mode,
    )
    solver = SingleSourceMDPSolver(config)
    result = solver.solve()
    threshold_analysis = analyze_threshold_structure(result.actions, result.states)

    action_table = result.to_action_table()
    action_table.to_csv(output_dir / "single_arm_action_table.csv", index=False)

    summary = {
        **result.to_summary_dict(),
        **threshold_analysis.to_dict(),
    }
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(output_dir / "single_arm_summary.csv", index=False)

    plot_state_action_mapping(
        states=result.states,
        actions=result.actions,
        output_path=output_dir / "state_action_mapping.png",
        title="Optimal Action vs AoI State",
    )
    plot_value_function(
        states=result.states,
        values=result.value_function,
        output_path=output_dir / "value_function.png",
        title="Relative Value Function vs AoI State",
    )

    return action_table, summary_df, summary


def main() -> None:
    args = parse_args()
    action_table, summary_df, summary = run_single_arm_experiment(args)

    print("=" * 72)
    print("Single-Source AoI MDP Solution")
    print("=" * 72)
    print(summary_df.to_string(index=False))
    print("-" * 72)
    print("Optimal action table:")
    print(action_table.to_string(index=False))
    print("-" * 72)
    print(f"Threshold exists : {summary['has_threshold_structure']}")
    print(f"Threshold state  : {summary['threshold_state']}")
    print(f"Average cost     : {summary['average_cost']:.6f}")
    print(f"Action table CSV : {Path(args.output_dir) / 'single_arm_action_table.csv'}")
    print(f"Summary CSV      : {Path(args.output_dir) / 'single_arm_summary.csv'}")
    print(f"Action plot      : {Path(args.output_dir) / 'state_action_mapping.png'}")
    print(f"Value plot       : {Path(args.output_dir) / 'value_function.png'}")


if __name__ == "__main__":
    main()
