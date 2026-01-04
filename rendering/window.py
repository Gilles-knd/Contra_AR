import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    WHITE, RED, BLUE, ORANGE, YELLOW, GRAY, DARK_GRAY, GREEN,
    PLAYER_MAX_LIVES, LEVEL_LENGTH,
    RADAR_RANGE_NEAR, RADAR_RANGE_MID, RADAR_RANGE_FAR
)
from constants import MAX_STEPS


class ContraWindow:

    def __init__(self, agent, fps=30):
        self.agent = agent
        self.env = agent.env
        self.fps = fps

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Contra RL - Enhanced Map")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)
        self.debug_mode = False

    def draw(self):
        # Mise à jour de la caméra
        self.env.camera.update(self.env.player.x)
        camera_x = self.env.camera.get_x()

        self.env.level.draw_background(self.screen, camera_x)

        # Déléguer le dessin aux entités
        self.env.level.draw(self.screen, camera_x)
        self.env.player.draw(self.screen, camera_x)

        for enemy in self.env.enemies:
            if enemy.active:
                enemy.draw(self.screen, camera_x)

        for bullet in self.env.bullets:
            if bullet.active:
                bullet.draw(self.screen, camera_x)

        # UI enrichie
        score_text = self.font.render(f"Score: {self.agent.score:.1f}", True, WHITE)
        steps_text = self.small_font.render(f"Steps: {self.env.steps}", True, WHITE)

        progress = int((self.env.player.x / LEVEL_LENGTH) * 100)
        progress_text = self.small_font.render(f"Progress: {progress}%", True, WHITE)

        state_text = self.small_font.render(f"State: {self.env.get_state()}", True, WHITE)
        qtable_text = self.small_font.render(f"Q-table: {len(self.agent.qtable)}", True, WHITE)

        if self.debug_mode:
            self._draw_debug_overlay(camera_x)

        # Life icons on the right (3 rectangles)
        icon_size = 18
        padding = 6
        bar_x = SCREEN_WIDTH - (icon_size + padding) * PLAYER_MAX_LIVES - 30
        bar_y = 20
        lives_label = self.small_font.render("Vies", True, WHITE)
        self.screen.blit(lives_label, (bar_x - lives_label.get_width() - 8, bar_y + 2))
        for i in range(PLAYER_MAX_LIVES):
            x = bar_x + i * (icon_size + padding)
            color = RED if i < self.env.player.lives else DARK_GRAY
            pygame.draw.rect(self.screen, color, (x, bar_y, icon_size, icon_size), border_radius=3)
            pygame.draw.rect(self.screen, WHITE, (x, bar_y, icon_size, icon_size), width=1, border_radius=3)

        self.screen.blit(score_text, (10, 10))
        self.screen.blit(steps_text, (10, 50))
        self.screen.blit(progress_text, (10, 80))
        self.screen.blit(state_text, (10, 110))
        self.screen.blit(qtable_text, (10, 140))

        if self.debug_mode:
            debug_text = self.small_font.render("DEBUG: distances (D pour basculer)", True, BLUE)
            self.screen.blit(debug_text, (10, 170))

        # Messages de fin
        if self.env.game_over:
            text = self.font.render("GAME OVER", True, RED)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        elif self.env.victory:
            text = self.font.render("VICTOIRE!", True, GREEN)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        self.clock.tick(self.fps)

    def _draw_debug_overlay(self, camera_x):
        """Visual debugging: radar rings + distance lines to threats."""
        player_rect = self.env.player.get_rect()
        player_center = (int(player_rect.centerx - camera_x), int(player_rect.centery))

        # Radar rings showing observation ranges
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ring_colors = [
            (0, 180, 255, 40),  # Near
            (0, 255, 120, 30),  # Mid
            (255, 220, 0, 25),  # Far
        ]
        for radius, color in zip(
            [RADAR_RANGE_NEAR, RADAR_RANGE_MID, RADAR_RANGE_FAR], ring_colors
        ):
            pygame.draw.circle(overlay, color, player_center, radius, width=2)
        self.screen.blit(overlay, (0, 0))

        # Helper to draw a line with distance label at midpoint
        def draw_distance_line(target_pos, color):
            pygame.draw.line(self.screen, color, player_center, target_pos, width=2)
            mid_x = (player_center[0] + target_pos[0]) // 2
            mid_y = (player_center[1] + target_pos[1]) // 2
            distance = ((player_center[0] - target_pos[0]) ** 2 + (player_center[1] - target_pos[1]) ** 2) ** 0.5
            label = self.tiny_font.render(f"{int(distance)} px", True, color)
            label_rect = label.get_rect(center=(mid_x, mid_y))
            self.screen.blit(label, label_rect)

        # enemy le plus proche
        active_enemies = [
            e for e in self.env.enemies
            if e.active and e.spawned
        ]
        if active_enemies:
            nearest_enemy = min(active_enemies, key=lambda e: abs(e.x - self.env.player.x))
            enemy_rect = nearest_enemy.get_rect()
            enemy_center = (int(enemy_rect.centerx - camera_x), int(enemy_rect.centery))
            draw_distance_line(enemy_center, ORANGE)

        # Le trou le plus proche (en face)
        pits_ahead = [
            pit for pit in self.env.level.pits
            if pit.x + pit.width > self.env.player.x  # in front or under
        ]
        if pits_ahead:
            nearest_pit = min(pits_ahead, key=lambda p: abs((p.x + p.width / 2) - self.env.player.x))
            pit_rect = nearest_pit.get_rect()
            pit_center = (int(pit_rect.centerx - camera_x), int(pit_rect.centery))
            draw_distance_line(pit_center, BLUE)

        # La balle la plus proche arrivant
        active_bullets = [b for b in self.env.bullets if b.active]
        if active_bullets:
            nearest_bullet = min(active_bullets, key=lambda b: abs(b.x - self.env.player.x))
            bullet_rect = nearest_bullet.get_rect()
            bullet_center = (int(bullet_rect.centerx - camera_x), int(bullet_rect.centery))
            draw_distance_line(bullet_center, YELLOW)

        # Sol/plateforme sous les pieds et plus proche devant
        player_rect = self.env.player.get_rect()
        standing_platforms = [p for p in self.env.level.platforms if player_rect.colliderect(p.get_rect()) or (p.y >= player_rect.bottom and p.x - camera_x < SCREEN_WIDTH + 100)]
        if standing_platforms:
            # Distance verticale au sol actuel
            current = min(standing_platforms, key=lambda p: abs(p.y - self.env.player.y))
            ground_distance = max(0, current.y - player_rect.bottom)
            label = self.tiny_font.render(f"Ground Δy: {int(ground_distance)}", True, WHITE)
            self.screen.blit(label, (player_center[0] + 10, player_center[1] + 10))

        # Plateforme la plus proche devant (pour anticiper)
        platforms_ahead = [p for p in self.env.level.platforms if p.x > self.env.player.x]
        if platforms_ahead:
            nearest_plat = min(platforms_ahead, key=lambda p: p.x - self.env.player.x)
            plat_rect = nearest_plat.get_rect()
            plat_center = (int(plat_rect.centerx - camera_x), int(plat_rect.centery))
            draw_distance_line(plat_center, GRAY)
            plat_height_diff = self.env.player.y - nearest_plat.y
            plat_label = self.tiny_font.render(f"Next plat Δy: {int(plat_height_diff)}", True, GRAY)
            self.screen.blit(plat_label, (plat_center[0] - 40, plat_center[1] - 10))

    def run_episode(self):
        """Exécute un épisode complet"""
        state = self.agent.reset()
        done = False

        while not done and self.env.steps < MAX_STEPS:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        return False
                    elif event.key == pygame.K_d:
                        self.debug_mode = not self.debug_mode

            # Action de l'agent
            action = self.agent.best_action()
            state, reward, done = self.agent.do(action)

            # Affichage
            self.draw()

        return True

    def close(self):
        pygame.quit()
