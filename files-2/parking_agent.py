"""Autonomous parking agent."""

from astar import astar
from config import AGENT_SPEED, REPLAN_COOLDOWN, AGENT_COLOR, PATH_COLOR
from graphics import draw_car, draw_path_dots
from lanes import slots_held, entry_slots, direction, vehicle_pose, route_points


class ParkingAgent:
    """
    The autonomous vehicle.

    It selects a free parking space, plans with A*, detects traffic
    blocking its path, and re-plans when required.
    """

    def __init__(self, grid):
        self.grid = grid
        self.position = grid.entrances[0]

        self.route = []
        self.route_index = 0
        self.progress = 0.0

        self.target = None
        self.replan_timer = 0.0
        self.replan_count = 0
        self.parked = False
        self.waiting = False
        self.arrival = None   # direction used to enter the current cell

    def reset(self):
        self.position = self.grid.entrances[0]
        self.route = []
        self.route_index = 0
        self.progress = 0.0
        self.target = None
        self.replan_timer = 0.0
        self.replan_count = 0
        self.parked = False
        self.waiting = False
        self.arrival = None

    def perceive(self, traffic_positions):
        """Return the traffic cells currently perceived by the agent."""
        return set(traffic_positions)

    def choose_parking_space(self, occupied_cells):
        """Select a free parking space."""
        spaces = self.grid.free_parking_spaces(occupied_cells)

        if not spaces:
            return None

        # Select the closest available parking space.
        spaces.sort(
            key=lambda p: abs(p[0] - self.position[0])
            + abs(p[1] - self.position[1])
        )

        return spaces[0]

    def plan_route(self, blocked_cells, traffic_slots=frozenset()):
        if self.target is None:
            return False

        # Do not block the target itself.
        blocked = set(blocked_cells)
        blocked.discard(self.target)

        route = astar(
            self.grid,
            self.position,
            self.target,
            blocked=blocked,
        )

        if not route:
            return False

        # Do not switch to a route whose first move needs lane space in
        # our own cell that another car is using.
        if len(route) > 1:
            first_move = direction(route[0], route[1])
            if self.grid.slots_for(self.position, self.arrival, first_move) & traffic_slots:
                return False

        self.route = route
        self.route_index = 0
        self.progress = 0.0
        return True

    def held_slots(self):
        """Lane slots this vehicle occupies (other cars must keep clear)."""
        return slots_held(
            self.grid, self.position, self.arrival,
            self.route, self.route_index, self.progress,
        )

    def route_blocked_ahead(self, traffic_slots, look_ahead=3):
        """Is traffic sitting in a lane slot we are about to need?"""
        last = min(self.route_index + 1 + look_ahead, len(self.route))
        for i in range(self.route_index + 1, last):
            arrive = direction(self.route[i - 1], self.route[i])
            leave = None
            if i + 1 < len(self.route):
                leave = direction(self.route[i], self.route[i + 1])

            if self.grid.slots_for(self.route[i], arrive, leave) & traffic_slots:
                return True
        return False

    def update(self, dt, traffic_positions, occupied_parking_spaces,
               traffic_slots=frozenset()):
        self.waiting = False

        if self.parked:
            return

        self.replan_timer = max(0, self.replan_timer - dt)

        # First decision: choose a parking destination.
        if self.target is None:
            self.target = self.choose_parking_space(
                occupied_parking_spaces
            )
            if self.target is None:
                return

            self.plan_route(traffic_positions)

        # Feedback: detect whether traffic blocks our current route.
        # Re-planning only happens at a cell centre, so the car never
        # jumps backwards.
        if self.route and self.progress <= 0 and self.replan_timer <= 0:
            if self.route_blocked_ahead(traffic_slots):
                self.replan_timer = REPLAN_COOLDOWN
                if self.plan_route(traffic_positions, traffic_slots):
                    self.replan_count += 1

        # If no route exists, try again after a short delay.
        if not self.route:
            if self.replan_timer <= 0:
                self.replan_timer = REPLAN_COOLDOWN
                self.plan_route(traffic_positions, traffic_slots)
            return

        # Arrived?
        if self.route_index + 1 >= len(self.route):
            self.parked = True
            return

        # Only start moving when the lane slot ahead is free.
        if self.progress <= 0:
            needed = entry_slots(
                self.grid, self.position, self.route, self.route_index
            )
            if needed & traffic_slots:
                self.waiting = True
                return

        self.progress += AGENT_SPEED * dt

        if self.progress >= 1.0:
            self.arrival = direction(self.position, self.route[self.route_index + 1])
            self.route_index += 1
            self.position = self.route[self.route_index]
            self.progress = 0.0

            if self.position == self.target:
                self.parked = True

    def draw(self, screen, cell_size):
        x, y, angle = vehicle_pose(
            self.grid, self.position, self.arrival, self.route,
            self.route_index, self.progress,
        )

        # Planned route as a dotted line, from the car onwards.
        if self.route and not self.parked:
            points = [(x, y)] + route_points(
                self.grid, self.route, self.route_index + 1
            )
            draw_path_dots(screen, points, PATH_COLOR)

        draw_car(screen, cell_size, (x, y), angle, AGENT_COLOR, sensor=True)
