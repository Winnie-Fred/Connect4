import socket


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

    def send(self, msg):
        message = msg.encode(self.FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b' ' * (self.HEADER - len(send_length))
        try:
            self.client.send(send_length)
            self.client.send(message)
        except socket.error as e:
            print(e)
        else:
            print(self.client.recv(2048).decode(self.FORMAT))

n = Network()
n.send("HELLO")
n.send(n.DISCONNECT_MESSAGE)
