import socket
import pickle

from connect4 import Connect4Game

connect4game = Connect4Game()


class Network:
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    def __init__(self):
        self.HEADERSIZE = 10
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
            self.play_game(self.client)
           

    def send_data(self, conn, data):
        data = pickle.dumps(data)
        data = bytes(f'{len(data):<{self.HEADERSIZE}}', self.FORMAT) + data
        conn.send(data)


    def play_game(self, client):

    
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
                print("LOADED JSON", loaded_json)
                new_msg = True
                full_msg = b''
                try:
                    if "connected" in loaded_json:
                        connect4game._about_game()
                        you = connect4game._get_player_name()                       
                        self.send_data(client, {'you':you})
                    elif 'players' in loaded_json:
                        players = loaded_json['players']
                        print("PLAYERS RECIEVED: ", players)
                        # self.send_data(client, {'DISCONNECT':self.DISCONNECT_MESSAGE})
                        # break

                except KeyError:
                    self.send_data(client, {'DISCONNECT':self.DISCONNECT_MESSAGE})
                    break

                    # ----------------Use loaded json data here----------------

n = Network()
# n.send_to_server(n.DISCONNECT_MESSAGE)
