import socket
import sys
import pickle
import string
import random
import copy
import threading

from typing import List

from core.exceptions import SendingDataError
from core.game import Game


class Server:
    def __init__(self):
        self.HEADERSIZE = 10
        self.SERVER = socket.gethostbyname(socket.gethostname())
        # self.SERVER = "127.0.0.1" #  Uncomment this line to test on localhost
        self.PORT = 5050
        self.ADDR = (self.SERVER, self.PORT)
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = "!DISCONNECT"

        self.TIMEOUT_FOR_RECV = 300
        self.TIMEOUT_FOR_OTHER_CLIENT_TO_JOIN = 300

        self.games: List[Game] = []
        self.games_lock = threading.RLock()

        self.stop_flag = threading.Event()

        try:
           self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            print(f"Error creating socket: {e}")
            sys.exit(1)

    def host_game(self):
        try:
            ip = input("Enter the IP address of this machine or press Enter "
                        f"to use {self.SERVER}\nTip - Visit https://github.com/Winnie-Fred/Connect4/blob/main/README.md#finding-your-internal-ipv4-address for help on how to find your internal IP address. If you are having trouble with this, or you do not wish to use this IP, "
                        "copy the IPv4 address of this machine and paste it here: ").strip()
        except EOFError:
            pass
        else:
            if ip:
                self.SERVER = ip
                self.ADDR = (self.SERVER, self.PORT)

        try:
            self.server.bind(self.ADDR)
            self.server.listen()
        except socket.error as e:
            self.server.close()
            print(e)
            sys.exit(1)
        else:
            if self.server is None:
                print('Could not open socket')
                sys.exit(1)
            self.start()

    def send_data(self, conn, data):
        copy_data = copy.copy(data)
        data = pickle.dumps(data)
        data = bytes(f'{len(data):<{self.HEADERSIZE}}', self.FORMAT) + data
        try:
            conn.sendall(data)
        except socket.error:
            raise SendingDataError(copy_data)

    def start(self):
        print("[STARTING] server is starting...")
        print(f"[LISTENING] server is listening on {self.SERVER}")
        self.server.settimeout(1)

        while True:
            try:
                conn, addr = self.server.accept()
            except socket.timeout:
                continue
            except socket.error as e:
                break

            create_or_join_game_thread = threading.Thread(target=self.create_or_join_game, args=(conn, addr, ))
            create_or_join_game_thread.daemon = True           
            create_or_join_game_thread.start()

        print("[CLOSED] server is closed")

    def create_or_join_game(self, conn, addr):
        full_msg = b''
        new_msg = True
        unpickled_json = None
        try:
            while True:
                conn.settimeout(self.TIMEOUT_FOR_RECV) #  Timeout for recv
                msg = conn.recv(16)                                                  

                if not msg:
                    break

                if new_msg:
                    msglen = int(msg[:self.HEADERSIZE])
                    new_msg = False


                full_msg += msg

                if len(full_msg)-self.HEADERSIZE >= msglen:
                    # ----------------Use unpickled json data here----------------

                    conn.settimeout(None) #  Reset timer for next msg
                    unpickled_json = pickle.loads(full_msg[self.HEADERSIZE:self.HEADERSIZE+msglen])
                    # print("unpickled_json: ",  unpickled_json)

                    if len(full_msg) - self.HEADERSIZE > msglen: #  Multiple messages were received together
                        full_msg = full_msg[self.HEADERSIZE+msglen:] #  Get the part of the next msg that was recieved with the previous one
                        msglen = int(full_msg[:self.HEADERSIZE])      
                    else:
                        new_msg = True
                        full_msg = b''
                        
                    if 'create_game' in unpickled_json or 'join_game_with_invite' in unpickled_json or 'join_any_game' in unpickled_json:
                        break
                    
            if unpickled_json is not None:       
                if 'create_game' in unpickled_json:
                    self.create_game(conn, addr, 'invite_only')
                elif 'join_game_with_invite' in unpickled_json:
                    self.join_game(conn, addr, 'invite_only', unpickled_json['join_game_with_invite'])
                elif 'join_any_game' in unpickled_json:
                    self.join_game(conn, addr, 'open')

        except ConnectionAbortedError as e:
            print(f"Connection Aborted: {e}") 
        except socket.timeout as e:
            print(f"recv timed out. Connection is half-open or client took too long to respond. Ensure this machine is still connected to the network.")               
        except SendingDataError as data:
            print(f"Error sending '{data}'")
            self.close_client(conn, addr)
        except ConnectionResetError as e: #  This exception is caught when the server tries to receive a msg from a disconnected client
            print(f"Connection Reset: {e}")
            self.close_client(conn, addr)       
        except (socket.error, Exception) as e:
            print(f"Some Error occured: {e}")
            self.close_client(conn, addr)                

    def generate_unique_random_game_id(self):
        # Create random unique id of length 16 without letters I and O and without the digit 0
        # This is because letter I and digit 1 can be mistaken for each other, same with letter O and digit 0
        base_alphabets_for_game_id = string.ascii_letters + string.digits
        base_alphabets_for_game_id = base_alphabets_for_game_id.replace("i", '').replace("I", '').replace("O", '').replace("o", '').replace("0", '').replace("1", '')
        game_id = ''.join(random.choices(base_alphabets_for_game_id, k=16))
        with self.games_lock:
            for game in self.games:
                if game.id == game_id:
                    self.generate_unique_random_game_id()
        return game_id

    def create_game(self, conn, addr, type='invite_only'):
        game_id = self.generate_unique_random_game_id()
        game = Game(game_id, [(conn, addr, )], type)
        game_lock = threading.RLock()

        print(f"[GAME CREATED] {game} created.")

        with self.games_lock:
            self.games.append(game)
            print(f"[NO OF GAMES] {len(self.games)}")

        if type == 'invite_only':
            self.send_data(conn, {'code':game_id})

        print("Game created. Waiting for another player to join the game. . .")
        self.send_data(conn, {"status":"Game created. Waiting for another player to join the game"})

        # Wait for other client to join or wait for keyboard interrupt which sets self.stop_flag and game.second_client_has_joined
        with game_lock:
            if game.second_client_has_joined.wait(self.TIMEOUT_FOR_OTHER_CLIENT_TO_JOIN):       
                if self.stop_flag.is_set():
                    return
                if game.second_client_has_joined.is_set():
                    print("Both clients connected. Starting game. . .")
                    for client in game.clients:
                        conn, addr = client
                        play_game_thread = threading.Thread(target=self.play_game, args=(conn, addr, game, game_lock, ))
                        play_game_thread.daemon = True                        
                        play_game_thread.start()
            else:
                print("Connection timed out: No other player joined the game. Try joining the connection again.")
                self.send_data(conn, {"timeout":"Connection timed out: No other player joined the game. Try joining the connection again."})
                self.destroy_game(game, game_lock)


    def join_game(self, conn, addr, type, game_id=''):
        game_found = False
        found_game = Game(None, [], '')
        with self.games_lock:
            if type == 'invite_only':
                for game in self.games:
                    if game.type == type and game.id == game_id:
                        if len(game.clients) >= 2:
                            print("Game full")
                            self.send_data(conn, {'game_full':'You cannot join this game as it has enough players. Try joining another game or creating a new one'})
                            self.close_client(conn, addr)
                            return
                        game_found = True
                        found_game = game
            elif type == 'open':
                for game in self.games:
                    if game.type == type and len(game.clients) == 1:
                        game_found = True
                        found_game = game
                       

        if not game_found:
            if type == 'invite_only':
                msg = "No games exist with that code. Ask for an up-to-date code, try creating your own game or try joining a different game"
                print(msg)
                self.send_data(conn, {'no_games_found':msg})
                self.close_client(conn, addr)
            elif type == 'open':
                msg = "No games were found for you to join. Creating new game"
                print(msg)
                self.send_data(conn, {'status':msg})              
                self.create_game(conn, addr, 'open')
        else:
            self.send_data(conn, {'join_successful':"Game joined successfully"})
            with self.games_lock:
                found_game.clients.append((conn, addr, ))
                found_game.second_client_has_joined.set()
       
    def destroy_game(self, game, game_lock):
        with game_lock:
            for client in game.clients:
                conn, _ = client
                conn.close()

        with self.games_lock:
            if game in self.games:
                self.games.remove(game)
                print(f"[GAME DESTROYED] {game} destroyed.")
                print(f"[NO OF GAMES LEFT] {len(self.games)}")

    def close_client(self, conn, addr):
        conn.close()
        print(f"[DISCONNECTION] {addr} disconnected.")    

    def play_game(self, conn, addr, game, game_lock):       

        print(f"[NEW GAME] {addr} connected.")

        try:
            with game_lock:
                conn1, addr1 = game.clients[0]
                conn2, addr2 = game.clients[1]
        except IndexError:
            print("Index error: Client no longer exists")
            with game_lock:
                self.destroy_game(game, game_lock)
            return
            
        id = None

        try:
            with game_lock:
                if conn == conn1:
                    id = game.clients.index((conn1, addr1))
                    self.send_data(conn1, {"id": id})
                else:
                    id = game.clients.index((conn2, addr2))
                    self.send_data(conn2, {"id": id})

            if not id: #  If id is 0 i.e. if first connected player...
                self.send_data(conn, {"get_first_player_name":True})
            else:
                self.send_data(conn, {"waiting_for_name":"Waiting for other player to enter their name"})

            full_msg = b''
            new_msg = True
            
            while True:
                
                conn.settimeout(self.TIMEOUT_FOR_RECV) #  Timeout for recv
                msg = conn.recv(16)                                                  

                if not msg:
                    break

                if new_msg:
                    msglen = int(msg[:self.HEADERSIZE])
                    new_msg = False


                full_msg += msg

                if len(full_msg)-self.HEADERSIZE >= msglen:
                        # ----------------Use unpickled json data here----------------

                        conn.settimeout(None) #  Reset timer for next msg
                        unpickled_json = pickle.loads(full_msg[self.HEADERSIZE:self.HEADERSIZE+msglen])
                        # print("unpickled_json: ",  unpickled_json)

                        if len(full_msg) - self.HEADERSIZE > msglen: #  Multiple messages were received together
                            full_msg = full_msg[self.HEADERSIZE+msglen:] #  Get the part of the next msg that was recieved with the previous one
                            msglen = int(full_msg[:self.HEADERSIZE])      
                        else:
                            new_msg = True
                            full_msg = b''
                    
                        if 'you' in unpickled_json:
                            you = unpickled_json['you']
                            if conn == conn1:
                                self.send_data(conn2, {'opponent':you})
                            elif conn == conn2:
                                self.send_data(conn1, {'opponent':you})                        
                        elif 'first' in unpickled_json:
                            self.send_data(conn1, {'first':unpickled_json['first']})                        
                            self.send_data(conn2, {'first':unpickled_json['first']})
                        elif 'colors' in unpickled_json:
                            self.send_data(conn1, {'colors':unpickled_json['colors']})
                            self.send_data(conn2, {'colors':unpickled_json['colors']})
                        elif 'opponent_player_object' in unpickled_json:
                            if conn == conn1:
                                self.send_data(conn2, {'opponent_player_object':unpickled_json['opponent_player_object']})
                            elif conn == conn2:
                                self.send_data(conn1, {'opponent_player_object':unpickled_json['opponent_player_object']})                                            
                        elif 'board' in unpickled_json:
                            if conn == conn1:
                                self.send_data(conn2, {'board':unpickled_json['board']})                            
                            elif conn == conn2:
                                self.send_data(conn1, {'board':unpickled_json['board']})  
                        elif 'round_over' in unpickled_json:
                            self.send_data(conn1, unpickled_json)
                            self.send_data(conn2, unpickled_json)
                        elif 'play_again' in unpickled_json:
                            if conn == conn1:
                                self.send_data(conn2, {'play_again':unpickled_json['play_again']})
                                if not unpickled_json['play_again']:
                                    print("Player has quit the game")
                                    break
                            elif conn == conn2:
                                self.send_data(conn1, {'play_again':unpickled_json['play_again']})
                                if not unpickled_json['play_again']:
                                    print("Player has quit the game")
                                    break
                        elif 'first_player' in unpickled_json:                        
                            self.send_data(conn1, {'first_player':unpickled_json['first_player']})                        
                            self.send_data(conn2, {'first_player':unpickled_json['first_player']})                                                
                        elif 'DISCONNECT' in unpickled_json:
                            if unpickled_json['DISCONNECT'] == self.DISCONNECT_MESSAGE:
                                if 'close_other_client' in unpickled_json:
                                    if unpickled_json['close_other_client']:
                                        if conn == conn1:
                                            self.send_data(conn2, {"other_client_disconnected":"Other client disconnected unexpectedly"})
                                        else:
                                            self.send_data(conn1, {"other_client_disconnected":"Other client disconnected unexpectedly"})
                                break
                                   
                            # ----------------Use unpickled json data here----------------
        except ConnectionAbortedError as e:
            print(f"Connection Aborted: {e}") 
        except socket.timeout as e:
            print(f"recv timed out. Connection is half-open or client took too long to respond. Ensure this machine is still connected to the network.")               
        except SendingDataError as data:
            print(f"Error sending '{data}'")            
        except ConnectionResetError as e: #  This exception is caught when the server tries to receive a msg from a disconnected client
            print(f"Connection Reset: {e}")
            try:
                if conn == conn1:
                    self.send_data(conn2, {"other_client_disconnected":"Other client disconnected unexpectedly"})
                else:
                    self.send_data(conn1, {"other_client_disconnected":"Other client disconnected unexpectedly"})
            except SendingDataError as data:
                print(f"Error sending '{data}'")
        except socket.error as e:            
            print(f"Some error occured: Socket may have been closed")
        except Exception:
            print(f"An error occured: {e}")
        
        with game_lock:
            self.destroy_game(game, game_lock)

    def terminate_program(self):

        """Wait for threads to complete and exit program"""

        self.stop_flag.set()

        with self.games_lock:
            for game in self.games:
                game.second_client_has_joined.set() #  Set this so that threads waiting for other client to join stop blocking
                for client in game.clients:
                    conn, _ = client
                    conn.close()

        self.server.close()

        main_thread = threading.main_thread()
        for thread in threading.enumerate():
            if thread is not main_thread:
                thread.join()

        print(f"\nKeyboard Interrupt detected")
        print("[CLOSED] server is closed")
        sys.exit(1)

if __name__ == "__main__":
    server = Server()
    try:
        server.host_game()
    except KeyboardInterrupt:
        server.terminate_program()        