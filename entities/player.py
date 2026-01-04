"""Player entity for Contra RL game."""

import os
import pygame
from constants import (SCREEN_HEIGHT, PLAYER_SIZE, GRAVITY, JUMP_FORCE,
                       PLAYER_SPEED, LEVEL_LENGTH, GREEN, PLAYER_MAX_LIVES, ACTION_LEFT, ACTION_RIGHT, ACTION_IDLE,
                       ACTION_JUMP, ACTION_SHOOT, DARK_GRAY, WHITE, BLUE)
from entities.bullet import Bullet


def _load_sprite(filename, size):
    """Load a sprite if present in assets folder, else return None."""
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    path = os.path.join(assets_dir, filename)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (size, size))
    return None


class Player:
    """Player character with physics and actions."""

    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT - 100
        self.size = PLAYER_SIZE
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.direction = 1
        self.lives = PLAYER_MAX_LIVES
        self.shoot_cooldown = 0
        self.sprite = _load_sprite("player.png", self.size)

    def move(self, action):
        """Execute action: 0=LEFT, 1=RIGHT, 2=JUMP, 3=SHOOT, 4=IDLE."""
        if action == ACTION_LEFT:
            self.vel_x = -PLAYER_SPEED
            self.direction = -1
        elif action == ACTION_RIGHT:
            self.vel_x = PLAYER_SPEED
            self.direction = 1
        elif action == ACTION_IDLE:
            self.vel_x = 0

        if action == ACTION_JUMP and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

        if action == ACTION_SHOOT:
            return self.shoot()
        return None

    def shoot(self):
        """Fire a bullet."""
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 15
            bullet_x = self.x + (self.size if self.direction == 1 else 0)
            bullet_y = self.y + self.size // 2
            return Bullet(bullet_x, bullet_y, self.direction, 'player')
        return None

    def update(self, platforms):
        """Update physics with gravity and collision detection."""
        # Apply gravity
        self.vel_y += GRAVITY

        # Horizontal movement with collision
        self.x += self.vel_x
        player_rect = self.get_rect()

        # Horizontal collision (walls)
        for platform in platforms:
            if player_rect.colliderect(platform.get_rect()):
                if self.vel_x > 0:  # Moving right
                    self.x = platform.x - self.size
                elif self.vel_x < 0:  # Moving left
                    self.x = platform.x + platform.width

        # Vertical movement
        self.y += self.vel_y
        player_rect = self.get_rect()
        self.on_ground = False

        # Vertical collision (floor/ceiling)
        for platform in platforms:
            plat_rect = platform.get_rect()
            if player_rect.colliderect(plat_rect):
                if self.vel_y > 0:  # Falling
                    self.y = platform.y - self.size
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:  # Jumping into ceiling
                    self.y = platform.y + platform.height
                    self.vel_y = 0

        # Level boundaries
        self.x = max(0, min(self.x, LEVEL_LENGTH - self.size))

        # Death by falling
        if self.y > SCREEN_HEIGHT + 50:
            return True

        # Update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        return False

    def take_damage(self):
        """Reduce lives and check if dead."""
        self.lives -= 1
        return self.lives <= 0

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, screen, camera_x):
        """Draw player on screen."""
        screen_x = self.x - camera_x
        if self.sprite:
            sprite = pygame.transform.flip(self.sprite, self.direction == -1, False)
            screen.blit(sprite, (int(screen_x), int(self.y)))
        else:
            body_rect = pygame.Rect(int(screen_x), int(self.y), self.size, self.size)
            # Torso
            pygame.draw.rect(screen, GREEN, body_rect, border_radius=4)
            # Helmet/visor
            visor_rect = pygame.Rect(body_rect.x + 4, body_rect.y + 6, self.size - 8, 8)
            pygame.draw.rect(screen, DARK_GRAY, visor_rect, border_radius=3)
            pygame.draw.rect(screen, BLUE, visor_rect.inflate(-4, -2), border_radius=3)
            # Legs
            leg_width = self.size // 4
            pygame.draw.rect(screen, DARK_GRAY, (body_rect.x + 3, body_rect.bottom - 6, leg_width, 6), border_radius=2)
            pygame.draw.rect(screen, DARK_GRAY, (body_rect.right - leg_width - 3, body_rect.bottom - 6, leg_width, 6), border_radius=2)
            # Outline
            pygame.draw.rect(screen, WHITE, body_rect, width=1, border_radius=4)
