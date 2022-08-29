import os
import sys
import time
import itertools
import socket
import pickle
from threading import Thread, Event

from termcolor import colored  # type: ignore

from connect4 import Connect4Game
from player import Player
from level import Level
from board import Board

os.system('') # To ensure that escape sequences work, and coloured text is displayed normally and not as weird characters

connect4game = Connect4Game()



class Network:
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"
    POINTS_FOR_WINNING_ONE_ROUND = 10
        

    def __init__(self):
        self.ID = None
        self.you = ""
        self.opponent = ""
        self.player = Player(name='', marker='')
        self.your_turn = False
        self.level = Level()
        

        self.HEADERSIZE = 10
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1"
        self.port = 5050
        self.addr = (self.server, self.port)

        self.loading_thread = Thread()
        self.loaded_json = {}
        self.board_updated_event = Event() 
        self.play_again_reply_received = Event() 
        self.first_player_received = Event()              

        self.connect()


    def connect(self):
        try:
            self.client.connect(self.addr)
        except Exception as e:
            print(f"Connection failed: {e}")
        else:
            self.loading_thread.start()
            Thread(target=self.play_game).start()
            
           

    def send_data(self, data):
        data = pickle.dumps(data)
        data = bytes(f'{len(data):<{self.HEADERSIZE}}', self.FORMAT) + data
        self.client.send(data)

    def _get_other_player_name(self, player):

        while True:
            other_player = input("Enter your name: ").strip()
            if other_player.lower() == player.lower():
                print("A player already exists with that name. Choose another name")
                continue
            if other_player:
                break
            print("You must enter a name")

        return other_player

    def simulate_loading_with_spinner(self, loading_msg, loaded_json):
        NO_OF_CHARACTERS_AFTER_LOADING_MSG = 5
        spaces_to_replace_spinner = ' ' * NO_OF_CHARACTERS_AFTER_LOADING_MSG
        if type(loading_msg) == list:
            yellow_first_part = colored(loading_msg[0], "yellow", attrs=['bold'])
            yellow_last_part = colored(loading_msg[2], "yellow", attrs=['bold'])
            green_first_part = colored(loading_msg[0], "green", attrs=['bold'])
            green_last_part = colored(loading_msg[2], "green", attrs=['bold'])
            yellow_loading_msg = f"{yellow_first_part}{loading_msg[1]}{yellow_last_part}"
            green_loading_msg = f"{green_first_part}{loading_msg[1]}{green_last_part}"
        else:
            yellow_loading_msg = colored(loading_msg, "yellow", attrs=['bold'])
            green_loading_msg = colored(loading_msg, "green", attrs=['bold'])
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if loaded_json != self.loaded_json:
                sys.stdout.write(f'\r{green_loading_msg}{spaces_to_replace_spinner}')
                print("\n")
                break
            sys.stdout.write(f'\r{yellow_loading_msg}  {c}  ')
            sys.stdout.flush()
            time.sleep(0.1)

    def main_game_thread(self):
        playing = True

        while playing:
            print("\n\n", f"ROUND {self.level.current_level}".center(50, '-'))
            self.board = Board()
            self.board.print_board() #  Print board at start of each round

            first_time = True
            while True:
                if self.your_turn:

                    if not first_time: #  Do not wait on first run of loop for board to be updated since no move has been made yet
                        self.board_updated_event.wait() #  Wait until board is updated with other player's latest move
                        self.board_updated_event.clear() #  Unset the event till it is set when board is updated again
                        self.board.print_board() #  Print board to show player their opponent's move

                    # At this point, the opponent has won so we want to break to end this loop and 
                    # so that we do not collect this user's input anymore.
                    if 'round_over' in self.loaded_json: 
                        if self.loaded_json['winner'] is not None:
                            print(f"\n{self.opponent.name} {self.opponent.marker} wins this round")
                            print("Better luck next time!\n")
                            self.opponent.points = self.loaded_json['winner'].points
                        break

                    self.board.play_at_position(self.player)
                    self.board.print_board()
                    self.your_turn = False
                    self.send_data({'board':self.board})

                    if self.board.check_win(self.player):
                        self.player.points += self.POINTS_FOR_WINNING_ONE_ROUND
                        print(f"\n{self.player.name} {self.player.marker} wins this round!\n")
                        self.send_data({'round_over':True, 'winner':self.player})
                        break

                    if self.board.check_tie():
                        print("\nIt's a tie!\n")
                        self.send_data({'round_over':True, 'winner':None})
                        break

                else:
                    # Text is split into a list so that text can be colored separate from marker in the simulate_loading_with_spinner function
                    # If raw string is entered directly, text after the marker does not get coloured.
                    loading_msg = [f"Waiting for {self.opponent.name} ", self.opponent.marker, " to play"]
                    self.your_turn = True
                    self.loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json))
                    self.loading_thread.start()
                first_time = False

            print(f"\n\nAt the end of round {self.level.current_level}, ")
            print(f"You have {self.player.points} points")
            print(f"{self.opponent.name} has {self.opponent.points} points\n\n")

            while True:
                play_again = input("Want to play another round? Choosing 'no' will end the game and close this connection. \nEnter 'Y' for 'yes' and 'N' for 'no': ").lower().strip()
                if play_again == 'y':
                    # Shuffle the players again before starting next round.
                    self.send_data({'play_again':True})

                    if 'play_again' not in self.loaded_json:
                        loading_msg = f"Waiting for {self.opponent.name} to reply"
                        self.loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json))
                        self.loading_thread.start()

                    self.play_again_reply_received.wait()
                    self.play_again_reply_received.clear()

                    if self.loaded_json['play_again']:
                        self.level.current_level += 1 

                        if not self.ID:
                            first_player = connect4game._shuffle_players([self.player, self.opponent])[0]
                            self.send_data({'first_player':first_player})

                        self.first_player_received.wait()
                        self.first_player_received.clear()

                        # The check is between Player objects' names and not the objects themselves because their 
                        # points may be different if one of them is leading from the previous round
                        if self.loaded_json['first_player'].name == self.player.name:
                            self.your_turn = True                            
                        else:
                            self.your_turn = False
                        first_time = True
                        break
                    else:
                        # Opponent does not want to play another round
                        print(f"{self.opponent.name} has quit")
                        print("At the end of the game, ")
                        connect4game._calculate_and_display_final_result([self.player, self.opponent])
                        print("Thanks for playing")
                        self.send_data({'wait_for_new_client':True})                        
                        playing = False
                        break
                elif play_again == 'n':
                    self.send_data({'play_again':False})
                    self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE})
                    print("At the end of the game, ")
                    connect4game._calculate_and_display_final_result([self.player, self.opponent])                    
                    print("Thanks for playing")                    
                    playing = False
                    break
                else:
                    print("Invalid input.")
                    continue        


    def play_game(self): 

        full_msg = b''
        new_msg = True
        while True:
            msg = self.client.recv(16)
            if not msg:
                break
            
            if new_msg:
                msglen = int(msg[:self.HEADERSIZE])                
                new_msg = False


            full_msg += msg


            if len(full_msg)-self.HEADERSIZE == msglen:
                
                # ----------------Use loaded json data here----------------

                self.loaded_json = pickle.loads(full_msg[self.HEADERSIZE:])                          

                # NOTE Calling .join on self.loading_thread ensures that the spinner function has completed 
                # NOTE (and finished using stdout) before attempting to print anything else to stdout.
                # NOTE The first time .join is called, it joins the self.loading_thread instantiated 
                # NOTE and started in the init function of the Network class.

                # ! .join must be called on loading_thread only after loaded pickle of full_msg is assigned to self.loaded_json.
                # ! Otherwise, condition for termination of spinner is never met
                self.loading_thread.join()                 

                new_msg = True
                full_msg = b''
                try:
                    if "id" in self.loaded_json:
                        self.ID = self.loaded_json["id"]
                        self.send_data({'id':self.ID})
                    elif "status" in self.loaded_json:                                                          
                        loading_msg = self.loaded_json['status']  
                        self.loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json))
                        self.loading_thread.start()                        
                    elif "waiting-for-name" in self.loaded_json:                                                              
                        loading_msg = self.loaded_json['waiting-for-name']                                        
                        self.loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json))
                        self.loading_thread.start()
                    elif "get-first-player-name" in self.loaded_json:                                                               
                        connect4game._about_game()                        
                        self.you = connect4game._get_player_name()
                        self.send_data({'you':self.you})
                        loading_msg = "Waiting for other player to enter their name"
                        self.loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json))
                        self.loading_thread.start()                        
                    elif "opponent" in self.loaded_json:                                                             
                        self.opponent = self.loaded_json['opponent']
                        if not self.you:
                            connect4game._about_game()
                            self.you = self._get_other_player_name(self.opponent)
                            self.send_data({'you':self.you})                        
                        print("You are up against: ", self.opponent)                        
                        # Shuffling player names
                        if not self.ID:
                            first_player = connect4game._shuffle_players([self.you, self.opponent])
                            self.send_data({'first':first_player})                      
                    elif "first" in self.loaded_json:
                        first = self.loaded_json['first'][0]
                        if self.ID:
                            print("Randomly choosing who to go first . . .")                    
                            print(f"{first} goes first")
                        if first == self.you:
                            colors = connect4game._get_players_colors(self.you)
                            self.send_data({'colors':colors})
                        else:
                            loading_msg = f"Waiting for {self.opponent} to choose their color"
                            self.loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json))
                            self.loading_thread.start()                            
                    elif "colors" in self.loaded_json:                                                                                     
                        colors = self.loaded_json['colors']                        
                        if first == self.you:
                            self.your_turn = True
                            self.player = Player(self.you, colored('O', colors[0], attrs=['bold']))                            
                        else:
                            self.your_turn = False
                            self.player = Player(self.you, colored('O', colors[1], attrs=['bold']))                        
                        self.send_data({'opponent_player_object':self.player})
                    elif "opponent_player_object" in self.loaded_json:
                        self.opponent = self.loaded_json['opponent_player_object']                        
                        main_game_thread = Thread(target=self.main_game_thread)
                        main_game_thread.start()                        
                    elif "board" in self.loaded_json:
                        self.board = self.loaded_json['board']
                        self.board_updated_event.set() 
                    elif 'play_again' in self.loaded_json:
                        self.play_again_reply_received.set()                        
                    elif 'first_player' in self.loaded_json:
                        self.first_player_received.set()

                except KeyError:
                    self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE})                   
                    break

        
        print("Disconnected")
                    # ----------------Use loaded json data here----------------

if __name__ == "__main__":
    n = Network()
