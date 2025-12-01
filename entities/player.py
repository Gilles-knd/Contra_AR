"""Player entity for Contra RL game."""

import pygame
from constants import (SCREEN_HEIGHT, PLAYER_SIZE, GRAVITY, JUMP_FORCE,
                       PLAYER_SPEED, LEVEL_LENGTH, GREEN)
from entities.bullet import Bullet


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
        self.lives = 3  # PLAYER_MAX_LIVES from constants
        self.shoot_cooldown = 0

    def move(self, action):
        """Execute action: 0=LEFT, 1=RIGHT, 2=JUMP, 3=SHOOT, 4=IDLE."""
        if action == 0:
            self.vel_x = -PLAYER_SPEED
            self.direction = -1
        elif action == 1:
            self.vel_x = PLAYER_SPEED
            self.direction = 1
        elif action == 4:
            self.vel_x = 0

        if action == 2 and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

        if action == 3:
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
        pygame.draw.rect(screen, GREEN, (int(screen_x), int(self.y), self.size, self.size))
