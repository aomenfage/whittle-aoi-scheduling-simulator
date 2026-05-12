from __future__ import annotations

import unittest

from env.aoi_env import AoIEnv
from env.channel import Channel
from env.source import Source


class AoIEnvTestCase(unittest.TestCase):
    def test_successful_update_resets_scheduled_aoi(self) -> None:
        sources = [
            Source(source_id=0, weight=1.0, sampling_rate=1.0, initial_aoi=3),
            Source(source_id=1, weight=2.0, sampling_rate=1.0, initial_aoi=2),
        ]
        env = AoIEnv(sources=sources, channel=Channel(success_prob=1.0), seed=1)
        env.reset()
        result = env.step(action=0)

        self.assertEqual(sources[0].aoi, 1)
        self.assertEqual(sources[1].aoi, 3)
        self.assertAlmostEqual(result["weighted_aoi"], 7.0)

    def test_failed_update_increments_all_aoi(self) -> None:
        sources = [
            Source(source_id=0, weight=1.0, sampling_rate=1.0, initial_aoi=2),
            Source(source_id=1, weight=1.0, sampling_rate=1.0, initial_aoi=4),
        ]
        env = AoIEnv(sources=sources, channel=Channel(success_prob=0.0), seed=1)
        env.reset()
        env.step(action=0)

        self.assertEqual(sources[0].aoi, 3)
        self.assertEqual(sources[1].aoi, 5)

    def test_invalid_action_raises(self) -> None:
        env = AoIEnv(
            sources=[Source(source_id=0, weight=1.0, sampling_rate=1.0)],
            channel=Channel(success_prob=1.0),
            seed=1,
        )
        env.reset()
        with self.assertRaises(ValueError):
            env.step(action=99)


if __name__ == "__main__":
    unittest.main()
