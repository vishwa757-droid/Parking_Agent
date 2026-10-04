"""Random traffic generation and traffic-car behavior."""

from dataclasses import dataclass, field
import random

from astar import astar
from config import (
    MAX_TRAFFIC_CARS,
    ROUTE_HISTORY_LENGTH,
    ALTERNATIVE_ROUTE_CHANCE,
    TRAFFIC_SPEED,
    TRAFFIC_COLORS,
    VISITOR_CHANCE,
    PARKED_TIME_MIN,
    PARKED_TIME_MAX,
    INITIAL_PARKED_CARS,
    INITIAL_PARKED_TIME_MIN,
    INITIAL_PARKED_TIME_MAX,
    MAX_WAIT_TIME,
)
from graphics import draw_car
from lanes import DIRECTIONS, direction, slots_held, entry_slots, vehicle_pose


def entry_slots_at_start(grid, route):
    """Slots a car occupies at the first cell of its route."""
    return grid.slots_for(route[0], None, direction(route[0], route[1]))


@dataclass
class TrafficCar:
    """
    phase:
      driving  - passing through, leaves by an entrance/exit
      arriving - heading to a parking bay
      parked   - sitting in its bay
      leaving  - driving from its bay to an exit
    """

    position: tuple[int, int]
    route: list[tuple[int, int]]
    color_index: int = 0
    route_index: int = 0
    progress: float = 0.0
    speed: float = TRAFFIC_SPEED
    route_signature: tuple = field(default_factory=tuple)
    phase: str = "driving"
    bay: tuple[int, int] | None = None
    dwell: float = 0.0
    waiting: bool = False
    wait_time: float = 0.0
    arrival: tuple[int, int] | None = None   # direction used to enter this cell

    def next_cell(self):
        if self.route_index + 1 < len(self.route):
            return self.route[self.route_index + 1]
        return None

    def at_end(self):
        return self.route_index >= len(self.route) - 1

    def held_slots(self, grid):
        return slots_held(
            grid, self.position, self.arrival,
            self.route, self.route_index, self.progress,
        )

    def update(self, dt, grid, blocked_slots):
        """Move toward the next cell if the lane slot there is free."""
        if self.at_end():
            return

        # Only check when starting a move; once moving, the slot is ours.
        if self.progress <= 0:
            needed = entry_slots(grid, self.position, self.route, self.route_index)
            if needed & blocked_slots:
                self.waiting = True
                self.wait_time += dt
                return

        self.waiting = False
        self.wait_time = 0.0
        self.progress += self.speed * dt

        if self.progress >= 1.0:
            self.arrival = direction(self.position, self.route[self.route_index + 1])
            self.route_index += 1
            self.position = self.route[self.route_index]
            self.progress = 0.0


class TrafficManager:
    """
    Creates unpredictable but valid traffic.

    Some cars drive straight through, others park in a free bay for a
    while and then leave. Route history is used as a penalty rather than
    a hard prohibition, because reachability must always win.
    """

    def __init__(self, grid, rng=None, agent=None):
        self.grid = grid
        self.rng = rng or random.Random()
        self.agent = agent

        self.cars = []
        self.route_history = []

        self.spawn_timer = 1.5

    # ------------------------------------------------ what others can see
    def held_slots(self, ignore=None):
        slots = set()
        for car in self.cars:
            if car is not ignore:
                slots |= car.held_slots(self.grid)
        return slots

    def occupied_cells(self):
        return {cell for cell, _ in self.held_slots()}

    def claimed_bays(self):
        """Bays that are taken, or that a car is on its way to."""
        return {
            car.bay
            for car in self.cars
            if car.bay is not None
            and (car.phase != "leaving" or car.position == car.bay)
        }

    def moving_cars(self):
        return [car for car in self.cars if car.phase != "parked"]

    def parked_cars(self):
        return [car for car in self.cars if car.phase == "parked"]

    # ------------------------------------------------------------ spawning
    def update(self, dt):
        self.spawn_timer -= dt

    def should_spawn(self):
        return (
            self.spawn_timer <= 0
            and len(self.moving_cars()) < MAX_TRAFFIC_CARS
        )

    def reset_spawn_timer(self, min_time, max_time):
        self.spawn_timer = self.rng.uniform(min_time, max_time)

    def seed_parked_cars(self, count=INITIAL_PARKED_CARS):
        """Start with some bays already taken."""
        bays = [space.position for space in self.grid.parking_spaces]

        for bay in self.rng.sample(bays, min(count, len(bays))):
            roads = [
                (bay[0] + dx, bay[1] + dy)
                for dx, dy in DIRECTIONS
                if self.grid.is_road((bay[0] + dx, bay[1] + dy))
            ]
            entry = self.rng.choice(roads)

            # The car "arrived" from the road cell, so it faces into the bay.
            self.cars.append(
                TrafficCar(
                    position=bay,
                    route=[entry, bay],
                    route_index=1,
                    arrival=direction(entry, bay),
                    color_index=self.rng.randrange(len(TRAFFIC_COLORS)),
                    phase="parked",
                    bay=bay,
                    dwell=self.rng.uniform(
                        INITIAL_PARKED_TIME_MIN, INITIAL_PARKED_TIME_MAX
                    ),
                )
            )

    def try_spawn(self):
        """Try to create one random traffic car."""
        if len(self.moving_cars()) >= MAX_TRAFFIC_CARS:
            return False

        busy = self.held_slots()
        if self.agent is not None:
            busy |= self.agent.held_slots()

        entrances = self.rng.sample(
            self.grid.entrances,
            len(self.grid.entrances)
        )

        for entrance in entrances:
            trip = self._plan_trip(entrance)
            if trip is None:
                continue

            route, phase, bay = trip

            # Do not appear on top of another car.
            if entry_slots_at_start(self.grid, route) & busy:
                continue

            car = TrafficCar(
                position=entrance,
                route=route,
                color_index=self.rng.randrange(len(TRAFFIC_COLORS)),
                route_signature=self._signature(route),
                phase=phase,
                bay=bay,
            )

            self.cars.append(car)
            self.route_history.append(car.route_signature)
            self.route_history = self.route_history[-ROUTE_HISTORY_LENGTH:]
            return True

        return False

    def _plan_trip(self, entrance):
        """Decide whether the new car parks or just drives through."""
        taken = self.claimed_bays()
        if self.agent is not None and self.agent.target is not None:
            taken.add(self.agent.target)

        free_bays = self.grid.free_parking_spaces(taken)

        if free_bays and self.rng.random() < VISITOR_CHANCE:
            bay = self.rng.choice(free_bays)
            route = self._choose_route(entrance, bay)
            if route:
                return route, "arriving", bay

        exits = [e for e in self.grid.entrances if e != entrance]
        route = self._choose_route(entrance, self.rng.choice(exits))
        if route:
            return route, "driving", None

        return None

    def _choose_route(self, start, destination):
        """
        Generate several valid routes by temporarily penalizing
        recently used cells/routes. The shortest route is still available.
        """
        candidates = []

        # First route: normal A*.
        route = astar(self.grid, start, destination)

        if route:
            candidates.append(route)

        # Alternative routes: block a few internal cells from previous
        # routes and try A* again. This produces genuine route variation.
        for _ in range(4):
            blocked = set()

            for old_route in self.route_history[-6:]:
                if len(old_route) > 4 and self.rng.random() < 0.65:
                    sample_size = min(2, len(old_route) - 2)
                    blocked.update(
                        self.rng.sample(old_route[1:-1], sample_size)
                    )

            alternative = astar(
                self.grid,
                start,
                destination,
                blocked=blocked,
            )

            if alternative:
                candidates.append(alternative)

        if not candidates:
            return []

        # Score route repetition.
        scored = []
        for candidate in candidates:
            signature = self._signature(candidate)
            repetition = self.route_history.count(signature)
            score = len(candidate) + repetition * 8

            # Sometimes choose a valid alternative instead of always
            # selecting the shortest route.
            if self.rng.random() < ALTERNATIVE_ROUTE_CHANCE:
                score += self.rng.uniform(0, 6)

            scored.append((score, candidate))

        scored.sort(key=lambda item: item[0])
        return scored[0][1]

    @staticmethod
    def _signature(route):
        """
        A route signature lets us recognize repeated route patterns.
        We include the full route for this small simulation.
        """
        return tuple(route)

    # -------------------------------------------------------------- moving
    def update_cars(self, dt):
        """Move all traffic cars, keeping lane slots free of collisions."""
        for car in list(self.cars):
            if car.phase == "parked":
                car.dwell -= dt
                if car.dwell <= 0:
                    self._start_leaving(car)
                continue

            blocked = self.held_slots(ignore=car)
            if self.agent is not None:
                blocked |= self.agent.held_slots()

            car.update(dt, self.grid, blocked)

            if car.at_end():
                if car.phase == "arriving":
                    car.phase = "parked"
                    car.dwell = self.rng.uniform(
                        PARKED_TIME_MIN, PARKED_TIME_MAX
                    )
                else:
                    # Reached the exit.
                    self.cars.remove(car)

            elif car.wait_time > MAX_WAIT_TIME:
                # Stuck for too long (safety net against gridlock).
                self.cars.remove(car)

    def _start_leaving(self, car):
        exit_cell = self.rng.choice(self.grid.entrances)
        route = astar(self.grid, car.position, exit_cell)

        if not route:
            car.dwell = 1.0  # try again shortly
            return

        car.route = route
        car.route_index = 0
        car.progress = 0.0
        car.phase = "leaving"
        car.arrival = None
        car.waiting = False
        car.wait_time = 0.0

    def draw(self, screen, cell_size):
        for car in self.cars:
            x, y, angle = vehicle_pose(
                self.grid, car.position, car.arrival, car.route,
                car.route_index, car.progress,
            )
            color = TRAFFIC_COLORS[car.color_index % len(TRAFFIC_COLORS)]
            draw_car(screen, cell_size, (x, y), angle, color)
