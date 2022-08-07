from random import shuffle
from tabulate import tabulate # type: ignore

class Player:
    def __init__(self, name, position):
        self.name = name
        self.position = position

class Board:
    grid = []
    COLUMNS = 7
    ROWS = 6

    for row in range(ROWS):
        grid.append([''] * COLUMNS)

    headers = [str(header) for header in range(COLUMNS)]
    row_ids = [str(row_id) for row_id in range(ROWS)]
    board = tabulate(grid, headers=headers, showindex=row_ids, tablefmt='fancy_grid')

    def __repr__(self):
        return self.board

    def __str__(self):
        return self.board

    def print_board(self):
        print('\n' * 5)
        print(self.board)
        print('\n' * 5)

def _get_player_names_and_shuffle():
    one_player = input("Enter your name: ")
    other_player = input("Enter other player's name: ")
    players = [one_player, other_player]
    shuffle(players)
    return players


def play_game():
    board = Board()
    print(board)
    players = _get_player_names_and_shuffle()
    print(players)
    print(f"{players[0]} goes first")

play_game()