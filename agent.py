# ============================================================================
# AGENT
# ============================================================================
import pickle

from constants import ACTIONS, GAMMA, ALPHA, EPSILON
from random import choice, random


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
        max_next_q = 0 if done else max(self.qtable[next_state].values())

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