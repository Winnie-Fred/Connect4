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
            clients.append(conn)
            thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
            

    def handle_connection(self, conn, addr):
        global opponent, clients
        print(f"[NEW CONNECTION] {addr} connected.")

        conn.send(str.encode("Connected"))

        connected = True
        while connected:
            try:
                msg = pickle.loads(conn.recv(2048))
            except:
                break
            else:
                if msg:
                    if msg == self.DISCONNECT_MESSAGE:
                        break

                    print(f"Received: ", msg)
                    
                else:
                    print("Disconnected")
                    break

                
                if not opponent:
                    conn.send(pickle.dumps("Waiting for other player's name . . ."))
                    if clients[0] == conn:
                        opponent = clients[1].recv(2048)
                    else:
                        opponent = clients[0].recv(2048)
                
                conn.send(pickle.dumps(opponent))

                

        print("Lost connection")
        opponent = ''
        clients.remove(conn)
        conn.close()

connect4_terminal_plus_socket = Connect4TerminalPlusSocket()
connect4_terminal_plus_socket.host_game()