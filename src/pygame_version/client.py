import os
import socket
import pickle
from threading import Thread, Event

from termcolor import colored  # type: ignore
from tabulate import tabulate  # type: ignore

from basic_version.connect4 import Connect4Game
from core.player import Player
from one_pair_of_clients_version.client import Client as BaseClient

from .choice import Choice

os.system('') # To ensure that escape sequences work, and coloured text is displayed normally and not as weird characters


class Client(BaseClient):
    def connect_to_game(self, choice):
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
            self._reset_game()
            if choice == Choice.CREATE_GAME:
                self.send_data({'create_game':'True'})
                text = "Creating game"
                return {'text':text, 'error': False}                
   
    def terminate_program(self):
        self.keyboard_interrupt_event.set()
        if self.client is not None:
            try:
                self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE, 'close_other_client':True})
            except socket.error:
                pass
            self.client.close()    
        self.end_thread_event.set() # Set event to terminate simulate_loading_with_spinner thread if it is running at the time of Keyboard Interrupt 
        with self.condition:
            self.condition.notify()
        self.wait_for_threads()
        error_msg = colored(f"Keyboard Interrupt: Program ended", "red", attrs=['bold'])        
        print(f"\n{error_msg}\n")