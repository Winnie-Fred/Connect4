import socket
import sys
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


class Server:
    def __init__(self):
        self.HEADERSIZE = 10
        # self.SERVER = socket.gethostbyname(socket.gethostname())
        self.SERVER = "127.0.0.1"
        self.PORT = 5050
        self.ADDR = (self.SERVER, self.PORT)
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = "!DISCONNECT"
        try:
           self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            print(f"Error creating socket: {e}")
            self.server = None

        self.TIMEOUT_FOR_CLIENT = 20
        

    def host_game(self):
        try:
            self.server.bind(self.ADDR)
            self.server.listen()
        except socket.error as e:
            self.server.close()
            self.server = None
            print(e)
        else:
            if self.server is None:
                print('Could not open socket')
                sys.exit(1)
            self.start()

    def send_data(self, conn, data):
        data = pickle.dumps(data)
        data = bytes(f'{len(data):<{self.HEADERSIZE}}', self.FORMAT) + data
        try:
            conn.send(data)
        except socket.error:
            raise


    def start(self):
        global clients
        print("[STARTING] server is starting...")
        print(f"[LISTENING] server is listening on {self.SERVER}")
        self.start_game_when_two_clients_thread = threading.Thread(target=self.start_game_when_two_clients)
        self.start_game_when_two_clients_thread.start()

        while True:
            try:
                conn, addr = self.server.accept()
            except OSError:
                break
            clients.append((conn, addr))

            print(f"[ACTIVE CONNECTIONS] {len(clients)}")
        print("[CLOSED] server is closed")
            
        
    def start_game_when_two_clients(self):
        global clients
        

        first_time_for_no_client = True
        first_time_for_one_client = True
        # lock = threading.Lock()

        while True: # Busy wait
            if not clients:
                if first_time_for_no_client:
                    print("Waiting for clients to join the connection. . .")
                    first_time_for_no_client = False #  Set to False so that print statement prints only once
                    first_time_for_one_client = True
                time.sleep(1) #  Sleep if not clients
                continue
            elif len(clients) == 1:
                conn, addr = clients[0]
                if first_time_for_one_client:
                    start_time = time.time()
                    print("Waiting for other player to join the connection. . .")
                    self.send_data(conn, {"status":"Waiting for other player to join the connection"})
                    first_time_for_one_client = False #  Set to False so that print statement prints only once and msg is sent only once
                    first_time_for_no_client = True
                if time.time() > start_time + self.TIMEOUT_FOR_CLIENT:
                    print("Connection timed out: No other player joined the game. Try joining the connection again.")
                    self.send_data(conn, {"timeout":"Connection timed out: No other player joined the game. Try joining the connection again."})
                    self.remove_client(conn, addr)
                time.sleep(1) #  Sleep if one client
                continue
            elif len(clients) == 2:                           
                print("Both clients connected. Starting game. . .")
                for client in clients:
                    conn, addr = client

                    thread = threading.Thread(target=self.play_game, args=(conn, addr))
                    thread.start()                   
                break
            

    def remove_client(self, conn, addr, start_new_game=True):
        global clients
        print("Lost connection")
        print(f"[DISCONNECTION] {addr} disconnected.")
        try:
            clients.remove((conn, addr))
        except ValueError:
            pass
        try:      
            conn.close()
        except socket.error:
            raise

        # Listen for new connection(s) after losing client only if the thread is not already running and if start_new_game is True
        if not self.start_game_when_two_clients_thread.is_alive() and start_new_game and len(clients) != 2:
            self.start_game_when_two_clients_thread = threading.Thread(target=self.start_game_when_two_clients)
            self.start_game_when_two_clients_thread.start()
                

    def play_game(self, conn, addr):
        global clients
        self.start_game_when_two_clients_thread.join()

        print(f"[NEW CONNECTION] {addr} connected.")

        conn1, addr1 = clients[0]
        conn2, addr2 = clients[1]

        if conn == conn1:
            self.send_data(conn1, {"id": clients.index((conn1, addr1))})
        else:
            self.send_data(conn2, {"id": clients.index((conn2, addr2))})
            

        full_msg = b''
        new_msg = True

        while True:
            try:
                try:
                    msg = conn.recv(16)   
                except ConnectionResetError as e: #  This exception is caught when the server tries to receive a msg from a disconnected client
                    print(f"Connection Reset: {e}")
                    if conn == conn1:
                        self.send_data(conn2, {"other_client_disconnected":"Other client disconnected unexpectedly"})
                    else:
                        self.send_data(conn1, {"other_client_disconnected":"Other client disconnected unexpectedly"})
                    self.remove_client(conn, addr)
                    break
                except socket.error as e:
                    print(f"Error receiving data: {e}")
                    if conn == conn1:
                        self.send_data(conn2, {"other_client_disconnected":"An error occured with the other client"})
                    else:
                        self.send_data(conn1, {"other_client_disconnected":"An error occured with the other client"})
                    self.remove_client(conn, addr)
                    break
                                

                if not msg:
                    self.remove_client(conn, addr)
                    break

                if new_msg:
                    msglen = int(msg[:self.HEADERSIZE])
                    new_msg = False


                full_msg += msg

                if len(full_msg)-self.HEADERSIZE == msglen:
                    # ----------------Use loaded json data here----------------

                    loaded_json = pickle.loads(full_msg[self.HEADERSIZE:])
                    # print("loaded_json: ",  loaded_json)
                    new_msg = True
                    full_msg = b''     
                    try:
                        if 'id' in loaded_json:
                            id = loaded_json['id']
                            if not id: #  If id is 0 i.e. if first connected player...
                                self.send_data(conn, {"get-first-player-name":True})
                            else:
                                self.send_data(conn, {"waiting-for-name":"Waiting for other player to enter their name"})
                        elif 'you' in loaded_json:
                            you = loaded_json['you']
                            if conn == conn1:
                                self.send_data(conn2, {'opponent':you})
                            elif conn == conn2:
                                self.send_data(conn1, {'opponent':you})                        
                        elif 'first' in loaded_json:
                            self.send_data(conn1, {'first':loaded_json['first']})                        
                            self.send_data(conn2, {'first':loaded_json['first']})
                        elif 'colors' in loaded_json:
                            self.send_data(conn1, {'colors':loaded_json['colors']})
                            self.send_data(conn2, {'colors':loaded_json['colors']})
                        elif 'opponent_player_object' in loaded_json:
                            if conn == conn1:
                                self.send_data(conn2, {'opponent_player_object':loaded_json['opponent_player_object']})
                            elif conn == conn2:
                                self.send_data(conn1, {'opponent_player_object':loaded_json['opponent_player_object']})                                            
                        elif 'board' in loaded_json:
                            if conn == conn1:
                                self.send_data(conn2, {'board':loaded_json['board']})                            
                            elif conn == conn2:
                                self.send_data(conn1, {'board':loaded_json['board']})  
                        elif 'round_over' in loaded_json:
                            self.send_data(conn1, loaded_json)
                            self.send_data(conn2, loaded_json)
                        elif 'play_again' in loaded_json:
                            try:
                                if conn == conn1:
                                    self.send_data(conn2, {'play_again':loaded_json['play_again']})
                                elif conn == conn2:
                                    self.send_data(conn1, {'play_again':loaded_json['play_again']})
                            except OSError: # Other client may have disconnected already so sending data to it will raise OSError exception
                                continue
                        elif 'first_player' in loaded_json:                        
                            self.send_data(conn1, {'first_player':loaded_json['first_player']})                        
                            self.send_data(conn2, {'first_player':loaded_json['first_player']})
                        elif 'wait_for_new_client' in loaded_json:
                            self.start_game_when_two_clients_thread = threading.Thread(target=self.start_game_when_two_clients)
                            self.start_game_when_two_clients_thread.start()
                            break
                        elif 'other_client_disconnected' in loaded_json:
                            break
                        elif 'DISCONNECT' in loaded_json:
                            if loaded_json['DISCONNECT'] == self.DISCONNECT_MESSAGE:                            
                                if 'disconnect_sent_to_end_game' in loaded_json and len(clients) == 2:
                                    self.remove_client(conn, addr, start_new_game=False)
                                else:
                                    self.remove_client(conn, addr)
                                break
                    except KeyError:
                        self.remove_client(conn, addr)
                        break               
                            # ----------------Use loaded json data here----------------
            except socket.error as e:
                print(f"Error sending data: {e}")
                if conn == conn1:
                    self.send_data(conn2, {"other_client_disconnected":"An error occured with the other client"})
                else:
                    self.send_data(conn1, {"other_client_disconnected":"An error occured with the other client"})
                self.remove_client(conn, addr)
                break


        
if __name__ == "__main__":
    server = Server()
    server.host_game()