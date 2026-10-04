"""Lane rules and vehicle positions, shared by traffic cars and the agent.

Roads are one grid cell wide but carry two lanes, so two cars driving in
opposite directions can pass each other inside the same cell.

To avoid crashes, every vehicle holds "slots":
  * on a straight piece of road a slot is (cell, travel direction), a lane
  * at junctions and bends a slot is just (cell, None), so only one
    vehicle can be there at a time
  * a car turning into or out of a parking bay takes both lanes
A vehicle only starts moving into a cell when all the slots it needs there
are free, and it keeps them reserved while it is on its way in.
"""

from config import CELL_SIZE, LANE_OFFSET, DRIVE_ON_LEFT

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# Sprite rotation (degrees, counter-clockwise) for each travel direction.
SETTLE_SPEED = 3.0   # how fast a turning car moves across into its lane
TURN_AT = 0.12       # progress at which a turning car rotates to its new heading

ANGLES = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}


def direction(a, b):
    return (b[0] - a[0], b[1] - a[1])


def slots_held(grid, position, arrival, route, index, progress):
    """
    Slots a vehicle occupies: its own cell, plus the cell it is entering.
    `arrival` is the direction it travelled to get into its current cell.

    A vehicle in (or entering) a junction also keeps the slots it needs to
    leave it, so it can never get stuck in the middle of a junction.
    """
    leave = None
    if route and index + 1 < len(route):
        leave = direction(position, route[index + 1])

    slots = set(grid.slots_for(position, arrival, leave))

    if leave is None:
        return slots

    nxt = route[index + 1]
    after = None
    if index + 2 < len(route):
        after = direction(nxt, route[index + 2])
    exit_slots = grid.slots_for(nxt, leave, after)

    # Sitting in a road junction: keep the way out reserved.
    if grid.is_road(position) and position not in grid.axis:
        slots |= exit_slots

    # Moving into the next cell.
    if progress > 0:
        slots |= exit_slots
        if after is not None and grid.is_road(nxt) and nxt not in grid.axis:
            beyond = route[index + 2]
            following = None
            if index + 3 < len(route):
                following = direction(beyond, route[index + 3])
            slots |= grid.slots_for(beyond, after, following)

    return slots


def entry_slots(grid, position, route, index):
    """Slots that must all be free before the vehicle may enter the next cell."""
    if not route or index + 1 >= len(route):
        return set()

    nxt = route[index + 1]
    after = None
    if index + 2 < len(route):
        after = direction(nxt, route[index + 2])

    slots = set(grid.slots_for(nxt, direction(position, nxt), after))

    # Do not stop inside a junction: only enter it if we can also get out.
    if after is not None and grid.is_road(nxt) and nxt not in grid.axis:
        beyond = route[index + 2]
        following = None
        if index + 3 < len(route):
            following = direction(beyond, route[index + 3])
        slots |= grid.slots_for(beyond, after, following)

    return slots


def lane_point(grid, cell, travel):
    """Pixel position of a vehicle travelling in direction `travel` in `cell`."""
    x = (cell[0] + 0.5) * CELL_SIZE
    y = (cell[1] + 0.5) * CELL_SIZE

    # Parking bays have no lanes: the car sits in the middle.
    if travel is not None and grid.is_road(cell):
        left = (travel[1], -travel[0])
        side = 1 if DRIVE_ON_LEFT else -1
        x += side * left[0] * LANE_OFFSET
        y += side * left[1] * LANE_OFFSET

    return x, y


def vehicle_pose(grid, position, arrival, route, index, progress):
    """
    (x, y, sprite angle) of a vehicle.

    A car rests in the lane it arrived in. When it moves on, it slides
    toward the lane position in the next cell, so it stays in its own
    lane until it reaches a junction and only then swings across.
    """
    leave = None
    if route and index + 1 < len(route):
        leave = direction(position, route[index + 1])

    face = arrival if arrival is not None else leave
    x, y = lane_point(grid, position, face)

    if leave is not None and progress > 0:
        nx, ny = lane_point(grid, route[index + 1], leave)

        # Move along the road steadily, but settle into the new lane
        # quickly so a turning car clears the lane it is leaving.
        settle = min(1.0, progress * SETTLE_SPEED)
        if leave[1] == 0:      # travelling horizontally
            x += (nx - x) * progress
            y += (ny - y) * settle
        else:                  # travelling vertically
            x += (nx - x) * settle
            y += (ny - y) * progress

        # Turn the car's nose a moment after it starts to move.
        if arrival is None or progress >= TURN_AT:
            face = leave

    return x, y, ANGLES.get(face, 0)


def route_points(grid, route, start):
    """Pixel points along the driving lane for route[start:] (start >= 1)."""
    return [
        lane_point(grid, route[i], direction(route[i - 1], route[i]))
        for i in range(start, len(route))
    ]
