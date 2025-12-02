import time
from game import ContraGame
from rl_agent import QLearningAgent


def play(episodes=5, delay=0.01):
    """Demonstration of trained agent."""
    game = ContraGame()
    agent = QLearningAgent()

    agent.load('q_table.pkl')

    print("=" * 70)
    print("DEMONSTRATION - TRAINED AGENT")
    print("=" * 70)
    print(f"Episodes: {episodes}")
    print(f"Mode: Pure exploitation (epsilon = 0)")
    print("=" * 70)

    for episode in range(1, episodes + 1):
        print(f"\nEpisode {episode}/{episodes}")

        state = game.reset()
        total_reward = 0
        steps = 0

        while True:
            game.render()
            time.sleep(delay)

            action = agent.choose_action(state, training=False)
            next_state, reward, done = game.step(action)

            total_reward += reward
            state = next_state
            steps += 1

            if done:
                if game.victory:
                    result = "VICTORY"
                else:
                    result = "DEFEAT"

                progress = int((game.player.x / game.level.flag_x) * 100)

                print(f"{result} | "
                      f"Reward: {total_reward:7.2f} | "
                      f"Score: {game.score:3d} | "
                      f"Steps: {steps:4d} | "
                      f"Progress: {progress}%")

                time.sleep(2)
                break

    print("\n" + "=" * 70)
    print("Demonstration completed")
    print("=" * 70)


if __name__ == "__main__":
    play(episodes=5, delay=0.01)
