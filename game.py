from random import shuffle
from typing import List

from tabulate import tabulate # type: ignore
from termcolor import colored  # type: ignore
import numpy as np


class Player:
    def __init__(self, name, marker):
        self.name = name
        self.marker = marker
                

class Board:
    grid: List[List[str]] = []
    COLUMNS = 7
    ROWS = 6

    for row in range(ROWS):
        grid.append([''] * COLUMNS)

    def tabulate_board(self):
        headers = [str(header) for header in range(self.COLUMNS)]
        row_ids = [str(row_id) for row_id in range(self.ROWS)]
        return tabulate(self.grid, headers=headers, showindex=row_ids, tablefmt='fancy_grid')

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
            choice = input(f"{player.name}, enter the position you want to play at between 0 and 6: ")
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
        # return self._check_vertical_win(player_marker)
        
        # return self._check_horizontal_win(player_marker)
        # return self._check_left_to_right_diagonal_win(player_marker)
        return self._check_right_to_left_diagonal_win(player_marker)


def _get_player_names_and_shuffle():
    one_player = input("Enter your name: ")
    other_player = input("Enter other player's name: ")
    players = [one_player, other_player]
    shuffle(players)
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
            print("Invalid input. Enter 'R' for Red or 'B' for Blue")
            continue

def play_game():
    board = Board()
    print("****CONNECT4*****")
    players = _get_player_names_and_shuffle()
    colors = _get_players_colors(players[0])

    board.print_board() #  Print board at start of game

    player_one = Player(players[0], colored('O', colors[0], attrs=['bold']))
    player_two = Player(players[1], colored('O', colors[1], attrs=['bold']))
    
    # Take turns to play till there's a winner
    while True:
        board.play_at_position(player_one)
        board.print_board()
        if board.check_win(player_one):
            print(f"{player_one.name} wins!")
            break
        board.play_at_position(player_two)
        board.print_board()
        if board.check_win(player_two):
            print(f"{player_two.name} wins!")
            break

play_game()
