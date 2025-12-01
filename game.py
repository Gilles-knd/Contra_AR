"""Main game class for Contra RL."""

import pygame
from constants import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, WHITE, RED, GREEN,
                       LEVEL_LENGTH)
from entities.player import Player
from entities.enemy import Enemy
from level.static_level import StaticLevel
from rendering.camera import Camera


class ContraGame:
    """Main game loop with RL environment interface."""

    def __init__(self):
        self._reached_50 = None
        self.camera = None
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Contra RL - Refactored")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.reset()

    def reset(self):
        """Reset game to initial state."""
        self.player = Player()
        self.level = StaticLevel()
        self.enemies = [Enemy(e.x, e.y, e.enemy_type, e.platform) for e in self.level.enemies]
        self.bullets = []
        self.camera = Camera()
        self.score = 0
        self.steps = 0
        self.game_over = False
        self.victory = False

        self._reached_25 = False
        self._reached_50 = False
        self._reached_75 = False

        # Oscillation detection history
        self.last_actions = []
        self.last_x_positions = []

        return self.get_state()

    def step(self, action):
        """Execute one game step with given action."""
        self.steps += 1
        reward = 0

        old_x = self.player.x
        old_lives = self.player.lives

        # Player action
        new_bullet = self.player.move(action)
        if new_bullet:
            self.bullets.append(new_bullet)

        # Player physics
        fell_off = self.player.update(self.level.platforms)
        if fell_off:
            reward = -50
            self.game_over = True
            return self.get_state(), reward, True

        # Oscillation detection
        self.last_actions.append(action)
        self.last_x_positions.append(self.player.x)

        if len(self.last_actions) > 10:
            self.last_actions.pop(0)
            self.last_x_positions.pop(0)

        if len(self.last_actions) >= 10:
            direction_changes = 0
            for i in range(1, len(self.last_actions)):
                if (self.last_actions[i] == 0 and self.last_actions[i - 1] == 1) or \
                        (self.last_actions[i] == 1 and self.last_actions[i - 1] == 0):
                    direction_changes += 1

            net_progress = self.last_x_positions[-1] - self.last_x_positions[0]
            if direction_changes > 4 and net_progress < 20:
                reward -= 3.0

        # Movement rewards
        distance_moved = self.player.x - old_x
        if distance_moved > 2:
            reward += 2.0
        elif distance_moved < -2:
            reward -= 1.0

        # Action rewards
        if action == 4:  # IDLE
            reward -= 1.0
        elif action in [0, 1]:  # Movement
            reward += 0.3

        # Spawn enemies
        for enemy in self.enemies:
            if not enemy.spawned and enemy.x < self.player.x + 500:
                enemy.spawned = True

        # Update enemies
        for enemy in self.enemies[:]:
            if not enemy.active:
                continue
            enemy_bullet = enemy.update(self.player.x, self.player.y)
            if enemy_bullet:
                self.bullets.append(enemy_bullet)

        # Update bullets
        for bullet in self.bullets[:]:
            if not bullet.active:
                self.bullets.remove(bullet)
                continue
            bullet.update(self.level.platforms)

        player_rect = self.player.get_rect()

        # Enemy collisions
        for enemy in self.enemies:
            if enemy.active and enemy.spawned and player_rect.colliderect(enemy.get_rect()):
                if self.player.take_damage():
                    reward = -50
                    self.game_over = True
                    return self.get_state(), reward, True
                else:
                    reward -= 20
                    enemy.active = False

        # Bullet collisions
        for bullet in self.bullets:
            if bullet.owner == 'enemy' and bullet.active:
                if player_rect.colliderect(bullet.get_rect()):
                    bullet.active = False
                    if self.player.take_damage():
                        reward = -50
                        self.game_over = True
                        return self.get_state(), reward, True
                    else:
                        reward -= 20

        # Player shooting enemies
        enemies_killed_this_step = 0
        for bullet in self.bullets[:]:
            if bullet.owner == 'player' and bullet.active:
                for enemy in self.enemies:
                    if enemy.active and enemy.spawned and bullet.get_rect().colliderect(enemy.get_rect()):
                        bullet.active = False
                        if enemy.take_damage():
                            enemies_killed_this_step += 1
                            reward += 25
                            self.score += 10
                        break

        # Combo bonus for killing without damage
        if enemies_killed_this_step > 0 and old_lives == self.player.lives:
            reward += 10 * enemies_killed_this_step

        # Progress milestones
        progress_percent = (self.player.x / self.level.flag_x) * 100

        if progress_percent > 25 and not self._reached_25:
            self._reached_25 = True
            bonus = 40 if self.player.lives == 3 else 30
            reward += bonus

        if progress_percent > 50 and not self._reached_50:
            self._reached_50 = True
            bonus = 70 if self.player.lives >= 2 else 50
            reward += bonus

        if progress_percent > 75 and not self._reached_75:
            self._reached_75 = True
            bonus = 100 if self.player.lives >= 2 else 70
            reward += bonus

        # Victory check
        flag_rect = pygame.Rect(self.level.flag_x, self.level.flag_y, 60, 60)
        if player_rect.colliderect(flag_rect):
            base_reward = 400
            life_bonus = 100 * self.player.lives
            reward = base_reward + life_bonus
            self.victory = True
            return self.get_state(), reward, True

        # Timeout
        if self.steps > 5000:
            reward = -30
            return self.get_state(), reward, True

        return self.get_state(), reward, False

    def get_state(self):
        """Get current game state for RL agent."""
        # Position discretization
        x_bucket = min(9, int(self.player.x / (self.level.flag_x / 10)))

        # On ground?
        on_ground = 1 if self.player.on_ground else 0

        # Enemy radar
        enemy_dist = 10
        enemy_direction = 0
        enemy_can_shoot = 0

        spawned_enemies = [e for e in self.enemies if e.active and e.spawned]
        if spawned_enemies:
            closest_enemy = min(spawned_enemies, key=lambda e: abs(e.x - self.player.x))
            distance = abs(closest_enemy.x - self.player.x)

            enemy_dist = min(9, int(distance / 100))
            enemy_direction = 1 if closest_enemy.x > self.player.x else -1

            if closest_enemy.enemy_type in ['shooter', 'stationary'] and distance < 400:
                enemy_can_shoot = 1

        # Bullet danger detection
        bullet_danger = 0
        bullet_height = 0

        enemy_bullets = [b for b in self.bullets if b.owner == 'enemy' and b.active]
        if enemy_bullets:
            dangerous_bullets = []
            for b in enemy_bullets:
                distance = abs(b.x - self.player.x)

                coming_at_me = (b.direction == 1 and b.x < self.player.x) or \
                               (b.direction == -1 and b.x > self.player.x)

                same_height = abs(b.y - (self.player.y + self.player.size // 2)) < 50

                if coming_at_me and same_height:
                    dangerous_bullets.append((distance, b))

            if dangerous_bullets:
                closest_distance, closest_bullet = min(dangerous_bullets, key=lambda x: x[0])

                if closest_distance < 100:
                    bullet_danger = 2
                elif closest_distance < 250:
                    bullet_danger = 1

                if closest_bullet.y < self.player.y:
                    bullet_height = 1
                elif closest_bullet.y > self.player.y + self.player.size:
                    bullet_height = -1
                else:
                    bullet_height = 0

        return (x_bucket, on_ground, enemy_dist, enemy_direction,
                enemy_can_shoot, bullet_danger, bullet_height)

    def render(self):
        """Render game graphics."""
        self.camera.update(self.player.x)
        camera_x = self.camera.get_x()

        self.screen.fill(BLACK)

        # Draw level
        self.level.draw(self.screen, camera_x)

        # Draw player
        self.player.draw(self.screen, camera_x)

        # Draw enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.draw(self.screen, camera_x)

        # Draw bullets
        for bullet in self.bullets:
            if bullet.active:
                bullet.draw(self.screen, camera_x)

        # UI
        lives_text = self.font.render(f"Vies: {self.player.lives}", True, WHITE)
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        progress = int((self.player.x / LEVEL_LENGTH) * 100)
        progress_text = self.small_font.render(f"Progression: {progress}%", True, WHITE)

        self.screen.blit(lives_text, (10, 10))
        self.screen.blit(score_text, (10, 50))
        self.screen.blit(progress_text, (10, 90))

        # Game over/victory
        if self.game_over:
            text = self.font.render("GAME OVER", True, RED)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        elif self.victory:
            text = self.font.render("VICTOIRE !", True, GREEN)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        self.clock.tick(FPS)

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True


if __name__ == "__main__":
    game = ContraGame()
    running = True

    while running:
        running = game.handle_events()

        keys = pygame.key.get_pressed()
        action = 4

        if keys[pygame.K_LEFT]:
            action = 0
        elif keys[pygame.K_RIGHT]:
            action = 1
        if keys[pygame.K_SPACE]:
            action = 2
        if keys[pygame.K_x]:
            action = 3

        state, reward, done = game.step(action)
        game.render()

        if done:
            print(f"Terminé ! Score: {game.score}, Progression: {int(game.player.x / LEVEL_LENGTH * 100)}%")
            pygame.time.wait(2000)
            game.reset()

    pygame.quit()
