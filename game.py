import pygame


# === CONSTANTES ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Tailles
PLAYER_SIZE = 32
ENEMY_SIZE = 32
BULLET_SIZE = 8
PLATFORM_HEIGHT = 20

# Physique
GRAVITY = 0.8
JUMP_FORCE = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 1.5
BULLET_SPEED = 10

# Gameplay
PLAYER_MAX_LIVES = 3
ENEMY_SHOOT_RANGE = 400
LEVEL_LENGTH = 3000

# Couleurs
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
ORANGE = (255, 165, 0)
DARK_GRAY = (64, 64, 64)


# === CLASSES ===

class Bullet:
    def __init__(self, x, y, direction, owner='player'):
        self.x = x
        self.y = y
        self.direction = direction
        self.owner = owner
        self.size = BULLET_SIZE
        self.speed = BULLET_SPEED
        self.active = True

    def update(self, platforms):
        """✅ FIX: Collision avec plateformes"""
        self.x += self.speed * self.direction

        # Limites du niveau
        if self.x < -100 or self.x > LEVEL_LENGTH + 100:
            self.active = False
            return

        # ✅ Collision avec plateformes
        bullet_rect = self.get_rect()
        for platform in platforms:
            if bullet_rect.colliderect(platform.get_rect()):
                self.active = False
                return

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, screen, camera_x):
        screen_x = self.x - camera_x
        if -50 < screen_x < SCREEN_WIDTH + 50:
            color = YELLOW if self.owner == 'player' else RED
            pygame.draw.circle(screen, color, (int(screen_x), int(self.y)), self.size // 2)


class Platform:
    def __init__(self, x, y, width, height=PLATFORM_HEIGHT):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x):
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, GRAY, (screen_x, self.y, self.width, self.height))


class Pit:
    def __init__(self, x, width):
        self.x = x
        self.width = width
        self.y = SCREEN_HEIGHT - 50
        self.height = 50

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x):
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, BLACK, (screen_x, self.y, self.width, self.height))
        for i in range(0, self.width, 20):
            pygame.draw.line(screen, RED,
                             (screen_x + i, self.y),
                             (screen_x + i + 15, self.y + self.height), 2)


class Player:
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

    def move(self, action):
        """Actions: 0=LEFT, 1=RIGHT, 2=JUMP, 3=SHOOT, 4=IDLE"""
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
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 15
            bullet_x = self.x + (self.size if self.direction == 1 else 0)
            bullet_y = self.y + self.size // 2
            return Bullet(bullet_x, bullet_y, self.direction, 'player')
        return None

    def update(self, platforms):
        """✅ FIX: Physique améliorée avec collision solide"""
        # Gravité
        self.vel_y += GRAVITY

        # ✅ Déplacement horizontal avec collision
        self.x += self.vel_x
        player_rect = self.get_rect()

        # Collision horizontale (murs)
        for platform in platforms:
            if player_rect.colliderect(platform.get_rect()):
                # Collision par la gauche ou droite
                if self.vel_x > 0:  # Mouvement vers la droite
                    self.x = platform.x - self.size
                elif self.vel_x < 0:  # Mouvement vers la gauche
                    self.x = platform.x + platform.width

        # ✅ Déplacement vertical
        self.y += self.vel_y
        player_rect = self.get_rect()
        self.on_ground = False

        # Collision verticale (sol/plafond)
        for platform in platforms:
            plat_rect = platform.get_rect()
            if player_rect.colliderect(plat_rect):
                # Collision par le haut (joueur tombe)
                if self.vel_y > 0:
                    self.y = platform.y - self.size
                    self.vel_y = 0
                    self.on_ground = True
                # Collision par le bas (joueur saute dans plafond)
                elif self.vel_y < 0:
                    self.y = platform.y + platform.height
                    self.vel_y = 0

        # Limites du niveau
        self.x = max(0, min(self.x, LEVEL_LENGTH - self.size))

        # Mort si chute
        if self.y > SCREEN_HEIGHT + 50:
            return True

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        return False

    def take_damage(self):
        self.lives -= 1
        return self.lives <= 0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, screen, camera_x):
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, GREEN, (int(screen_x), int(self.y), self.size, self.size))


class Enemy:
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

    def update(self, player_x, player_y):
        if self.x < player_x - 1000:
            self.active = False

        if self.enemy_type == 'walker' and self.spawned and self.platform:
            self.x += self.speed * self.direction

            if self.x <= self.platform.x:
                self.x = self.platform.x
                self.direction = 1
            elif self.x >= self.platform.x + self.platform.width - self.size:
                self.x = self.platform.x + self.platform.width - self.size
                self.direction = -1

        if self.enemy_type in ['shooter', 'stationary'] and self.spawned:
            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1

            distance = abs(self.x - player_x)
            if distance < ENEMY_SHOOT_RANGE and self.shoot_cooldown == 0:
                self.shoot_cooldown = 120
                return self.shoot(player_x, player_y)

        return None

    def shoot(self, player_x, player_y):
        direction = -1 if player_x < self.x else 1
        bullet_x = self.x + self.size // 2
        bullet_y = self.y + self.size // 2
        return Bullet(bullet_x, bullet_y, direction, 'enemy')

    def take_damage(self):
        self.hp -= 1
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, screen, camera_x):
        if not self.spawned:
            return

        screen_x = self.x - camera_x
        color = RED if self.enemy_type == 'walker' else ORANGE
        pygame.draw.rect(screen, color, (int(screen_x), int(self.y), self.size, self.size))


class StaticLevel:
    """Niveau statique FINAL - Drapeau aligné"""

    def __init__(self):
        self.platforms = []
        self.pits = []
        self.enemies = []
        # ✅ Drapeau positionné sur la dernière plateforme
        self.flag_x = LEVEL_LENGTH - 150
        self.flag_y = SCREEN_HEIGHT - PLATFORM_HEIGHT - 60  # Sur la plateforme
        self.generate_static_level()

    def generate_static_level(self):
        ground_y = SCREEN_HEIGHT - PLATFORM_HEIGHT

        # === SEGMENT 1 (0 → 600) ===
        plat1 = Platform(0, ground_y, 600)
        self.platforms.append(plat1)
        self.enemies.append(Enemy(450, ground_y - ENEMY_SIZE, 'walker', plat1))

        # === SEGMENT 2 (600 → 900) ===
        plat2 = Platform(600, ground_y, 300)
        self.platforms.append(plat2)

        plat_high = Platform(650, ground_y - 120, 200)
        self.platforms.append(plat_high)

        self.enemies.append(Enemy(700, ground_y - ENEMY_SIZE, 'walker', plat2))
        self.enemies.append(Enemy(750, ground_y - 120 - ENEMY_SIZE, 'shooter', plat_high))

        # === FOSSÉ 1 (900 → 1000) ===
        self.platforms.append(Platform(900, ground_y, 50))
        self.pits.append(Pit(950, 100))

        # === SEGMENT 3 (1050 → 1700) ===
        plat3 = Platform(1050, ground_y, 650)
        self.platforms.append(plat3)
        self.enemies.append(Enemy(1200, ground_y - ENEMY_SIZE, 'walker', plat3))
        self.enemies.append(Enemy(1250, ground_y - ENEMY_SIZE, 'walker', plat3))
        self.enemies.append(Enemy(1400, ground_y - ENEMY_SIZE, 'shooter', plat3))

        # === MONTÉE (1700 → 2100) ===
        for i in range(4):
            plat_x = 1700 + i * 100
            plat_y = ground_y - (i * 25)
            self.platforms.append(Platform(plat_x, plat_y, 100))

        # === BUNKER (2100 → 2500) ===
        plat4 = Platform(2100, ground_y - 100, 400)
        self.platforms.append(plat4)
        self.platforms.append(Platform(2250, ground_y - 180, 150, 80))
        self.enemies.append(Enemy(2300, ground_y - 180 - ENEMY_SIZE, 'shooter'))

        # === PLATEFORMES ORANGES (2500 → 2800) ===
        plat_orange1 = Platform(2500, ground_y - 100, 120)
        #plat_orange2 = Platform(2650, ground_y - 100, 120)
        self.platforms.append(plat_orange1)
        #self.platforms.append(plat_orange2)
        self.enemies.append(Enemy(2520, ground_y - 100 - ENEMY_SIZE, 'shooter', plat_orange1))
        #self.enemies.append(Enemy(2670, ground_y - 100 - ENEMY_SIZE, 'shooter', plat_orange2))

        final_plat = Platform(2770, ground_y, LEVEL_LENGTH - 2770)
        self.platforms.append(final_plat)


    def draw(self, screen, camera_x):
        for platform in self.platforms:
            platform.draw(screen, camera_x)

        for pit in self.pits:
            pit.draw(screen, camera_x)

        # Drapeau
        flag_screen_x = self.flag_x - camera_x
        if -100 < flag_screen_x < SCREEN_WIDTH + 100:
            pygame.draw.rect(screen, ORANGE, (flag_screen_x, self.flag_y, 10, 60))
            pygame.draw.polygon(screen, ORANGE, [
                (flag_screen_x + 10, self.flag_y),
                (flag_screen_x + 60, self.flag_y + 15),
                (flag_screen_x + 10, self.flag_y + 30)
            ])


class ContraGame:
    def __init__(self):
        self._reached_50 = None
        self.camera_x = None
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Contra RL - Niveau Statique FINAL")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.reset()

    def reset(self):
        self.player = Player()
        self.level = StaticLevel()
        self.enemies = [Enemy(e.x, e.y, e.enemy_type, e.platform) for e in self.level.enemies]
        self.bullets = []
        self.camera_x = 0
        self.score = 0
        self.steps = 0
        self.game_over = False
        self.victory = False

        self._reached_25 = False
        self._reached_50 = False
        self._reached_75 = False

        # ✅ NOUVEAU : Historique pour détecter vibration
        self.last_actions = []
        self.last_x_positions = []

        return self.get_state()

    def step(self, action):
        self.steps += 1
        reward = 0

        old_x = self.player.x
        old_lives = self.player.lives

        new_bullet = self.player.move(action)
        if new_bullet:
            self.bullets.append(new_bullet)

        fell_off = self.player.update(self.level.platforms)
        if fell_off:
            reward = -50  # ✅ Punition plus sévère
            self.game_over = True
            return self.get_state(), reward, True

        # === DÉTECTION VIBRATION ===
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
                reward -= 3.0  # ✅ Punition vibration augmentée

        # === MOUVEMENT ===
        distance_moved = self.player.x - old_x
        if distance_moved > 2:
            reward += 2.0  # ✅ Récompense avancer augmentée
        elif distance_moved < -2:
            reward -= 1.0  # ✅ Punition reculer augmentée

        # === ACTIONS ===
        if action == 4:  # IDLE
            reward -= 1.0  # ✅ Punition immobilité augmentée
        elif action in [0, 1]:  # Mouvement
            reward += 0.3

        # Spawner ennemis
        for enemy in self.enemies:
            if not enemy.spawned and enemy.x < self.player.x + 500:
                enemy.spawned = True

        # Update ennemis
        for enemy in self.enemies[:]:
            if not enemy.active:
                continue
            enemy_bullet = enemy.update(self.player.x, self.player.y)
            if enemy_bullet:
                self.bullets.append(enemy_bullet)

        # Update projectiles
        for bullet in self.bullets[:]:
            if not bullet.active:
                self.bullets.remove(bullet)
                continue
            bullet.update(self.level.platforms)

        player_rect = self.player.get_rect()

        # === COLLISIONS ENNEMIS ===
        for enemy in self.enemies:
            if enemy.active and enemy.spawned and player_rect.colliderect(enemy.get_rect()):
                if self.player.take_damage():
                    reward = -50  # ✅ Mort = punition sévère
                    self.game_over = True
                    return self.get_state(), reward, True
                else:
                    reward -= 20  # ✅ Perdre vie = très mauvais
                    enemy.active = False

        # === COLLISIONS PROJECTILES ===
        for bullet in self.bullets:
            if bullet.owner == 'enemy' and bullet.active:
                if player_rect.colliderect(bullet.get_rect()):
                    bullet.active = False
                    if self.player.take_damage():
                        reward = -50
                        self.game_over = True
                        return self.get_state(), reward, True
                    else:
                        reward -= 20  # ✅ Touché par balle = très mauvais

        # === TIR JOUEUR ===
        enemies_killed_this_step = 0
        for bullet in self.bullets[:]:
            if bullet.owner == 'player' and bullet.active:
                for enemy in self.enemies:
                    if enemy.active and enemy.spawned and bullet.get_rect().colliderect(enemy.get_rect()):
                        bullet.active = False
                        if enemy.take_damage():
                            enemies_killed_this_step += 1
                            reward += 25  # ✅ Tuer ennemi = très bon
                            self.score += 10
                        break

        # === BONUS SI TUE ENNEMI SANS PERDRE VIE ===
        if enemies_killed_this_step > 0 and old_lives == self.player.lives:
            reward += 10 * enemies_killed_this_step  # Bonus combo

        # === BONUS PROGRESSION ===
        progress_percent = (self.player.x / self.level.flag_x) * 100

        if progress_percent > 25 and not self._reached_25:
            self._reached_25 = True
            # Bonus si atteint avec toutes les vies
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

        # === VICTOIRE ===
        flag_rect = pygame.Rect(self.level.flag_x, self.level.flag_y, 60, 60)
        if player_rect.colliderect(flag_rect):
            # Bonus massif selon vies restantes
            base_reward = 400
            life_bonus = 100 * self.player.lives  # +100 par vie restante
            reward = base_reward + life_bonus  # ✅ Max 700 si 3 vies
            self.victory = True
            return self.get_state(), reward, True

        # Timeout
        if self.steps > 5000:
            reward = -30
            return self.get_state(), reward, True

        return self.get_state(), reward, False

    def get_state(self):
        """État enrichi avec meilleur radar pour projectiles et ennemis"""

        # Position discrétisée (0-9)
        x_bucket = min(9, int(self.player.x / (self.level.flag_x / 10)))

        # Au sol ?
        on_ground = 1 if self.player.on_ground else 0

        # === RADAR ENNEMI AMÉLIORÉ ===
        enemy_dist = 10  # 10 = aucun ennemi
        enemy_direction = 0  # -1=gauche, 0=aucun, 1=droite
        enemy_can_shoot = 0  # 1 si ennemi peut tirer

        spawned_enemies = [e for e in self.enemies if e.active and e.spawned]
        if spawned_enemies:
            # Trouver l'ennemi le plus proche
            closest_enemy = min(spawned_enemies, key=lambda e: abs(e.x - self.player.x))
            distance = abs(closest_enemy.x - self.player.x)

            enemy_dist = min(9, int(distance / 100))
            enemy_direction = 1 if closest_enemy.x > self.player.x else -1

            # L'ennemi peut-il tirer ? (shooter ou stationary à portée)
            if closest_enemy.enemy_type in ['shooter', 'stationary'] and distance < 400:
                enemy_can_shoot = 1

        # === RADAR PROJECTILE CRITIQUE ===
        bullet_danger = 0  # 0=safe, 1=danger proche, 2=DANGER IMMÉDIAT
        bullet_height = 0  # -1=bas, 0=même hauteur, 1=haut

        enemy_bullets = [b for b in self.bullets if b.owner == 'enemy' and b.active]
        if enemy_bullets:
            # Trouver le projectile le plus dangereux
            dangerous_bullets = []
            for b in enemy_bullets:
                distance = abs(b.x - self.player.x)

                # Projectile vient vers moi ?
                coming_at_me = (b.direction == 1 and b.x < self.player.x) or \
                               (b.direction == -1 and b.x > self.player.x)

                # Même hauteur ? (±50 pixels)
                same_height = abs(b.y - (self.player.y + self.player.size // 2)) < 50

                if coming_at_me and same_height:
                    dangerous_bullets.append((distance, b))

            if dangerous_bullets:
                closest_distance, closest_bullet = min(dangerous_bullets, key=lambda x: x[0])

                # Niveaux de danger
                if closest_distance < 100:
                    bullet_danger = 2  # DANGER IMMÉDIAT - SAUTER MAINTENANT
                elif closest_distance < 250:
                    bullet_danger = 1  # Danger proche - se préparer

                # Hauteur relative
                if closest_bullet.y < self.player.y:
                    bullet_height = 1  # Haut
                elif closest_bullet.y > self.player.y + self.player.size:
                    bullet_height = -1  # Bas
                else:
                    bullet_height = 0  # Même hauteur

        return (x_bucket, on_ground, enemy_dist, enemy_direction,
                enemy_can_shoot, bullet_danger, bullet_height)

    def render(self):
        self.camera_x = max(0, min(self.player.x - SCREEN_WIDTH // 3, LEVEL_LENGTH - SCREEN_WIDTH))

        self.screen.fill(BLACK)

        self.level.draw(self.screen, self.camera_x)
        self.player.draw(self.screen, self.camera_x)

        for enemy in self.enemies:
            if enemy.active:
                enemy.draw(self.screen, self.camera_x)

        for bullet in self.bullets:
            if bullet.active:
                bullet.draw(self.screen, self.camera_x)

        lives_text = self.font.render(f"Vies: {self.player.lives}", True, WHITE)
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        progress = int((self.player.x / LEVEL_LENGTH) * 100)
        progress_text = self.small_font.render(f"Progression: {progress}%", True, WHITE)

        self.screen.blit(lives_text, (10, 10))
        self.screen.blit(score_text, (10, 50))
        self.screen.blit(progress_text, (10, 90))

        if self.game_over:
            text = self.font.render("GAME OVER", True, RED)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        elif self.victory:
            text = self.font.render("VICTOIRE !", True, GREEN)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        self.clock.tick(FPS)

    def handle_events(self):
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