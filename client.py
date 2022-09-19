import os
import sys
import time
import itertools
import socket
import pickle
from threading import Thread, Event, Condition, RLock

from termcolor import colored  # type: ignore

from connect4 import Connect4Game
from player import Player
from level import Level
from board import Board

os.system('') # To ensure that escape sequences work, and coloured text is displayed normally and not as weird characters

connect4game = Connect4Game()



class Client:
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"
    POINTS_FOR_WINNING_ONE_ROUND = 10

    def __init__(self):

        self.HEADERSIZE = 10

        self.server = "127.0.0.1"
        self.port = 5050
        self.addr = (self.server, self.port)

        self.spinner_thread_complete = Event()
        self.main_game_thread_complete = Event()
        self.main_game_started = Event()
        self.keyboard_interrupt_event = Event()
        self.stop_flag = Event()
    
        self.spinner_thread_complete.set()
        self.main_game_thread_complete.set()
        self._reset_session()
        self._reset_game()        
        self.connect_to_game()

    def connect_to_game(self):
        try:
            connect = input("\nReady to play Connect4?\nPress Enter to join a game or Q to quit: ").strip().lower()
        except EOFError:
            self.stop_flag.set()
            return
        
        print("\n")
        if connect == "q":
            print(f"Goodbye\n")
            self.stop_flag.set()
            return
        else:

            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except socket.error as e:
                print(colored(f"Error creating socket: {e}", "red", attrs=['bold']))
                self.client = None

            try:
                self.client.connect(self.addr)
            except socket.gaierror as e:
                print(colored(f"Address-related error connecting to server: {e}", "red", attrs=['bold']))
                self.client.close()
                self.stop_flag.set()
            except socket.error as e:
                print(colored(f"Connection error: {e}", "red", attrs=['bold']))
                self.client.close()
                self.stop_flag.set()
            else:
                if self.client is None:
                    print(colored(f"Could not open socket", "red", attrs=['bold']))                
                    self.stop_flag.set()
                    return

                self._reset_session()
                self._reset_game()
               
                self.play_game_thread = Thread(target=self.play_game)
                self.play_game_thread.daemon = True
                self.play_game_thread.start()
            
    def send_data(self, data):
        data = pickle.dumps(data)
        data = bytes(f'{len(data):<{self.HEADERSIZE}}', self.FORMAT) + data
        try:
            self.client.send(data)
        except socket.error:
            raise

    def _get_other_player_name(self, player):

        while True:
            try:
                other_player = input("Enter your name: ").strip()
            except EOFError:
                return
            if other_player.lower() == player.lower():
                print("A player already exists with that name. Choose another name")
                continue
            if other_player:
                break
            print("You must enter a name")

        return other_player

    def simulate_loading_with_spinner(self, loading_msg, loaded_json):
        self.spinner_thread_complete.clear()
        NO_OF_CHARACTERS_AFTER_LOADING_MSG = 5
        spaces_to_replace_spinner = ' ' * NO_OF_CHARACTERS_AFTER_LOADING_MSG

        def color_final_loading_msg():
            if type(loading_msg) == list:                
                if ('other_client_disconnected' in self.loaded_json or 'timeout' in self.loaded_json) or self.end_thread_event.is_set():
                    red_first_part = colored(loading_msg[0], "red", attrs=['bold'])
                    red_last_part = colored(loading_msg[2], "red", attrs=['bold'])
                    final_loading_msg = f"{red_first_part}{loading_msg[1]}{red_last_part}"                
                else:
                    green_first_part = colored(loading_msg[0], "green", attrs=['bold'])
                    green_last_part = colored(loading_msg[2], "green", attrs=['bold'])
                    final_loading_msg = f"{green_first_part}{loading_msg[1]}{green_last_part}"
            else:
                if ('other_client_disconnected' in self.loaded_json or 'timeout' in self.loaded_json) or self.end_thread_event.is_set():
                    final_loading_msg = colored(loading_msg, "red", attrs=['bold'])
                else:
                    final_loading_msg = colored(loading_msg, "green", attrs=['bold'])
            return final_loading_msg

        if type(loading_msg) == list:
            yellow_first_part = colored(loading_msg[0], "yellow", attrs=['bold'])
            yellow_last_part = colored(loading_msg[2], "yellow", attrs=['bold'])
            yellow_loading_msg = f"{yellow_first_part}{loading_msg[1]}{yellow_last_part}"
        else:
            yellow_loading_msg = colored(loading_msg, "yellow", attrs=['bold'])
            
                
        for c in itertools.cycle(['|', '/', '-', '\\']):
            with self.loaded_json_lock:         
                if loaded_json != self.loaded_json or self.end_thread_event.is_set():
                    sys.stdout.write(f'\r{color_final_loading_msg()}{spaces_to_replace_spinner}')
                    print("\n")
                    break
            sys.stdout.write(f'\r{yellow_loading_msg}  {c}  ')
            sys.stdout.flush()
            time.sleep(0.1)
        self.spinner_thread_complete.set()

    def _print_result(self, round_or_game="round"):
        if round_or_game == "round":
            print(f"\n\nAt the end of round {self.level.current_level}, ")
            print(f"You have {self.player.points} points")
            print(f"{self.opponent.name} has {self.opponent.points} points\n\n")
        elif round_or_game == "game":
            
            if self.level.current_level == 1:
                print(f"At the end of the game,")
            else:
                print(f"At the end of the game, after {self.level.current_level} rounds,")
                
            connect4game._calculate_and_display_final_result([self.player, self.opponent])
            print("Thanks for playing\n")

    def _wait_for_one_of_multiple_events(self, some_event):
        while not (some_event.is_set() or self.other_client_disconnected.is_set() or self.end_thread_event.is_set()):   
            with self.condition:
                self.condition.wait()
        if some_event.is_set():
            some_event.clear()
            return False
        elif self.other_client_disconnected.is_set():
            self.other_client_disconnected.clear()            
            return True
        elif self.end_thread_event.is_set():
            return True

    def _set_up_to_terminate_program(self, error_msg):
            
        if not self.end_thread_event.is_set(): #  print game stats and error msg only if these have not been done before
            self.end_thread_event.set()

            if not self.spinner_thread_complete.is_set(): 
                self.spinner_thread_complete.wait() #  Wait for simulate_loading_with_spinner thread to complete

            with self.condition:
                self.condition.notify()           

            if not self.main_game_thread_complete.is_set():
                self.main_game_thread_complete.wait() #  Wait for main_game_thread thread to complete

            if not self.game_ended.is_set() and not self.game_over_event.is_set():
                # If one of the conditions is satisfied, player objects have non-empty values and can be safely accessed 
                # in _print_result() method. Also, there's no need to print results if the round did not start at all
                if error_msg:
                    print(f"\n{error_msg}\n") #  Print exception or error

                # Print game stats
                if self.main_game_started.is_set():                                         
                    self._print_result("round")
                    self._print_result("game")                   

    def _reset_session(self):
        self.loaded_json = {}
        self.loaded_json_lock = RLock()

        self.play_game_thread = Thread()
        self.play_game_thread.daemon = True
        self.play_game_thread.start()

    def _reset_for_new_round(self):
        self.board = Board()
        self.play_again_reply = False
        self.first_player_for_next_round = Player(name='', marker='')
        self.round_over_json = {}

        self.board_updated_event = Event() 
        self.play_again_reply_received = Event() 
        self.first_player_received = Event() 
        self.round_over_event = Event()

    def _reset_game(self):
        self.ID = None
        self.you = ""
        self.opponent = Player(name='', marker='')
        self.player = Player(name='', marker='')
        self.your_turn = False
        self.level = Level()

        self.end_thread_event = Event()
        self.other_client_disconnected = Event()
        self.game_over_event = Event() # This is set when player no longer wants to play
        self.game_ended = Event() # This is set when opponent no longer wants to play
        self.condition = Condition() # condition that waits for some event or other_client_disconnected event to be set

        self._reset_for_new_round()

    def main_game_thread(self):
        self.main_game_thread_complete.clear()
        playing = True

        while playing:            
            print("\n\n", f"ROUND {self.level.current_level}".center(50, '-'))
            self._reset_for_new_round() # Reset board, round_over_json, etc for new round

            self.board.print_board() #  Print board at start of each round

            first_time = True
            while True:

                if self.your_turn:
                    if not first_time: #  Do not wait on first run of loop for board to be updated since no move has been made yet                        
                        # Wait until board is updated with other player's latest move or until other_client_disconnected event is set or until end_thread_event is set
                        if self._wait_for_one_of_multiple_events(self.board_updated_event): #  Other client has disconnected or end_thread_event is set
                            self.main_game_thread_complete.set()
                            return  #  "return" is used instead of "break" so that the play_again loop will not run
                        self.board.print_board() #  Print board to show player their opponent's move

                    # At this point, the opponent has won so we want to break to end this loop and 
                    # so that we do not collect this user's input anymore.
                    if self.round_over_event.wait(0.1):
                        self.round_over_event.clear()
                        if self.round_over_json['round_over']:
                            if self.round_over_json['winner'] is not None:
                                print(f"\n{self.opponent.name} {self.opponent.marker} wins this round")
                                print("Better luck next time!\n")
                                self.opponent.points = self.round_over_json['winner'].points
                            break

                    self.board.play_at_position(self.player)

                    if self.other_client_disconnected.wait(0.1) or self.end_thread_event.wait(0.1) or self.keyboard_interrupt_event.wait(0.1):
                        self.main_game_thread_complete.set()
                        return

                    try:
                        self.send_data({'board':self.board})
                    except socket.error:
                        error_msg = colored(f"Error sending data: Other client may have disconnected", "red", attrs=['bold'])
                        # ! self.main_game_thread_complete must be set before self._set_up_to_terminate_program(), 
                        # ! otherwise, deadlock will occur as self.main_game_thread_complete.wait() will block infinitely
                        self.main_game_thread_complete.set()
                        self._set_up_to_terminate_program(error_msg)
                        return                   

                    self.board.print_board()
                    self.your_turn = False

                    if self.board.check_win(self.player):
                        self.player.points += self.POINTS_FOR_WINNING_ONE_ROUND
                        print(f"\n{self.player.name} {self.player.marker} wins this round!\n")
                        try:
                            self.send_data({'round_over':True, 'winner':self.player})
                        except socket.error:
                            error_msg = colored(f"Error sending data: Other client may have disconnected", "red", attrs=['bold'])
                            self.main_game_thread_complete.set()
                            self._set_up_to_terminate_program(error_msg)
                            return                        
                        break

                    if self.board.check_tie():
                        print("\nIt's a tie!\n")
                        try:
                            self.send_data({'round_over':True, 'winner':None})
                        except socket.error:
                            error_msg = colored(f"Error sending data: Other client may have disconnected", "red", attrs=['bold'])
                            self.main_game_thread_complete.set()
                            self._set_up_to_terminate_program(error_msg)
                            return
                        break
                else:             
                    # Text is split into a list so that text can be colored separate from marker in the simulate_loading_with_spinner function
                    # If raw string is entered directly, text after the marker does not get coloured.
                    loading_msg = [f"Waiting for {self.opponent.name} ", self.opponent.marker, " to play"]
                    self.your_turn = True
                    with self.loaded_json_lock:
                        loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json, ))
                    loading_thread.daemon = True
                    loading_thread.start()
                first_time = False

            self._print_result("round")

            while True:
                try:
                    play_again = input("Want to play another round?\nEnter 'Y' for 'yes' and 'N' for 'no': ").lower().strip()
                except EOFError:
                    self.main_game_thread_complete.set()
                    return

                if play_again == 'y':
                    # Shuffle the players again before starting next round.
                    if not self.other_client_disconnected.is_set() and not self.end_thread_event.is_set():
                        try:
                            self.send_data({'play_again':True})
                        except socket.error:
                            error_msg = colored(f"Error sending data: Other client may have disconnected", "red", attrs=['bold'])
                            self.main_game_thread_complete.set()
                            self._set_up_to_terminate_program(error_msg)
                            return

                    if not self.play_again_reply_received.is_set() and not self.other_client_disconnected.is_set():
                        loading_msg = f"Waiting for {self.opponent.name} to reply"
                        with self.loaded_json_lock:
                            loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json, ))
                        loading_thread.daemon = True
                        loading_thread.start()

                    # Wait until opponent replies or until other_client_disconnected event is set or until end_thread_event is set
                    if self._wait_for_one_of_multiple_events(self.play_again_reply_received):  #  Other client has disconnected or end_thread_event is set
                        playing = False
                        break
                    
                    if self.play_again_reply:
                        self.level.current_level += 1 

                        if not self.ID:
                            first_player = connect4game._shuffle_players([self.player, self.opponent])[0]
                            try:
                                self.send_data({'first_player':first_player})
                            except socket.error as e:
                                error_msg = colored(f"Error sending data: Other client may have disconnected", "red", attrs=['bold'])
                                self.main_game_thread_complete.set()
                                self._set_up_to_terminate_program(error_msg)
                                return

                        # Wait until first player is received or until other_client_disconnected event is set or until end_thread_event is set
                        if self._wait_for_one_of_multiple_events(self.first_player_received):  #  Other client has disconnected or end_thread_event is set
                            playing = False
                            break                

                        if self.ID: #  Show that it is shuffling for the player other than the one that shuffled
                            print("Randomly choosing who to go first . . .")
                            print(f"{self.first_player_for_next_round.name} goes first")

                        # The check is between Player objects' names and not the objects themselves because their 
                        # points may be different if one of them is leading from the previous round
                        if self.first_player_for_next_round.name == self.player.name:
                            self.your_turn = True                            
                        else:                            
                            self.your_turn = False
                        break
                    else:
                            # Opponent does not want to play another round
                            self.game_ended.set()
                            print(f"{self.opponent.name} has quit")
                            self._print_result("game")
                            playing = False
                            break
                elif play_again == 'n':
                    self.game_over_event.set()
                    self._print_result("game")
                    if not self.other_client_disconnected.is_set() and not self.end_thread_event.is_set():
                        try:
                            self.send_data({'play_again':False})
                            self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE})
                        except socket.error:
                            error_msg = colored(f"Error sending data: Other client may have disconnected", "red", attrs=['bold'])
                            # Unlike other places where this funciton is called, loop is not terminated immediately
                            # because it will terminate anyway in the outer block, and so that it will end naturally like when client quits 
                            self.main_game_thread_complete.set()
                            self._set_up_to_terminate_program(error_msg)
                    playing = False
                    break
                else:
                    print("Invalid input.")
                    continue
        self.main_game_thread_complete.set()

    def play_game(self): 

        main_game_thread = Thread()
        main_game_thread.daemon = True
        main_game_thread.start()

        self.main_game_started.clear()

        full_msg = b''
        new_msg = True
        while True:            
            try:
                msg = self.client.recv(16)
            except ConnectionResetError: #  This exception is caught when the client tries to receive a msg from a disconnected server
                error_msg = colored(f"Connection Reset: Other client may have disconnected", "red", attrs=['bold'])
                self._set_up_to_terminate_program(error_msg)
                break
            except socket.error:
                error_msg = colored(f"Error receiving data: Other client may have disconnected", "red", attrs=['bold'])
                self._set_up_to_terminate_program(error_msg)
                break
            
            if not msg: #  This breaks out of the loop when disconnect msg has been sent to server and/or client conn has been closed server-side
                error_msg = ''
                
                if not self.keyboard_interrupt_event.is_set() and not self.game_ended.is_set() and not self.game_over_event.is_set(): 
                    # Connection was forcibly closed by server
                    error_msg = colored("An error occured or other client may have disconnected", "red", attrs=['bold'])

                self._set_up_to_terminate_program(error_msg)
                break
            
            if new_msg:
                msglen = int(msg[:self.HEADERSIZE])                
                new_msg = False


            full_msg += msg


            if len(full_msg)-self.HEADERSIZE == msglen:
                
                # -------------------------------------Use loaded json data here-------------------------------------

                with self.loaded_json_lock:
                    self.loaded_json = pickle.loads(full_msg[self.HEADERSIZE:])                  
                
                # ! Wait for simulate_loading_with_spinner thread to complete only after unpickled full_msg 
                # ! is assigned to self.loaded_json. Otherwise, condition for termination of spinner thread may not be met

                if not self.spinner_thread_complete.is_set():
                    self.spinner_thread_complete.wait() #  Wait for simulate_loading_with_spinner thread to complete


                new_msg = True
                full_msg = b''

                try:
                    self.loaded_json_lock.acquire()
                    # print("Loaded_json", self.loaded_json)
                    if "server_full" in self.loaded_json:
                        print(colored(f"{self.loaded_json['server_full']}", "red", attrs=['bold']))
                        self.loaded_json_lock.release()
                        break
                    elif "id" in self.loaded_json:
                        self.ID = self.loaded_json["id"]
                        loading_msg = "Both clients connected. Starting game"
                        loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json, ))
                        self.loaded_json_lock.release()
                        loading_thread.daemon = True
                        loading_thread.start()                                                                        
                    elif "other_client_disconnected" in self.loaded_json:
                        self.other_client_disconnected.set()
                        disconnect_msg = colored(self.loaded_json['other_client_disconnected'], "red", attrs=['bold'])
                        self.loaded_json_lock.release()
                        with self.condition:
                            self.condition.notify()                        
                        self._set_up_to_terminate_program(disconnect_msg)
                        break
                    elif "status" in self.loaded_json:                                                          
                        loading_msg = self.loaded_json['status'] 
                        self.main_game_started.clear() #  Unset value as game setup has begun again or as game is being set up for the first time
                        if self.game_ended.is_set():
                            main_game_thread.join() #  Make sure main_game_thread has ended before starting process of setting up game again
                        loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json, ))
                        self.loaded_json_lock.release()
                        loading_thread.daemon = True
                        loading_thread.start()               
                    elif "waiting_for_name" in self.loaded_json:
                        loading_msg = self.loaded_json['waiting_for_name']                                        
                        loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json, ))
                        self.loaded_json_lock.release()
                        loading_thread.daemon = True
                        loading_thread.start()
                    elif "get_first_player_name" in self.loaded_json:                                                               
                        connect4game._about_game()                        
                        loading_msg = "Waiting for other player to enter their name"
                        loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json, ))
                        self.loaded_json_lock.release()
                        loading_thread.daemon = True
                        self.you = connect4game._get_player_name()
                        self.send_data({'you':self.you})
                        loading_thread.start()                        
                    elif "opponent" in self.loaded_json:                                                             
                        self.opponent = self.loaded_json['opponent']
                        self.loaded_json_lock.release()
                        if not self.you:
                            connect4game._about_game()
                            self.you = self._get_other_player_name(self.opponent)
                            self.send_data({'you':self.you})                        
                        print("You are up against: ", self.opponent)                        
                        # Shuffling player names
                        if not self.ID:
                            first_player = connect4game._shuffle_players([self.you, self.opponent])
                            self.send_data({'first':first_player})                      
                    elif "first" in self.loaded_json:
                        first = self.loaded_json['first'][0]
                        loading_msg = f"Waiting for {self.opponent} to choose their color"
                        loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_msg, self.loaded_json, ))
                        self.loaded_json_lock.release()
                        loading_thread.daemon = True
                        if self.ID:
                            print("Randomly choosing who to go first . . .")                
                            print(f"{first} goes first")
                        if first == self.you:
                            colors = connect4game._get_players_colors(self.you)                               
                            self.send_data({'colors':colors})
                        else:
                            loading_thread.start()                            
                    elif "colors" in self.loaded_json:                                                                                     
                        colors = self.loaded_json['colors']                        
                        self.loaded_json_lock.release()
                        if first == self.you:
                            self.your_turn = True
                            self.player = Player(self.you, colored('O', colors[0], attrs=['bold']))                            
                        else:
                            self.your_turn = False
                            self.player = Player(self.you, colored('O', colors[1], attrs=['bold']))                        
                        self.send_data({'opponent_player_object':self.player})
                    elif "opponent_player_object" in self.loaded_json:
                        self.opponent = self.loaded_json['opponent_player_object']                        
                        self.loaded_json_lock.release()
                        main_game_thread = Thread(target=self.main_game_thread)
                        main_game_thread.daemon = True
                        with self.condition:
                            main_game_thread.start()
                        self.main_game_started.set()
                        self.game_ended.clear()               
                    elif "board" in self.loaded_json:
                        self.board = self.loaded_json['board']
                        self.loaded_json_lock.release()
                        self.board_updated_event.set() 
                        with self.condition:
                            self.condition.notify()
                    elif "round_over" in self.loaded_json and "winner" in self.loaded_json:
                        self.round_over_json = self.loaded_json
                        self.loaded_json_lock.release()
                        self.round_over_event.set()
                    elif 'play_again' in self.loaded_json:
                        self.play_again_reply = self.loaded_json['play_again']
                        self.loaded_json_lock.release()
                        self.play_again_reply_received.set()                        
                        with self.condition:
                            self.condition.notify()
                    elif 'first_player' in self.loaded_json:
                        self.first_player_for_next_round = self.loaded_json['first_player']
                        self.loaded_json_lock.release()
                        self.first_player_received.set()
                        with self.condition:
                            self.condition.notify()
                    elif 'timeout' in self.loaded_json:
                        print(colored(self.loaded_json['timeout'], "red", attrs=['bold']))
                        self.loaded_json_lock.release()
                        break                
                except (socket.error, Exception):
                    if not self.keyboard_interrupt_event.is_set():
                        error_msg = colored(f"An error occured or other client may have disconnected", "red", attrs=['bold'])
                        self._set_up_to_terminate_program(error_msg)
                    break        
                # -------------------------------------Use loaded json data here-------------------------------------

        if not self.spinner_thread_complete.is_set():
            self.spinner_thread_complete.wait() #  Wait for simulate_loading_with_spinner thread to complete

        if not self.main_game_thread_complete.is_set():
            self.main_game_thread_complete.wait() #  Wait for main_game_thread thread to complete

        if self.keyboard_interrupt_event.is_set():
            self.stop_flag.set()
        else:
            self.connect_to_game()

    def main_thread_to_exit_program(self):
        try:
            while not self.stop_flag.is_set():  # allow other threads to exit the main thread too
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.keyboard_interrupt_event.set()
            error_msg = colored(f"Keyboard Interrupt: Program ended", "red", attrs=['bold'])        
            self._set_up_to_terminate_program('')
            try:
                self.send_data({'DISCONNECT':self.DISCONNECT_MESSAGE, 'close_other_client':True})
            except socket.error:
                pass
            self.client.close()
            self.play_game_thread.join()
            print(f"\n{error_msg}\n")
        

if __name__ == "__main__":
    try:
        client = Client()
    except KeyboardInterrupt:
        error_msg = colored(f"Keyboard Interrupt: Program ended", "red", attrs=['bold'])        
        print(f"\n{error_msg}\n")
    else:
        client.main_thread_to_exit_program()
