from random import shuffle
from typing import List

from tabulate import tabulate # type: ignore
from termcolor import colored  # type: ignore


class Player:
    def __init__(self, name, marker):
        self.name = name
        self.marker = marker
        self._points = 0

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, value):
        if type(value) == int:
            if (value % 10) == 0:
                self._points = value
            else:
                raise ValueError("Point must be a multiple of 10")
        else:
            raise ValueError("Point must be an integer")


class Board:
    COLUMNS = 7
    ROWS = 6

    def __init__(self):
        self.grid: List[List[str]] = []
        for row in range(self.ROWS):
            self.grid.append([''] * self.COLUMNS)

    def tabulate_board(self):
        headers = [str(header) for header in range(self.COLUMNS)]
        return tabulate(self.grid, headers=headers, tablefmt="fancy_grid", numalign="center", stralign="center")

    def __repr__(self):
        return self.tabulate_board()

    def __str__(self):
        return self.tabulate_board()

    def print_board(self):
        
        print('\n' * 5)
        print(self.tabulate_board())
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
            if '' in row: #  Board not full, no tie yet
                return False
        return True

def _get_player_names():
    while True:
        one_player = input("Enter your name: ").strip()
        if one_player:
            break
        print("You must enter a name")

    while True:
        other_player = input("Enter other player's name: ").strip()
        if other_player.lower() == one_player.lower():
            print("A player already exists with that name. Choose another name")
            continue
        if other_player:
            break
        print("You must enter a name")

    return [one_player, other_player]

def shuffle_players(players):
    shuffle(players)
    try:
        print(f"{players[0].name} goes first")
    except AttributeError:
        print(f"{players[0]} goes first")
    return tuple(players)


def _get_players_colors(player):
    while True:
        color = input(f"{player}, Choose a color between Red and Blue. Enter 'R' for Red or 'B' for Blue: ")
        if color.lower() == 'r':
            return ('red', 'blue')
        if color.lower() == 'b':
            return ('blue', 'red')
        else:
            print("Invalid input.")
            continue

def _calculate_and_display_final_result(players):
    player_one, player_two = players
    print(f"\n{player_one.name} has {player_one.points} points")
    print(f"{player_two.name} has {player_two.points} points\n")
    if player_one.points > player_two.points:
        print(f"{player_one.name} {player_one.marker} wins!\n")
    elif player_two.points > player_one.points:
        print(f"{player_two.name} {player_two.marker} wins!\n")
    else:
        print("Game ends in a tie\n")

def play_game():
    print("****CONNECT4*****")
    players = shuffle_players(_get_player_names())
    colors = _get_players_colors(players[0])


    player_one = Player(players[0], colored('O', colors[0], attrs=['bold']))
    player_two = Player(players[1], colored('O', colors[1], attrs=['bold']))
    
    playing = True

    while playing:
        board = Board()
        board.print_board() #  Print board at start of game

        # Take turns to play till there's a winner
        while True:

            board.play_at_position(player_one)
            board.print_board()

            if board.check_win(player_one):
                player_one.points += 10
                print(f"\n{player_one.name} {player_one.marker} wins this round!\n")
                break

            if board.check_tie():
                print("\nIt's a tie!\n")
                break


            board.play_at_position(player_two)
            board.print_board()

            if board.check_win(player_two):
                player_two.points += 10
                print(f"\n{player_two.name} {player_two.marker} wins this round!\n")
                break

            if board.check_tie():
                print("\nIt's a tie!\n")
                break
        
        print("\n\nAt the end of this round, ")
        print(f"{player_one.name} has {player_one.points} points")
        print(f"{player_two.name} has {player_two.points} points\n\n")

        while True:
            play_again = input("Want to play another round? Enter 'Y' for 'yes' and 'N' for 'no': ").lower()
            if play_again == 'y':
                player_one, player_two = shuffle_players([player_one, player_two])
                break
            elif play_again == 'n':
                print("\n\nGame ended")
                _calculate_and_display_final_result([player_one, player_two])
                print("Thanks for playing")
                playing = False
                break
            else:
                print("Invalid input.")
                continue

        
if __name__ == "__main__":
    play_game()