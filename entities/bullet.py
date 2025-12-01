"""Bullet entity for Contra RL game."""

import pygame
from constants import BULLET_SIZE, BULLET_SPEED, LEVEL_LENGTH, SCREEN_WIDTH, YELLOW, RED


class Bullet:
    """Bullet projectile for player and enemies."""

    def __init__(self, x, y, direction, owner='player'):
        self.x = x
        self.y = y
        self.direction = direction
        self.owner = owner
        self.size = BULLET_SIZE
        self.speed = BULLET_SPEED
        self.active = True

    def update(self, platforms):
        """Update bullet position and check collisions."""
        self.x += self.speed * self.direction

        # Out of bounds check
        if self.x < -100 or self.x > LEVEL_LENGTH + 100:
            self.active = False
            return

        # Platform collision
        bullet_rect = self.get_rect()
        for platform in platforms:
            if bullet_rect.colliderect(platform.get_rect()):
                self.active = False
                return

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, screen, camera_x):
        """Draw bullet on screen."""
        screen_x = self.x - camera_x
        if -50 < screen_x < SCREEN_WIDTH + 50:
            color = YELLOW if self.owner == 'player' else RED
            pygame.draw.circle(screen, color, (int(screen_x), int(self.y)), self.size // 2)
