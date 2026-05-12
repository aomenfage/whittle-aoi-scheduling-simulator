from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_average_weighted_aoi(summary_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ordered_df = summary_df.sort_values(by="average_weighted_aoi", ascending=True)
    ax.bar(ordered_df["strategy"], ordered_df["average_weighted_aoi"], color="steelblue")
    ax.set_title("Average Weighted AoI by Strategy")
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Average Weighted AoI")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_average_aoi_by_source(
    summary_df: pd.DataFrame,
    source_ids: Iterable[int],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    source_ids = list(source_ids)
    strategies = list(summary_df["strategy"])
    x = np.arange(len(source_ids))
    width = 0.8 / max(len(strategies), 1)

    fig, ax = plt.subplots(figsize=(10, 5))
    for index, strategy in enumerate(strategies):
        row = summary_df.loc[summary_df["strategy"] == strategy].iloc[0]
        values = [row[f"avg_aoi_{source_id}"] for source_id in source_ids]
        ax.bar(x + index * width, values, width=width, label=strategy)

    ax.set_title("Average AoI of Each Source by Strategy")
    ax.set_xlabel("Source ID")
    ax.set_ylabel("Average AoI")
    ax.set_xticks(x + width * (len(strategies) - 1) / 2)
    ax.set_xticklabels([str(source_id) for source_id in source_ids])
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_aoi_trajectories(
    history_df: pd.DataFrame,
    source_ids: List[int],
    strategy_name: str,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    for source_id in source_ids:
        ax.plot(history_df["slot"], history_df[f"aoi_{source_id}"], label=f"source_{source_id}")

    ax.set_title(f"AoI Evolution Over Time: {strategy_name}")
    ax.set_xlabel("Slot")
    ax.set_ylabel("AoI")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_state_action_mapping(
    states: Iterable[int],
    actions: Iterable[int],
    output_path: Path,
    title: str = "Optimal Action Mapping",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    states = list(states)
    actions = list(actions)
    labels = ["passive" if action == 0 else "active" for action in actions]
    y_values = [0 if action == 0 else 1 for action in actions]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.step(states, y_values, where="post", linewidth=2, color="darkorange")
    ax.scatter(states, y_values, color="darkorange", s=30)
    ax.set_title(title)
    ax.set_xlabel("AoI State")
    ax.set_ylabel("Optimal Action")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["passive", "active"])
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_value_function(
    states: Iterable[int],
    values: Iterable[float],
    output_path: Path,
    title: str = "Relative Value Function",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    states = list(states)
    values = list(values)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(states, values, marker="o", linewidth=2, color="seagreen")
    ax.set_title(title)
    ax.set_xlabel("AoI State")
    ax.set_ylabel("Value")
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_grouped_metric_with_errorbars(
    summary_df: pd.DataFrame,
    scenario_order: List[str],
    strategy_order: List[str],
    metric_mean_col: str,
    metric_std_col: str,
    output_path: Path,
    title: str,
    ylabel: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(scenario_order))
    width = 0.8 / max(len(strategy_order), 1)

    for idx, strategy in enumerate(strategy_order):
        values = []
        errors = []
        for scenario_name in scenario_order:
            row = summary_df[
                (summary_df["scenario_name"] == scenario_name)
                & (summary_df["strategy"] == strategy)
            ]
            if row.empty:
                values.append(0.0)
                errors.append(0.0)
            else:
                values.append(float(row.iloc[0][metric_mean_col]))
                errors.append(float(row.iloc[0][metric_std_col]))

        ax.bar(
            x + idx * width,
            values,
            width=width,
            yerr=errors,
            capsize=4,
            label=strategy,
        )

    ax.set_title(title)
    ax.set_xlabel("Scenario")
    ax.set_ylabel(ylabel)
    ax.set_xticks(x + width * (len(strategy_order) - 1) / 2)
    ax.set_xticklabels(scenario_order, rotation=15)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_metric_vs_parameter(
    summary_df: pd.DataFrame,
    parameter_col: str,
    strategy_order: List[str],
    metric_mean_col: str,
    metric_std_col: str,
    output_path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    parameter_values = sorted(summary_df[parameter_col].dropna().unique().tolist())

    for strategy in strategy_order:
        strategy_df = summary_df[summary_df["strategy"] == strategy].sort_values(by=parameter_col)
        x = strategy_df[parameter_col].tolist()
        y = strategy_df[metric_mean_col].tolist()
        yerr = strategy_df[metric_std_col].tolist()
        ax.errorbar(x, y, yerr=yerr, marker="o", linewidth=2, capsize=4, label=strategy)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if parameter_values:
        ax.set_xticks(parameter_values)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
