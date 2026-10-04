"""Central configuration for the parking simulation."""

# Grid
CELL_SIZE = 40
GRID_COLS = 22
GRID_ROWS = 15

# Window: the parking lot on the left, an info panel on the right.
PANEL_WIDTH = 240
SCREEN_WIDTH = GRID_COLS * CELL_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = GRID_ROWS * CELL_SIZE
FPS = 60

# Traffic
MAX_TRAFFIC_CARS = 10          # cars driving at the same time (parked cars not counted)
MIN_SPAWN_TIME = 1.0
MAX_SPAWN_TIME = 3.5
MIN_CAR_DISTANCE = 1.2
ROUTE_HISTORY_LENGTH = 12
ALTERNATIVE_ROUTE_CHANCE = 0.35

# Lanes: every road has two lanes, so opposite cars can pass each other.
LANE_OFFSET = 10          # pixels from the road centre to the middle of a lane
DRIVE_ON_LEFT = True      # set to False for right-hand traffic

# Parking behaviour of traffic cars
VISITOR_CHANCE = 0.45             # chance a new car comes to park (else it drives through)
PARKED_TIME_MIN = 6.0             # seconds a visitor stays parked
PARKED_TIME_MAX = 14.0
INITIAL_PARKED_CARS = 6           # bays that are already taken when the simulation starts
INITIAL_PARKED_TIME_MIN = 20.0
INITIAL_PARKED_TIME_MAX = 60.0
MAX_WAIT_TIME = 10.0              # a traffic car stuck this long gives up and leaves

# Autonomous agent
AGENT_SPEED = 3.0
TRAFFIC_SPEED = 2.0
REPLAN_COOLDOWN = 0.35

# Reproducibility
DEFAULT_SEED = None  # Set to an integer, e.g. 42, to reproduce a scenario.

# ---------------------------------------------------------------- Colors
# Lot
ROAD_COLOR = (58, 61, 68)
ROAD_EDGE_COLOR = (120, 124, 132)
LANE_MARK_COLOR = (200, 180, 90)
GRASS_COLOR = (72, 110, 72)
GRASS_ALT_COLOR = (76, 116, 76)
WALL_COLOR = (35, 35, 38)

# Parking bays
SLOT_COLOR = (66, 70, 78)
SLOT_LINE_COLOR = (225, 225, 225)
SLOT_TEXT_COLOR = (120, 125, 134)
TARGET_SLOT_COLOR = (44, 98, 62)
TARGET_LINE_COLOR = (120, 235, 145)

# Trees (the fixed obstacles)
TREE_SHADOW_COLOR = (52, 86, 54)
TREE_DARK_COLOR = (36, 82, 46)
TREE_LIGHT_COLOR = (60, 120, 62)
TREE_HIGHLIGHT_COLOR = (92, 150, 88)

# Gates
GATE_RED = (210, 60, 55)
GATE_WHITE = (235, 235, 235)

# Cars and path
AGENT_COLOR = (50, 150, 255)
TRAFFIC_COLOR = (225, 90, 75)
TRAFFIC_COLORS = [
    (225, 90, 75),
    (240, 190, 60),
    (232, 232, 235),
    (130, 135, 148),
    (160, 105, 205),
]
PATH_COLOR = (120, 195, 255)
BLOCKED_COLOR = (220, 80, 80)

# UI panel
TEXT_COLOR = (235, 235, 235)
MUTED_TEXT_COLOR = (130, 136, 148)
PANEL_COLOR = (30, 33, 38)
PANEL_LINE_COLOR = (58, 62, 70)
KEY_COLOR = (48, 52, 60)
ACCENT_COLOR = (90, 175, 255)
PARKING_COLOR = (205, 180, 90)
FREE_PARKING_COLOR = (100, 180, 105)
