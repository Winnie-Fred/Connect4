import socket
import threading
import pickle
import time
import copy

from typing import List

from connect4 import Connect4Game

connect4game = Connect4Game()


to_shuffle = threading.Event()
to_shuffle.set()

clients: List = []
players: List = []


class Connect4TerminalPlusSocket:
    def __init__(self):
        self.HEADERSIZE = 10
        # SERVER = socket.gethostbyname(socket.gethostname())
        self.SERVER = "127.0.0.1"
        self.PORT = 5050
        self.ADDR = (self.SERVER, self.PORT)
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = "!DISCONNECT"
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def host_game(self):
        try:
            self.server.bind(self.ADDR)
        except socket.error as e:
            print(e)
        else:
            self.start()

    def send_data(self, conn, data):
        data = pickle.dumps(data)
        data = bytes(f'{len(data):<{self.HEADERSIZE}}', self.FORMAT) + data
        conn.send(data)


    def start(self):
        global clients
        print("[STARTING] server is starting...")
        self.server.listen(2)
        print(f"[LISTENING] server is listening on {self.SERVER}")
        thread = threading.Thread(target=self.start_game_when_two_clients)
        thread.start()

        i = 1
        while True:
            conn, addr = self.server.accept()
            clients.append((conn, addr))

            print(f"[ACTIVE CONNECTIONS] {i}")
            i += 1
            
        
    def start_game_when_two_clients(self):
        global clients
        
        first_time = True
        lock = threading.Lock()

        while True:
            if len(clients) == 1:
                if first_time:
                    print("Waiting for other player to join the connection. . .")
                    conn, _ = clients[0]
                    self.send_data(conn, {"status":"Waiting for other player to join the connection"})
                time.sleep(1)
                first_time = False
                continue
                    
            # TODO: Close conn if no other client joins connection after specified time
            # elif len(clients) == 1:
            #     print("Connection timed out. No other player joined the game")
            #     self.reset_client()

            elif len(clients) == 2: 
                id = 0           
                print("Both clients connected. Starting game. . .")
                for client in clients:
                    conn, addr = client
                    self.send_data(conn, {"id": id})
                    time.sleep(1)
                    self.send_data(conn, {"status":"Both clients connected. Starting game"})
                    time.sleep(1)
                    if client == clients[1]:
                        self.send_data(conn, {"waiting-for-name":"Waiting for other player to enter their name"})
                        time.sleep(1)
                    id += 1

                    thread = threading.Thread(target=self.play_game, args=(conn, addr, lock))
                    thread.start()               
                break
            

    def reset_client(self, conn, addr):
        global clients
        print("Lost connection")
        clients.remove((conn, addr))
        self.conn.close()
                

    def play_game(self, conn, addr, lock):
        print(f"[NEW CONNECTION] {addr} connected.")
        global players, clients

        lock.acquire()
        clients = copy.copy(clients)
        lock.release()

        conn1, _ = clients[0]
        conn2, _ = clients[1]

        opponent = ''
        you = ''
        id = None

        full_msg = b''
        new_msg = True

        while True:
            msg = conn.recv(16)        
            if new_msg:
                msglen = int(msg[:self.HEADERSIZE])
                new_msg = False


            full_msg += msg

            if len(full_msg)-self.HEADERSIZE == msglen:
                # ----------------Use loaded json data here----------------

                loaded_json = pickle.loads(full_msg[self.HEADERSIZE:])
                # print("loaded_json: ",  loaded_json)
                new_msg = True
                full_msg = b''     
                try:
                    if 'id' in loaded_json:
                        id = loaded_json['id']
                        if not id:
                            self.send_data(conn, {"get-first-player-name":"True"})
                    elif 'you' in loaded_json:
                        you = loaded_json['you']
                        if conn == conn1:
                            self.send_data(conn2, {'opponent':you})
                        elif conn == conn2:
                            self.send_data(conn1, {'opponent':you})                        
                        
                    elif 'opponent' in loaded_json:
                        opponent = loaded_json['opponent']
                    elif 'first' in loaded_json:
                        self.send_data(conn1, {'first':loaded_json['first']})                        
                        self.send_data(conn2, {'first':loaded_json['first']})
                    elif 'colors' in loaded_json:
                        self.send_data(conn1, {'colors':loaded_json['colors']})
                        self.send_data(conn2, {'colors':loaded_json['colors']})                  
                                            
                    elif 'DISCONNECT' in loaded_json:
                        if loaded_json['DISCONNECT'] == self.DISCONNECT_MESSAGE:                            
                            self.reset_client(conn, addr)

                except KeyError:
                    self.reset_client(conn, addr)                          

                    # ----------------Use loaded json data here---------------- 
        
if __name__ == "__main__":
    connect4_terminal_plus_socket = Connect4TerminalPlusSocket()
    connect4_terminal_plus_socket.host_game()