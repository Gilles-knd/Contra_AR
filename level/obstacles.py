
import pygame
from arcade.csscolor import DARK_GREEN
from arcade.uicolor import GREEN_NEPHRITIS

from constants import PLATFORM_HEIGHT, SCREEN_HEIGHT, GRAY, BLACK, RED, GROUND_BROWN, GROUND_DARK


class Platform:

    def __init__(self, x, y, width, height=PLATFORM_HEIGHT):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_rect(self):
        """collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x):
        """désinner les plateformes à l'écran"""
        screen_x = self.x - camera_x

        # Base
        pygame.draw.rect(screen, GREEN_NEPHRITIS, (screen_x, self.y, self.width, self.height))

        # Edge shading
        pygame.draw.rect(screen, DARK_GREEN, (screen_x, self.y + self.height - 4, self.width, 4))

        # Hachures
        for i in range(int(self.width // 20)):
            pygame.draw.line(screen, DARK_GREEN, (screen_x + i * 20, self.y + 4),
                             (screen_x + i * 20 + 10, self.y + 4), 2)


class Pit:
    """Trou mortel"""

    def __init__(self, x, width):
        self.x = x
        self.width = width
        self.y = SCREEN_HEIGHT - 50
        self.height = 50

    def get_rect(self):
        """Get le rectangle de collision"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x):
        """Afficher le trou (transparent)"""
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, RED, (screen_x, self.y, self.width, 0))
