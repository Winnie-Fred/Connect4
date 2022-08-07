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


def play_game():
    board = Board()
    print(board)

play_game()