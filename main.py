# main.py - Contra RL avec map complète et architecture propre
"""
SYSTÈME DE REWARDS - VERSION 2.1 (Anti-Vibration Fix)

Ce fichier implémente un environnement RL pour le jeu Contra avec un système
de récompenses optimisé qui encourage la VRAIE progression.

CHANGEMENTS V2.1 (FIX VIBRATION):
  ✅ REWARD_PROGRESS augmenté 5x (1.0 → 5.0)
  ✅ TIME_PENALTY supprimé (encourageait vibration)
  ✅ IDLE_PENALTY augmenté 3x (-0.1 → -0.3)
  ✅ Bonus vitesse ajouté pour victoires rapides
  ✅ REWARD_DAMAGE augmenté (-20 → -30)

POURQUOI L'AGENT VIBRAIT (V2.0):
  Problème: Avancer 100px = +10 points, mais coûte -2 en temps
           Vibrer = -2 en temps seulement
  Solution: Supprimer time penalty, augmenter reward progression 5x

REWARDS PAR CATÉGORIE:

Progression:
  REWARD_PROGRESS = +5.0      Vraie progression (5x augmenté!)
  REWARD_BACKWARD = -1.0      Reculer (2x augmenté)
  REWARD_IDLE = -0.3          Inactivité (3x augmenté)
  REWARD_TIME_PENALTY = 0     SUPPRIMÉ

Combat:
  REWARD_SHOOT = 0            Tir neutre
  REWARD_ENEMY_HIT = +50      Tuer ennemi
  REWARD_WASTED_BULLET = -1   Tir inutile (réduit)
  REWARD_DAMAGE = -30         Prendre dégât (augmenté)

Fin de partie:
  REWARD_DEATH = -50          Mort/chute fossé
  REWARD_GOAL = +1000         Atteindre flag
  REWARD_LIFE_BONUS = +100    Bonus par vie
  SPEED_BONUS = 0-400         Bonus vitesse (victoire rapide)
  REWARD_TIMEOUT = -30        Timeout

EXEMPLE CALCULS:
  Avancer 100px:     5.0 * (100/10) = +50 points  ✅
  Vibrer 100 steps:  0 progression = 0 points     ❌
  Idle 100 steps:    100 * -0.3 = -30 points      ❌

  Victoire rapide (1000 steps, 3 vies):
    - Goal: 1000
    - Vies: 300
    - Speed bonus: (5000-1000)/10 = 400
    - Progression: ~1500
    - Total: ~3200 points

SCORES ESTIMÉS (V2.1):
  Maximum théorique: ~3000-3500 points
  Typique avec victoire: 1500-2500 points
  Typique sans victoire: 200-800 points

HYPERPARAMÈTRES:
  Epsilon: 0.9 → 0.01 (decay 0.995)
  Alpha: 0.2
  Gamma: 0.95
"""

import pygame
import pickle
import os
import matplotlib.pyplot as plt
from random import choice, random
from collections import defaultdict

# Imports des constants centralisés
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BLACK, WHITE, RED, GREEN, BLUE, ORANGE, GRAY, YELLOW,
    GRAVITY, JUMP_FORCE, PLAYER_SPEED,
    PLAYER_SIZE, ENEMY_SIZE, BULLET_SIZE,
    LEVEL_LENGTH, PLAYER_MAX_LIVES,
    ACTIONS, ACTION_LEFT, ACTION_RIGHT, ACTION_JUMP, ACTION_SHOOT, ACTION_IDLE,
    EPSILON, ALPHA, GAMMA  # Hyperparamètres Q-Learning
)

# Imports des composants modulaires
from entities.player import Player
from entities.enemy import Enemy
from entities.bullet import Bullet
from level.static_level import StaticLevel
from rendering.camera import Camera

# ============================================================================
# RL CONSTANTS
# ============================================================================
MAX_STEPS = 5000  # Limite de steps par épisode


# Rewards - Actions
REWARD_SHOOT = 0  # Neutre (punition si rate, reward si touche)
REWARD_PROGRESS = 5.0  # Vraie progression (augmenté 5x pour valoriser mouvement)
REWARD_BACKWARD = -1.0  # Punition recul (augmentée 2x)
REWARD_IDLE = -0.3  # Punition inactivité (augmentée 3x)

# Rewards - Combat
REWARD_ENEMY_HIT = 50  # Tuer ennemi
REWARD_DAMAGE = -30  # Augmenté pour éviter contact
REWARD_WASTED_BULLET = -1  # Réduit (était trop punitif)

# Rewards - Fin de partie
REWARD_DEATH = -50
REWARD_GOAL = 100
REWARD_LIFE_BONUS = 30
REWARD_TIMEOUT = -30


# ============================================================================
# ENVIRONNEMENT (utilise les composants modulaires)
# ============================================================================
class Environment:
    """RL Environment using modular game components.

    State Space (11 dimensions):
    - x_bucket: Position (0-29, 100px per bucket)
    - on_ground: On platform (0-1)
    - vel_y_bucket: Vertical velocity (0=ground, 1=rising, 2=falling)
    - vel_x_bucket: Horizontal velocity (-1=left, 0=idle, 1=right)
    - near_pit: Pit proximity (-1=left, 0=none, 1=right)
    - ground_ahead: Platform ahead (0=no, 1=yes, 2=enemy on platform)
    - enemy_dist: Closest enemy distance (0-10)
    - enemy_direction: Enemy position (-1=left, 0=none, 1=right)
    - enemy_can_shoot: Shooter in range (0-1)
    - bullet_danger: Incoming bullet threat (0=safe, 1=far, 2=close)
    - bullet_height: Bullet vertical position (-1=below, 0=level, 1=above)
    """

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

        # 8. VICTORY CHECK
        flag_rect = pygame.Rect(self.level.flag_x, self.level.flag_y, 60, 60)
        if player_rect.colliderect(flag_rect):
            # Bonus vitesse: moins de steps = plus de points
            # Optimal ~1000 steps, max 5000
            speed_bonus = max(0, (5000 - self.steps) / 10)  # 0-400 points
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
        from constants import BUCKET_SIZE, RADAR_RANGE_FAR, PLAYER_SIZE

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
        from constants import BUCKET_SIZE, RADAR_RANGE_FAR

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
        from constants import BUCKET_SIZE, RADAR_RANGE_NEAR

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
        from constants import BUCKET_SIZE

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
        from constants import LEVEL_LENGTH

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
        from constants import BUCKET_SIZE

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


# ============================================================================
# AGENT
# ============================================================================
class Agent:
    def __init__(self, env):
        self.env = env
        self.qtable = {}
        self.history = []
        self.score = 0

        # Hyperparamètres Q-Learning (depuis constants.py)
        self.epsilon = EPSILON
        self.alpha = ALPHA
        self.gamma = GAMMA

        # Métriques d'apprentissage
        self.wins = 0
        self.total_episodes = 0
        self.progress_history = []
        self.win_history = []

    def reset(self):
        if self.score != 0:
            self.history.append(self.score)
        self.score = 0
        return self.env.reset()

    def best_action(self):
        state = self.env.get_state()

        # Exploration vs Exploitation (epsilon-greedy)
        if random() < self.epsilon:
            # Exploration: action aléatoire
            return choice(ACTIONS)

        # Exploitation : meilleure action connue
        if state in self.qtable:
            q_values = self.qtable[state]
            max_q = max(q_values.values())
            best_actions = [a for a, q in q_values.items() if q == max_q]
            return choice(best_actions)
        else:
            # État non vu, initialiser
            self.qtable[state] = {a: 0 for a in ACTIONS}
            return choice(ACTIONS)

    def do(self, action):
        state = self.env.get_state()
        next_state, reward, done = self.env.do(action)

        # Initialiser Q-values si nécessaire
        if state not in self.qtable:
            self.qtable[state] = {a: 0 for a in ACTIONS}
        if next_state not in self.qtable:
            self.qtable[next_state] = {a: 0 for a in ACTIONS}

        # Q-learning
        old_q = self.qtable[state][action]
        max_next_q = max(self.qtable[next_state].values())

        # Formule: Q(s,a) = Q(s,a) + α[r + γ*maxQ(s',a') - Q(s,a)]
        new_q = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)
        self.qtable[state][action] = new_q

        self.score += reward
        return next_state, reward, done

    def get_metrics(self):
        """Calcule les métriques d'apprentissage simplifiées."""
        # Taux de VRAIE victoire (100 derniers épisodes) = % qui atteignent le flag
        if len(self.win_history) > 0:
            recent_wins = sum(self.win_history[-100:])
            win_rate = (recent_wins / min(100, len(self.win_history))) * 100
        else:
            win_rate = 0

        # Score moyen (100 derniers)
        avg_score = sum(self.history[-100:]) / min(100, len(self.history)) if self.history else 0

        return {
            'win_rate': win_rate,
            'avg_score': avg_score,
            'q_size': len(self.qtable),
            'epsilon': self.epsilon,
        }

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump((self.qtable, self.history, self.win_history, self.progress_history), f)

    def load(self, filename):
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            # Support ancien format (qtable, history) et nouveau (qtable, history, win_history, progress_history)
            if len(data) == 2:
                self.qtable, self.history = data
                # Reconstruire win_history et progress_history à partir de history (approximation)
                self.win_history = [1 if s > 1000 else 0 for s in self.history]
                self.progress_history = []  # Pas de données historiques
            elif len(data) == 4:
                self.qtable, self.history, self.win_history, self.progress_history = data


# ============================================================================
# FENÊTRE PYGAME (avec Camera et délégation)
# ============================================================================
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

    def draw(self):
        # Mise à jour de la caméra
        self.env.camera.update(self.env.player.x)
        camera_x = self.env.camera.get_x()

        self.screen.fill(BLACK)

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
        lives_text = self.font.render(f"Vies: {self.env.player.lives}", True, WHITE)
        score_text = self.font.render(f"Score: {self.agent.score:.1f}", True, WHITE)
        steps_text = self.small_font.render(f"Steps: {self.env.steps}", True, WHITE)

        progress = int((self.env.player.x / LEVEL_LENGTH) * 100)
        progress_text = self.small_font.render(f"Progress: {progress}%", True, WHITE)

        state_text = self.small_font.render(f"State: {self.env.get_state()}", True, WHITE)
        qtable_text = self.small_font.render(f"Q-table: {len(self.agent.qtable)}", True, WHITE)

        self.screen.blit(lives_text, (10, 10))
        self.screen.blit(score_text, (10, 50))
        self.screen.blit(steps_text, (10, 90))
        self.screen.blit(progress_text, (10, 120))
        self.screen.blit(state_text, (10, 150))
        self.screen.blit(qtable_text, (10, 180))

        # Messages de fin
        if self.env.game_over:
            text = self.font.render("GAME OVER", True, RED)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        elif self.env.victory:
            text = self.font.render("VICTOIRE!", True, GREEN)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        self.clock.tick(self.fps)

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

            # Action de l'agent
            action = self.agent.best_action()
            state, reward, done = self.agent.do(action)

            # Affichage
            self.draw()

        return True

    def close(self):
        pygame.quit()


# ============================================================================
# ENTRÂNEMENT ET EXÉCUTION (comme dans maze)
# ============================================================================
def train(episodes=1000, render_every=100):
    """Entraînement Q-Learning simplifié pour présentation académique"""
    env = Environment()
    agent = Agent(env)

    # Charger si existe
    if os.path.exists("agent.pkl"):
        agent.load("agent.pkl")
        print("Agent chargé depuis agent.pkl")

    print("="*60)
    print("ENTRAÎNEMENT Q-LEARNING - Contra RL")
    print("="*60)
    print(f"Épisodes: {episodes}")
    print(f"Hyperparamètres:")
    print(f"  • Epsilon (exploration):  {agent.epsilon:.3f}")
    print(f"  • Alpha (learning rate):  {agent.alpha:.3f}")
    print(f"  • Gamma (discount):       {agent.gamma:.3f}")
    print("="*60 + "\n")

    # Sauvegarder la taille initiale de l'historique pour les graphiques
    initial_history_size = len(agent.history)

    # Créer fenêtre de rendering si nécessaire
    window = None
    if render_every > 0:
        window = ContraWindow(agent, fps=60)

    for episode in range(episodes):
        state = agent.reset()
        done = False
        total_reward = 0
        steps = 0
        max_x = 0  # Tracking de la progression maximale

        # Détermine si on affiche cet épisode
        should_render = render_every > 0 and episode % render_every == 0

        while not done and steps < MAX_STEPS:
            # Affichage occasionnel
            if should_render and window:
                # Gérer événements pygame pour éviter freeze
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print("\nFermeture de la fenêtre détectée. Arrêt du training.")
                        if window:
                            pygame.quit()
                        agent.save("agent.pkl")
                        return

                # Dessiner l'état actuel
                window.draw()

            action = agent.best_action()
            next_state, reward, done = agent.do(action)
            state = next_state
            total_reward += reward
            steps += 1

            # Tracker la progression maximale
            max_x = max(max_x, agent.env.player.x)

        # Tracking
        agent.total_episodes += 1
        progress_pct = (max_x / LEVEL_LENGTH) * 100

        # Vraie victoire = atteindre le flag (95%+ du niveau)
        is_victory = progress_pct >= 95
        if is_victory:
            agent.wins += 1

        agent.progress_history.append(progress_pct)
        agent.win_history.append(1 if is_victory else 0)

        # Logs
        if episode % 50 == 0:
            metrics = agent.get_metrics()
            qtable_size = len(agent.qtable)

            # Calculer progression moyenne
            if len(agent.progress_history) > 0:
                avg_progress = sum(agent.progress_history[-100:]) / min(100, len(agent.progress_history))
            else:
                avg_progress = 0

            print(f"Ep {episode}: "
                  f"Score={total_reward:.1f}, "
                  f"Avg={metrics['avg_score']:.1f}, "
                  f"Win%={metrics['win_rate']:.1f}, "
                  f"Prog={avg_progress:.1f}%, "
                  f"Q-size={qtable_size}, "
                  f"ε={agent.epsilon:.3f}, "
                  f"α={agent.alpha:.3f}, "
                  f"γ={agent.gamma:.3f}")

    # Sauvegarde conditionnelle: basée sur PROGRESSION MOYENNE (critère principal)
    save_model = True
    final_metrics = agent.get_metrics()

    # Calculer progression moyenne du nouveau modèle
    if len(agent.progress_history) > 0:
        new_avg_progress = sum(agent.progress_history[-100:]) / min(100, len(agent.progress_history))
    else:
        new_avg_progress = 0

    if os.path.exists("agent.pkl"):
        # Charger ancien modèle pour comparaison
        try:
            with open("agent.pkl", 'rb') as f:
                old_data = pickle.load(f)

            # Support ancien format et nouveau format
            if len(old_data) == 2:
                old_qtable, old_history = old_data
                old_win_history = [1 if s > 1000 else 0 for s in old_history]
                # Ancien format: pas de progression historique, on approxime
                old_avg_progress = 0  # Inconnu, on sauvegarde le nouveau
            elif len(old_data) == 4:
                old_qtable, old_history, old_win_history, old_progress_history = old_data
                # Calculer progression moyenne de l'ancien modèle
                if len(old_progress_history) > 0:
                    old_avg_progress = sum(old_progress_history[-100:]) / min(100, len(old_progress_history))
                else:
                    old_avg_progress = 0
            else:
                # Format inconnu
                old_avg_progress = 0
                old_win_history = []

            # Calculer aussi Win% pour affichage
            old_wins = sum(old_win_history[-100:]) if old_win_history else 0
            old_win_rate = (old_wins / min(100, len(old_win_history))) * 100 if old_win_history else 0
            new_win_rate = final_metrics['win_rate']

            # CRITÈRE DE SAUVEGARDE: Progression moyenne (critère principal)
            # On sauvegarde si: nouvelle progression > ancienne progression
            # OU si progression égale mais Win% meilleur
            if new_avg_progress > old_avg_progress + 0.5:  # +0.5% d'amélioration minimum
                print(f"\n✓ Nouveau modèle MEILLEUR:")
                print(f"  Progression: {new_avg_progress:.1f}% > {old_avg_progress:.1f}%")
                print(f"  Win Rate: {new_win_rate:.1f}% (vs {old_win_rate:.1f}%)")
                print(f"  → Sauvegarde dans agent.pkl")
                save_model = True
            elif abs(new_avg_progress - old_avg_progress) <= 0.5 and new_win_rate > old_win_rate:
                print(f"\n✓ Nouveau modèle MEILLEUR:")
                print(f"  Progression: {new_avg_progress:.1f}% ≈ {old_avg_progress:.1f}%")
                print(f"  Win Rate: {new_win_rate:.1f}% > {old_win_rate:.1f}%")
                print(f"  → Sauvegarde dans agent.pkl")
                save_model = True
            else:
                print(f"\n⚠ Nouveau modèle moins bon ou équivalent:")
                print(f"  Progression: {new_avg_progress:.1f}% vs {old_avg_progress:.1f}%")
                print(f"  Win Rate: {new_win_rate:.1f}% vs {old_win_rate:.1f}%")
                print(f"  → Conservation de l'ancien modèle")
                save_model = False
        except Exception as e:
            print(f"\n✓ Erreur de lecture ancien modèle ({e}) → Sauvegarde nouveau modèle")
            save_model = True
    else:
        print(f"\n✓ Premier modèle → Sauvegarde dans agent.pkl")
        print(f"  Progression: {new_avg_progress:.1f}%, Win Rate: {final_metrics['win_rate']:.1f}%")

    if save_model:
        agent.save("agent.pkl")
        print(f"✓ Modèle sauvegardé (Win%={final_metrics['win_rate']:.1f}%)")

    # Graphiques de présentation académique (3 panels) - SESSION ACTUELLE UNIQUEMENT
    if len(agent.history) > initial_history_size:
        # Extraire seulement les épisodes de cette session
        session_history = agent.history[initial_history_size:]

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # Panel 1: Score par épisode (SESSION ACTUELLE)
        axes[0].plot(session_history, color='blue', alpha=0.6)
        axes[0].set_title(f'Score par Épisode - Session Actuelle ({len(session_history)} eps)',
                         fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Épisode')
        axes[0].set_ylabel('Score')
        axes[0].axhline(y=1000, color='r', linestyle='--', label='Seuil victoire (atteint flag)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Panel 2: Win rate glissant (100 épisodes) - SESSION ACTUELLE
        window = 100
        if len(agent.win_history) > 0:
            win_rate_rolling = [sum(agent.win_history[max(0, i-window):i]) / min(window, i) * 100
                               for i in range(1, len(agent.win_history)+1)]
            axes[1].plot(win_rate_rolling, color='green')
            axes[1].set_title(f'Taux de Victoire - Session Actuelle (fenêtre {window} eps)',
                             fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Épisode')
            axes[1].set_ylabel('Win Rate (%)')
            axes[1].axhline(y=95, color='orange', linestyle='--', label='Objectif 95%')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)

        # Panel 3: Progression dans le niveau - SESSION ACTUELLE
        if len(agent.progress_history) > 0:
            axes[2].plot(agent.progress_history, color='purple', alpha=0.7)
            axes[2].set_title('Progression dans Niveau - Session Actuelle',
                             fontsize=12, fontweight='bold')
            axes[2].set_xlabel('Épisode')
            axes[2].set_ylabel('Progression (%)')
            axes[2].axhline(y=100, color='g', linestyle='--', label='Flag (100%)')
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('training_metrics.png', dpi=150, bbox_inches='tight')
        print(f"\n✓ Graphiques sauvegardés: training_metrics.png ({len(session_history)} épisodes)")
        plt.show()
    else:
        print("\n⚠ Pas de nouveaux épisodes à afficher dans les graphiques")

    # Fermer la fenêtre pygame si elle existe
    if window:
        pygame.quit()
        print("✓ Fenêtre de rendering fermée")

    return agent


def play(agent=None):
    """Jouer avec l'agent entraîné"""
    if agent is None:
        env = Environment()
        agent = Agent(env)
        if os.path.exists("agent.pkl"):
            agent.load("agent.pkl")
            print("Agent chargé depuis agent.pkl")
        else:
            print("Aucun agent entraîné trouvé! Utilisation d'un agent non entraîné...")
            agent.epsilon = 1.0  # Plus d'exploration pour un agent non entraîné

    window = ContraWindow(agent)

    print("Démarrage de la démo... (Q pour quitter)")

    running = True
    while running:
        running = window.run_episode()
        print(f"Épisode terminé! Score: {agent.score:.1f}")
        pygame.time.wait(1000)  # Pause entre épisodes

    window.close()


# ============================================================================
# MAIN (comme dans maze)
# ============================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "train":
            episodes = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
            render_every = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            train(episodes=episodes, render_every=render_every)
        elif sys.argv[1] == "play":
            play()
    else:
        # Mode interactif
        print("Usage:")
        print("  python main.py train [episodes] [render_every]  # Entraîner l'agent")
        print("    Exemple: python main.py train 1000 50          # Affiche tous les 50 épisodes")
        print("    Exemple: python main.py train 1000 0           # Pas d'affichage (rapide)")
        print("  python main.py play                             # Jouer avec l'agent")
        print("  python main.py                                  # Ce message")