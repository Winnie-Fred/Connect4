from random import shuffle
from termcolor import colored  # type: ignore

from player import Player
from board import Board
from level import Level

class Connect4Game:

    POINTS_FOR_WINNING_ONE_ROUND = 10

    def __init__(self):
        self.level = Level()

    def _about_game(self):
        print("\n\n")
        print("CONNECT4".center(100, '-'))
        print("\nWelcome! The rules are simple. The first player to connect four of their tokens in a row\n"
            "horizontally, vertically or diagonally wins the round and earns 10 points.\n"
            "Note that the tokens occupy the lowest available space within the column.\n"
            "This game uses a board with 6 rows and 7 columns.\n"
            "You can play as many rounds as you like. "
            "Points from each round will be added up at the end of the game.\n"
            "The overall winner of the game is the player with the most points at the end of the game.\n"
            "That's it. You are all set!\n")
        input("Press Enter key to continue . . . ")


    def _get_player_names(self):
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

    def _shuffle_players(self, players):
        shuffle(players)
        print("Randomly choosing who to go first . . .")
        try:
            print(f"{players[0].name} goes first")
        except AttributeError:
            print(f"{players[0]} goes first")
        return tuple(players)


    def _get_players_colors(self, player):
        while True:
            color = input(f"{player}, Choose a color for your token between Red and Blue. Enter 'R' for Red or 'B' for Blue: ")
            if color.lower() == 'r':
                return ('red', 'blue')
            if color.lower() == 'b':
                return ('blue', 'red')
            else:
                print("Invalid input.")
                continue

    def _calculate_and_display_final_result(self, players):
        player_one, player_two = players
        print(f"\n{player_one.name} has {player_one.points} points")
        print(f"{player_two.name} has {player_two.points} points\n")
        if player_one.points > player_two.points:
            print(f"{player_one.name} {player_one.marker} wins!\n")
        elif player_two.points > player_one.points:
            print(f"{player_two.name} {player_two.marker} wins!\n")
        else:
            print("Game ends in a tie\n")

    def play_game(self):
        self._about_game()
        players = self._shuffle_players(self._get_player_names())
        colors = self._get_players_colors(players[0])


        player_one = Player(players[0], colored('O', colors[0], attrs=['bold']))
        player_two = Player(players[1], colored('O', colors[1], attrs=['bold']))
        
        playing = True

        while playing:
            print("\n\n", f"ROUND {self.level.current_level}".center(50, '-'))
            board = Board()
            board.print_board() #  Print board at start of each round

            # Take turns to play till there's a winner
            while True:

                board.play_at_position(player_one)
                board.print_board()

                if board.check_win(player_one):
                    player_one.points += self.POINTS_FOR_WINNING_ONE_ROUND
                    print(f"\n{player_one.name} {player_one.marker} wins this round!\n")
                    break

                if board.check_tie():
                    print("\nIt's a tie!\n")
                    break


                board.play_at_position(player_two)
                board.print_board()

                if board.check_win(player_two):
                    player_two.points += self.POINTS_FOR_WINNING_ONE_ROUND
                    print(f"\n{player_two.name} {player_two.marker} wins this round!\n")
                    break

                if board.check_tie():
                    print("\nIt's a tie!\n")
                    break
            
            print(f"\n\nAt the end of round {self.level.current_level}, ")
            print(f"{player_one.name} has {player_one.points} points")
            print(f"{player_two.name} has {player_two.points} points\n\n")

            while True:
                play_again = input("Want to play another round? Enter 'Y' for 'yes' and 'N' for 'no': ").lower()
                if play_again == 'y':
                    # Shuffle the players again before starting next round.
                    self.level.current_level += 1
                    player_one, player_two = self._shuffle_players([player_one, player_two])
                    break
                elif play_again == 'n':
                    self._calculate_and_display_final_result([player_one, player_two])
                    print("Thanks for playing")
                    playing = False
                    break
                else:
                    print("Invalid input.")
                    continue

        
if __name__ == "__main__":
    connect4game = Connect4Game()
    connect4game.play_game()