import pygame
import ENVIRONMENT.world as world  # imported as module so we can mutate it
from DATA.constants import FPS, TRACTION_THRESHOLD, AIR_DRAG_THRESHOLD
from USER.player import Player
from USER.camera import Camera
from ENVIRONMENT.area_manager import AreaManager

pygame.init()
debug_font = pygame.font.SysFont("monospace", 11)

screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Platformer")
clock = pygame.time.Clock()

area_manager = AreaManager(WIDTH, HEIGHT, start_area="area_1", start_spawn="default")

# Sync world.platforms so player.py's collision loop sees the right list
world.platforms = area_manager.platforms

player = Player()
camera = Camera(WIDTH, HEIGHT)
camera.x = player.feet_x - WIDTH // 2
camera.y = player.feet_y - HEIGHT // 2

game_running = True

while game_running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False

    keys = pygame.key.get_pressed()

    if keys[pygame.K_r]:
        player.reset()

    # --- Area transition update ---
    area_manager.update()

    # Check if we just hit the fully-black frame and need to swap area + player pos
    pending = area_manager.consume_pending_load()
    if pending:
        area_key, spawn_key = pending
        area_manager.execute_load(area_key, spawn_key)
        world.platforms = area_manager.platforms  # sync the global list

        fx, fy = area_manager.get_spawn(spawn_key)
        player.feet_x, player.feet_y = fx, fy
        player.vel_x = player.vel_y = 0.0
        player.on_ground = False
        player.rect = player._make_rect()

        camera.x = player.feet_x - WIDTH // 2
        camera.y = player.feet_y - HEIGHT // 2

    # Only allow normal input when not transitioning
    if not area_manager.is_transitioning():
        area_manager.check_triggers(player)

        prev_on_ground = player.on_ground
        player.update(keys)

        if player.on_ground and not prev_on_ground:
            camera.trigger_shake(player.last_vel_y)

    camera.update(player)

    # Apply camera bounds from current area
    bounds = area_manager.get_cam_bounds()
    if bounds:
        if bounds.get("x_min") is not None:
            camera.x = max(camera.x, bounds["x_min"])
        if bounds.get("x_max") is not None:
            camera.x = min(camera.x, bounds["x_max"] - WIDTH)
        if bounds.get("y_min") is not None:
            camera.y = max(camera.y, bounds["y_min"])
        if bounds.get("y_max") is not None:
            camera.y = min(camera.y, bounds["y_max"] - HEIGHT)

    ox, oy = camera.get_offset()

    # --- Draw ---
    screen.fill((30, 30, 30))

    # Grid
    grid_color = (50, 50, 50)
    start_x = (ox // 100) * 100
    start_y = (oy // 100) * 100
    for gx in range(start_x, ox + WIDTH + 100, 100):
        sx = gx - ox
        pygame.draw.line(screen, grid_color, (sx, 0), (sx, HEIGHT))
        screen.blit(debug_font.render(str(gx), True, (90, 90, 90)), (sx + 2, 2))
    for gy in range(start_y, oy + HEIGHT + 100, 100):
        sy = gy - oy
        pygame.draw.line(screen, grid_color, (0, sy), (WIDTH, sy))
        screen.blit(debug_font.render(str(gy), True, (90, 90, 90)), (2, sy + 2))

    # Platforms
    for plat in world.platforms:
        pygame.draw.rect(screen, (80, 80, 80), plat.move(-ox, -oy))

    # Player
    pygame.draw.rect(screen, (70, 130, 200), player.rect.move(-ox, -oy))

    # Debug text
    tier = player.debug_tier()
    debug_info = (
        f"area: {area_manager.current_key} | "
        f"pos: ({player.feet_x:.1f}, {player.feet_y:.1f}) | "
        f"vel: ({player.vel_x:.2f}, {player.vel_y:.2f}) | "
        f"tier: {tier} | on_ground: {player.on_ground} | "
        f"crouching: {player.crouching} | sliding: {player.sliding}"
    )
    screen.blit(debug_font.render(debug_info, True, (200, 200, 200)), (4, HEIGHT - 16))

    # Fade overlay — always drawn last
    area_manager.draw_fade(screen)

    pygame.display.flip()

pygame.quit()
