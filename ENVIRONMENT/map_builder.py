import pygame
from DATA.constants import TILE


def build_platforms(map_string, tile=TILE, origin_x=0, origin_y=0):
    """
    Parse an ASCII map string into a list of pygame.Rects.
    '#' = solid tile, anything else = open space.
    Strips leading/trailing blank lines automatically.
    """
    rows = map_string.strip().split("\n")
    rects = []
    for row_i, row in enumerate(rows):
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
