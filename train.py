import matplotlib.pyplot as plt
import numpy as np
from game import ContraGame
from rl_agent import QLearningAgent


def train(episodes=1000, render_every=0, continue_training=True):
    """Train Q-Learning agent on Contra RL."""
    game = ContraGame()
    agent = QLearningAgent(
        actions=[0, 1, 2, 3, 4],
        alpha=0.1,
        gamma=0.95,
        epsilon=0
    )

    # Charger Q-table existante si demandé
    best_win_rate = 0
    if continue_training:
        try:
            agent.load('q_table.pkl')
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

    print("=" * 80)
    print("🚀 ENTRAÎNEMENT Q-LEARNING - CONTRA RL")
    print("=" * 80)
    print(f"Épisodes : {episodes}")
    print(f"Alpha : {agent.alpha} | Gamma : {agent.gamma} | Epsilon : {agent.epsilon}")
    print(f"Q-table initiale : {len(agent.q_table)} états-actions")
    print("=" * 80)

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

        # ✅ LOGS DÉTAILLÉS avec ÉTAT
        if episode % 50 == 0:
            avg_reward = np.mean(rewards_history[-50:])
            avg_steps = np.mean(steps_history[-50:])
            win_rate = (wins / episode) * 100

            # ✅ TAILLE Q-TABLE
            qtable_size = len(agent.q_table)

            print(f"📊 Ep {episode:5d}/{episodes} | "
                  f"Reward: {avg_reward:7.2f} | "
                  f"Steps: {avg_steps:6.1f} | "
                  f"ε: {agent.epsilon:.3f} | "
                  f"Wins: {wins:4d} ({win_rate:5.1f}%) | "
                  f"Best: {best_progress:3d}% | "
                  f"Q-table: {qtable_size:6d}")  # ✅ TAILLE Q-TABLE

            # ✅ AFFICHER L'ÉTAT ACTUEL
            print(f"    └─ État actuel: {state}")
            print(f"       (x_pos={state[0]}, au_sol={state[1]}, "
                  f"ennemi_dist={state[2]}, balle_dist={state[3]})")

    final_win_rate = (wins / episodes) * 100

    print("\n" + "=" * 80)
    print("✅ ENTRAÎNEMENT TERMINÉ")
    print("=" * 80)
    print(f"Victoires : {wins}/{episodes} ({final_win_rate:.1f}%)")
    print(f"Meilleure progression : {best_progress}%")
    print(f"Récompense moyenne (100 derniers) : {np.mean(rewards_history[-100:]):.2f}")
    print(f"Q-table finale : {len(agent.q_table)} états-actions appris")  # ✅ TAILLE FINALE

    # Sauvegarder UNIQUEMENT si c'est mieux
    if final_win_rate >= best_win_rate:
        print(f"\n🏆 NOUVEAU RECORD ! {final_win_rate:.1f}% > {best_win_rate:.1f}%")
        agent.save('q_table.pkl')

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

    # ✅ GRAPHIQUE APRÈS ENTRAÎNEMENT
    print("\n📈 Génération du graphique d'apprentissage...")
    plot_training(rewards_history, wins, episodes, agent)

    return agent, rewards_history


def plot_training(rewards_history, wins, episodes, agent):
    """Génère un graphique de l'apprentissage APRÈS entraînement"""

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    # === GRAPHIQUE 1 : RÉCOMPENSES ===
    ax1.plot(rewards_history, alpha=0.3, color='blue', label='Récompense par épisode')

    window = 100
    if len(rewards_history) >= window:
        moving_avg = np.convolve(rewards_history, np.ones(window) / window, mode='valid')
        ax1.plot(range(window - 1, len(rewards_history)), moving_avg,
                 linewidth=2, color='red', label=f'Moyenne mobile ({window} épisodes)')

    ax1.set_xlabel('Épisode', fontsize=11)
    ax1.set_ylabel('Récompense totale', fontsize=11)
    ax1.set_title(f'Récompenses - {episodes} épisodes', fontsize=12, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=9)
    ax1.grid(True, alpha=0.3)

    # === GRAPHIQUE 2 : TAUX DE VICTOIRE ===
    window_win = 50
    win_rates = []
    for i in range(window_win, len(rewards_history) + 1):
        recent = rewards_history[i - window_win:i]
        victories = sum(1 for r in recent if r > 100)
        win_rates.append((victories / window_win) * 100)

    if len(win_rates) > 0:
        ax2.plot(range(window_win, len(rewards_history) + 1), win_rates,
                 linewidth=2, color='green', label=f'Taux victoire ({window_win} épisodes)')

    ax2.set_xlabel('Épisode', fontsize=11)
    ax2.set_ylabel('Taux de victoire (%)', fontsize=11)
    ax2.set_title('Taux de victoire', fontsize=12, fontweight='bold')
    ax2.legend(loc='lower right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 100])

    # === GRAPHIQUE 3 : CROISSANCE Q-TABLE ===
    # (Simulé car on ne stocke pas l'historique, mais on peut l'estimer)
    ax3.text(0.5, 0.5, f'Q-TABLE FINALE\n\n{len(agent.q_table)} états-actions\n\nappris',
             ha='center', va='center', fontsize=16, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax3.axis('off')

    # === GRAPHIQUE 4 : STATISTIQUES FINALES ===
    final_win_rate = (wins / episodes) * 100
    avg_final_reward = np.mean(rewards_history[-100:]) if len(rewards_history) >= 100 else np.mean(rewards_history)

    stats_text = f"""
    STATISTIQUES FINALES

    Victoires: {wins}/{episodes} ({final_win_rate:.1f}%)

    Récompense moyenne (100 derniers): {avg_final_reward:.2f}

    Taille Q-table: {len(agent.q_table)} états

    Epsilon final: {agent.epsilon:.4f}
    """

    ax4.text(0.1, 0.5, stats_text, ha='left', va='center', fontsize=11,
             family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    ax4.axis('off')

    plt.suptitle(f'Entraînement Q-Learning - Contra RL', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('training.png', dpi=150, bbox_inches='tight')
    print(f"✅ Graphique sauvegardé : training.png")

    plt.show()


if __name__ == "__main__":
    train(episodes=5000, render_every=0, continue_training=True)