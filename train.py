import matplotlib.pyplot as plt
import numpy as np
from game import ContraGame
from rl_agent import QLearningAgent



def train(episodes=1000, render_every=0, continue_training=True):
    """
    Entraîne l'agent Q-Learning sur Contra RL

    Args:
        episodes: Nombre d'épisodes d'entraînement
        render_every: Afficher le jeu tous les N épisodes (0 = jamais)
        continue_training: Charger la Q-table existante si True
    """
    game = ContraGame()
    agent = QLearningAgent(
        actions=[0, 1, 2, 3, 4],
        alpha=0.1,
        gamma=0.95,
        epsilon=0.5  # ✅ Epsilon plus élevé
    )

    # ✅ NOUVEAU : Charger Q-table existante si demandé
    best_win_rate = 0
    if continue_training:
        try:
            agent.load('q_table.pkl')
            # Charger aussi les stats précédentes
            import json
            with open('training_stats.json', 'r') as f:
                stats = json.load(f)
                best_win_rate = stats.get('best_win_rate', 0)
            print(f"📊 Meilleur taux précédent : {best_win_rate:.1f}%")
        except:
            print("🆕 Nouvelle Q-table créée")

    rewards_history = []
    steps_history = []
    wins = 0
    best_progress = 0

    print("=" * 70)
    print("🚀 ENTRAÎNEMENT Q-LEARNING - CONTRA RL")
    print("=" * 70)
    print(f"Épisodes : {episodes}")
    print(f"Alpha : {agent.alpha} | Gamma : {agent.gamma} | Epsilon : {agent.epsilon}")
    print(f"Q-table : {len(agent.q_table)} états-actions")
    print("=" * 70)

    for episode in range(1, episodes + 1):
        state = game.reset()
        total_reward = 0
        steps = 0

        while True:
            if render_every > 0 and episode % render_every == 0:
                game.render()

            action = agent.choose_action(state, training=True)
            next_state, reward, done = game.step(action)
            agent.learn(state, action, reward, next_state, done)

            total_reward += reward
            state = next_state
            steps += 1

            if done:
                break

        agent.decay_epsilon()
        rewards_history.append(total_reward)
        steps_history.append(steps)

        if game.victory:
            wins += 1

        progress = int((game.player.x / game.level.flag_x) * 100)
        if progress > best_progress:
            best_progress = progress

        if episode % 50 == 0:
            avg_reward = np.mean(rewards_history[-50:])
            avg_steps = np.mean(steps_history[-50:])
            win_rate = (wins / episode) * 100

            print(f"📊 Episode {episode:4d}/{episodes} | "
                  f"Reward: {avg_reward:7.2f} | "
                  f"Steps: {avg_steps:6.1f} | "
                  f"ε: {agent.epsilon:.3f} | "
                  f"Wins: {wins:3d} ({win_rate:4.1f}%) | "
                  f"Best: {best_progress}%")

    final_win_rate = (wins / episodes) * 100

    print("\n" + "=" * 70)
    print("✅ ENTRAÎNEMENT TERMINÉ")
    print("=" * 70)
    print(f"Victoires : {wins}/{episodes} ({final_win_rate:.1f}%)")
    print(f"Meilleure progression : {best_progress}%")

    # ✅ NOUVEAU : Sauvegarder UNIQUEMENT si c'est mieux
    if final_win_rate >= best_win_rate:
        print(f"\n🏆 NOUVEAU RECORD ! {final_win_rate:.1f}% > {best_win_rate:.1f}%")
        agent.save('q_table.pkl')

        # Sauvegarder les stats
        import json
        with open('training_stats.json', 'w') as f:
            json.dump({
                'best_win_rate': final_win_rate,
                'best_progress': best_progress,
                'episodes': episodes,
                'q_table_size': len(agent.q_table)
            }, f)
    else:
        print(f"\n⚠️  Pas d'amélioration ({final_win_rate:.1f}% < {best_win_rate:.1f}%)")
        print("   Q-table précédente conservée.")

    plot_training(rewards_history, wins, episodes)
    return agent, rewards_history


def plot_training(rewards_history, wins, episodes):
    """Génère un graphique de l'apprentissage"""
    import matplotlib.pyplot as plt
    import numpy as np

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Graphique 1 : Récompenses
    ax1.plot(rewards_history, alpha=0.3, color='blue', label='Récompense par épisode')

    # Moyenne mobile (100 épisodes)
    window = 100
    if len(rewards_history) >= window:
        moving_avg = np.convolve(rewards_history, np.ones(window) / window, mode='valid')
        ax1.plot(range(window - 1, len(rewards_history)), moving_avg,
                 linewidth=2, color='red', label=f'Moyenne mobile ({window} épisodes)')

    ax1.set_xlabel('Épisode', fontsize=12)
    ax1.set_ylabel('Récompense totale', fontsize=12)
    ax1.set_title(f'Entraînement Q-Learning - Contra RL ({episodes} épisodes)', fontsize=14, fontweight='bold')
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)

    # Graphique 2 : Taux de victoire
    window_win = 50
    win_rates = []
    for i in range(window_win, len(rewards_history) + 1):
        # Compter les victoires dans la fenêtre (récompense proche de 100 = victoire)
        recent = rewards_history[i - window_win:i]
        victories = sum(1 for r in recent if r > 100)  # Heuristique ajustée
        win_rates.append((victories / window_win) * 100)

    if len(win_rates) > 0:
        ax2.plot(range(window_win, len(rewards_history) + 1), win_rates,
                 linewidth=2, color='green', label=f'Taux de victoire ({window_win} épisodes)')

    ax2.set_xlabel('Épisode', fontsize=12)
    ax2.set_ylabel('Taux de victoire (%)', fontsize=12)
    ax2.set_title('Évolution du taux de victoire', fontsize=12, fontweight='bold')
    ax2.legend(loc='lower right')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 100])

    plt.tight_layout()
    plt.savefig('training.png', dpi=150, bbox_inches='tight')
    print(f"✅ Graphique sauvegardé : training.png")
    plt.close()


if __name__ == "__main__":
    # ✅ continue_training=True pour continuer l'apprentissage
    train(episodes=10000, render_every=0, continue_training=True)