"""Static level definition for Contra RL game."""

import pygame
from constants import (
    SCREEN_HEIGHT, PLATFORM_HEIGHT, ENEMY_SIZE, LEVEL_LENGTH, ORANGE, SCREEN_WIDTH,
    SKY_TOP, SKY_BOTTOM, GROUND_BROWN, GROUND_DARK, FLAG_GREEN, GRAY, WHITE
)
from level.obstacles import Platform, Pit
from entities.enemy import Enemy
import os


class StaticLevel:
    """Static level with platforms, enemies, pits, and flag."""

    def __init__(self):
        self.platforms = []
        self.pits = []
        self.enemies = []

        # Flag positioned on last platform
        self.flag_x = LEVEL_LENGTH - 150
        self.flag_y = SCREEN_HEIGHT - PLATFORM_HEIGHT - 60

        # Clouds for parallax background
        self.clouds = [
            (200, 80, 70),
            (600, 120, 60),
            (1000, 90, 80),
            (1600, 70, 65),
            (2100, 110, 75),
            (2600, 100, 80)
        ]

        # Optional background/flag textures
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        bg_path = os.path.join(assets_dir, "background.png")
        self.bg_image = pygame.image.load(bg_path).convert() if os.path.exists(bg_path) else None
        flag_path = os.path.join(assets_dir, "flag.png")
        self.flag_image = pygame.image.load(flag_path).convert_alpha() if os.path.exists(flag_path) else None
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

    def draw_background(self, screen, camera_x):
        """Draw sky gradient, clouds, and distant ground."""
        if self.bg_image:
            # Tile horizontally
            img_width = self.bg_image.get_width()
            start_x = -int(camera_x * 0.5) % img_width - img_width
            for x in range(start_x, SCREEN_WIDTH + img_width, img_width):
                screen.blit(self.bg_image, (x, 0))
        else:
            # Sky gradient fallback
            for i in range(SCREEN_HEIGHT):
                t = i / SCREEN_HEIGHT
                r = int(SKY_TOP[0] * (1 - t) + SKY_BOTTOM[0] * t)
                g = int(SKY_TOP[1] * (1 - t) + SKY_BOTTOM[1] * t)
                b = int(SKY_TOP[2] * (1 - t) + SKY_BOTTOM[2] * t)
                pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))

        # Distant ground band
        horizon_y = SCREEN_HEIGHT - 120
        #pygame.draw.rect(screen, GROUND_DARK, (0, horizon_y, SCREEN_WIDTH, 140))

        # Clouds (parallax)
        for cx, cy, size in self.clouds:
            # Parallax factor 0.5 for slow movement
            sx = cx - camera_x * 0.5
            if -150 < sx < SCREEN_WIDTH + 150:
                self._draw_cloud(screen, sx, cy, size)

    def _draw_cloud(self, screen, x, y, size):
        """Simple rounded cloud."""
        pygame.draw.circle(screen, WHITE, (int(x), int(y)), size // 2)
        pygame.draw.circle(screen, WHITE, (int(x + size * 0.4), int(y + 5)), int(size * 0.35))
        pygame.draw.circle(screen, WHITE, (int(x - size * 0.4), int(y + 5)), int(size * 0.35))
        pygame.draw.rect(screen, WHITE, (int(x - size * 0.6), int(y), int(size * 1.2), int(size * 0.4)))

    def draw(self, screen, camera_x):
        """Draw all level elements (foreground)."""
        # Draw platforms
        for platform in self.platforms:
            platform.draw(screen, camera_x)

        # Draw pits
        for pit in self.pits:
            pit.draw(screen, camera_x)

        # Draw flag
        flag_screen_x = self.flag_x - camera_x
        if -100 < flag_screen_x < SCREEN_WIDTH + 100:
            if self.flag_image:
                screen.blit(self.flag_image, (flag_screen_x, self.flag_y - self.flag_image.get_height() + 20))
            else:
                # Pole
                pygame.draw.rect(screen, GRAY, (flag_screen_x, self.flag_y - 10, 12, 80), border_radius=3)
                # Flag cloth
                pygame.draw.polygon(screen, FLAG_GREEN, [
                    (flag_screen_x + 12, self.flag_y - 5),
                    (flag_screen_x + 70, self.flag_y + 15),
                    (flag_screen_x + 12, self.flag_y + 35)
                ])
                # Flag tip
                pygame.draw.circle(screen, FLAG_GREEN, (flag_screen_x + 70, self.flag_y + 15), 6)
