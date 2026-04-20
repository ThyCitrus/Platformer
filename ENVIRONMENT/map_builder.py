import pygame
from DATA.constants import TILE

# '#' = solid tile, '.' = open space
# Each character = TILE x TILE pixels, origin is top-left of the grid.
#
# To offset the whole map in world space, change MAP_ORIGIN_X / MAP_ORIGIN_Y.
# Player spawn is set in player.py relative to wherever the floor ends up.

MAP_ORIGIN_X = 0
MAP_ORIGIN_Y = 0

STARTING_MAP = """
....................................................
....................................................
....................................................
.............................#####..................
............................######..................
..........................########..................
.......................###########..................
.......................###########..................
####...................###########..................
.......................###########..................
....####............##############..................
........####........................................
########################################............
########################################............
""".strip().split(
    "\n"
)


def build_platforms(
    map_grid=STARTING_MAP, tile=TILE, origin_x=MAP_ORIGIN_X, origin_y=MAP_ORIGIN_Y
):
    rects = []
    for row_i, row in enumerate(map_grid):
        for col_i, char in enumerate(row):
            if char == "#":
                rects.append(
                    pygame.Rect(
                        origin_x + col_i * tile,
                        origin_y + row_i * tile,
                        tile,
                        tile,
                    )
                )
    return rects
