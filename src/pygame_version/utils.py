from collections import namedtuple
from core.board import Board as BaseBoard


class Board(BaseBoard):
    def __init__(self):
        super().__init__()

    def play_at_position(self, player, choice):
        play_status = namedtuple("play_status", "status, details")
        for i, row in reversed(list(enumerate(self.grid))):
            if row[choice] == '':
                row[choice] = player.marker
                return play_status(True, '')
            else:
                if i == 0:
                    return play_status(False, "That column is full")
                continue