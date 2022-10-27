from collections import namedtuple

import pygame
from pygame.sprite import Sprite

from core.board import Board as BaseBoard
from pygame_version.states import TokenState

check_win_result = namedtuple("check_win_result", "win_or_not, four_in_a_row, marker")

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

    def _check_horizontal_win(self, player_marker):
        win_pattern = [player_marker] * 4
        four_in_a_row = ()
        for row_num, row in enumerate(self.grid):
            for idx in range(len(row) - len(win_pattern) + 1):
                if row[idx : idx + len(win_pattern)] == win_pattern:
                    four_in_a_row = ((row_num, idx), (row_num, idx+1), (row_num, idx+2), (row_num, idx+3))
                    return check_win_result(True, four_in_a_row, row[idx])
        return check_win_result(False, four_in_a_row, None)

    def _check_vertical_win(self, player_marker):
        four_in_a_row = ()
        for col in range(self.COLUMNS):
            for row in range(self.ROWS-3):
                if player_marker == self.grid[row][col] == self.grid[row+1][col] == self.grid[row+2][col] == self.grid[row+3][col]:
                    four_in_a_row = ((row, col), (row+1, col), (row+2, col), (row+3, col))
                    return check_win_result(True, four_in_a_row, self.grid[row][col])
        return check_win_result(False, four_in_a_row, None)

    def _check_left_to_right_diagonal_win(self, player_marker):
        four_in_a_row = ()
        for col in range(self.COLUMNS-3):
            for row in range(self.ROWS-3):
                if player_marker == self.grid[row][col] == self.grid[row+1][col+1] == self.grid[row+2][col+2] == self.grid[row+3][col+3]:
                    four_in_a_row = ((row, col), (row+1, col+1), (row+2, col+2), (row+3, col+3))
                    return check_win_result(True, four_in_a_row, self.grid[row][col])
        return check_win_result(False, four_in_a_row, None)

    def _check_right_to_left_diagonal_win(self, player_marker):
        four_in_a_row = ()
        for col in range(self.COLUMNS-1, 2, -1):
            for row in range(self.ROWS-3):
                if player_marker == self.grid[row][col] == self.grid[row+1][col-1] == self.grid[row+2][col-2] == self.grid[row+3][col-3]:
                    four_in_a_row = ((row, col), (row+1, col-1), (row+2, col-2), (row+3, col-3))
                    return check_win_result(True, four_in_a_row, self.grid[row][col])
        return check_win_result(False, four_in_a_row, None)

    def check_win(self, player):
        player_marker = player.marker
        win_check_results = [self._check_horizontal_win(player_marker), self._check_vertical_win(player_marker), self._check_right_to_left_diagonal_win(player_marker), self._check_left_to_right_diagonal_win(player_marker)]
        for win_check in win_check_results:
            if True is win_check.win_or_not:
                return win_check
        return check_win_result(False, (), None)


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
        

class GlowingToken(Sprite):
    def __init__(self, token_color, position):
        super().__init__()
        self.position = position
        self.not_glowing_token = pygame.image.load(f'../../images/glowing tokens/not glowing {token_color} token.png').convert_alpha()
        self.glowing_token = pygame.image.load(f'../../images/glowing tokens/glowing {token_color} token.png').convert_alpha()
        self.fully_glowing_token = pygame.image.load(f'../../images/glowing tokens/fully glowing {token_color} token.png').convert_alpha()
        self.glowing_tokens = [self.not_glowing_token, self.glowing_token, self.fully_glowing_token]
        self.token_image = self.not_glowing_token
        self.current_token = 0
        self.last_update = pygame.time.get_ticks()
        self.cooldown = 500

    @property
    def image(self):
        return self.token_image

    @property
    def rect(self):
        position_x, position_y = self.position
        x_pos = position_x - 34
        if self.token_image == self.not_glowing_token or self.token_image == self.glowing_token:
            return (x_pos, position_y-28)        
        if self.token_image == self.fully_glowing_token:        
            return (x_pos, position_y-40)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self):
        self.current_time = pygame.time.get_ticks()
        
        if self.current_time - self.last_update >= self.cooldown:
            self.current_token += 1
            self.last_update = self.current_time
            if self.current_token >= len(self.glowing_tokens):
                self.current_token = 0
        self.token_image = self.glowing_tokens[self.current_token]

