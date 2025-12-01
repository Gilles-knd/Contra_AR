import pickle
import random
from collections import defaultdict


class QLearningAgent:
    """
    Agent Q-Learning pour Contra RL

    Utilise la formule de Q-Learning :
    Q(s,a) ← Q(s,a) + α[r + γ·max_a' Q(s',a') - Q(s,a)]

    où:
    - α (alpha) = learning rate (vitesse d'apprentissage)
    - γ (gamma) = discount factor (importance du futur)
    - ε (epsilon) = exploration rate (exploration vs exploitation)
    """

    def __init__(self, actions=[0, 1, 2, 3, 4], alpha=0.1, gamma=0.95, epsilon=0.3):
        """
        Initialise l'agent Q-Learning

        Args:
            actions: Actions possibles [0=LEFT, 1=RIGHT, 2=JUMP, 3=SHOOT, 4=IDLE]
            alpha: Learning rate (0.1 = apprentissage modéré)
            gamma: Discount factor (0.95 = valorise le futur)
            epsilon: Exploration rate (0.3 = 30% exploration)
        """
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = 0.01  # Minimum d'exploration
        self.epsilon_decay = 0.995  # Décroissance progressive

        # Q-table : dictionnaire {(état, action): Q-value}
        # Utilise defaultdict pour initialiser à 0 automatiquement
        self.q_table = defaultdict(float)

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
        Mise à jour Q-Learning après une action

        Formule : Q(s,a) ← Q(s,a) + α[r + γ·max_a' Q(s',a') - Q(s,a)]

        Args:
            state: État avant l'action
            action: Action prise
            reward: Récompense reçue
            next_state: État après l'action
            done: True si l'épisode est terminé
        """
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