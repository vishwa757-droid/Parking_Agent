# Autonomous Parking Agent

A simple, understandable Python + Pygame simulation of an autonomous parking agent.

The project demonstrates:

Perceive → Analyze → Search → Decide → Move → Detect Changes → Re-route → Park

## Features

- Autonomous parking agent uses A* pathfinding.
- Random traffic cars spawn from multiple entrances.
- Traffic cars choose different destinations and routes.
- Route history discourages repeated traffic routes.
- Traffic cars become dynamic obstacles.
- The parking agent re-plans when traffic blocks its route.
- Two-lane roads: cars heading in opposite directions pass each other
  (left-hand traffic; set `DRIVE_ON_LEFT = False` in `config.py` for right-hand).
- Collision avoidance: cars reserve the lane space they are moving into
  (see `lanes.py`), and never block a junction they cannot leave.
- Traffic cars either drive through or park in a free bay for a while,
  and some bays are already taken when the simulation starts.
- Configurable traffic settings.
- Reproducible scenarios with a random seed.
- Simple visual interface.

## Requirements

Python 3.10+ and Pygame.

Install:

```bash
pip install -r requirements.txt   # installs pygame-ce, which works on new Python versions too
```

Run:

```bash
python main.py
```

## Controls

- `R` = reset simulation
- `Space` = pause/unpause
- `N` = create one random traffic car
- `S` = change random seed
- `Esc` = quit

## Project structure

```text
autonomous_parking_agent/
│
├── main.py                 # Starts the simulation
├── config.py               # Easy-to-change settings
├── grid.py                 # Parking-lot road/grid layout
├── astar.py                # A* pathfinding
├── traffic.py              # Random traffic generation and movement
├── lanes.py                # Lane and collision-avoidance rules
├── graphics.py             # Car sprites and drawing helpers
├── parking_agent.py        # Autonomous parking agent
├── simulation.py           # Main simulation coordinator
├── requirements.txt
└── README.md
```

The code intentionally avoids machine learning. It uses classical AI techniques, especially state-space representation, A*, rule-based decisions, and dynamic re-planning.
