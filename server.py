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
        print(f"[LISTENING] Server is listening on {self.SERVER}")
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
        i = 0
        lock = threading.Lock()

        while True:
            if len(clients) == 1:
                if i == 0:
                    print("Waiting for other player to join the connection. . .")
                    conn, _ = clients[0]
                    self.send_data(conn, {"status":"Waiting for other player to join the connection. . ."})
                time.sleep(5)
                i += 1
                continue
                    
            # TODO: Close conn if no other client joins connection after specified time
            # elif len(clients) == 1:
            #     print("Connection timed out. No other player joined the game")
            #     self.reset_client()

            elif len(clients) == 2:            
                print("Both clients connected. Starting game. . .")
                for client in clients:
                    conn, _ = client
                    self.send_data(conn, {"status":"Both clients connected. Starting game. . ."})
                    if client == clients[1]:
                        self.send_data(conn, {"waiting-for-name":"Waiting for other player to enter their name. . ."})

                for client in clients:
                    conn, addr = client
                    thread = threading.Thread(target=self.get_player_names, args=(conn, addr, lock))
                    thread.start()
                    thread.join()

                for client in clients:
                    conn, addr = client
                    thread = threading.Thread(target=self.play_game, args=(conn, addr, lock))
                    thread.start()
                break
            

    def reset_client(self, conn, addr):
        global clients
        print("Lost connection")
        clients.remove((conn, addr))
        self.conn.close()
                

    def get_player_names(self, conn, addr, lock):
        print("Player names thread running. . . ")
        global players

        print(f"[NEW CONNECTION] {addr} connected.")

        # lock.acquire()
        # conn1, _ = clients[0]
        # conn2, _ = clients[1]

        # if len(players) == 1:
        #     if conn == conn1:
        #         self.send_data(conn2, {"waiting-for-name":"Wait while other player enters their name"})
        #     elif conn == conn2:
        #         self.send_data(conn1, {"waiting-for-name":"Wait while other player enters their name"})
        # lock.release()

        
        self.send_data(conn, {"connected":"True"})

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
                print("loaded_json: ",  loaded_json)
                new_msg = True
                full_msg = b''     
                try:
                    if 'you' in loaded_json:
                        you = loaded_json['you']
                        
                        lock.acquire()                        
                        players.append(you)
                        lock.release()

                        break                    
                    elif 'DISCONNECT' in loaded_json:
                        if loaded_json['DISCONNECT'] == self.DISCONNECT_MESSAGE:                            
                            self.reset_client(conn, addr)                            
                except KeyError:
                    self.reset_client(conn, addr)                          

                    # ----------------Use loaded json data here---------------- 




    def play_game(self, conn, addr, lock):
        print("play game thread running. . . ")
        global players
        global clients
        
        with lock:
            clients = copy.copy(clients)
            players = copy.copy(players)
        
        self.send_data(conn, {"players":players})
        
        conn1, _ = clients[0]
        conn2, _ = clients[1]

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
                print("loaded_json: ",  loaded_json)
                new_msg = True
                full_msg = b''     
                try:                    
                    if 'DISCONNECT' in loaded_json:
                        if loaded_json['DISCONNECT'] == self.DISCONNECT_MESSAGE:                            
                            break
                except KeyError:                
                    break

                    # ----------------Use loaded json data here----------------   


        self.reset_client(conn, addr)
        

connect4_terminal_plus_socket = Connect4TerminalPlusSocket()
connect4_terminal_plus_socket.host_game()