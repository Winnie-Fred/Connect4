import os
import socket
import pickle

from termcolor import colored  # type: ignore

from pygame_version.choice import Choice

os.system('') # To ensure that escape sequences work, and coloured text is displayed normally and not as weird characters


class Client:
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    def __init__(self):

        self.HEADERSIZE = 10

        self.client = None
        self.server = None
        # self.server = "127.0.0.1" #  Uncomment this line to test on localhost
        self.port = 5050
        self.addr = None

    def get_default_ip(self):
        return socket.gethostbyname(socket.gethostname())

    def connect_to_game(self, choice, ip, code):
        self.server = ip
        self.addr = (self.server, self.port)

        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            text = f"Error creating socket"
            print(colored(f"{text}: {e}", "red", attrs=['bold']))
            return {'text':text, 'error': True}

        try:
            self.client.connect(self.addr)
        except socket.gaierror as e:
            text = f"Address-related error connecting to server"
            print(colored(f"{text}: {e}", "red", attrs=['bold']))
            self.client.close()
            return {'text':text, 'error': True}
        except socket.error as e:
            text = f"Connection error"
            print(colored(f"{text}: {e}", "red", attrs=['bold']))
            self.client.close()
            return {'text':text, 'error': True}
        else:
            if choice == Choice.CREATE_GAME:
                self.send_data({'create_game':'True'})
                text = "Creating game"
                return {'text':text, 'error': False}
            elif choice == Choice.JOIN_ANY_GAME:
                self.send_data({'join_any_game':'True'})
                text = "Searching for game to join"
                return {'text':text, 'error': False}
            elif choice == Choice.JOIN_GAME_WITH_CODE:
                self.send_data({'join_game_with_invite':code})
                text = "Searching for game to join"
                return {'text':text, 'error': False}

        
    def send_data(self, data):
        data = pickle.dumps(data)
        data = bytes(f'{len(data):<{self.HEADERSIZE}}', self.FORMAT) + data
        try:
            self.client.sendall(data)
        except socket.error:
            raise