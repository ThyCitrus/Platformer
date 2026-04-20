import pygame
from DATA.constants import TILE
from ENVIRONMENT.map_builder import build_platforms


# ---------------------------------------------------------------------------
# Area definitions
# ---------------------------------------------------------------------------
# Each _build_* function returns a dict:
#
#   "platforms"  : list[pygame.Rect]
#   "spawns"     : dict[str, (float, float)]   feet_x, feet_y
#   "triggers"   : list[dict]
#   "cam_bounds" : dict | None
#
# Trigger keys:  "rect", "target", "spawn"
# cam_bounds keys: "x_min", "x_max", "y_min", "y_max"  (None = unclamped)
# ---------------------------------------------------------------------------


def _build_area_1():
    MAP = """
####################################################
...................................................#
...................................................#
....................................##############.#
..............................##############.......#
..........................############.######.##.###
.......................#############.....###..######
.......................#############......##.#######
####...................############........#.......#
.......................############........######..#
....####............##############.........#.......#
........####...............................#.#.#####
########################################...#.#.....#
########################################...#.#####.#
...........................................#.......#
...........................................#.......#
...........................................#####.###
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
...................................................#
....................................................
####################################################
"""
    plats = build_platforms(MAP)
    plats += [
        pygame.Rect(0, 1200 - 40, 4000, 40),
        pygame.Rect(-950, -2000, 1000, 4000),
        pygame.Rect(300, 1090, 200, 20),
        pygame.Rect(600, 1000, 180, 20),
        pygame.Rect(900, 950, 220, 20),
        pygame.Rect(600, 900, 160, 20),
        pygame.Rect(700, 770, 200, 20),
        pygame.Rect(1100, 750, 240, 20),
        pygame.Rect(1300, 1200 - 150, 300, 20),
        pygame.Rect(2000, 1090 - 390, 1400, 400),
    ]
    return {
        "platforms": plats,
        "spawns": {
            "default": (100.0, 1160.0),
            "from_area2": (3800.0, 1160.0),
        },
        "triggers": [
            {
                "rect": pygame.Rect(4500, 2000, 100, 100),
                "target": "area_2",
                "spawn": "from_area1",
            },
        ],
        "cam_bounds": {
            "x_min": 0,
            "x_max": None,
            "y_min": None,
            "y_max": None,
        },
    }


def _build_area_2():
    MAP = """
....................................................
....................................................
....................................................
....................................................
....................................................
....................................................
....................................................
..........#####.....................................
......##.....#######................................
.....####.........##########........................
########################################............
########################################............
"""
    plats = build_platforms(MAP)
    plats += [
        pygame.Rect(-90, -2000, 100, 900),
    ]
    return {
        "platforms": plats,
        "spawns": {
            "from_area1": (80.0, 1000.0),
            "default": (80.0, 1160.0),
        },
        "triggers": [
            {
                "rect": pygame.Rect(-150, 0, 100, 2000),
                "target": "area_1",
                "spawn": "from_area2",
            },
        ],
        "cam_bounds": {
            "x_min": 0,
            "x_max": 4000,
            "y_min": None,
            "y_max": 1200,
        },
    }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

AREAS = {
    "area_1": _build_area_1,
    "area_2": _build_area_2,
}


# ---------------------------------------------------------------------------
# AreaManager
# ---------------------------------------------------------------------------


class AreaManager:
    FADE_FRAMES = 20

    def __init__(self, screen_w, screen_h, start_area="area_1", start_spawn="default"):
        self.screen_w = screen_w
        self.screen_h = screen_h

        self._current_key = None
        self._area = None

        self._fade_surface = pygame.Surface((screen_w, screen_h))
        self._fade_surface.fill((0, 0, 0))
        self._fade_alpha = 0
        self._fade_timer = 0
        self._pending_target = None
        self._fading_out = False
        self._fading_in = False

        self._load(start_area, start_spawn, instant=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def platforms(self):
        return self._area["platforms"]

    @property
    def current_key(self):
        return self._current_key

    def get_spawn(self, name="default"):
        return self._area["spawns"].get(name, self._area["spawns"]["default"])

    def get_cam_bounds(self):
        return self._area.get("cam_bounds")

    def is_transitioning(self):
        return self._fading_out or self._fading_in

    def check_triggers(self, player):
        if self.is_transitioning():
            return None
        for trigger in self._area["triggers"]:
            if player.rect.colliderect(trigger["rect"]):
                self._start_transition(trigger["target"], trigger["spawn"])
                return (trigger["target"], trigger["spawn"])
        return None

    def update(self):
        if self._fading_out:
            self._fade_timer += 1
            self._fade_alpha = int(255 * self._fade_timer / self.FADE_FRAMES)
            if self._fade_timer >= self.FADE_FRAMES:
                self._fading_out = False
                self._fading_in = True
                self._fade_timer = 0
                self._fade_alpha = 255

        elif self._fading_in:
            self._fade_timer += 1
            self._fade_alpha = int(255 * (1 - self._fade_timer / self.FADE_FRAMES))
            if self._fade_timer >= self.FADE_FRAMES:
                self._fading_in = False
                self._fade_timer = 0
                self._fade_alpha = 0

        self._fade_surface.set_alpha(self._fade_alpha)

    def draw_fade(self, screen):
        if self._fade_alpha > 0:
            screen.blit(self._fade_surface, (0, 0))

    def consume_pending_load(self):
        """Returns (area_key, spawn_key) exactly once when the screen is fully
        black (start of fade-in). main.py should call execute_load() then."""
        if self._fading_in and self._fade_timer == 0 and self._pending_target:
            result = self._pending_target
            self._pending_target = None
            return result
        return None

    def execute_load(self, area_key, spawn_key):
        self._load(area_key, spawn_key)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _start_transition(self, area_key, spawn_key):
        self._fading_out = True
        self._fading_in = False
        self._fade_timer = 0
        self._pending_target = (area_key, spawn_key)

    def _load(self, area_key, spawn_key, instant=False):
        self._area = AREAS[area_key]()
        self._current_key = area_key
        if instant:
            self._fade_alpha = 0
