from constants import SCREEN_WIDTH, LEVEL_LENGTH


class Camera:
    def __init__(self):
        self.x = 0

    def update(self, player_x):
        """Mettre à jour la caméra pour suivre le joueur."""
        self.x = max(0, min(player_x - SCREEN_WIDTH // 3, LEVEL_LENGTH - SCREEN_WIDTH))

    def get_x(self):
        """Get la position de la caméra"""
        return self.x
