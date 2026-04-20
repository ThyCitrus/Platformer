import pygame

platforms: list[pygame.Rect] = []


def get_spawn():
    # Spawn is now handled per-area by AreaManager.get_spawn().
    # This fallback exists only if something calls it directly.
    return 180.0, 1160.0
