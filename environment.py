import pygame
from constants import (
    PLAYER_SIZE, RADAR_RANGE_NEAR, RADAR_RANGE_FAR, RADAR_RANGE_MID,
    BUCKET_SIZE, LEVEL_LENGTH, ACTION_IDLE,
    MAX_STEPS,
    REWARD_SHOOT, REWARD_PROGRESS, REWARD_BACKWARD, REWARD_IDLE,
    REWARD_ENEMY_HIT, REWARD_DAMAGE, REWARD_WASTED_BULLET,
    REWARD_SHOOT_NO_TARGET, REWARD_ENEMY_PASSED,
    REWARD_DEATH, REWARD_GOAL, REWARD_LIFE_BONUS, REWARD_TIMEOUT
)
from entities.player import Player
from entities.enemy import Enemy
from level.static_level import StaticLevel
from rendering.camera import Camera


class Environment:
    def __init__(self):
        # Utiliser StaticLevel au lieu du parsing ASCII
        self.level = StaticLevel()

        # Utiliser Player au lieu de player_pos
        self.player = Player()

        # Utiliser Enemy instances au lieu de dicts
        self.enemies = [Enemy(e.x, e.y, e.enemy_type, e.platform if hasattr(e, 'platform') else None)
                       for e in self.level.enemies]

        # Bullet system
        self.bullets = []
        self.player_bullets_shot = []  # Track bullets pour punir tirs inutiles

        # Camera pour la map 3000px
        self.camera = Camera()

        # Tracking
        self.steps = 0
        self.max_x = 0  # Progression maximale (empêche reward pour surplace)
        self.game_over = False
        self.victory = False

    def reset(self):
        self.__init__()
        return self.get_state()

    def step(self, action):
        """Execute one game step with given action.
        Returns: (state, reward, done)
        """
        self.steps += 1
        reward = 0
        old_x = self.player.x
        old_max_x = self.max_x

        # 1. PLAYER ACTION (delegate to Player)
        new_bullet = self.player.move(action)
        if new_bullet:
            self.bullets.append(new_bullet)
            self.player_bullets_shot.append(new_bullet)  # Track pour punir si rate
            reward += REWARD_SHOOT  # Neutre (0)
            # Tir inutile si aucune menace proche
            nearest_enemy_dist = min(
                (abs(e.x - self.player.x) for e in self.enemies if e.active and e.spawned),
                default=None
            )
            if nearest_enemy_dist is None or nearest_enemy_dist > RADAR_RANGE_NEAR:
                reward += REWARD_SHOOT_NO_TARGET

        # 2. PLAYER PHYSICS (delegate to Player)
        fell_off = self.player.update(self.level.platforms)
        if fell_off:
            self.game_over = True
            return self.get_state(), REWARD_DEATH, True

        # 3. PROGRESSION REWARDS (basé sur max_x, pas juste mouvement)
        self.max_x = max(self.max_x, self.player.x)

        # Récompense SEULEMENT si vraie progression (nouveau record)
        if self.player.x > old_max_x:
            progress_amount = self.player.x - old_max_x
            reward += REWARD_PROGRESS * (progress_amount / 10)  # Scaled reward

        # Punition pour recul
        elif self.player.x < old_x - 2:
            reward += REWARD_BACKWARD

        # 5. IDLE PENALTY
        if action == ACTION_IDLE:
            reward += REWARD_IDLE

        # 5. ENEMY SPAWNING & UPDATE
        for enemy in self.enemies:
            # Spawn when player approaches
            if not enemy.spawned and enemy.x < self.player.x + 500:
                enemy.spawned = True

            # Update (movement + shooting for shooters)
            if enemy.active:
                enemy_bullet = enemy.update(self.player.x, self.player.y)
                if enemy_bullet:
                    self.bullets.append(enemy_bullet)

        # 6. BULLET UPDATE & WASTED BULLET PENALTY
        for bullet in self.bullets[:]:
            if not bullet.active:
                # Punir bullets du joueur qui n'ont touché personne
                if bullet.owner == 'player' and bullet in self.player_bullets_shot:
                    reward += REWARD_WASTED_BULLET
                    self.player_bullets_shot.remove(bullet)
                self.bullets.remove(bullet)
                continue
            bullet.update(self.level.platforms)

        # 7. COLLISION DETECTION
        player_rect = self.player.get_rect()

        # Enemy-Player collision
        for enemy in self.enemies:
            if enemy.active and enemy.spawned:
                if player_rect.colliderect(enemy.get_rect()):
                    if self.player.take_damage():
                        self.game_over = True
                        return self.get_state(), REWARD_DEATH, True
                    else:
                        reward += REWARD_DAMAGE  # Déjà négatif
                        enemy.active = False

        # Enemy Bullet-Player collision
        for bullet in self.bullets[:]:
            if bullet.owner == 'enemy' and bullet.active:
                if player_rect.colliderect(bullet.get_rect()):
                    bullet.active = False
                    if self.player.take_damage():
                        self.game_over = True
                        return self.get_state(), REWARD_DEATH, True
                    else:
                        reward += REWARD_DAMAGE  # Déjà négatif

        # Player Bullet-Enemy collision
        for bullet in self.bullets[:]:
            if bullet.owner == 'player' and bullet.active:
                for enemy in self.enemies:
                    if enemy.active and enemy.spawned:
                        if bullet.get_rect().colliderect(enemy.get_rect()):
                            bullet.active = False
                            # Retirer de la liste des bullets à punir (a touché un ennemi!)
                            if bullet in self.player_bullets_shot:
                                self.player_bullets_shot.remove(bullet)
                            if enemy.take_damage():
                                reward += REWARD_ENEMY_HIT
                            break

        # 7bis. Punir les ennemis laissés derrière (non éliminés)
        for enemy in self.enemies:
            if enemy.active and enemy.spawned and enemy.x < self.player.x - 250:
                reward += REWARD_ENEMY_PASSED

        # 8. VICTORY CHECK
        flag_rect = pygame.Rect(self.level.flag_x, self.level.flag_y, 60, 60)
        if player_rect.colliderect(flag_rect):
            # Bonus vitesse: moins de steps = plus de points
            # Optimal ~1000 steps, max 5000
            speed_bonus = max(0, (5000 - self.steps) / 5)  # 0-1000 points
            reward = REWARD_GOAL + (REWARD_LIFE_BONUS * self.player.lives) + speed_bonus
            self.victory = True
            return self.get_state(), reward, True

        # 9. TIMEOUT
        if self.steps > MAX_STEPS:
            return self.get_state(), REWARD_TIMEOUT, True

        return self.get_state(), reward, False

    def do(self, action):
        """Wrapper pour compatibilité avec Agent"""
        return self.step(action)

    def _observe_pits(self):
        """Détection fossés avec largeur et sol restant."""
        # 1. Chercher fossé le plus proche (0-600px devant)
        closest_pit = None
        pit_distance = 0
        pit_width = 0

        for pit in self.level.pits:
            dist = pit.x - self.player.x
            if 0 < dist < RADAR_RANGE_FAR:
                if closest_pit is None or dist < pit_distance:
                    closest_pit = pit
                    pit_distance = dist
                    pit_width = pit.width

        # Bucketing
        pit_dist_bucket = min(12, int(pit_distance / BUCKET_SIZE)) if closest_pit else 0
        pit_width_bucket = min(5, int(pit_width / BUCKET_SIZE) + 1) if closest_pit else 0

        # 2. Sol sous les pieds (pixels avant le vide)
        ground_under_feet = 0
        for platform in self.level.platforms:
            if platform.y <= self.player.y + PLAYER_SIZE <= platform.y + platform.height:
                pixels_remaining = (platform.x + platform.width) - (self.player.x + PLAYER_SIZE)
                if pixels_remaining > 0:
                    if pixels_remaining < 30:
                        ground_under_feet = 1
                    elif pixels_remaining < 60:
                        ground_under_feet = 2
                    elif pixels_remaining < 100:
                        ground_under_feet = 3
                    else:
                        ground_under_feet = 4
                    break

        return (pit_dist_bucket, pit_width_bucket, ground_under_feet)

    def _observe_platforms(self):
        """Analyser plateformes devant pour navigation."""
        platforms_ahead = [p for p in self.level.platforms
                          if 0 < p.x - self.player.x < RADAR_RANGE_FAR]

        if not platforms_ahead:
            return (0, 0)

        # Plateforme la plus proche
        closest = min(platforms_ahead, key=lambda p: abs(p.x - self.player.x))
        distance = closest.x - self.player.x

        # Distance bucket
        platform_ahead_dist = min(12, int(distance / BUCKET_SIZE))

        # Hauteur relative
        height_diff = self.player.y - closest.y
        if height_diff < -80:
            platform_ahead_height = 2    # Beaucoup plus haut
        elif height_diff < -40:
            platform_ahead_height = 1    # Plus haut
        elif height_diff < 40:
            platform_ahead_height = 0    # Même niveau
        elif height_diff < 80:
            platform_ahead_height = -1   # Plus bas
        else:
            platform_ahead_height = -2   # Beaucoup plus bas

        return (platform_ahead_dist, platform_ahead_height)

    def _observe_enemies(self):
        """Tracker ennemis multiples avec type."""
        spawned = [e for e in self.enemies if e.active and e.spawned]

        if not spawned:
            return (0, 0, 0)

        # Ennemi le plus proche
        closest = min(spawned, key=lambda e: abs(e.x - self.player.x))
        distance = abs(closest.x - self.player.x)

        closest_enemy_dist = min(12, int(distance / BUCKET_SIZE))
        closest_enemy_type = 2 if closest.enemy_type in ['shooter', 'stationary'] else 1

        # Comptage zone proche (<200px)
        enemy_count_near = min(3, sum(1 for e in spawned
                                      if abs(e.x - self.player.x) < RADAR_RANGE_NEAR))

        return (closest_enemy_dist, closest_enemy_type, enemy_count_near)

    def _observe_bullets(self):
        """Tracker balles multiples incoming."""
        enemy_bullets = [b for b in self.bullets if b.owner == 'enemy' and b.active]

        if not enemy_bullets:
            return (0, 0, 0)

        # Filtrer balles dangereuses (incoming + même hauteur)
        dangerous = []
        for b in enemy_bullets:
            distance = abs(b.x - self.player.x)
            coming = (b.direction == 1 and b.x < self.player.x) or \
                    (b.direction == -1 and b.x > self.player.x)
            same_height = abs(b.y - self.player.y) < 50

            if coming and same_height:
                dangerous.append((distance, b))

        if not dangerous:
            return (0, 0, 0)

        # Trier par distance
        dangerous.sort()
        closest_dist = dangerous[0][0]

        # Niveau danger
        if closest_dist < 100:
            bullet_danger_level = 3
        elif closest_dist < 200:
            bullet_danger_level = 2
        elif closest_dist < 400:
            bullet_danger_level = 1
        else:
            bullet_danger_level = 0

        closest_bullet_dist = min(8, int(closest_dist / BUCKET_SIZE))
        bullet_count = min(3, len(dangerous))

        return (bullet_danger_level, closest_bullet_dist, bullet_count)

    def _observe_goal(self):
        """Direction et distance au drapeau."""
        flag_x = LEVEL_LENGTH - 100  # Position approximative du drapeau

        distance = flag_x - self.player.x

        if distance < 0:
            flag_direction = -1
        elif distance < 50:
            flag_direction = 0  # Atteint
        else:
            flag_direction = 1

        flag_distance = min(10, int(abs(distance) / 300))

        return (flag_direction, flag_distance)

    def get_state(self):
        """État enrichi 18D avec radar multi-menaces."""
        # A. Player state (5D)
        x_bucket = min(59, int(self.player.x / BUCKET_SIZE))  # 50px buckets
        on_ground = 1 if self.player.on_ground else 0

        # Velocity Y bucket (0=ground, 1=rising, 2=falling)
        if self.player.on_ground:
            vel_y_bucket = 0
        elif self.player.vel_y < -5:
            vel_y_bucket = 1  # Rising
        else:
            vel_y_bucket = 2  # Falling

        # Velocity X bucket (-1=left, 0=idle, 1=right)
        if self.player.vel_x < -1:
            vel_x_bucket = -1
        elif self.player.vel_x > 1:
            vel_x_bucket = 1
        else:
            vel_x_bucket = 0

        can_jump = 1 if self.player.on_ground else 0

        # B-F. Observation modules
        pit_state = self._observe_pits()           # 3D: pit_distance, pit_width, ground_under_feet
        platform_state = self._observe_platforms() # 2D: platform_ahead_dist, platform_ahead_height
        enemy_state = self._observe_enemies()      # 3D: closest_enemy_dist, closest_enemy_type, enemy_count_near
        bullet_state = self._observe_bullets()     # 3D: bullet_danger_level, closest_bullet_dist, bullet_count
        goal_state = self._observe_goal()          # 2D: flag_direction, flag_distance

        # Retour état 18D (5 + 3 + 2 + 3 + 3 + 2 = 18)
        return (x_bucket, on_ground, vel_y_bucket, vel_x_bucket, can_jump,
                *pit_state, *platform_state, *enemy_state, *bullet_state, *goal_state)
