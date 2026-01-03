"""Game constants for Contra RL."""

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Sizes
PLAYER_SIZE = 32
ENEMY_SIZE = 32
BULLET_SIZE = 8
PLATFORM_HEIGHT = 20

# Physics
GRAVITY = 0.8
JUMP_FORCE = -15
PLAYER_SPEED = 10
ENEMY_SPEED = 2.5
BULLET_SPEED = 20

# Gameplay
PLAYER_MAX_LIVES = 3
ENEMY_SHOOT_RANGE = 400
LEVEL_LENGTH = 3000

# Actions
ACTION_LEFT = 0
ACTION_RIGHT = 1
ACTION_JUMP = 2
ACTION_SHOOT = 3
ACTION_IDLE = 4

ACTIONS = [ACTION_LEFT, ACTION_RIGHT, ACTION_JUMP, ACTION_SHOOT, ACTION_IDLE]

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
ORANGE = (255, 165, 0)
DARK_GRAY = (64, 64, 64)

# ============================================================================
# HYPERPARAMÈTRES Q-LEARNING (Modifiables pour Exploration/Exploitation)
# ============================================================================

# PHASE D'EXPLORATION (Début d'entraînement)
# - EPSILON élevé (0.8-0.9) = beaucoup d'exploration
# - ALPHA élevé (0.2-0.3) = apprentissage rapide
# - GAMMA moyen (0.9-0.95) = équilibre présent/futur

# PHASE D'EXPLOITATION (Après convergence ~95% Win%)
# - EPSILON bas (0.0-0.1) = exploitation de la politique apprise
# - ALPHA bas (0.01-0.05) = raffiner sans tout casser
# - GAMMA élevé (0.95-0.99) = valoriser objectif long terme

EPSILON = 0.3   # Taux d'exploration (0.0 = 100% exploitation, 1.0 = 100% exploration)
ALPHA = 0.1    # Learning rate (0.0 = pas d'apprentissage, 1.0 = apprentissage immédiat)
GAMMA = 1.0   # Discount factor (0.0 = ignorer futur, 1.0 = futur = présent)

# ============================================================================
# RADAR CONFIGURATION (Système d'observation 18D)
# ============================================================================

RADAR_RANGE_NEAR = 200      # Zone menace immédiate (px)
RADAR_RANGE_MID = 400       # Zone menace moyenne (px)
RADAR_RANGE_FAR = 600       # Zone planning/anticipation (px)
BUCKET_SIZE = 50            # Discrétisation spatiale (px)
GROUND_CHECK_AHEAD = 100    # Vérification continuité plateforme (px)
