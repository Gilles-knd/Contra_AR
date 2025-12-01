"""Camera system for Contra RL game."""

from constants import SCREEN_WIDTH, LEVEL_LENGTH


class Camera:
    """Camera that follows the player."""

    def __init__(self):
        self.x = 0

    def update(self, player_x):
        """Update camera position to follow player."""
        self.x = max(0, min(player_x - SCREEN_WIDTH // 3, LEVEL_LENGTH - SCREEN_WIDTH))

    def get_x(self):
        """Get camera x position."""
        return self.x
