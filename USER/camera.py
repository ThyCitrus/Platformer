import random
from DATA.constants import CAM_LERP, LEAD_X, LEAD_Y, LEAD_SMOOTH, MOVE_SPEED, MAX_FALL


class Camera:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.x = 0.0
        self.y = 0.0
        self.lead_offset_x = 0.0
        self.lead_offset_y = 0.0
        self.shake_timer = 0
        self.shake_magnitude = 0

    def update(self, player):
        vel_x = player.vel_x
        vel_y = player.vel_y

        VAR = MOVE_SPEED if vel_y >= MAX_FALL / 1.5 else MAX_FALL
        self.lead_offset_x += (
            vel_x / MOVE_SPEED * LEAD_X - self.lead_offset_x
        ) * LEAD_SMOOTH
        self.lead_offset_y += (vel_y / VAR * LEAD_Y - self.lead_offset_y) * LEAD_SMOOTH

        target_x = player.feet_x - self.screen_w // 2 + self.lead_offset_x
        target_y = player.feet_y - self.screen_h // 2 + self.lead_offset_y

        from main import HEIGHT  # Import here to avoid circular dependency

        if self.y > 1200 - HEIGHT and not player.feet_y > 1200:
            self.y = 1200 - HEIGHT

        self.x += (target_x - self.x) * CAM_LERP
        self.y += (target_y - self.y) * CAM_LERP

    def trigger_shake(self, last_vel_y):
        if last_vel_y >= 30:
            self.shake_timer = 30
            self.shake_magnitude = 12
        elif last_vel_y >= 24:
            self.shake_timer = 20
            self.shake_magnitude = 7
        elif last_vel_y >= 20:
            self.shake_timer = 10
            self.shake_magnitude = 3

    def get_offset(self):
        shake_x = shake_y = 0
        if self.shake_timer > 0:
            self.shake_timer -= 1
            decay = self.shake_timer / 30
            shake_x = random.randint(-1, 1) * self.shake_magnitude * decay
            shake_y = random.randint(-1, 1) * self.shake_magnitude * decay
        return int(self.x + shake_x), int(self.y + shake_y)
