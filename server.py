import socket
import threading
import pickle
import time

from typing import List

from connect4 import Connect4Game

connect4game = Connect4Game()

clients: List = []
players: List = []


class Connect4TerminalPlusSocket:
    def __init__(self):
        self.HEADER = 64
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

    def start(self):
        global clients
        print("[STARTING] server is starting...")
        self.server.listen(2)
        print(f"[LISTENING] Server is listening on {self.SERVER}")
        while True:
            conn, addr = self.server.accept()
            clients.append((conn, addr))
            thread = threading.Thread(target=self.start_game_when_two_clients, args=(conn, addr))
            thread.start()
            
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
        
    def start_game_when_two_clients(self, conn, addr):
        global clients
        if len(clients) == 1:
            print("Waiting for other player to join the connection")
            while len(clients) != 2:
                time.sleep(5)
                

        if len(clients) == 1:
            print("Connection timed out. No other player joined the game")
            self.reset_client()
        elif len(clients) == 2:
            print("Both clients connected. Starting game. . .")
            for client in clients:
                conn, addr = client
                thread = threading.Thread(target=self.play_game, args=(conn, addr))
                thread.start()

    def reset_client(self, conn, addr):
        global clients
        print("Lost connection")
        clients.remove((conn, addr))
        self.conn.close()
                

    def play_game(self, conn, addr):
        global clients
        print(f"[NEW CONNECTION] {addr} connected.")
        conn.send(str.encode("CONNECTED"))
        
        while True:
            conn1, _ = clients[0]
            conn2, _ = clients[1]

            you = msg = conn.recv(2048).decode(self.FORMAT)
            opponent = ''
            
            if conn1 == conn:
                conn2.send(str.encode(you))
            else:
                conn1.send(str.encode(you))
            # conn.send(str.encode("Waiting for other player to join. . ."))
            
            shuffled_players = connect4game._shuffle_players([you, opponent])

            conn.sendall(pickle.dumps(shuffled_players))    

            if msg:
                if msg == self.DISCONNECT_MESSAGE:
                    break
            else:
                print("Disconnected")
                break

        self.reset_client(conn, addr)
        

connect4_terminal_plus_socket = Connect4TerminalPlusSocket()
connect4_terminal_plus_socket.host_game()