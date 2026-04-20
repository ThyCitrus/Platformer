import pygame
from DATA.constants import FPS, TRACTION_THRESHOLD, AIR_DRAG_THRESHOLD
from ENVIRONMENT.world import platforms
from USER.player import Player
from USER.camera import Camera

pygame.init()
debug_font = pygame.font.SysFont("monospace", 11)

screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Platformer")
clock = pygame.time.Clock()

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

    prev_on_ground = player.on_ground
    player.update(keys)

    # Trigger camera shake on landing
    if player.on_ground and not prev_on_ground:
        camera.trigger_shake(player.last_vel_y)

    camera.update(player)
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
    for plat in platforms:
        pygame.draw.rect(screen, (80, 80, 80), plat.move(-ox, -oy))

    # Player
    pygame.draw.rect(screen, (70, 130, 200), player.rect.move(-ox, -oy))

    # Debug text
    tier = player.debug_tier()
    debug_info = (
        f"pos: ({player.feet_x:.1f}, {player.feet_y:.1f}) | "
        f"vel: ({player.vel_x:.2f}, {player.vel_y:.2f}) | "
        f"tier: {tier} | on_ground: {player.on_ground} | coyote: {player.coyote_timer} | "
        f"crouching: {player.crouching} | sliding: {player.sliding} | "
        f"cooldown: {player.slide_cooldown} | slide_vel: {player.slide_vel_x:.2f} | "
        f"boosted: {player.slide_boosted} | jump_held: {player.jump_held}"
    )
    screen.blit(debug_font.render(debug_info, True, (200, 200, 200)), (4, HEIGHT - 16))

    pygame.display.flip()

pygame.quit()
