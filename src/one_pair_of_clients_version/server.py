import socket
import sys
import threading
import pickle
import copy

from typing import List

from core.exceptions import SendingDataError


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

        self.clients: List = []
        self.clients_lock = threading.RLock()       

        self.new_client_event = threading.Event()
        self.stop_flag = threading.Event()
        self.wait_for_new_client_thread_complete = threading.Event()
        self.condition = threading.Condition()


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
            except socket.error as e:
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
                    self.new_client_event.set() #  Set event anyway even though KeyboardInterrupt occured so that wait_for_new_client thread ends on its own instead of terminating forcefully
                    break
            elif len(self.clients) == 2:                         
                self.new_client_event.clear()
                print("Both clients connected. Starting game. . .")                

                for client in self.clients:
                    conn, addr = client

                    thread = threading.Thread(target=self.play_game, args=(conn, addr))
                    thread.daemon = True
                    thread.start()                   
                self.clients_lock.release()
                break

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
        if self.new_client_event.wait(self.TIMEOUT_FOR_OTHER_CLIENT_TO_JOIN):
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
            if (conn, addr) in self.clients:
                self.clients.remove((conn, addr))
                print(f"[DISCONNECTION] {addr} disconnected.")

    def terminate_program(self):

        """Wait for threads to complete and exit program"""

        self.stop_flag.set()
        with self.condition:
            self.condition.notify()

        self.server.close()
        with self.clients_lock:
            for client in self.clients:
                conn, _ = client
                conn.close()

        main_thread = threading.main_thread()
        for thread in threading.enumerate():
            if thread is not main_thread:
                thread.join()

        print(f"\nKeyboard Interrupt detected")
        print("[CLOSED] server is closed")
        sys.exit(1)

    def play_game(self, conn, addr):        

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
                    conn.settimeout(self.TIMEOUT_FOR_RECV) #  Timeout for recv
                    msg = conn.recv(16)                                  
                except ConnectionAbortedError as e:
                    print(f"Connection Aborted: {e}") 
                    break
                except socket.timeout as e:
                    print(f"recv timed out. Connection is half-open or client took too long to respond. Ensure this machine is still connected to the network.")               
                    break

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

                    try:
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
                    except KeyError:
                        break               
                            # ----------------Use unpickled json data here----------------
        
        except SendingDataError as data:
            print(f"Error sending '{data}'")            
        except ConnectionResetError as e: #  This exception is caught when the server tries to receive a msg from a disconnected client
            print(f"Connection Reset: {e}")
            if conn == conn1:
                self.send_data(conn2, {"other_client_disconnected":"Other client disconnected unexpectedly"})
            else:
                self.send_data(conn1, {"other_client_disconnected":"Other client disconnected unexpectedly"})
        except (socket.error, Exception) as e:
            if e != 'timed out':
                print(f"Some Error occured: {e}")

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
