import pygame
from ENVIRONMENT.map_builder import (
    build_platforms,
    STARTING_MAP,
    MAP_ORIGIN_X,
    MAP_ORIGIN_Y,
)
from DATA.constants import TILE

# Start with all tile-based platforms from the ASCII map
platforms = build_platforms()

# Hand-placed detail rects appended on top — add/remove freely
platforms += [
    # --- Starting area ---
    pygame.Rect(0, 1200 - 40, 4000, 40),
    pygame.Rect(-1000, -2000, 1000, 4000),
    pygame.Rect(300, 1090, 200, 20),
    pygame.Rect(600, 1000, 180, 20),
    pygame.Rect(900, 950, 220, 20),
    pygame.Rect(600, 900, 160, 20),
    pygame.Rect(700, 770, 200, 20),
    pygame.Rect(1100, 750, 240, 20),
    pygame.Rect(1300, 1200 - 150, 300, 20),
    pygame.Rect(2000, 1090 - 390, 1400, 400),
]


def get_spawn():
    """
    Returns (feet_x, feet_y) — one tile above the first '#' in the bottom
    row of the map, so the player always starts standing on the floor.
    You can override this with a fixed coordinate if you prefer.
    """
    rows = STARTING_MAP
    for row_i in range(len(rows) - 1, -1, -1):
        for col_i, char in enumerate(rows[row_i]):
            if char == "#":
                floor_top_y = MAP_ORIGIN_Y + row_i * TILE
                spawn_x = float(MAP_ORIGIN_X + col_i * TILE + TILE // 2)
                spawn_y = float(floor_top_y)  # feet sit on top of the tile
                return spawn_x, spawn_y
    # Fallback if map is empty
    return 100.0, 1000.0
