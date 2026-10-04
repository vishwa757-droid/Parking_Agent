"""A* pathfinding for the parking-lot grid."""

import heapq


def manhattan(a, b):
    """Estimate distance between two grid cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal, blocked=None):
    """
    Find a safe path from start to goal.

    blocked is a set of cells temporarily occupied by traffic.
    Returns a list including start and goal, or [] if no route exists.
    """
    blocked = blocked or set()

    if start == goal:
        return [start]

    if goal in blocked:
        return []

    open_heap = []
    heapq.heappush(open_heap, (0, start))

    came_from = {}
    cost_so_far = {start: 0}

    while open_heap:
        _, current = heapq.heappop(open_heap)

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in grid.neighbors(current, goal):
            if neighbor in blocked and neighbor != goal:
                continue

            new_cost = cost_so_far[current] + 1

            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost

                # Small deterministic heuristic.
                priority = new_cost + manhattan(neighbor, goal)

                came_from[neighbor] = current
                heapq.heappush(open_heap, (priority, neighbor))

    return []


def reconstruct_path(came_from, current):
    path = [current]

    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path
