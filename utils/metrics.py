from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd


def _get_source_ids(sources: Iterable) -> List[int]:
    return [source.source_id for source in sources]


def _get_high_weight_source_ids(sources: Iterable, high_weight_threshold: Optional[float]) -> List[int]:
    if high_weight_threshold is None:
        weights = sorted(source.weight for source in sources)
        median_index = len(weights) // 2
        high_weight_threshold = weights[median_index]
    return [source.source_id for source in sources if source.weight >= high_weight_threshold]


def compute_run_metrics(
    history_df: pd.DataFrame,
    sources: Iterable,
    strategy_name: str,
    high_weight_threshold: Optional[float] = None,
) -> Dict[str, float]:
    """Compute core AoI metrics for one simulation run."""
    source_ids = _get_source_ids(sources)
    high_weight_source_ids = _get_high_weight_source_ids(sources, high_weight_threshold)

    metrics: Dict[str, float] = {
        "strategy": strategy_name,
        "slots": int(len(history_df)),
        "average_weighted_aoi": float(history_df["weighted_aoi"].mean()),
        "peak_weighted_aoi": float(history_df["weighted_aoi"].max()),
    }

    peak_aoi_values = []
    high_weight_column_names = []

    for source in sources:
        column_name = f"aoi_{source.source_id}"
        avg_aoi = float(history_df[column_name].mean())
        peak_aoi = float(history_df[column_name].max())
        peak_aoi_values.append(peak_aoi)

        metrics[f"avg_aoi_{source.source_id}"] = avg_aoi
        metrics[f"peak_aoi_{source.source_id}"] = peak_aoi
        metrics[f"weight_{source.source_id}"] = float(source.weight)

        if source.source_id in high_weight_source_ids:
            high_weight_column_names.append(column_name)

    metrics["system_peak_aoi"] = float(max(peak_aoi_values))
    metrics["high_weight_threshold"] = (
        float(high_weight_threshold)
        if high_weight_threshold is not None
        else float(min(source.weight for source in sources if source.source_id in high_weight_source_ids))
    )
    metrics["high_weight_avg_aoi"] = float(history_df[high_weight_column_names].mean().mean())
    return metrics


def save_history_csv(history_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    history_df.to_csv(output_path, index=False)


def save_summary_csv(summary_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)


def aggregate_run_metrics(run_metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate repeated experiment runs into mean/std tables."""
    if run_metrics_df.empty:
        raise ValueError("run_metrics_df must not be empty.")

    candidate_group_keys = ["experiment_name", "scenario_name", "strategy"]
    group_keys = [column for column in candidate_group_keys if column in run_metrics_df.columns]
    metric_columns = [
        column
        for column in run_metrics_df.columns
        if column not in {"run_id", *group_keys}
        and pd.api.types.is_numeric_dtype(run_metrics_df[column])
    ]

    grouped = run_metrics_df.groupby(group_keys, dropna=False)[metric_columns]
    mean_df = grouped.mean().reset_index()
    std_df = grouped.std(ddof=0).reset_index().fillna(0.0)

    renamed_mean = {
        column: f"{column}_mean"
        for column in mean_df.columns
        if column not in group_keys
    }
    renamed_std = {
        column: f"{column}_std"
        for column in std_df.columns
        if column not in group_keys
    }

    mean_df = mean_df.rename(columns=renamed_mean)
    std_df = std_df.rename(columns=renamed_std)
    summary_df = mean_df.merge(std_df, on=group_keys, how="left")
    return summary_df
