from __future__ import annotations

import unittest

from algorithms.greedy import GreedyScheduler
from algorithms.periodic import PeriodicScheduler
from algorithms.random_scheduler import RandomScheduler
from algorithms.round_robin import RoundRobinScheduler
from algorithms.whittle import WhittleScheduler
from env.aoi_env import AoIEnv
from env.channel import Channel
from env.source import Source


def build_test_env() -> AoIEnv:
    sources = [
        Source(source_id=0, weight=1.0, sampling_rate=1.0, initial_aoi=2),
        Source(source_id=1, weight=3.0, sampling_rate=1.0, initial_aoi=3),
        Source(source_id=2, weight=2.0, sampling_rate=1.0, initial_aoi=4),
    ]
    env = AoIEnv(sources=sources, channel=Channel(success_prob={0: 0.9, 1: 0.8, 2: 0.7}), seed=1)
    env.reset()
    return env


class SchedulerInterfaceTestCase(unittest.TestCase):
    def test_round_robin_cycles(self) -> None:
        scheduler = RoundRobinScheduler(source_ids=[0, 1, 2])
        self.assertEqual(scheduler.select_action(), 0)
        self.assertEqual(scheduler.select_action(), 1)
        self.assertEqual(scheduler.select_action(), 2)
        self.assertEqual(scheduler.select_action(), 0)

    def test_periodic_respects_pattern(self) -> None:
        scheduler = PeriodicScheduler(pattern=[2, 2, 1])
        self.assertEqual([scheduler.select_action() for _ in range(4)], [2, 2, 1, 2])

    def test_greedy_returns_valid_source(self) -> None:
        env = build_test_env()
        action = GreedyScheduler().select_action(env)
        self.assertIn(action, [0, 1, 2])
        self.assertEqual(action, 1)

    def test_random_scheduler_returns_valid_source(self) -> None:
        env = build_test_env()
        action = RandomScheduler(source_ids=[0, 1, 2]).select_action(env)
        self.assertIn(action, [0, 1, 2])

    def test_whittle_scheduler_returns_valid_source(self) -> None:
        env = build_test_env()
        scheduler = WhittleScheduler(sources=env.sources, channel=env.channel, a_max=8)
        action = scheduler.select_action(env)
        self.assertIn(action, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
