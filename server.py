import socket
import threading


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
        print("[STARTING] server is starting...")
        self.server.listen(1)
        print(f"[LISTENING] Server is listening on {self.SERVER}")
    
        conn, addr = self.server.accept()
        thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
        thread.start()
        self.server.close()

    def handle_connection(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.")

        connected = True
        while connected:
            conn.send(str.encode("Connected"))
            try:
                msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    msg = conn.recv(msg_length).decode(self.FORMAT)
                    if msg == self.DISCONNECT_MESSAGE:
                        break

                    # print(f"[{addr}] says {msg}")
                    print(f"Received: ", msg)
                    print(f"Sending: ", msg)
                else:
                    print("Disconnected")
                    connected = False
            except:
                break

        print("Lost connection")
        conn.close()

connect4_terminal_plus_socket = Connect4TerminalPlusSocket()
connect4_terminal_plus_socket.host_game()