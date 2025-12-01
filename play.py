import time
from game import ContraGame
from rl_agent import QLearningAgent


def play(episodes=5, delay=0.01):
    """
    Démonstration de l'agent entraîné

    Args:
        episodes: Nombre d'épisodes à jouer
        delay: Délai entre chaque frame (en secondes)
    """
    # Initialisation
    game = ContraGame()
    agent = QLearningAgent()

    # Charger la Q-table entraînée
    agent.load('q_table.pkl')

    print("=" * 70)
    print("🎮 DÉMONSTRATION - AGENT ENTRAÎNÉ")
    print("=" * 70)
    print(f"Nombre d'épisodes : {episodes}")
    print(f"Mode : EXPLOITATION PURE (epsilon = 0)")
    print("=" * 70)

    for episode in range(1, episodes + 1):
        print(f"\n▶️  Épisode {episode}/{episodes}")

        state = game.reset()
        total_reward = 0
        steps = 0

        while True:
            # Rendu graphique
            game.render()
            time.sleep(delay)

            # Choisir la MEILLEURE action (pas d'exploration)
            action = agent.choose_action(state, training=False)

            # Exécuter l'action
            next_state, reward, done = game.step(action)

            total_reward += reward
            state = next_state
            steps += 1

            if done:
                # Résultat de l'épisode
                if game.victory:
                    result = "✅ VICTOIRE"
                    color = "\033[92m"  # Vert
                else:
                    result = "❌ DÉFAITE"
                    color = "\033[91m"  # Rouge

                reset = "\033[0m"  # Reset couleur

                progress = int((game.player.x / game.level.flag_x) * 100)

                print(f"{color}{result}{reset} | "
                      f"Reward: {total_reward:7.2f} | "
                      f"Score: {game.score:3d} | "
                      f"Steps: {steps:4d} | "
                      f"Progression: {progress}%")

                time.sleep(2)  # Pause avant l'épisode suivant
                break

    print("\n" + "=" * 70)
    print("✅ Démonstration terminée")
    print("=" * 70)


if __name__ == "__main__":
    # Lancer la démonstration
    play(episodes=5, delay=0.01)