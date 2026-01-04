"""Static level definition for Contra RL game."""

import pygame
from constants import SCREEN_HEIGHT, PLATFORM_HEIGHT, ENEMY_SIZE, LEVEL_LENGTH, ORANGE, SCREEN_WIDTH
from level.obstacles import Platform, Pit
from entities.enemy import Enemy


class StaticLevel:
    """Static level with platforms, enemies, pits, and flag."""

    def __init__(self):
        self.platforms = []
        self.pits = []
        self.enemies = []
        # Flag positioned on last platform
        self.flag_x = LEVEL_LENGTH - 150
        self.flag_y = SCREEN_HEIGHT - PLATFORM_HEIGHT - 60
        self.generate_static_level()

    def generate_static_level(self):
        """Generate the complete static level layout."""
        ground_y = SCREEN_HEIGHT - PLATFORM_HEIGHT

        # SEGMENT 1 (0 → 600)
        plat1 = Platform(0, ground_y, 600)
        self.platforms.append(plat1)

        # SEGMENT 2 (600 → 900)
        plat2 = Platform(600, ground_y, 300)
        self.platforms.append(plat2)

        plat_high = Platform(650, ground_y - 120, 200)
        self.platforms.append(plat_high)

        self.enemies.append(Enemy(700, ground_y - ENEMY_SIZE, 'walker', plat2))
        self.enemies.append(Enemy(750, ground_y - 120 - ENEMY_SIZE, 'shooter', plat_high))

        # PIT 1 (900 → 1000)
        self.platforms.append(Platform(900, ground_y, 50))
        self.pits.append(Pit(950, 100))

        # SEGMENT 3 (1050 → 1700)
        plat3 = Platform(1050, ground_y, 650)
        self.platforms.append(plat3)
        self.enemies.append(Enemy(1200, ground_y - ENEMY_SIZE, 'walker', plat3))
        self.enemies.append(Enemy(1400, ground_y - ENEMY_SIZE, 'shooter', plat3))

        # STAIRS (1700 → 2100)
        for i in range(4):
            plat_x = 1700 + i * 100
            plat_y = ground_y - (i * 25)
            self.platforms.append(Platform(plat_x, plat_y, 100))

        # BUNKER (2100 → 2500)
        plat4 = Platform(2100, ground_y - 100, 400)
        self.platforms.append(plat4)
        self.platforms.append(Platform(2250, ground_y - 180, 150, 80))
        self.enemies.append(Enemy(2300, ground_y - 180 - ENEMY_SIZE, 'shooter'))

        # ORANGE PLATFORMS (2500 → 2800)
        plat_orange1 = Platform(2500, ground_y - 100, 120)
        self.platforms.append(plat_orange1)
        self.enemies.append(Enemy(2520, ground_y - 100 - ENEMY_SIZE, 'shooter', plat_orange1))

        # FINAL PLATFORM
        final_plat = Platform(2770, ground_y, LEVEL_LENGTH - 2770)
        self.platforms.append(final_plat)

    def draw(self, screen, camera_x):
        """Draw all level elements."""
        # Draw platforms
        for platform in self.platforms:
            platform.draw(screen, camera_x)

        # Draw pits
        for pit in self.pits:
            pit.draw(screen, camera_x)

        # Draw flag
        flag_screen_x = self.flag_x - camera_x
        if -100 < flag_screen_x < SCREEN_WIDTH + 100:
            pygame.draw.rect(screen, ORANGE, (flag_screen_x, self.flag_y, 10, 60))
            pygame.draw.polygon(screen, ORANGE, [
                (flag_screen_x + 10, self.flag_y),
                (flag_screen_x + 60, self.flag_y + 15),
                (flag_screen_x + 10, self.flag_y + 30)
            ])
