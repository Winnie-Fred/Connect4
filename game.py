class Player:
    def __init__(self, name, position):
        self.name = name
        self.position = position

def print_board():
    COLUMNS = 7
    ROWS = 6
    board = []
    print('\n' * 5)
    for row in range(ROWS):
        board.append([''] * COLUMNS)
    for row in board:
        print(row)
    print('\n' * 5)

print_board()
