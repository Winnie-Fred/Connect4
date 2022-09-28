from typing import List
from threading import Event

class Game:
    def __init__(self, id, clients, type):
        self.id: str = id
        self.clients: List = clients
        self.type: str = type
        self.second_client_has_joined = Event()

    def __str__(self):
        client_addresses = ''
        for idx, client in enumerate(self.clients):
            _, addr = client
            if idx == 1:
                client_addresses += ' and '
            client_addresses += str(addr)

        type = self.type
        if type == 'invite_only':
            type = type.replace('_', '-')
        return f"{type.capitalize()} game for {client_addresses}"