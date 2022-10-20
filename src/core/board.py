from typing import List
from tabulate import tabulate # type: ignore


class Board:
    COLUMNS = 7
    ROWS = 6

    def __init__(self):
        self.grid: List[List[str]] = []
        for _ in range(self.ROWS):
            self.grid.append([''] * self.COLUMNS)

    def _tabulate_board(self):
        headers = [str(header) for header in range(self.COLUMNS)]
        return tabulate(self.grid, headers=headers, tablefmt="fancy_grid", numalign="center", stralign="center")

    def __repr__(self):
        return self._tabulate_board()

    def __str__(self):
        return self._tabulate_board()

    def print_board(self):
        
        print('\n' * 5)
        print(self._tabulate_board())
        print('\n' * 5)

    def _get_position(self, player):
        while True:
            choice = input(f"{player.name} {player.marker}, enter the position you want to play at between 0 and 6: ")
           
            try:
                choice = int(choice)
                if not choice in range(0, 7):
                    raise ValueError("Input must be between 0 and 6")
            except ValueError:
                print(f"{player.name}, you must enter a number between 0 and 6")     
                continue       
            else:
                return choice


    def play_at_position(self, player):
        choice = self._get_position(player)        
        for i, row in reversed(list(enumerate(self.grid))):
            if row[choice] == '':
                row[choice] = player.marker
                break
            else:
                if i == 0:
                    print("That column is full")
                    self.play_at_position(player) #  Call function again to take in another input
                continue         

    def _check_horizontal_win(self, player_marker):
        win_pattern = [player_marker] * 4
        for row in self.grid:
            for idx in range(len(row) - len(win_pattern) + 1):
                if row[idx : idx + len(win_pattern)] == win_pattern:
                    return True
        return False

    def _check_vertical_win(self, player_marker):
        for col in range(self.COLUMNS):
            for row in range(self.ROWS-3):
                if player_marker == self.grid[row][col] == self.grid[row+1][col] == self.grid[row+2][col] == self.grid[row+3][col]:
                    return True
        return False

    def _check_left_to_right_diagonal_win(self, player_marker):
        for col in range(self.COLUMNS-3):
            for row in range(self.ROWS-3):
                if player_marker == self.grid[row][col] == self.grid[row+1][col+1] == self.grid[row+2][col+2] == self.grid[row+3][col+3]:
                    return True
        return False

    def _check_right_to_left_diagonal_win(self, player_marker):
        for col in range(self.COLUMNS-1, 2, -1):
            for row in range(self.ROWS-3):
                if player_marker == self.grid[row][col] == self.grid[row+1][col-1] == self.grid[row+2][col-2] == self.grid[row+3][col-3]:
                    return True
        return False

    def check_win(self, player):
        player_marker = player.marker
        return any([self._check_horizontal_win(player_marker), self._check_vertical_win(player_marker), self._check_right_to_left_diagonal_win(player_marker), self._check_left_to_right_diagonal_win(player_marker)])

    def check_tie(self):
        for row in self.grid:
            return '' not in row