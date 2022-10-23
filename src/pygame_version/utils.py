from collections import namedtuple

from pygame.sprite import Sprite

from core.board import Board as BaseBoard
from pygame_version.states import TokenState

class Board(BaseBoard):
    def __init__(self):
        super().__init__()

    def play_at_position(self, player, choice):
        play_status = namedtuple("play_status", "status, details")
        for i, row in reversed(list(enumerate(self.grid))):
            if row[choice] == '':
                row[choice] = player.marker
                return play_status(True, "")
            else:
                if i == 0:
                    return play_status(False, "That column is full")
                continue

    def check_if_column_is_full(self, column):
        for i, row in reversed(list(enumerate(self.grid))):
            if row[column] == '':
                continue
            else:
                if i == 0:
                    return True
        return False


class Token(Sprite):
    GRAVITY = 0.6
    def __init__(self, token, marker, position_on_grid, final_position, initial_position):
        super().__init__()
        self.marker = marker
        self.image = token
        self.position_on_grid = position_on_grid
        self.current_position = initial_position
        self.final_position = final_position
        self.speed = 0
        self.token_state = TokenState.FALLING
        

    @property
    def rect(self):
        return self.current_position

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self):
        """Make the token fall with increasing speed (with gravity) if it hasn't reached the lowest possible point in the column"""
        if self.current_position != self.final_position:
            self.speed += self.GRAVITY
            current_pos_x, current_pos_y = self.current_position
            _, final_pos_y = self.final_position

            y_position = current_pos_y + self.speed
            distance = final_pos_y - y_position
            if distance <= 0:
                self.current_position = self.final_position
                self.token_state = TokenState.JUST_LANDED
            else:          
                self.current_position = (current_pos_x, y_position)
        else:
            self.token_state = TokenState.HAS_LANDED
        return self.token_state
        
