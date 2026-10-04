"""Main simulation coordinator."""

import random

from config import (
    MIN_SPAWN_TIME,
    MAX_SPAWN_TIME,
    DEFAULT_SEED,
)
from grid import ParkingLot
from parking_agent import ParkingAgent
from traffic import TrafficManager


class Simulation:
    """Connects the environment, traffic, and autonomous agent."""

    def __init__(self, seed=DEFAULT_SEED):
        self.seed = seed
        self._build()

    def _build(self):
        self.rng = random.Random(self.seed)

        self.grid = ParkingLot()
        self.agent = ParkingAgent(self.grid)
        self.traffic = TrafficManager(self.grid, self.rng, agent=self.agent)
        self.traffic.seed_parked_cars()

        self.paused = False
        self.total_time = 0.0

    def reset(self, seed=None):
        if seed is not None:
            self.seed = seed

        self._build()

    def update(self, dt):
        if self.paused:
            return

        self.total_time += dt

        # Spawn cars at random intervals.
        self.traffic.update(dt)

        if self.traffic.should_spawn():
            self.traffic.try_spawn()
            self.traffic.reset_spawn_timer(
                MIN_SPAWN_TIME,
                MAX_SPAWN_TIME,
            )

        # Move traffic.
        self.traffic.update_cars(dt)

        # Agent perceives the current traffic and the taken parking bays.
        traffic_positions = self.traffic.occupied_cells()
        taken_bays = self.traffic.claimed_bays()

        # Agent reasons and acts.
        self.agent.update(
            dt,
            traffic_positions,
            occupied_parking_spaces=taken_bays,
            traffic_slots=self.traffic.held_slots(),
        )

    def add_random_car(self):
        """Manual test button: create one traffic car immediately."""
        self.traffic.try_spawn()

    def new_random_seed(self):
        """Generate a new seed and reset the whole scenario."""
        self.seed = random.randrange(1, 1_000_000)
        self.reset(self.seed)

    def statistics(self):
        return {
            "time": self.total_time,
            "traffic_cars": len(self.traffic.moving_cars()),
            "parked_cars": len(self.traffic.parked_cars()),
            "replans": self.agent.replan_count,
            "parked": self.agent.parked,
            "target": self.agent.target,
        }
