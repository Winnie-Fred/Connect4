import os
import socket
import pickle

from termcolor import colored  # type: ignore

from pygame_version.states import Choice
from multiple_pairs_of_clients_version.client import Client as BaseClient

os.system('') # To ensure that escape sequences work, and coloured text is displayed normally and not as weird characters


class Client(BaseClient):
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    def __init__(self):

        self.HEADERSIZE = 10

        self.client = None
        self.addr = None
        self.service_found = False

    def connect_to_game(self, choice, code):        

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