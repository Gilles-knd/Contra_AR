"""Enemy entity for Contra RL game."""

import pygame
from constants import ENEMY_SIZE, ENEMY_SPEED, ENEMY_SHOOT_RANGE, RED, ORANGE
from entities.bullet import Bullet


class Enemy:
    """Enemy with walker, shooter, or stationary behavior."""

    def __init__(self, x, y, enemy_type='walker', platform=None):
        self.x = x
        self.y = y
        self.size = ENEMY_SIZE
        self.enemy_type = enemy_type
        self.speed = ENEMY_SPEED if enemy_type == 'walker' else 0
        self.hp = 1
        self.shoot_cooldown = 0
        self.active = True
        self.spawned = False
        self.direction = -1
        self.platform = platform

    def update(self, player_x, player_y):
        """Update enemy behavior and shooting."""
        # Deactivate if too far behind player
        if self.x < player_x - 1000:
            self.active = False

        # Walker movement
        if self.enemy_type == 'walker' and self.spawned and self.platform:
            self.x += self.speed * self.direction

            # Platform boundary detection
            if self.x <= self.platform.x:
                self.x = self.platform.x
                self.direction = 1
            elif self.x >= self.platform.x + self.platform.width - self.size:
                self.x = self.platform.x + self.platform.width - self.size
                self.direction = -1

        # Shooter behavior
        if self.enemy_type in ['shooter', 'stationary'] and self.spawned:
            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1

            distance = abs(self.x - player_x)
            if distance < ENEMY_SHOOT_RANGE and self.shoot_cooldown == 0:
                self.shoot_cooldown = 120
                return self.shoot(player_x, player_y)

        return None

    def shoot(self, player_x, player_y):
        """Fire bullet towards player."""
        direction = -1 if player_x < self.x else 1
        bullet_x = self.x + self.size // 2
        bullet_y = self.y + self.size // 2
        return Bullet(bullet_x, bullet_y, direction, 'enemy')

    def take_damage(self):
        """Take damage and check if dead."""
        self.hp -= 1
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, screen, camera_x):
        """Draw enemy on screen."""
        if not self.spawned:
            return

        screen_x = self.x - camera_x
        color = RED if self.enemy_type == 'walker' else ORANGE
        pygame.draw.rect(screen, color, (int(screen_x), int(self.y), self.size, self.size))
