import socket
import pickle

from connect4 import Connect4Game

connect4game = Connect4Game()


class Network:
    HEADER = 64
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1"
        self.port = 5050
        self.addr = (self.server, self.port)
        self.p = self.connect()


    def connect(self):
        try:
            self.client.connect(self.addr)
        except:
            print("Connection failed")
        else:
            return self.client.recv(2048).decode(self.FORMAT)

    def play_game(self):
        connect4game._about_game()
        you = connect4game._get_player_name()
        waiting = pickle.loads(self.client.recv(2048))
        if waiting.startswith("Waiting for the other"):
            print(waiting)
        else:
            opponent_name = waiting

        shuffled_players = connect4game._shuffle_players([you, opponent_name])
        print("Players shuffled", shuffled_players)

    def send_to_server(self, msg):
        try:
            self.client.send(pickle.dumps(msg))
        except socket.error as e:
            print(e)
        else:
            return pickle.loads(self.client.recv(2048))

n = Network()
n.play_game()
# n.send_to_server(n.DISCONNECT_MESSAGE)
