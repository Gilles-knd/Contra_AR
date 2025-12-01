import pickle
import random
from collections import defaultdict, deque


class QLearningAgent:
    """
    Enhanced Q-Learning Agent with Experience Replay for Contra RL

    Utilise la formule de Q-Learning :
    Q(s,a) ← Q(s,a) + α[r + γ·max_a' Q(s',a') - Q(s,a)]

    où:
    - α (alpha) = learning rate (vitesse d'apprentissage)
    - γ (gamma) = discount factor (importance du futur)
    - ε (epsilon) = exploration rate (exploration vs exploitation)
    """

    def __init__(self, actions=[0, 1, 2, 3, 4], alpha=0.1, gamma=0.95, epsilon=0.5):
        """
        Initialise l'agent Q-Learning avec experience replay

        Args:
            actions: Actions possibles [0=LEFT, 1=RIGHT, 2=JUMP, 3=SHOOT, 4=IDLE]
            alpha: Learning rate (0.1 = apprentissage modéré)
            gamma: Discount factor (0.95 = valorise le futur)
            epsilon: Exploration rate (0.5 = 50% exploration initiale)
        """
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = 0.01  # Minimum d'exploration
        self.epsilon_decay = 0.9992  # FIXED: Much slower decay (was 0.995)

        # Q-table : dictionnaire {(état, action): Q-value}
        # Utilise defaultdict pour initialiser à 0 automatiquement
        self.q_table = defaultdict(float)

        # NEW: Experience replay buffer
        self.replay_buffer = deque(maxlen=10000)
        self.replay_batch_size = 32
        self.replay_frequency = 5  # Replay every N steps
        self.step_counter = 0

    def choose_action(self, state, training=True):
        """
        Stratégie epsilon-greedy : exploration vs exploitation

        Args:
            state: État actuel du jeu (x_bucket, on_ground, enemy_dist, bullet_dist)
            training: Si True, fait de l'exploration. Si False, exploitation pure.

        Returns:
            action: Action choisie (0-4)
        """
        if training and random.random() < self.epsilon:
            # EXPLORATION : action aléatoire
            return random.choice(self.actions)
        else:
            # EXPLOITATION : meilleure action connue
            q_values = [self.q_table[(state, action)] for action in self.actions]
            max_q = max(q_values)

            # Si plusieurs actions ont la même Q-value, choisir aléatoirement parmi elles
            best_actions = [a for a, q in zip(self.actions, q_values) if q == max_q]
            return random.choice(best_actions)

    def learn(self, state, action, reward, next_state, done):
        """
        Mise à jour Q-Learning avec experience replay

        Formule : Q(s,a) ← Q(s,a) + α[r + γ·max_a' Q(s',a') - Q(s,a)]

        Args:
            state: État avant l'action
            action: Action prise
            reward: Récompense reçue
            next_state: État après l'action
            done: True si l'épisode est terminé
        """
        # Store experience in replay buffer
        self.remember(state, action, reward, next_state, done)

        # Immediate learning from current experience
        self._update_q_value(state, action, reward, next_state, done)

        # Periodic replay from buffer
        self.step_counter += 1
        if self.step_counter % self.replay_frequency == 0:
            self.replay()

    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer."""
        self.replay_buffer.append((state, action, reward, next_state, done))

    def _update_q_value(self, state, action, reward, next_state, done):
        """Update Q-value for a single experience."""
        # Q-value actuelle
        current_q = self.q_table[(state, action)]

        if done:
            # Si l'épisode est terminé, pas de futur
            target_q = reward
        else:
            # Sinon, on calcule la meilleure Q-value pour l'état suivant
            next_q_values = [self.q_table[(next_state, a)] for a in self.actions]
            max_next_q = max(next_q_values)
            target_q = reward + self.gamma * max_next_q

        # Mise à jour de la Q-value
        self.q_table[(state, action)] = current_q + self.alpha * (target_q - current_q)

    def replay(self):
        """Learn from a batch of stored experiences."""
        if len(self.replay_buffer) < self.replay_batch_size:
            return

        # Sample random batch
        batch = random.sample(self.replay_buffer, self.replay_batch_size)

        # Learn from each experience in batch
        for state, action, reward, next_state, done in batch:
            self._update_q_value(state, action, reward, next_state, done)

    def decay_epsilon(self):
        """Réduit epsilon après chaque épisode pour moins explorer avec le temps"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, filepath='q_table.pkl'):
        """Sauvegarde la Q-table dans un fichier"""
        with open(filepath, 'wb') as f:
            pickle.dump(dict(self.q_table), f)
        print(f"✅ Q-table sauvegardée : {filepath}")
        print(f"   Taille : {len(self.q_table)} états-actions appris")

    def load(self, filepath='q_table.pkl'):
        """Charge une Q-table depuis un fichier"""
        try:
            with open(filepath, 'rb') as f:
                loaded_table = pickle.load(f)
                self.q_table = defaultdict(float, loaded_table)
            print(f"✅ Q-table chargée : {filepath}")
            print(f"   Taille : {len(self.q_table)} états-actions")
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé : {filepath}")
            print("   Une nouvelle Q-table sera créée.")