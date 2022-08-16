import socket
import threading
import pickle


from typing import List

from connect4 import Connect4Game

connect4game = Connect4Game()

opponent = ''
clients: List = []


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
            thread = threading.Thread(target=self.play_game, args=(conn, addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
            

    def play_game(self, conn, addr):
        global opponent, clients
        print(f"[NEW CONNECTION] {addr} connected.")
        conn.send(str.encode("CONNECTED"))
        while True:
            conn1, _ = clients[0]
            conn2, _ = clients[1]

            if conn1 == conn:
                you = msg = pickle.loads(conn1.recv(2048))
            else:
                you = msg = pickle.loads(conn2.recv(2048))

            if not opponent:
                conn.send(pickle.dumps("Waiting for other player's name . . ."))
                if conn1 == conn:
                    opponent = pickle.loads(conn2.recv(2048))
                else:
                    opponent = pickle.loads(conn1.recv(2048))
            
            shuffled_players = connect4game._shuffle_players([you, opponent])

            conn.sendall(pickle.dumps(shuffled_players))    

            if msg:
                if msg == self.DISCONNECT_MESSAGE:
                    break
            else:
                print("Disconnected")
                break

        print("Lost connection")
        opponent = ''
        clients.remove((conn, addr))
        conn.close()

connect4_terminal_plus_socket = Connect4TerminalPlusSocket()
connect4_terminal_plus_socket.host_game()