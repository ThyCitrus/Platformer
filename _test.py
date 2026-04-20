import random
import pygame

pygame.init()
debug_font = pygame.font.SysFont("monospace", 11)

screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Platformer Base")
clock = pygame.time.Clock()
FPS = 60

# --- Constants ---
GRAVITY = 0.55
JUMP_FORCE = -13
JUMP_CUT = 0.45
MOVE_SPEED = 5
SPRINT_SPEED = 11.25
CROUCH_SPEED = 3
SLIDE_BOOST = 1.2
SLIDE_DECEL = 0.88
MAX_FALL = 32
COYOTE_TIME = 5
SLAM_FORCE = 28
SLIDE_MAX = 30

STAND_W, STAND_H = 60, 80
CROUCH_W, CROUCH_H = 60, 44

# --- Movement System Constants ---
# Ground
TRACTION_THRESHOLD = 5.0
COUNTER_FRICTION = 0.82
GROUND_ACCEL_BASE = 0.22  # was 0.10 — snappier walk pickup
GROUND_ACCEL_MOM = 0.10
GROUND_DECEL = 0.82  # was 0.75 — less aggressive stop, less "sticky"

# Air
AIR_STEER_FORCE = 1.2  # was 0.5 — actually feel your inputs
AIR_DRAG_THRESHOLD = 20.0
AIR_DRAG_BLEED = 0.15  # was 0.1 — overdrive bleeds a bit faster so it's not permanent
AIR_OVERDRIVE_MAX = 30.0

# --- Camera ---
CAM_LERP = 0.08
LEAD_X = 80
LEAD_Y = 60
LEAD_SMOOTH = 0.13

# --- World ---
platforms = [
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

# --- Player state ---
feet_x = 100.0
feet_y = float(1200 - 40)
vel_x = 0.0
vel_y = 0.0
on_ground = False
coyote_timer = 0
jump_held = False
crouching = False
sliding = False
slide_cooldown = False
slide_vel_x = 0.0
slide_boosted = False
slam_used = False
slide_jump_used = False
stun_timer = 0
shake_timer = 0
shake_magnitude = 0
last_vel_y = 0.0
p_w, p_h = STAND_W, STAND_H


def make_rect(fx, fy, w, h):
    return pygame.Rect(fx - w // 2, fy - h, w, h)


def can_stand(fx, fy):
    test = make_rect(fx, fy, STAND_W, STAND_H)
    for plat in platforms:
        if test.colliderect(plat):
            return False
    return True


def cancel_slide(stand=False):
    global sliding, slide_cooldown, slide_vel_x, crouching, p_w, p_h
    sliding = False
    slide_cooldown = False
    slide_vel_x = 0.0
    if stand and can_stand(feet_x, feet_y):
        crouching = False
        p_w, p_h = STAND_W, STAND_H
    else:
        crouching = True
        p_w, p_h = CROUCH_W, CROUCH_H


player = make_rect(feet_x, feet_y, p_w, p_h)

cam_x = feet_x - WIDTH // 2
cam_y = feet_y - HEIGHT // 2
lead_offset_x = 0.0
lead_offset_y = 0.0

game_running = True


def update_player_state(keys, on_ground, vel_x, vel_y, feet_x, feet_y):
    global crouching, sliding, slide_cooldown, slide_vel_x, slide_boosted, p_w, p_h, slide_jump_used

    jump_key = keys[pygame.K_SPACE]
    crouch_key = keys[pygame.K_LCTRL] or keys[pygame.K_s] or keys[pygame.K_DOWN]
    sprint_key = keys[pygame.K_LSHIFT] or keys[pygame.K_q]

    can_stand_now = can_stand(feet_x, feet_y)
    locked = sliding
    carry_momentum = False

    if crouch_key and not locked:
        if on_ground and (abs(vel_x) > 5 or abs(vel_y) > 5):
            new_sliding = True
            new_crouching = False
            if not slide_boosted:
                new_slide_vel_x = vel_x * SLIDE_BOOST
                slide_boosted = True
                if abs(new_slide_vel_x) > SLIDE_MAX:
                    new_slide_vel_x = SLIDE_MAX if new_slide_vel_x > 0 else -SLIDE_MAX
            else:
                new_slide_vel_x = vel_x
        else:
            new_sliding = False
            new_crouching = True
            new_slide_vel_x = 0.0
    elif sliding and not crouch_key:
        new_sliding = False
        if on_ground and sprint_key and can_stand_now:
            new_crouching = False
            slide_cooldown = False
            carry_momentum = True
            new_slide_vel_x = slide_vel_x
        elif on_ground:
            new_crouching = True
            slide_cooldown = True
            new_slide_vel_x = slide_vel_x
        else:
            new_crouching = not can_stand_now
            new_slide_vel_x = 0.0
    elif slide_cooldown and on_ground:
        slide_vel_x *= SLIDE_DECEL
        if abs(slide_vel_x) <= CROUCH_SPEED:
            slide_cooldown = False
            slide_jump_used = False
            slide_vel_x = 0.0
        new_sliding = False
        new_crouching = True
        new_slide_vel_x = slide_vel_x
    elif (
        crouching
        and not locked
        and not slide_cooldown
        and not crouch_key
        and can_stand_now
    ):
        new_crouching = False
        new_sliding = False
        new_slide_vel_x = 0.0
    else:
        new_sliding = sliding
        new_crouching = crouching
        new_slide_vel_x = slide_vel_x
        if not new_crouching and can_stand_now and not crouch_key:
            new_crouching = False

    if new_sliding and abs(new_slide_vel_x) <= CROUCH_SPEED:
        new_sliding = False
        new_crouching = True
        new_slide_vel_x = 0.0

    sliding = new_sliding
    crouching = new_crouching
    slide_vel_x = new_slide_vel_x

    if sliding or crouching:
        p_w, p_h = CROUCH_W, CROUCH_H
    else:
        p_w, p_h = STAND_W, STAND_H

    return carry_momentum


def apply_ground_movement(vel_x, keys, crouching, carry_momentum):
    """
    Traction Threshold system:
      Base Zone  (|vel_x| <= TRACTION_THRESHOLD): snappy accel, instant direction.
      Momentum Zone (|vel_x| > TRACTION_THRESHOLD): counter-friction skid on reversal.
      Sprint 'lock-in': holding sprint preserves speed above SPRINT_SPEED.
    Returns new vel_x.
    """
    sprint_key = keys[pygame.K_LSHIFT] or keys[pygame.K_q]
    moving_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
    moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

    if carry_momentum:
        # Momentum carried from slide-release; let sprint lock-in handle it below.
        pass
    elif moving_left or moving_right:
        direction = -1 if moving_left else 1
        speed = abs(vel_x)

        if crouching:
            # Crouch always snappy, capped at CROUCH_SPEED
            target = CROUCH_SPEED
            vel_x = direction * min(speed + (target - speed) * 0.4413, target)
        elif speed <= TRACTION_THRESHOLD or (
            vel_x != 0 and (vel_x > 0) == (direction > 0)
        ):
            # Base Zone OR same direction in Momentum Zone: normal accel
            if sprint_key:
                target = max(SPRINT_SPEED, speed)
                accel = 0.8
            else:
                target = MOVE_SPEED
                accel = 1.1

            vel_x += direction * accel
            if abs(vel_x) > target:
                vel_x = direction * target
        else:
            # Momentum Zone, REVERSING direction: Counter-Friction skid
            vel_x *= COUNTER_FRICTION
            # Once we've bled into Base Zone, let normal accel take over next frame
    else:
        # No input: standard decel
        vel_x *= GROUND_DECEL
        if abs(vel_x) < 0.1:
            vel_x = 0.0

    # Sprint lock-in: if sprinting and already above SPRINT_SPEED, don't let
    # non-reversal decel drop us below it (only applies with directional input).
    if (moving_left or moving_right) and not crouching:
        sprint_key = keys[pygame.K_LSHIFT] or keys[pygame.K_q]
        direction = -1 if moving_left else 1
        if sprint_key and abs(vel_x) > SPRINT_SPEED and (vel_x > 0) == (direction > 0):
            # Preserve speed; only clamp direction
            vel_x = direction * abs(vel_x)

    return vel_x


def apply_air_movement(vel_x, keys):
    moving_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
    moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

    if moving_left or moving_right:
        direction = -1 if moving_left else 1
        same_dir = (vel_x == 0) or ((vel_x > 0) == (direction > 0))

        if same_dir:
            # Only push if below the natural air max — otherwise leave it alone
            if abs(vel_x) < MOVE_SPEED:
                vel_x += direction * AIR_STEER_FORCE
                vel_x = max(-MOVE_SPEED, min(MOVE_SPEED, vel_x))
        else:
            # Opposing direction: raw force, no cap — heaviness emerges from math
            vel_x += direction * AIR_STEER_FORCE

    # Passive drag above threshold
    speed = abs(vel_x)
    if speed > AIR_DRAG_THRESHOLD:
        drag = (
            AIR_DRAG_BLEED
            * (speed - AIR_DRAG_THRESHOLD)
            / (AIR_OVERDRIVE_MAX - AIR_DRAG_THRESHOLD)
        )
        vel_x = (vel_x / speed) * max(speed - drag, AIR_DRAG_THRESHOLD)

    # Hard cap
    vel_x = max(-AIR_OVERDRIVE_MAX, min(AIR_OVERDRIVE_MAX, vel_x))

    return vel_x


while game_running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False

    keys = pygame.key.get_pressed()
    jump_key = keys[pygame.K_SPACE]
    crouch_key = keys[pygame.K_LCTRL] or keys[pygame.K_s] or keys[pygame.K_DOWN]
    sprint_key = keys[pygame.K_LSHIFT] or keys[pygame.K_q]
    slam_key = keys[pygame.K_RSHIFT]

    was_on_ground = on_ground
    carry_momentum = update_player_state(keys, on_ground, vel_x, vel_y, feet_x, feet_y)
    locked = sliding

    # --- Horizontal velocity ---
    if locked:
        feet_x += slide_vel_x
        vel_x = slide_vel_x
    elif slide_cooldown and on_ground:
        feet_x += slide_vel_x
        vel_x = slide_vel_x
    else:
        if on_ground:
            if stun_timer > 0:
                vel_x *= GROUND_DECEL  # slide to a stop, no input
            else:
                vel_x = apply_ground_movement(vel_x, keys, crouching, carry_momentum)
        else:
            vel_x = apply_air_movement(vel_x, keys)

        feet_x += vel_x

    # --- Jump ---
    can_jump = coyote_timer > 0 and not jump_held

    if jump_key and can_jump:
        if sliding:
            vel_y = JUMP_FORCE * 0.75
            sliding = False
            slide_cooldown = False
            slide_jump_used = True
        elif crouching or slide_cooldown:
            vel_y = JUMP_FORCE * 0.75
        else:
            vel_y = JUMP_FORCE
        coyote_timer = 0
        jump_held = True
        # vel_x is preserved as-is into the air (including skid velocity)

    if not jump_key and vel_y <= 0:
        if jump_held:
            vel_y *= JUMP_CUT
        jump_held = False

    # --- Slam ---
    if slam_key and not on_ground and not slam_used:
        vel_y = SLAM_FORCE
        vel_x = 0.0
        slide_vel_x = 0.0
        sliding = False
        slide_cooldown = False
        slam_used = True

    # --- Horizontal collision ---
    player = make_rect(feet_x, feet_y, p_w, p_h)
    for plat in platforms:
        if player.colliderect(plat):
            if vel_x > 0:
                feet_x = float(plat.left - p_w // 2)
            elif vel_x < 0:
                feet_x = float(plat.right + p_w // 2)
            if locked:
                cancel_slide(stand=False)
            vel_x = 0.0
            slide_vel_x = 0.0
            player = make_rect(feet_x, feet_y, p_w, p_h)

    # --- Vertical collision ---
    vel_y = min(vel_y + GRAVITY, MAX_FALL)
    feet_y += vel_y
    player = make_rect(feet_x, feet_y, p_w, p_h)
    last_vel_y = vel_y
    for plat in platforms:
        if player.colliderect(plat):
            if vel_y > 0:
                feet_y = float(plat.top)
                vel_y = 0
            elif vel_y < 0:
                feet_y = float(plat.bottom + p_h)
                vel_y = 0
                jump_held = False
                coyote_timer = 0
            player = make_rect(feet_x, feet_y, p_w, p_h)

    # --- Resolve remaining overlaps ---
    player = make_rect(feet_x, feet_y, p_w, p_h)
    for plat in platforms:
        if player.colliderect(plat):
            overlap_left = player.right - plat.left
            overlap_right = plat.right - player.left
            overlap_top = player.bottom - plat.top
            overlap_bottom = plat.bottom - player.top

            overlaps = [overlap_left, overlap_right, overlap_top, overlap_bottom]
            min_overlap = min(overlaps)
            min_index = overlaps.index(min_overlap)

            if min_index == 0:
                feet_x -= min_overlap
                vel_x = 0.0
            elif min_index == 1:
                feet_x += min_overlap
                vel_x = 0.0
            elif min_index == 2:
                feet_y -= min_overlap
                vel_y = 0.0
            elif min_index == 3:
                feet_y += min_overlap
                vel_y = 0.0

            player = make_rect(feet_x, feet_y, p_w, p_h)

    # --- Ground check ---
    ground_rect = pygame.Rect(player.left, player.bottom, player.width, 1)
    on_ground = False
    for plat in platforms:
        if ground_rect.colliderect(plat):
            on_ground = True
            break
    if on_ground and not was_on_ground:  # just landed this frame
        if last_vel_y >= 30:
            stun_timer = 40
            shake_timer = 30
            shake_magnitude = 12
        elif last_vel_y >= 24:
            stun_timer = 25
            shake_timer = 20
            shake_magnitude = 7
        elif last_vel_y >= 20:
            stun_timer = 15
            shake_timer = 10
            shake_magnitude = 3
    elif on_ground:
        coyote_timer = COYOTE_TIME
        vel_y = 0
        slam_used = False
        if not sliding and not slide_cooldown and not crouching:
            if slide_jump_used:
                slide_boosted = False
            slide_jump_used = False
    elif coyote_timer > 0:
        coyote_timer -= 1

    if stun_timer > 0:
        stun_timer -= 1

    # --- Camera ---
    VAR = MOVE_SPEED if vel_y >= MAX_FALL / 1.5 else MAX_FALL
    lead_offset_x += (vel_x / MOVE_SPEED * LEAD_X - lead_offset_x) * LEAD_SMOOTH
    lead_offset_y += (vel_y / VAR * LEAD_Y - lead_offset_y) * LEAD_SMOOTH

    target_x = feet_x - WIDTH // 2 + lead_offset_x
    target_y = feet_y - HEIGHT // 2 + lead_offset_y

    cam_x += (target_x - cam_x) * CAM_LERP
    cam_y += (target_y - cam_y) * CAM_LERP

    if cam_y > 1200 - HEIGHT and not feet_y > 1200:
        cam_y = 1200 - HEIGHT

    shake_x, shake_y = 0, 0
    if shake_timer > 0:
        shake_timer -= 1
        decay = shake_timer / 30  # normalized 0-1
        shake_x = random.randint(-1, 1) * shake_magnitude * decay
        shake_y = random.randint(-1, 1) * shake_magnitude * decay

    ox, oy = int(cam_x + shake_x), int(cam_y + shake_y)

    # Speed tier for debug readout
    spd = abs(vel_x)
    if crouching or sliding:
        tier = "CROUCH/SLIDE"
    elif on_ground:
        tier = "BASE" if spd <= TRACTION_THRESHOLD else "MOMENTUM"
    else:
        tier = "OVERDRIVE" if spd > AIR_DRAG_THRESHOLD else "AIR GLIDE"

    debug_info = (
        f"pos: ({feet_x:.1f}, {feet_y:.1f}) | vel: ({vel_x:.2f}, {vel_y:.2f}) | "
        f"tier: {tier} | on_ground: {on_ground} | coyote: {coyote_timer} | "
        f"crouching: {crouching} | sliding: {sliding} | cooldown: {slide_cooldown} | "
        f"slide_vel: {slide_vel_x:.2f} | boosted: {slide_boosted} | jump_held: {jump_held}"
    )
    print(debug_info)

    if keys[pygame.K_r]:
        feet_x, feet_y = 100.0, float(1200 - 40)
        vel_x = vel_y = 0.0
        on_ground = False
        coyote_timer = 0
        jump_held = crouching = sliding = slide_cooldown = False
        slide_vel_x = 0.0
        slide_boosted = False
        p_w, p_h = STAND_W, STAND_H

    # --- Draw ---
    screen.fill((30, 30, 30))

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

    for plat in platforms:
        pygame.draw.rect(screen, (80, 80, 80), plat.move(-ox, -oy))
    pygame.draw.rect(screen, (70, 130, 200), player.move(-ox, -oy))
    pygame.display.flip()

pygame.quit()
