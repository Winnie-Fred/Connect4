from random import shuffle
from typing import List

from tabulate import tabulate # type: ignore
from termcolor import colored  # type: ignore


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
            choice = input(f"{player.name}, Enter the position you want to play at: ")
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
                    self.play_at_position(player) # Call function again to take in another input
                continue    

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

    player_one = Player(players[0], colored('O', colors[0], attrs=['bold']))
    board.play_at_position(player_one)
    board.print_board()
    
    player_two = Player(players[1], colored('O', colors[1], attrs=['bold']))
    board.play_at_position(player_two)
    board.print_board()
        

play_game()

