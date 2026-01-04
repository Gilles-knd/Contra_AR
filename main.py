import pygame
import pickle
import os
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # Backend sans display pour l'entraînement headless
import matplotlib.pyplot as plt

# Imports des composants modulaires
from constants import (
    EPSILON, EPSILON_DECAY, EPSILON_MIN, LEVEL_LENGTH,
    MAX_STEPS,
    REWARD_PROGRESS, REWARD_BACKWARD, REWARD_IDLE,
    REWARD_ENEMY_HIT, REWARD_ENEMY_PASSED, REWARD_WASTED_BULLET,
    REWARD_SHOOT_NO_TARGET, REWARD_GOAL, REWARD_LIFE_BONUS, REWARD_DAMAGE
)
from environment import Environment
from agent import Agent
from rendering.window import ContraWindow
from logging_utils import append_training_log


# ============================================================================
# ENTRAÎNEMENT ET EXÉCUTION
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
    initial_progress_size = len(agent.progress_history)
    initial_win_size = len(agent.win_history)

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
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                        window.debug_mode = not window.debug_mode

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

        # Décroissance epsilon (exploration) par épisode
        agent.epsilon = max(EPSILON_MIN, agent.epsilon * EPSILON_DECAY)

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
    save_model = False

    # Calculer progression moyenne du nouveau modèle (SESSION uniquement)
    session_progress = agent.progress_history[initial_progress_size:]
    session_wins = agent.win_history[initial_win_size:]

    def avg_last_100(seq):
        return sum(seq[-100:]) / min(100, len(seq)) if seq else 0

    new_avg_progress = avg_last_100(session_progress)
    new_win_rate = avg_last_100(session_wins) * 100
    final_metrics = agent.get_metrics()

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
        save_model = True

    if save_model:
        agent.save("agent.pkl")
        final_metrics = agent.get_metrics()
        print(f"✓ Modèle sauvegardé (Win%={final_metrics['win_rate']:.1f}%)")

    # Journaliser la session dans training_stats.json
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "episodes": episodes,
        "alpha": agent.alpha,
        "gamma": agent.gamma,
        "epsilon_start": EPSILON,
        "epsilon_min": EPSILON_MIN,
        "epsilon_decay": EPSILON_DECAY,
        "rewards": {
            "progress": REWARD_PROGRESS,
            "backward": REWARD_BACKWARD,
            "idle": REWARD_IDLE,
            "enemy_hit": REWARD_ENEMY_HIT,
            "enemy_passed": REWARD_ENEMY_PASSED,
            "wasted_bullet": REWARD_WASTED_BULLET,
            "shoot_no_target": REWARD_SHOOT_NO_TARGET,
            "goal": REWARD_GOAL,
            "life_bonus": REWARD_LIFE_BONUS,
            "damage": REWARD_DAMAGE,
        },
        "session_win_rate": round(new_win_rate, 2),
        "session_progress": round(new_avg_progress, 2),
    }
    append_training_log(log_entry)

    # Graphiques de présentation académique (3 panels) - SESSION ACTUELLE UNIQUEMENT
    if len(agent.history) > initial_history_size:
        # Extraire seulement les épisodes de cette session
        session_history = agent.history[initial_history_size:]
        session_win_history = agent.win_history[initial_win_size:]
        session_progress_history = agent.progress_history[initial_progress_size:]

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
        window_size = 100
        if len(session_win_history) > 0:
            win_rate_rolling = [
                sum(session_win_history[max(0, i-window_size):i]) / min(window_size, i) * 100
                for i in range(1, len(session_win_history)+1)
            ]
            axes[1].plot(win_rate_rolling, color='green')
            axes[1].set_title(f'Taux de Victoire - Session Actuelle ({len(session_win_history)} eps, fenêtre {window_size})',
                             fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Épisode')
            axes[1].set_ylabel('Win Rate (%)')
            axes[1].axhline(y=95, color='orange', linestyle='--', label='Objectif 95%')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)

        # Panel 3: Progression dans le niveau - SESSION ACTUELLE
        if len(session_progress_history) > 0:
            axes[2].plot(session_progress_history, color='purple', alpha=0.7)
            axes[2].set_title(f'Progression dans Niveau - Session Actuelle ({len(session_progress_history)} eps)',
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
# MAIN
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
