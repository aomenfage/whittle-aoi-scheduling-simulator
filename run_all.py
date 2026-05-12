from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.exp_compare import run_experiment as run_baseline_compare
from experiments.exp_single_arm_mdp import run_single_arm_experiment
from experiments.exp_whittle_demo import evaluate_decisions
from runner import main as runner_main
from tools.generate_readme import main as generate_readme_main
from utils.metrics import save_summary_csv


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_standard_suite(config_path: Path) -> None:
    old_argv = sys.argv[:]
    try:
        sys.argv = ["runner.py", "--suite", "standard", "--config", str(config_path)]
        runner_main()
    finally:
        sys.argv = old_argv


def run_extended_suite(output_root: Path) -> None:
    old_argv = sys.argv[:]
    try:
        sys.argv = ["runner.py", "--suite", "extended", "--output-root", str(output_root)]
        runner_main()
    finally:
        sys.argv = old_argv


def run_single_arm_section(config: dict) -> None:
    args = SimpleNamespace(
        weight=float(config["weight"]),
        success_prob=float(config["success_prob"]),
        lambda_value=float(config["lambda_value"]),
        a_max=int(config["a_max"]),
        lambda_mode=str(config["lambda_mode"]),
        output_dir=str(PROJECT_ROOT / str(config["output_dir"])),
    )
    run_single_arm_experiment(args)


def run_baseline_compare_section(config: dict) -> None:
    output_dir = PROJECT_ROOT / str(config["output_dir"])
    run_baseline_compare(
        strategies=list(config["strategies"]),
        horizon=int(config["horizon"]),
        seed=int(config["seed"]),
        high_weight_threshold=float(config["high_weight_threshold"]),
        output_dir=output_dir,
    )


def run_whittle_demo_section(config: dict) -> None:
    output_csv = PROJECT_ROOT / str(config["output_csv"])
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    _, detail_df, greedy_action, whittle_action = evaluate_decisions(max_test_aoi=int(config["max_test_aoi"]))
    detail_df["greedy_action"] = greedy_action
    detail_df["whittle_action"] = whittle_action
    detail_df.to_csv(output_csv, index=False)


def run_tests() -> None:
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=PROJECT_ROOT,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all core experiments for AoI paper reproduction.")
    parser.add_argument(
        "--config",
        type=str,
        default=str(PROJECT_ROOT / "config" / "run_all_default.json"),
        help="Path to the run-all JSON config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)
    print("[run_all] pipeline start", flush=True)
    print(f"[run_all] config={config_path}", flush=True)

    if bool(config.get("generate_readme", True)):
        print("[run_all] generating README", flush=True)
        generate_readme_main()

    if bool(config.get("generate_summary_template", True)):
        print("[run_all] checking summary template", flush=True)
        template_path = PROJECT_ROOT / "templates" / "template_paper_results_summary.md"
        if not template_path.exists():
            raise FileNotFoundError(f"summary template not found: {template_path}")

    standard_suite = config.get("standard_suite", {})
    standard_output_dir = None
    if standard_suite:
        standard_config_path = PROJECT_ROOT / str(standard_suite["config_path"])
        standard_runner_config = load_config(standard_config_path)
        standard_output_dir = PROJECT_ROOT / str(
            standard_runner_config.get("output_dir", "results/runner")
        )
        print("[run_all] running standard suite", flush=True)
        run_standard_suite(standard_config_path)

    extended_suite = config.get("extended_suite", {})
    if extended_suite.get("enabled", False):
        print("[run_all] running extended suite", flush=True)
        run_extended_suite(PROJECT_ROOT / str(extended_suite["output_root"]))

    single_arm_config = config.get("single_arm_mdp", {})
    if single_arm_config.get("enabled", False):
        print("[run_all] running single-arm MDP section", flush=True)
        run_single_arm_section(single_arm_config)

    baseline_compare_config = config.get("baseline_compare", {})
    if baseline_compare_config.get("enabled", False):
        print("[run_all] running baseline comparison section", flush=True)
        run_baseline_compare_section(baseline_compare_config)

    whittle_demo_config = config.get("whittle_demo", {})
    if whittle_demo_config.get("enabled", False):
        print("[run_all] running Whittle demo section", flush=True)
        run_whittle_demo_section(whittle_demo_config)

    if bool(config.get("run_tests", True)):
        print("[run_all] running tests", flush=True)
        run_tests()

    summary_df = pd.DataFrame(
        [
            {"section": "readme", "status": "done"},
            {"section": "standard_suite", "status": "done"},
            {"section": "extended_suite", "status": "done" if extended_suite.get("enabled", False) else "skipped"},
            {"section": "single_arm_mdp", "status": "done" if single_arm_config.get("enabled", False) else "skipped"},
            {"section": "baseline_compare", "status": "done" if baseline_compare_config.get("enabled", False) else "skipped"},
            {"section": "whittle_demo", "status": "done" if whittle_demo_config.get("enabled", False) else "skipped"},
            {"section": "tests", "status": "done" if bool(config.get("run_tests", True)) else "skipped"},
        ]
    )
    save_summary_csv(summary_df, PROJECT_ROOT / "results" / "run_all_summary.csv")

    print("=" * 72)
    print("Run-All Pipeline Finished")
    print("=" * 72)
    print(f"Config          : {config_path}")
    print(f"README          : {PROJECT_ROOT / 'README.md'}")
    print(f"Summary CSV     : {PROJECT_ROOT / 'results' / 'run_all_summary.csv'}")
    print(f"Standard suite  : {standard_output_dir}")
    print(f"Extended suite  : {PROJECT_ROOT / str(extended_suite.get('output_root', 'results/extended_suite'))}")


if __name__ == "__main__":
    main()
