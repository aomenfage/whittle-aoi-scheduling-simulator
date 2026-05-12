from __future__ import annotations

import unittest

import pandas as pd

from env.source import Source
from utils.metrics import aggregate_run_metrics, compute_run_metrics


class MetricsTestCase(unittest.TestCase):
    def test_compute_run_metrics(self) -> None:
        history_df = pd.DataFrame(
            [
                {"slot": 1, "weighted_aoi": 5.0, "aoi_0": 1, "aoi_1": 2},
                {"slot": 2, "weighted_aoi": 7.0, "aoi_0": 2, "aoi_1": 3},
                {"slot": 3, "weighted_aoi": 9.0, "aoi_0": 3, "aoi_1": 4},
            ]
        )
        sources = [
            Source(source_id=0, weight=1.0, sampling_rate=1.0),
            Source(source_id=1, weight=3.0, sampling_rate=1.0),
        ]

        metrics = compute_run_metrics(
            history_df=history_df,
            sources=sources,
            strategy_name="unit_test",
            high_weight_threshold=2.0,
        )

        self.assertAlmostEqual(metrics["average_weighted_aoi"], 7.0)
        self.assertAlmostEqual(metrics["avg_aoi_0"], 2.0)
        self.assertAlmostEqual(metrics["avg_aoi_1"], 3.0)
        self.assertAlmostEqual(metrics["peak_aoi_1"], 4.0)
        self.assertAlmostEqual(metrics["high_weight_avg_aoi"], 3.0)

    def test_aggregate_run_metrics(self) -> None:
        df = pd.DataFrame(
            [
                {"experiment_name": "exp", "scenario_name": "s1", "strategy": "a", "run_id": 0, "average_weighted_aoi": 10.0},
                {"experiment_name": "exp", "scenario_name": "s1", "strategy": "a", "run_id": 1, "average_weighted_aoi": 14.0},
            ]
        )
        summary_df = aggregate_run_metrics(df)
        self.assertEqual(len(summary_df), 1)
        self.assertAlmostEqual(float(summary_df.iloc[0]["average_weighted_aoi_mean"]), 12.0)
        self.assertAlmostEqual(float(summary_df.iloc[0]["average_weighted_aoi_std"]), 2.0)


if __name__ == "__main__":
    unittest.main()
