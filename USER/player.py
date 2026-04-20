import pygame
from DATA.constants import *
import ENVIRONMENT.world as world
from ENVIRONMENT.world import get_spawn


def make_rect(fx, fy, w, h):
    return pygame.Rect(fx - w // 2, fy - h, w, h)


def can_stand(fx, fy):
    test = make_rect(fx, fy, STAND_W, STAND_H)
    for plat in world.platforms:
        if test.colliderect(plat):
            return False
    return True


class Player:
    def __init__(self):
        spawn_x, spawn_y = get_spawn()
        self.feet_x = spawn_x
        self.feet_y = spawn_y
        self.vel_x = 0.0
        self.vel_y = 0.0

        self.on_ground = False
        self.was_on_ground = False
        self.coyote_timer = 0
        self.jump_held = False

        self.crouching = False
        self.sliding = False
        self.slide_cooldown = False
        self.slide_vel_x = 0.0
        self.slide_boosted = False
        self.slide_jump_used = False

        self.slam_used = False
        self.stun_timer = 0
        self.last_vel_y = 0.0

        self.p_w = STAND_W
        self.p_h = STAND_H
        self.rect = make_rect(self.feet_x, self.feet_y, self.p_w, self.p_h)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_rect(self):
        return make_rect(self.feet_x, self.feet_y, self.p_w, self.p_h)

    def _can_stand(self):
        return can_stand(self.feet_x, self.feet_y)

    def cancel_slide(self, stand=False):
        self.sliding = False
        self.slide_cooldown = False
        self.slide_vel_x = 0.0
        if stand and self._can_stand():
            self.crouching = False
            self.p_w, self.p_h = STAND_W, STAND_H
        else:
            self.crouching = True
            self.p_w, self.p_h = CROUCH_W, CROUCH_H

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _update_state(self, keys):
        """Crouch / slide / stand state transitions. Returns carry_momentum."""
        crouch_key = keys[pygame.K_LCTRL] or keys[pygame.K_s] or keys[pygame.K_DOWN]
        sprint_key = keys[pygame.K_LSHIFT] or keys[pygame.K_q]

        can_stand_now = self._can_stand()
        locked = self.sliding
        carry_momentum = False

        if crouch_key and not locked:
            if self.on_ground and (abs(self.vel_x) > 5 or abs(self.vel_y) > 5):
                new_sliding = True
                new_crouching = False
                if not self.slide_boosted:
                    new_slide_vel_x = self.vel_x * SLIDE_BOOST
                    self.slide_boosted = True
                    if abs(new_slide_vel_x) > SLIDE_MAX:
                        new_slide_vel_x = (
                            SLIDE_MAX if new_slide_vel_x > 0 else -SLIDE_MAX
                        )
                else:
                    new_slide_vel_x = self.vel_x
            else:
                new_sliding = False
                new_crouching = True
                new_slide_vel_x = 0.0

        elif self.sliding and not crouch_key:
            new_sliding = False
            if self.on_ground and sprint_key and can_stand_now:
                new_crouching = False
                self.slide_cooldown = False
                carry_momentum = True
                new_slide_vel_x = self.slide_vel_x
            elif self.on_ground:
                new_crouching = True
                self.slide_cooldown = True
                new_slide_vel_x = self.slide_vel_x
            else:
                new_crouching = not can_stand_now
                new_slide_vel_x = 0.0

        elif self.slide_cooldown and self.on_ground:
            self.slide_vel_x *= SLIDE_DECEL
            if abs(self.slide_vel_x) <= CROUCH_SPEED:
                self.slide_cooldown = False
                self.slide_jump_used = False
                self.slide_vel_x = 0.0
            new_sliding = False
            new_crouching = True
            new_slide_vel_x = self.slide_vel_x

        elif (
            self.crouching
            and not locked
            and not self.slide_cooldown
            and not crouch_key
            and can_stand_now
        ):
            new_crouching = False
            new_sliding = False
            new_slide_vel_x = 0.0

        else:
            new_sliding = self.sliding
            new_crouching = self.crouching
            new_slide_vel_x = self.slide_vel_x
            if not new_crouching and can_stand_now and not crouch_key:
                new_crouching = False

        if new_sliding and abs(new_slide_vel_x) <= CROUCH_SPEED:
            new_sliding = False
            new_crouching = True
            new_slide_vel_x = 0.0

        self.sliding = new_sliding
        self.crouching = new_crouching
        self.slide_vel_x = new_slide_vel_x

        self.p_w, self.p_h = (
            (CROUCH_W, CROUCH_H)
            if (self.sliding or self.crouching)
            else (STAND_W, STAND_H)
        )
        return carry_momentum

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _apply_ground_movement(self, keys, carry_momentum):
        sprint_key = keys[pygame.K_LSHIFT] or keys[pygame.K_q]
        moving_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        vel_x = self.vel_x

        if carry_momentum:
            pass
        elif moving_left or moving_right:
            direction = -1 if moving_left else 1
            speed = abs(vel_x)

            if self.crouching:
                target = CROUCH_SPEED
                vel_x = direction * min(speed + (target - speed) * 0.4413, target)
            elif speed <= TRACTION_THRESHOLD or (
                vel_x != 0 and (vel_x > 0) == (direction > 0)
            ):
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
                vel_x *= COUNTER_FRICTION
        else:
            vel_x *= GROUND_DECEL
            if abs(vel_x) < 0.1:
                vel_x = 0.0

        if (moving_left or moving_right) and not self.crouching:
            direction = -1 if moving_left else 1
            if (
                sprint_key
                and abs(vel_x) > SPRINT_SPEED
                and (vel_x > 0) == (direction > 0)
            ):
                vel_x = direction * abs(vel_x)

        self.vel_x = vel_x

    def _apply_air_movement(self, keys):
        moving_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        vel_x = self.vel_x

        if moving_left or moving_right:
            direction = -1 if moving_left else 1
            same_dir = (vel_x == 0) or ((vel_x > 0) == (direction > 0))
            if same_dir:
                if abs(vel_x) < MOVE_SPEED:
                    vel_x += direction * AIR_STEER_FORCE
                    vel_x = max(-MOVE_SPEED, min(MOVE_SPEED, vel_x))
            else:
                vel_x += direction * AIR_STEER_FORCE

        speed = abs(vel_x)
        if speed > AIR_DRAG_THRESHOLD:
            drag = (
                AIR_DRAG_BLEED
                * (speed - AIR_DRAG_THRESHOLD)
                / (AIR_OVERDRIVE_MAX - AIR_DRAG_THRESHOLD)
            )
            vel_x = (vel_x / speed) * max(speed - drag, AIR_DRAG_THRESHOLD)

        vel_x = max(-AIR_OVERDRIVE_MAX, min(AIR_OVERDRIVE_MAX, vel_x))
        self.vel_x = vel_x

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------

    def update(self, keys):
        self.was_on_ground = self.on_ground
        carry_momentum = self._update_state(keys)
        locked = self.sliding

        jump_key = keys[pygame.K_SPACE]
        slam_key = keys[pygame.K_RSHIFT]

        # --- Horizontal ---
        if locked or (self.slide_cooldown and self.on_ground):
            self.feet_x += self.slide_vel_x
            self.vel_x = self.slide_vel_x
        else:
            if self.on_ground:
                if self.stun_timer > 0:
                    self.vel_x *= GROUND_DECEL
                else:
                    self._apply_ground_movement(keys, carry_momentum)
            else:
                self._apply_air_movement(keys)
            self.feet_x += self.vel_x

        # --- Jump ---
        can_jump = self.coyote_timer > 0 and not self.jump_held
        if jump_key and can_jump:
            if self.sliding:
                self.vel_y = JUMP_FORCE * 0.75
                self.slide_cooldown = False
                self.slide_jump_used = True
            elif self.crouching or self.slide_cooldown:
                self.vel_y = JUMP_FORCE * 0.75
            else:
                self.vel_y = JUMP_FORCE
            self.coyote_timer = 0
            self.jump_held = True

        if not jump_key and self.vel_y <= 0:
            if self.jump_held:
                self.vel_y *= JUMP_CUT
            self.jump_held = False

        # --- Slam ---
        if slam_key and not self.on_ground and not self.slam_used:
            self.vel_y = SLAM_FORCE
            self.vel_x = 0.0
            self.slide_vel_x = 0.0
            self.sliding = False
            self.slide_cooldown = False
            self.slam_used = True

        # --- Horizontal collision ---
        self.rect = self._make_rect()
        for plat in world.platforms:
            if self.rect.colliderect(plat):
                if self.vel_x > 0:
                    self.feet_x = float(plat.left - self.p_w // 2)
                elif self.vel_x < 0:
                    self.feet_x = float(plat.right + self.p_w // 2)
                if locked:
                    self.cancel_slide(stand=False)
                self.vel_x = 0.0
                self.slide_vel_x = 0.0
                self.rect = self._make_rect()

        # --- Vertical ---
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL)
        self.feet_y += self.vel_y
        self.rect = self._make_rect()
        self.last_vel_y = self.vel_y
        for plat in world.platforms:
            if self.rect.colliderect(plat):
                if self.vel_y > 0:
                    self.feet_y = float(plat.top)
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.feet_y = float(plat.bottom + self.p_h)
                    self.vel_y = 0
                    self.jump_held = False
                    self.coyote_timer = 0
                self.rect = self._make_rect()

        # --- Resolve remaining overlaps ---
        self.rect = self._make_rect()
        for plat in world.platforms:
            if self.rect.colliderect(plat):
                ol = self.rect.right - plat.left
                or_ = plat.right - self.rect.left
                ot = self.rect.bottom - plat.top
                ob = plat.bottom - self.rect.top
                overlaps = [ol, or_, ot, ob]
                mi = overlaps.index(min(overlaps))
                if mi == 0:
                    self.feet_x -= ol
                    self.vel_x = 0.0
                elif mi == 1:
                    self.feet_x += or_
                    self.vel_x = 0.0
                elif mi == 2:
                    self.feet_y -= ot
                    self.vel_y = 0.0
                elif mi == 3:
                    self.feet_y += ob
                    self.vel_y = 0.0
                self.rect = self._make_rect()

        # --- Ground check ---
        ground_probe = pygame.Rect(self.rect.left, self.rect.bottom, self.rect.width, 1)
        self.on_ground = any(ground_probe.colliderect(p) for p in world.platforms)

        if self.on_ground and not self.was_on_ground and not self.sliding:
            if self.last_vel_y >= 30:
                self.stun_timer = 40
            elif self.last_vel_y >= 24:
                self.stun_timer = 25
            elif self.last_vel_y >= 20:
                self.stun_timer = 15
        elif self.on_ground:
            self.coyote_timer = COYOTE_TIME
            self.vel_y = 0
            self.slam_used = False
            if not self.sliding and not self.slide_cooldown and not self.crouching:
                if self.slide_jump_used:
                    self.slide_boosted = False
                self.slide_jump_used = False
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        if self.stun_timer > 0:
            self.stun_timer -= 1

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self):
        spawn_x, spawn_y = get_spawn()
        self.feet_x = spawn_x
        self.feet_y = spawn_y
        self.vel_x = self.vel_y = 0.0
        self.on_ground = False
        self.coyote_timer = 0
        self.jump_held = self.crouching = self.slide_cooldown = False
        self.slide_vel_x = 0.0
        self.slide_boosted = False
        self.stun_timer = 0
        self.p_w, self.p_h = STAND_W, STAND_H
        self.rect = self._make_rect()

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def debug_tier(self):
        spd = abs(self.vel_x)
        if self.crouching or self.sliding:
            return "CROUCH/SLIDE"
        elif self.on_ground:
            return "BASE" if spd <= TRACTION_THRESHOLD else "MOMENTUM"
        else:
            return "OVERDRIVE" if spd > AIR_DRAG_THRESHOLD else "AIR GLIDE"
