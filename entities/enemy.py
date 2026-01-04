"""Enemy entity for Contra RL game."""

import os
import pygame
from constants import ENEMY_SIZE, ENEMY_SPEED, ENEMY_SHOOT_RANGE, RED, ORANGE, PURPLE, WHITE, DARK_GRAY
from entities.bullet import Bullet


_enemy_sprite_cache = {}


def _load_sprite(name, size):
    """Load enemy sprite if present; cache results."""
    key = (name, size)
    if key in _enemy_sprite_cache:
        return _enemy_sprite_cache[key]
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    path = os.path.join(assets_dir, name)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (size, size))
        _enemy_sprite_cache[key] = img
        return img
    _enemy_sprite_cache[key] = None
    return None


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
        # Optional sprite by type
        sprite_name = {
            'walker': 'enemy_walker.png',
            'shooter': 'enemy_shooter.png',
            'stationary': 'enemy_stationary.png'
        }.get(enemy_type, 'enemy_walker.png')
        self.sprite = _load_sprite(sprite_name, self.size)

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
        base_rect = pygame.Rect(int(screen_x), int(self.y), self.size, self.size)

        if self.sprite:
            screen.blit(self.sprite, (base_rect.x, base_rect.y))
        else:
            if self.enemy_type == 'walker':
                pygame.draw.rect(screen, RED, base_rect, border_radius=3)
                pygame.draw.rect(screen, DARK_GRAY, (base_rect.x + 3, base_rect.bottom - 6, self.size - 6, 6), border_radius=2)
            elif self.enemy_type == 'shooter':
                pygame.draw.rect(screen, ORANGE, base_rect, border_radius=3)
                visor = pygame.Rect(base_rect.x + 3, base_rect.y + 6, self.size - 6, 6)
                pygame.draw.rect(screen, DARK_GRAY, visor, border_radius=2)
            else:  # stationary
                pygame.draw.rect(screen, PURPLE, base_rect, border_radius=3)
                pygame.draw.rect(screen, DARK_GRAY, (base_rect.x + 2, base_rect.bottom - 5, self.size - 4, 4), border_radius=2)

            pygame.draw.rect(screen, WHITE, base_rect, width=1, border_radius=3)
