# AOI State Update Simulation with Whittle Index Scheduling

## Description
This project studies status update scheduling for network monitoring scenarios with a focus on minimizing Weighted Age of Information (Weighted AoI), rather than transmission delay alone.

The repository implements a complete simulation and experiment pipeline for:

1. Basic AoI environment modeling
2. Multiple online baseline schedulers
3. Single-arm average-cost MDP analysis
4. Threshold-structure verification
5. Lagrangian relaxation and Whittle index scheduling
6. Standard comparison experiments and extended sensitivity studies

The current codebase models a single MEC node, multiple monitored sources, single-hop status updates, and a discrete-time slotted system where at most one source is scheduled in each slot.

## Repository Structure

```text
AOITest/
|-- algorithms/    Scheduling policies: Round Robin / Periodic / Greedy / Random / Whittle
|-- config/        JSON configuration files for experiments
|-- docs/          Method notes, experiment design, and result analysis
|-- env/           Simulation environment: Source / Channel / AoIEnv
|-- experiments/   Standalone experiment scripts and helpers
|-- results/       Generated CSV files, plots, and reports
|-- solver/        Single-arm MDP, threshold analysis, and Lagrangian tools
|-- tests/         Basic unit tests
|-- tools/         Utility scripts such as README generation
|-- utils/         Metrics, plotting, and logging helpers
|-- main.py        Quick entry point for a single scenario
|-- runner.py      Standard and extended experiment runner
`-- run_all.py     One-command pipeline for core reproduction
```

## Environment Requirements

Recommended Python version: 3.11+

Core dependencies:

```text
numpy
pandas
matplotlib
```

Install dependencies with a virtual environment if needed:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start

### 1. Run a single strategy in the demo scenario

```bash
python main.py --strategy all
python main.py --strategy whittle
```

Available strategy names:

- `all`
- `round_robin`
- `periodic`
- `greedy`
- `random`
- `whittle`

### 2. Run the standard comparison suite

```bash
python runner.py --suite standard --config config/runner_default.json
```

### 3. Run the extended sensitivity suite

```bash
python runner.py --suite extended
```

### 4. Reproduce the core pipeline in one command

```bash
python run_all.py --config config/run_all_default.json
```

### 5. Run the single-arm MDP experiment

```bash
python experiments/exp_single_arm_mdp.py --lambda-value 8.0
```

### 6. Compare Whittle and Greedy decisions

```bash
python experiments/exp_whittle_demo.py
```

### 7. Run basic tests

```bash
python -m unittest discover -s tests -v
```

## Reproduction Workflow

1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `python run_all.py --config config/run_all_default.json`.
4. Inspect generated CSV files and plots under `results/`.
5. Run `python runner.py --suite standard` if you only need the main comparison tables.
6. Run `python runner.py --suite extended` if you also want the sensitivity experiments.

## Output and Results

Typical outputs include:

- Per-run metrics in CSV format
- Aggregated summary tables
- AoI trajectory data
- Comparison figures for Weighted AoI and high-priority sources
- Sensitivity-study results for scale, weights, channel quality, and peak AoI

Important output locations:

- `results/runner_default/`
- `results/runner_final/`
- `results/final_extended_suite/`
- `results/single_arm_mdp/`
- `results/exp_compare/`

## Method Overview

The project is built around a unified AoI optimization objective:

```text
C(t) = sum_i w_i * A_i(t)
```

Where:

- `w_i` is the priority weight of source `i`
- `A_i(t)` is the AoI of source `i` at slot `t`

Implemented scheduling policies include:

1. Round Robin
2. Periodic
3. Greedy
4. Random
5. Whittle Index

The Whittle-based scheduler is the main method of interest and is supported by single-arm MDP modeling, threshold verification, and Lagrangian relaxation modules in `solver/`.

## Notes

- Experiment parameters are primarily managed through JSON config files in `config/`.
- Metrics are centralized in `utils/metrics.py`.
- Plot generation is centralized in `utils/plotter.py`.
- Standard and extended suites share the same environment and metric definitions for fair comparison.

## Contribution

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a pull request.
