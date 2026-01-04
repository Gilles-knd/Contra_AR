"""Obstacles (platforms, pits) for Contra RL game."""

import pygame
from constants import PLATFORM_HEIGHT, SCREEN_HEIGHT, GRAY, BLACK, RED, GROUND_BROWN, GROUND_DARK


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
        # Base
        pygame.draw.rect(screen, GROUND_BROWN, (screen_x, self.y, self.width, self.height))
        # Edge shading
        pygame.draw.rect(screen, GROUND_DARK, (screen_x, self.y + self.height - 4, self.width, 4))
        # Top texture stripes
        for i in range(int(self.width // 20)):
            pygame.draw.line(screen, GRAY, (screen_x + i * 20, self.y + 4),
                             (screen_x + i * 20 + 10, self.y + 4), 2)


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
        """Draw pit as transparent gap (background shows through)."""
        # No fill: just leave empty so background is visible.
        # Optional rim to hint danger:
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, RED, (screen_x, self.y, self.width, 0))
