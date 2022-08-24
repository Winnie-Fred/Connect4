import socket
import pickle

from colorama import init # type: ignore
init(autoreset= True)

from termcolor import colored  # type: ignore

from connect4 import Connect4Game
from player import Player
from level import Level
from board import Board


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
        self.connect()


    def connect(self):
        try:
            self.client.connect(self.addr)
        except Exception as e:
            print(f"Connection failed: {e}")
        else:
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

                loaded_json = pickle.loads(full_msg[self.HEADERSIZE:])
                # print("LOADED JSON", loaded_json)
                new_msg = True
                full_msg = b''
                try:
                    if "id" in loaded_json:
                        self.ID = loaded_json["id"]
                        self.send_data({'id':self.ID})
                    elif "status" in loaded_json:
                        print(loaded_json['status'])
                    elif "waiting-for-name" in loaded_json:
                        print(loaded_json['waiting-for-name'])
                    elif "get-first-player-name" in loaded_json:  
                        connect4game._about_game()                        
                        self.you = connect4game._get_player_name()
                        self.send_data({'you':self.you})
                        print("Waiting for other player to enter their name. . .")
                    elif "opponent" in loaded_json:
                        self.opponent = loaded_json['opponent']
                        if not self.you:
                            connect4game._about_game()
                            self.you = self._get_other_player_name(self.opponent)
                            self.send_data({'you':self.you})                        
                        print("You are up against: ", self.opponent)
                        self.send_data({'opponent':self.opponent})
                        # Shuffling player names
                        if not self.ID:
                            first_player = connect4game._shuffle_players([self.you, self.opponent])
                            self.send_data({'first':first_player})                      
                    elif "first" in loaded_json:
                        first = loaded_json['first'][0]
                        if self.ID:
                            print("Randomly choosing who to go first . . .")                    
                            print(f"{first} goes first")
                        if first == self.you:
                            colors = connect4game._get_players_colors(self.you)
                            self.send_data({'colors':colors})
                        else:
                            print(f"Waiting for {self.opponent} to choose their color. . .")
                    elif "colors" in loaded_json:
                        colors = loaded_json['colors']                        
                        if first == self.you:
                            self.your_turn = True
                            self.player = Player(self.you, colored('O', colors[0], attrs=['bold']))
                        else:
                            self.your_turn = False
                            self.player = Player(self.you, colored('O', colors[1], attrs=['bold']))
                        
                        print("\n\n", f"ROUND {self.level.current_level}".center(50, '-'))
                        board = Board()
                        board.print_board() #  Print board at start of each round
                        
                        if self.your_turn:
                            board.play_at_position(self.player)
                            board.print_board()
                            self.send_data({'board':board})
                            self.your_turn = False
                        else:
                            print(f"Waiting for {self.opponent} to play. . .")
                            self.your_turn = True

                    elif "board" in loaded_json:
                        board = loaded_json['board']
                        print(board)

                        # self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE})
                        # break

                except KeyError:
                    self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE})
                    break

                    # ----------------Use loaded json data here----------------
if __name__ == "__main__":
    n = Network()
    # n.send_to_server(n.DISCONNECT_MESSAGE)
