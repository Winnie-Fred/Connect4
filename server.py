import socket
import sys
import threading
import pickle
import copy

from typing import List

from exceptions import SendingDataError


class Server:
    def __init__(self):
        self.HEADERSIZE = 10
        # self.SERVER = socket.gethostbyname(socket.gethostname())
        self.SERVER = "127.0.0.1"
        self.PORT = 5050
        self.ADDR = (self.SERVER, self.PORT)
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = "!DISCONNECT"

        self.clients: List = []
        self.clients_lock = threading.RLock()

        self.play_game_threads: List = []
        self.play_game_threads_lock = threading.RLock()

        self.new_client_event = threading.Event()
        self.stop_flag = threading.Event()
        self.wait_for_new_client_thread_complete = threading.Event()
        self.start_game_when_two_clients_thread_complete = threading.Event()
        self.start_game_when_two_clients_thread_complete.set()
        self.condition = threading.Condition()


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
            conn.send(data)
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
            except OSError:
                break            

            with self.clients_lock:
                if len(self.clients) < 2: #  Continue with program only if number of clients connected is not yet two
                    self.clients.append((conn, addr))
                    self.new_client_event.set()
                else: #  Send error msg and close the conn
                    try:
                        self.send_data(conn, {"server_full":"Maximum number of clients connected. Try again later"})
                    except:
                        pass
                    conn.close()
                    continue

                if len(self.clients) == 1:
                    thread = threading.Thread(target=self.start_game_when_two_clients)
                    thread.daemon = True
                    thread.start()

                print(f"[ACTIVE CONNECTIONS] {len(self.clients)}")

        print("[CLOSED] server is closed")
                 
    def start_game_when_two_clients(self):
        self.start_game_when_two_clients_thread_complete.clear()
        while True:
            if self.stop_flag.is_set():
                break

            self.clients_lock.acquire()
            if len(self.clients) == 1:
                self.clients_lock.release()
                self.new_client_event.clear()
                conn, addr = self.clients[0]
                
                print("Waiting for other player to join the connection. . .")
                try:
                    self.send_data(conn, {"status":"Waiting for other player to join the connection"})
                except SendingDataError:
                    self.remove_client(conn, addr)

                thread = threading.Thread(target=self.wait_for_new_client)
                thread.daemon = True
                thread.start()

                if self.wait_for_one_of_multiple_events(self.wait_for_new_client_thread_complete):
                    if self.new_client_event.is_set():
                        continue                    
                    else:
                        print("Connection timed out: No other player joined the game. Try joining the connection again.")
                        try:
                            self.send_data(conn, {"timeout":"Connection timed out: No other player joined the game. Try joining the connection again."})
                        except SendingDataError:
                            pass
                        self.remove_client(conn, addr)
                        break
                else:
                    break
            elif len(self.clients) == 2:                           
                self.new_client_event.clear()
                print("Both clients connected. Starting game. . .")
                for client in self.clients:
                    conn, addr = client

                    thread = threading.Thread(target=self.play_game, args=(conn, addr))
                    thread.daemon = True

                    with self.play_game_threads_lock:
                        self.play_game_threads.append(thread)

                    thread.start()                   
                self.clients_lock.release()
                break
        self.start_game_when_two_clients_thread_complete.set()

    def wait_for_one_of_multiple_events(self, some_event):

        """Wait for some event or keyboard interrupt which sets self.stop_flag"""

        while not (some_event.is_set() or self.stop_flag.is_set()):
            with self.condition:
                self.condition.wait()
        if some_event.is_set():
            return True
        elif self.stop_flag.is_set():
            return False

    def wait_for_new_client(self):
        self.wait_for_new_client_thread_complete.clear()
        if self.new_client_event.wait(self.TIMEOUT_FOR_CLIENT):
            self.wait_for_new_client_thread_complete.set()
            with self.condition:
                self.condition.notify()
            return True
        self.wait_for_new_client_thread_complete.set()
        with self.condition:
            self.condition.notify()
        return False

    def remove_client(self, conn, addr):
        with self.clients_lock:
            conn.close()
            try:
                self.clients.remove((conn, addr))
            except ValueError:
                print("Client already removed from list")
            else:
                print(f"[DISCONNECTION] {addr} disconnected.")

    def terminate_program(self):

        """Wait for threads to complete and exit program"""

        self.stop_flag.set()
        with self.condition:
            self.condition.notify()

        if not self.start_game_when_two_clients_thread_complete.is_set():
            self.start_game_when_two_clients_thread_complete.wait()

        self.server.close()
        with self.clients_lock:
            for client in self.clients:
                conn, _ = client
                conn.close()

        with self.play_game_threads_lock:
            for thread in self.play_game_threads:
                if thread.is_alive():
                    thread.join()

        print("Keyboard Interrupt detected")
        print("[CLOSED] server is closed")
        sys.exit(1)

    def play_game(self, conn, addr):
        if not self.start_game_when_two_clients_thread_complete.is_set():
            self.start_game_when_two_clients_thread_complete.wait()

        print(f"[NEW CONNECTION] {addr} connected.")

        
        full_msg = b''
        new_msg = True
        id = None

        with self.clients_lock:
            try:
                conn1, addr1 = self.clients[0]
                conn2, addr2 = self.clients[1]
            except IndexError:
                print("Index error: Client no longer exists")
                self.remove_client(conn, addr)
                return

        try:
            with self.clients_lock:
                if conn == conn1:
                    id = self.clients.index((conn1, addr1))
                    self.send_data(conn1, {"id": id})
                else:
                    id = self.clients.index((conn2, addr2))
                    self.send_data(conn2, {"id": id})

            if not id: #  If id is 0 i.e. if first connected player...
                self.send_data(conn, {"get_first_player_name":True})
            else:
                self.send_data(conn, {"waiting_for_name":"Waiting for other player to enter their name"})
                
            while True:
                try:
                    msg = conn.recv(16)                                  
                except ConnectionAbortedError as e:
                    print(f"Connection Aborted: {e}") 
                    break                

                if not msg:
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
                        if 'you' in loaded_json:
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
                            if conn == conn1:
                                self.send_data(conn2, {'play_again':loaded_json['play_again']})
                                if not loaded_json['play_again']:
                                    self.remove_client(conn2, addr2)
                                    print("Player has quit the game")
                                    break
                            elif conn == conn2:
                                self.send_data(conn1, {'play_again':loaded_json['play_again']})
                                if not loaded_json['play_again']:
                                    self.remove_client(conn1, addr1)
                                    print("Player has quit the game")
                                    break
                        elif 'first_player' in loaded_json:                        
                            self.send_data(conn1, {'first_player':loaded_json['first_player']})                        
                            self.send_data(conn2, {'first_player':loaded_json['first_player']})                                                
                        elif 'DISCONNECT' in loaded_json:
                            if loaded_json['DISCONNECT'] == self.DISCONNECT_MESSAGE:
                                if 'close_other_client' in loaded_json:
                                    if loaded_json['close_other_client']:
                                        if conn == conn1:
                                            self.send_data(conn2, {"other_client_disconnected":"Other client disconnected unexpectedly"})
                                        else:
                                            self.send_data(conn1, {"other_client_disconnected":"Other client disconnected unexpectedly"})
                                break
                    except KeyError:
                        break               
                            # ----------------Use loaded json data here----------------
        
        except SendingDataError as data:
            print(f"Error sending '{data}'")            
        except ConnectionResetError as e: #  This exception is caught when the server tries to receive a msg from a disconnected client
            print(f"Connection Reset: {e}")
            if conn == conn1:
                self.send_data(conn2, {"other_client_disconnected":"Other client disconnected unexpectedly"})
            else:
                self.send_data(conn1, {"other_client_disconnected":"Other client disconnected unexpectedly"})
        except (socket.error, Exception) as e:
            print(f"Some Error occured: {e}")
            print("Closing both clients...")

        # Close other and current client
        if conn == conn1:
            self.remove_client(conn2, addr2)
        else:
            self.remove_client(conn1, addr1)
        
        self.remove_client(conn, addr)
        
if __name__ == "__main__":
    server = Server()
    try:
        server.host_game()
    except KeyboardInterrupt:
        server.terminate_program()