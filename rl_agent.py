import pickle
import random
from collections import defaultdict, deque


class QLearningAgent:
    """Enhanced Q-Learning Agent with Experience Replay."""

    def __init__(self, actions=[0, 1, 2, 3, 4], alpha=0.1, gamma=0.95, epsilon=0.5):
        """Initialize Q-Learning agent with experience replay."""
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.9992

        self.q_table = defaultdict(float)

        self.replay_buffer = deque(maxlen=10000)
        self.replay_batch_size = 32
        self.replay_frequency = 5
        self.step_counter = 0

    def choose_action(self, state, training=True):
        """Choose action using epsilon-greedy strategy."""
        if training and random.random() < self.epsilon:
            return random.choice(self.actions)
        else:
            q_values = [self.q_table[(state, action)] for action in self.actions]
            max_q = max(q_values)
            best_actions = [a for a, q in zip(self.actions, q_values) if q == max_q]
            return random.choice(best_actions)

    def learn(self, state, action, reward, next_state, done):
        """Update Q-Learning with experience replay."""
        self.remember(state, action, reward, next_state, done)
        self._update_q_value(state, action, reward, next_state, done)

        self.step_counter += 1
        if self.step_counter % self.replay_frequency == 0:
            self.replay()

    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer."""
        self.replay_buffer.append((state, action, reward, next_state, done))

    def _update_q_value(self, state, action, reward, next_state, done):
        """Update Q-value for a single experience."""
        current_q = self.q_table[(state, action)]

        if done:
            target_q = reward
        else:
            next_q_values = [self.q_table[(next_state, a)] for a in self.actions]
            max_next_q = max(next_q_values)
            target_q = reward + self.gamma * max_next_q

        self.q_table[(state, action)] = current_q + self.alpha * (target_q - current_q)

    def replay(self):
        """Learn from a batch of stored experiences."""
        if len(self.replay_buffer) < self.replay_batch_size:
            return

        batch = random.sample(self.replay_buffer, self.replay_batch_size)

        for state, action, reward, next_state, done in batch:
            self._update_q_value(state, action, reward, next_state, done)

    def decay_epsilon(self):
        """Decay epsilon after each episode."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, filepath='q_table.pkl'):
        """Save Q-table to file."""
        with open(filepath, 'wb') as f:
            pickle.dump(dict(self.q_table), f)
        print(f"Q-table saved: {filepath}")
        print(f"Size: {len(self.q_table)} state-actions")

    def load(self, filepath='q_table.pkl'):
        """Load Q-table from file."""
        try:
            with open(filepath, 'rb') as f:
                loaded_table = pickle.load(f)
                self.q_table = defaultdict(float, loaded_table)
            print(f"Q-table loaded: {filepath}")
            print(f"Size: {len(self.q_table)} state-actions")
        except FileNotFoundError:
            print(f"File not found: {filepath}")
            print("New Q-table will be created.")