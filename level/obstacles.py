"""Obstacles (platforms, pits) for Contra RL game."""

import pygame
from constants import PLATFORM_HEIGHT, SCREEN_HEIGHT, GRAY, BLACK, RED


class Platform:
    """Solid platform for player and enemies."""

    def __init__(self, x, y, width, height=PLATFORM_HEIGHT):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x):
        """Draw platform on screen."""
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, GRAY, (screen_x, self.y, self.width, self.height))


class Pit:
    """Deadly pit (instant death)."""

    def __init__(self, x, width):
        self.x = x
        self.width = width
        self.y = SCREEN_HEIGHT - 50
        self.height = 50

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x):
        """Draw pit on screen with danger pattern."""
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, BLACK, (screen_x, self.y, self.width, self.height))

        # Danger lines
        for i in range(0, self.width, 20):
            pygame.draw.line(screen, RED,
                             (screen_x + i, self.y),
                             (screen_x + i + 15, self.y + self.height), 2)
