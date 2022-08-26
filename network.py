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
        self.board = Board()

        self.HEADERSIZE = 10
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1"
        self.port = 5050
        self.addr = (self.server, self.port)

        self.loading_thread = Thread()
        self.loaded_json = {}
        self.board_updated_event = Event()

        self.connect()


    def connect(self):
        try:
            self.client.connect(self.addr)
        except Exception as e:
            print(f"Connection failed: {e}")
        else:
            self.loading_thread.start()
            self.play_game()
           

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
        spaces_to_replace_loader = '  '
        yellow_loading_msg = colored(loading_msg, "yellow", attrs=['bold'])
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if loaded_json != self.loaded_json:
                green_loading_msg = colored(loading_msg, "green", attrs=['bold'])
                sys.stdout.write(f'\r{green_loading_msg}{spaces_to_replace_loader}')
                print("\n")
                break
            sys.stdout.write(f'\r{yellow_loading_msg} {c}')
            sys.stdout.flush()
            time.sleep(0.1)

    def main_game_thread(self):
        print("\n\n", f"ROUND {self.level.current_level}".center(50, '-'))
        self.board.print_board() #  Print board at start of each round

        first_time = True
        while True:
            self.loading_thread.join() # Wait for spinner to stop before printing to stdout

            if self.your_turn:
                if not first_time: #  Do not wait on first run of loop for board to be updated since no move has been made yet
                    self.board_updated_event.wait() #  Wait until board is updated with other player's latest move
                    self.board_updated_event.clear() #  Unset the event till it is set when board is updated again
                    self.board.print_board() # Print board to show player their opponent's move

                self.board.play_at_position(self.player)
                self.board.print_board()
                self.your_turn = False
                self.send_data({'board':self.board})
            else:
                loading_msg = f"Waiting for {self.opponent.name} {self.opponent.marker} to play"
                self.your_turn = True
                self.loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json))
                self.loading_thread.start()
            first_time = False

    def play_game(self): 

        full_msg = b''
        new_msg = True
        while True:
            msg = self.client.recv(16)
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
                # ! Otherwise, condtion for termination of spinner is never met
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
                        

                        # self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE})
                        # break

                except KeyError:
                    self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE})
                    break                
                    

                    # ----------------Use loaded json data here----------------
if __name__ == "__main__":
    n = Network()
    # n.send_to_server(n.DISCONNECT_MESSAGE)
