class Player:
    def __init__(self, name, position):
        self.name = name
        self.position = position

class Board:
    board = []
    COLUMNS = 7
    ROWS = 6

    for row in range(ROWS):
        board.append([''] * COLUMNS)

    def print_board(self):
        print('\n' * 5) 
        for row in self.board:
            print(row)
        print('\n' * 5)

board = Board()
board.print_board()
