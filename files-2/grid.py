"""Parking-lot layout and grid utilities."""

from dataclasses import dataclass
from typing import Iterable

import pygame

from config import (
    CELL_SIZE, GRID_COLS, GRID_ROWS,
    ROAD_COLOR, ROAD_EDGE_COLOR, LANE_MARK_COLOR,
    GRASS_COLOR, GRASS_ALT_COLOR,
    SLOT_COLOR, SLOT_LINE_COLOR, SLOT_TEXT_COLOR,
    TARGET_SLOT_COLOR, TARGET_LINE_COLOR,
    TREE_SHADOW_COLOR, TREE_DARK_COLOR, TREE_LIGHT_COLOR,
    TREE_HIGHLIGHT_COLOR,
    GATE_RED, GATE_WHITE,
)

from lanes import DIRECTIONS


@dataclass(frozen=True)
class ParkingSpace:
    position: tuple[int, int]
    occupied: bool = False


class ParkingLot:
    """Creates a simple road network with parking spaces and entrances."""

    def __init__(self):
        self.cols = GRID_COLS
        self.rows = GRID_ROWS

        self.road_cells = set()
        self.obstacles = set()
        self.entrances = []
        self.parking_spaces = []
        self.axis = {}
        self._font = None

        self._build_layout()

    def _build_layout(self):
        # Horizontal roads.
        horizontal_rows = [2, 6, 10, 13]
        for y in horizontal_rows:
            for x in range(1, self.cols - 1):
                self.road_cells.add((x, y))

        # Vertical roads.
        vertical_cols = [2, 7, 12, 17, 20]
        for x in vertical_cols:
            for y in range(1, self.rows - 1):
                self.road_cells.add((x, y))

        # Entrances/exits on the boundary.
        self.entrances = [
            (0, 2),
            (self.cols - 1, 6),
            (0, 10),
            (self.cols - 1, 13),
        ]

        # Connect entrances to nearby road cells.
        for entrance in self.entrances:
            x, y = entrance
            if x == 0:
                self.road_cells.add((x, y))
                self.road_cells.add((x + 1, y))
            else:
                self.road_cells.add((x, y))
                self.road_cells.add((x - 1, y))

        # Parking spaces sit beside roads. A bay is only created when a
        # road touches it, otherwise no car could ever drive into it.
        for x in range(3, 20, 2):
            for y in [4, 8, 12]:
                if (x, y) in self.road_cells:
                    continue
                touches_road = any(
                    (x + dx, y + dy) in self.road_cells
                    for dx, dy in DIRECTIONS
                )
                if touches_road:
                    self.parking_spaces.append(ParkingSpace((x, y)))

        # A few fixed obstacles.
        self.obstacles = {
            (5, 5), (6, 5),
            (14, 5), (15, 5),
            (9, 11), (10, 11),
        }

        # Never make an obstacle a road.
        self.road_cells -= self.obstacles

        self._find_junctions()

    def _find_junctions(self):
        """
        Work out which road cells are straight pieces with two lanes.
        Everything else (junctions, bends, dead ends) holds one vehicle
        at a time.
        """
        self.axis = {}

        for x, y in self.road_cells:
            links = {
                d for d in DIRECTIONS
                if (x + d[0], y + d[1]) in self.road_cells
            }
            # Entrances only link to one road cell but are still straight.
            through = len(links) == 2 or (x, y) in self.entrances

            if through and links <= {(1, 0), (-1, 0)}:
                self.axis[(x, y)] = (1, 0)
            elif through and links <= {(0, 1), (0, -1)}:
                self.axis[(x, y)] = (0, 1)

    def slots_for(self, cell, arrive, leave):
        """
        Slots a vehicle needs in `cell`, given the direction it arrives
        with and the direction it leaves with (either may be None).
        """
        axis = self.axis.get(cell)

        if axis is None:
            return {(cell, None)}

        lanes = {axis, (-axis[0], -axis[1])}
        moves = {d for d in (arrive, leave) if d is not None}

        # Driving along the road: just one lane.
        if len(moves) == 1 and moves <= lanes:
            return {(cell, next(iter(moves)))}

        # Turning, or crossing the road to/from a bay: block both lanes.
        return {(cell, d) for d in lanes}

    def is_inside(self, cell):
        x, y = cell
        return 0 <= x < self.cols and 0 <= y < self.rows

    def is_road(self, cell):
        return cell in self.road_cells

    def is_obstacle(self, cell):
        return cell in self.obstacles

    def neighbors(self, cell, goal=None):
        """
        Cells a vehicle can move to from `cell`.

        Vehicles drive on road cells. The only non-road cell they may
        enter is the parking space they are heading for (`goal`).
        """
        x, y = cell
        candidates = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]

        return [
            p for p in candidates
            if self.is_inside(p) and (self.is_road(p) or p == goal)
        ]

    def free_parking_spaces(self, occupied_positions: Iterable[tuple[int, int]]):
        occupied = set(occupied_positions)
        return [
            space.position
            for space in self.parking_spaces
            if space.position not in occupied
        ]

    # ------------------------------------------------------------ drawing
    def draw(self, screen, target=None):
        """Draw the whole lot. `target` is the agent's chosen parking space."""
        self._draw_ground(screen)
        self._draw_road_markings(screen)
        self._draw_parking_spaces(screen, target)
        self._draw_gates(screen)
        self._draw_trees(screen)

    def _draw_ground(self, screen):
        cs = CELL_SIZE
        for y in range(self.rows):
            for x in range(self.cols):
                if (x, y) in self.road_cells:
                    color = ROAD_COLOR
                else:
                    # Two very similar greens give the grass some texture.
                    color = GRASS_COLOR if (x + y) % 2 == 0 else GRASS_ALT_COLOR
                pygame.draw.rect(screen, color, (x * cs, y * cs, cs, cs))

    def _draw_road_markings(self, screen):
        cs = CELL_SIZE
        spaces = {space.position for space in self.parking_spaces}

        for x, y in self.road_cells:
            left, top = x * cs, y * cs

            # Kerb line wherever the road meets grass.
            for dx, dy in DIRECTIONS:
                n = (x + dx, y + dy)
                if (n in self.road_cells or n in spaces
                        or not self.is_inside(n)):
                    continue

                if dx == 1:
                    a, b = (left + cs - 1, top), (left + cs - 1, top + cs)
                elif dx == -1:
                    a, b = (left + 1, top), (left + 1, top + cs)
                elif dy == 1:
                    a, b = (left, top + cs - 1), (left + cs, top + cs - 1)
                else:
                    a, b = (left, top + 1), (left + cs, top + 1)
                pygame.draw.line(screen, ROAD_EDGE_COLOR, a, b, 2)

            # Dashed centre line on straight road sections.
            horizontal = ((x - 1, y) in self.road_cells
                          and (x + 1, y) in self.road_cells)
            vertical = ((x, y - 1) in self.road_cells
                        and (x, y + 1) in self.road_cells)
            cx, cy = left + cs // 2, top + cs // 2

            if horizontal and not vertical:
                pygame.draw.line(
                    screen, LANE_MARK_COLOR, (cx - 9, cy), (cx + 9, cy), 2
                )
            elif vertical and not horizontal:
                pygame.draw.line(
                    screen, LANE_MARK_COLOR, (cx, cy - 9), (cx, cy + 9), 2
                )

    def _draw_parking_spaces(self, screen, target):
        cs = CELL_SIZE

        if self._font is None:
            self._font = pygame.font.Font(None, 24)

        for space in self.parking_spaces:
            x, y = space.position
            left, top = x * cs, y * cs
            is_target = space.position == target

            fill = TARGET_SLOT_COLOR if is_target else SLOT_COLOR
            line = TARGET_LINE_COLOR if is_target else SLOT_LINE_COLOR
            pygame.draw.rect(screen, fill, (left, top, cs, cs))

            # Paint lines on every side except the one facing the road.
            for dx, dy in DIRECTIONS:
                if (x + dx, y + dy) in self.road_cells:
                    continue

                if dx == 1:
                    a, b = (left + cs - 3, top + 2), (left + cs - 3, top + cs - 2)
                elif dx == -1:
                    a, b = (left + 2, top + 2), (left + 2, top + cs - 2)
                elif dy == 1:
                    a, b = (left + 2, top + cs - 3), (left + cs - 2, top + cs - 3)
                else:
                    a, b = (left + 2, top + 2), (left + cs - 2, top + 2)
                pygame.draw.line(screen, line, a, b, 2)

            # A faint "P" marks the bay (brighter for the chosen one).
            label_color = TARGET_LINE_COLOR if is_target else SLOT_TEXT_COLOR
            label = self._font.render("P", True, label_color)
            screen.blit(
                label,
                label.get_rect(center=(left + cs // 2, top + cs // 2)),
            )

    def _draw_gates(self, screen):
        """Red/white barrier at each entrance."""
        cs = CELL_SIZE
        for x, y in self.entrances:
            bar_x = x * cs if x == 0 else x * cs + cs - 5
            stripe = (cs - 8) // 4
            for i in range(4):
                color = GATE_RED if i % 2 == 0 else GATE_WHITE
                pygame.draw.rect(
                    screen, color, (bar_x, y * cs + 4 + i * stripe, 5, stripe)
                )

    def _draw_trees(self, screen):
        """The fixed obstacles are drawn as small trees."""
        cs = CELL_SIZE
        for x, y in self.obstacles:
            cx, cy = x * cs + cs // 2, y * cs + cs // 2
            pygame.draw.circle(screen, TREE_SHADOW_COLOR, (cx + 3, cy + 4), 16)
            pygame.draw.circle(screen, TREE_DARK_COLOR, (cx, cy), 16)
            pygame.draw.circle(screen, TREE_LIGHT_COLOR, (cx - 2, cy - 2), 11)
            pygame.draw.circle(
                screen, TREE_HIGHLIGHT_COLOR, (cx - 5, cy - 5), 4
            )
