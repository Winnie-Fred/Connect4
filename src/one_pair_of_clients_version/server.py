import socket
import sys
import threading
import pickle
import copy

from typing import List
from zeroconf import ServiceInfo, Zeroconf

from core.exceptions import SendingDataError
from core.config import service_name, service_type


class Server:
    def __init__(self):
        self.HEADERSIZE = 10
        self.SERVER = "0.0.0.0"
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

        try:
           self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            print(f"Error creating socket: {e}")
            sys.exit(1)

        

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
            ip_address = socket.gethostbyname(socket.gethostname())
            self.zeroconf = Zeroconf()            
            self.service_info = ServiceInfo(type_=service_type, name=service_name, addresses=[ip_address], port=self.PORT, properties={})
            self.zeroconf.register_service(self.service_info)
            print("[REGISTERED] Connect4 service is registered")
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
            except socket.error:
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

                if self.new_client_event.wait(self.TIMEOUT_FOR_OTHER_CLIENT_TO_JOIN):
                    if self.stop_flag.is_set():
                        break
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

    def remove_client(self, conn, addr):
        with self.clients_lock:
            conn.close()
            if (conn, addr) in self.clients:
                self.clients.remove((conn, addr))
                print(f"[DISCONNECTION] {addr} disconnected.")

    def terminate_program(self):

        """Wait for threads to complete and exit program"""
        self.stop_flag.set()
        self.new_client_event.set() #  Set this so that thread waiting for other client to join stops blocking

        self.server.close()
        with self.clients_lock:
            for client in self.clients:
                conn, _ = client
                conn.close()

        self.zeroconf.unregister_service(self.service_info)
        self.zeroconf.close()

        main_thread = threading.main_thread()
        for thread in threading.enumerate():
            if thread is not main_thread:
                thread.join()

        print(f"\nKeyboard Interrupt detected")
        print("[CLOSED] server is closed")
        print("[CLOSED] Connect4 service is closed")
        sys.exit(1)

    def process_message(self, conn, unpickled_json, conn1, conn2):
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
            elif conn == conn2:
                self.send_data(conn1, {'play_again':unpickled_json['play_again']})
                if not unpickled_json['play_again']:
                    print("Player has quit the game")
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
                return False
        return True

    def play_game(self, conn, addr):        

        print(f"[NEW CONNECTION] {addr} connected.")

    
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
                
            buffer = b""
            receiving = True
            while receiving:
                
                conn.settimeout(self.TIMEOUT_FOR_RECV) #  Timeout for recv
                msg = conn.recv(16)                                  
                

                if not msg:
                    break

                # Add received data to the buffer
                buffer += msg 

                # Process complete messages
                while len(buffer) >= self.HEADERSIZE:
                    # Extract the header and determine the message length
                    header = buffer[:self.HEADERSIZE]
                    message_length = int(header)

                    # Check if the complete message is available in the buffer
                    if len(buffer) >= self.HEADERSIZE + message_length:

                        # -------------------------------------Use unpickled json data here-------------------------------------

                        # Extract the complete message
                        message = buffer[self.HEADERSIZE:self.HEADERSIZE + message_length]
                        unpickled_json = pickle.loads(message) 

                        conn.settimeout(None) #  Reset timer for next msg
                        # print("unpickled_json", unpickled_json)           

                    
                        if not self.process_message(conn, unpickled_json, conn1, conn2):
                            receiving = False
                            break
                        # -------------------------------------Use unpickled json data here-------------------------------------
                        
                        # Remove the processed message from the buffer
                        buffer = buffer[self.HEADERSIZE + message_length:]
                    else:
                        # Incomplete message, break out of the loop and wait for more data
                        break
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
        except Exception as e:
            print(f"An error occured: {e}")

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
    else:
        server.zeroconf.unregister_service(server.service_info)
        server.zeroconf.close()
        print("[CLOSED] Connect4 service is closed")
