import sys
import time
import socket
import pickle
import select
import re
from cgitb import text
from collections import namedtuple

import pygame
import pygame.freetype
import pyperclip # type: ignore

from pygame.rect import Rect
from pygame.sprite import RenderUpdates

from pygame_version.client import Client
from pygame_version.choice import Choice
from pygame_version.gamestate import GameState
from pygame_version.ui_tools import UIElement, CopyButtonElement, DisabledOrEnabledBtn, InputBox, FadeOutText, create_text_to_draw

from termcolor import colored  # type: ignore

BLUE = (106, 159, 181)
RED = (204, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
MAX_GAME_CODE_LENGTH = 16
MAX_IP_ADDR_LENGTH = 15
MIN_IP_ADDR_LENGTH = 7


class Connect4:

    def __init__(self):
        self.client = Client()
        self.ID = None
        self.code = ''
        self.keyboard_interrupt = False
    
    def run_game(self):
        pygame.init()

        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Connect4")
        game_state = GameState.MENU
        
        while True:          

            if game_state == GameState.MENU:
                game_state = self.menu_screen(screen)                

            if game_state == GameState.CREATE_GAME:
                game_state = self.collect_ip_screen(screen, self.main_game_screen, choice=Choice.CREATE_GAME)

            if game_state == GameState.JOIN_ANY_GAME:
                game_state = self.collect_ip_screen(screen, self.main_game_screen, choice=Choice.JOIN_ANY_GAME)

            if game_state == GameState.JOIN_GAME_WITH_CODE:
                game_state = self.collect_ip_screen(screen, self.join_game_with_code_screen)

            if game_state == GameState.JOIN_GAME_WITH_ENTERED_CODE:
                game_state = self.main_game_screen(screen, Choice.JOIN_GAME_WITH_CODE, code=self.code)

            if game_state == GameState.QUIT:                
                pygame.quit()
                return

    def menu_screen(self, screen):
        menu_header = create_text_to_draw("Ready to play Connect4?", 30, WHITE, BLUE, (400, 100))

        create_game_btn = UIElement(
            center_position=(400, 200),
            font_size=25,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Create a game",
            action=GameState.CREATE_GAME,
        )
        join_any_game_btn = UIElement(
            center_position=(400, 300),
            font_size=25,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Join any game",
            action=GameState.JOIN_ANY_GAME,
        )
        join_game_with_code_btn = UIElement(
            center_position=(400, 400),
            font_size=25,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Join game with code",
            action=GameState.JOIN_GAME_WITH_CODE,
        )
        quit_btn = UIElement(
            center_position=(400, 500),
            font_size=25,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Quit",
            action=GameState.QUIT,
        )

        buttons = RenderUpdates(create_game_btn, join_any_game_btn, join_game_with_code_btn, quit_btn)

        return self.game_menu_loop(screen, buttons, menu_header)

    def main_game_screen(self, screen, choice, code=''):
        frames = []
        for i in range(1, 50):
            frames.append(pygame.image.load(f'../../images/loading-animation-balls/frame-{i}.png').convert_alpha())

        return_btn = UIElement(
            center_position=(140, 570),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Return to main menu",
            action=GameState.MENU,
        )

        copy_btn = CopyButtonElement(
            center_position=(600, 250),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Copy",
            text_after_mouse_up_event="Copied",
            action=GameState.COPY,
        )

        buttons = RenderUpdates(return_btn)
        copy_btn = RenderUpdates(copy_btn)
        
        return self.play_game(screen, buttons, copy_btn, choice, frames)

    def collect_ip_screen(self, screen, next_screen, **kwargs):
        submit_ip_btn = DisabledOrEnabledBtn(
            center_position=(400, 400),
            font_size=20,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            grayed_out_text_rgb=GRAY,
            text="Continue",
            action=GameState.CONTINUE,
        )

        return_btn = UIElement(
            center_position=(140, 570),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Return to main menu",
            action=GameState.MENU,
        )
        
        paste_btn = UIElement(
            center_position=(600, 200),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Paste",
            action=GameState.PASTE,
        )

        input_box = InputBox(
            center_position = (400, 200),
            placeholder_text='Enter IP here',
            font_size=20,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            max_input_length=MAX_IP_ADDR_LENGTH,
            min_input_length=MIN_IP_ADDR_LENGTH,
        )

        fade_out_text = FadeOutText(
            font_size=15,
            text_rgb=RED,
            bg_rgb=BLUE,
            center_position=(400, 300))

        buttons = RenderUpdates(return_btn, paste_btn)

        ui_action = self.collect_input_loop(screen, buttons=buttons, submit_input_btn=submit_ip_btn, input_box=input_box, fade_out_text=fade_out_text)
        if ui_action != GameState.MENU:
            if 'choice' in kwargs:
                choice = kwargs['choice']
                return next_screen(screen, choice=choice)
            return next_screen(screen)
        return ui_action

    def join_game_with_code_screen(self, screen):
        join_game_btn = DisabledOrEnabledBtn(
            center_position=(400, 400),
            font_size=20,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            grayed_out_text_rgb=GRAY,
            text="Join game",
            action=GameState.JOIN_GAME_WITH_ENTERED_CODE,
        )

        return_btn = UIElement(
            center_position=(140, 570),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Return to main menu",
            action=GameState.MENU,
        )
        
        paste_btn = UIElement(
            center_position=(600, 200),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Paste",
            action=GameState.PASTE,
        )

        input_box = InputBox(
            center_position = (400, 200),
            placeholder_text='Enter code here',
            font_size=20,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            max_input_length=MAX_GAME_CODE_LENGTH,
            min_input_length=MAX_GAME_CODE_LENGTH,
        )

        fade_out_text = FadeOutText(
            font_size=15,
            text_rgb=RED,
            bg_rgb=BLUE,
            center_position=(400, 300))

        buttons = RenderUpdates(return_btn, paste_btn)

        return self.collect_input_loop(screen, buttons=buttons, submit_input_btn=join_game_btn, input_box=input_box, fade_out_text=fade_out_text)

    def game_menu_loop(self, screen, buttons, menu_header):
        """ Handles game menu loop until an action is return by a button in the
            buttons sprite renderer.
        """

        if self.client.client is not None:
            self.client.client.close()

        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True            
                
            screen.fill(BLUE)

            menu_header.draw(screen)

            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
                if ui_action != GameState.NO_ACTION:                                                               
                    return ui_action

            buttons.draw(screen)
            pygame.display.flip()

    def collect_input_loop(self, screen, buttons, input_box, submit_input_btn, fade_out_text):
        """ Collects input in loop until an action is return by a button in the
            buttons sprite renderer.
        """
        
        submit_btn_enabled = False
        error = ''
        returned_input = ''
        alpha = 255  # The current alpha value of the text surface.

        time_until_fade = 4000
        time_of_error = None     
        

        while True:
            pasted_input = None
            mouse_up = False
            key_down = False
            backspace = False
            pressed_key = None
            validation = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True
                
                if event.type == pygame.KEYDOWN:
                    key_down = True
                    if event.key == pygame.K_BACKSPACE:
                        backspace = True
                    else:
                        pressed_key = event.unicode
                
            screen.fill(BLUE)

            if error:
                # TODO: Make error fade out after some time, possibly display error when they have entered max characters              

                fade_out_text.text = error
                
                current_time = pygame.time.get_ticks()
                if current_time - time_of_error >= time_until_fade:
                    if alpha > 0:
                        # Reduce alpha each frame, but make sure it doesn't get below 0.
                        alpha = max(alpha-4, 0)

                if not fade_out_text.update(alpha):
                    error = ''
                    alpha = 255
                    
                fade_out_text.draw(screen)                    
            

            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
                if ui_action != GameState.NO_ACTION:
                    if ui_action == GameState.PASTE:
                        pasted_input = pyperclip.paste()
                    else:                                              
                        return ui_action

            buttons.draw(screen)

            ui_action = submit_input_btn.update(pygame.mouse.get_pos(), mouse_up, submit_btn_enabled)
            if ui_action != GameState.NO_ACTION:
                if ui_action == GameState.JOIN_GAME_WITH_ENTERED_CODE:
                    validation = self.validate_game_code(returned_input)
                elif ui_action == GameState.CONTINUE:
                    validation = self.validate_ip_address(returned_input)
                if validation is not None:
                    if validation.passed_validation:
                        self.code = validation.code_or_error
                        return ui_action
                    else:
                        # Validation failed
                        time_of_error = pygame.time.get_ticks()
                        error = validation.code_or_error                    
                else:
                    return ui_action
            submit_input_btn.draw(screen)

            after_input = input_box.update(pygame.mouse.get_pos(), mouse_up, key_down, pressed_key, backspace, pasted_input)                   
            input_box.draw(screen)
            pygame.draw.rect(screen, after_input.color, (input_box.rect.left-3, input_box.rect.top-5, input_box.rect.w+10, input_box.rect.h*2), 2)
            submit_btn_enabled = after_input.submit_btn_enabled
            returned_input = after_input.returned_input

            pygame.display.flip()
    
    def play_game(self, screen, buttons, copy_btn, choice, frames):

        def clear_screen():
            nonlocal loading_text, texts
            loading_text = ''
            texts = []

        last_update = pygame.time.get_ticks()
        last_click = None
        enabled = False
        time_until_enable = 3000
        animation_cooldown = 50
        frame = 0

        error = ''
        loading_text = ''
        general_error_msg = "Server closed the connection or other client may have disconnected"
        something_went_wrong_msg = "Oops! Something went wrong"
        code_to_display = None
        code_to_copy = ''
        unpickled_json = {}
        texts = []

        full_msg = b''
        new_msg = True

        text_and_error = self.client.connect_to_game(choice)
        if text_and_error['error']:
            error = text_and_error['text']
        else:
            loading_text = "Creating game"

        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True
            screen.fill(BLUE)

            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
                if ui_action != GameState.NO_ACTION:
                    return ui_action                    
                        
                buttons.draw(screen)

            if error:
                clear_screen()
                error_text = create_text_to_draw(error, 15, RED, BLUE, (400, 400))
                error_text.draw(screen)

            for text in texts:
                text.draw(screen)

            if code_to_display in texts:
                current_time = pygame.time.get_ticks()
                if last_click is None or current_time - last_click >= time_until_enable:
                    enabled = True
                for button in copy_btn:
                    ui_action = button.update(pygame.mouse.get_pos(), mouse_up, enabled)
                if ui_action != GameState.NO_ACTION:
                    if ui_action == GameState.COPY:                        
                        last_click = current_time
                        pyperclip.copy(code_to_copy)
                        enabled = False                         
                copy_btn.draw(screen)


            if loading_text:
                current_time = pygame.time.get_ticks()
                if current_time - last_update >= animation_cooldown:
                    frame += 1
                    last_update = current_time
                    if frame >= len(frames):
                        frame = 0

                screen.blit(frames[frame], (300, 50))
                loading_msg = create_text_to_draw(loading_text, 15, WHITE, BLUE, (400, 400))
                loading_msg.draw(screen)

            if not error:
                client = self.client.client
                # Get the list of sockets which are readable
                read_sockets, _, _ = select.select([client] , [], [], 0)
                for sock in read_sockets:
                    # incoming message from remote server
                    if sock == client:
                        try:
                            msg = client.recv(16)
                        except ConnectionResetError: #  This exception is caught when the client tries to receive a msg from a disconnected server
                            error = "Connection Reset: Server closed the connection or other client may have disconnected"
                            print(self.color_error_msg_red(error))
                            continue
                        except socket.error:
                            print(self.color_error_msg_red(general_error_msg))
                            error = general_error_msg
                            continue
                        
                        if not msg: #  This breaks out of the loop when disconnect msg has been sent to server and/or client conn has been closed server-side
                            error_msg = ''
                            
                            if not self.keyboard_interrupt: 
                                # Connection was forcibly closed by server
                                error_msg = general_error_msg

                            print(self.color_error_msg_red(error_msg))
                            error = error_msg
                            continue
                        
                        if new_msg:
                            msglen = int(msg[:self.client.HEADERSIZE])  
                            new_msg = False


                        full_msg += msg

                        if len(full_msg) - self.client.HEADERSIZE >= msglen:
                            
                            # -------------------------------------Use unpickled json data here-------------------------------------

                            unpickled_json = pickle.loads(full_msg[self.client.HEADERSIZE:self.client.HEADERSIZE+msglen]) 


                            if len(full_msg) - self.client.HEADERSIZE > msglen: #  Multiple messages were received together
                                full_msg = full_msg[self.client.HEADERSIZE+msglen:] #  Get the part of the next msg that was recieved with the previous one
                                msglen = int(full_msg[:self.client.HEADERSIZE])      
                            else:
                                new_msg = True
                                full_msg = b''                
                            
                            print("unpickled_json", unpickled_json)
                            # -------------------------------------Use unpickled json data here-------------------------------------
                            loading_text = ''

                     

                try:
                    if "code" in unpickled_json:
                        code_to_copy = unpickled_json['code']
                        code_to_display = create_text_to_draw(code_to_copy, 30, WHITE, BLUE, (400, 250))
                        texts = []
                        texts.append(code_to_display)
                        msg = "This is your special code. Send it to someone you wish to join this game."
                        texts.append(create_text_to_draw(msg, 15, WHITE, BLUE, (400, 300)))
                    # elif "no_games_found" in unpickled_json:
                    #     print(colored(unpickled_json['no_games_found'], "red", attrs=['bold']))
                    #     break
                    # elif "game_full" in unpickled_json:
                    #     print(colored(unpickled_json['game_full'], "red", attrs=['bold']))
                    #     break
                    # elif "join_successful" in unpickled_json:
                    #     print(colored(unpickled_json['join_successful'], "green", attrs=['bold']))
                    # elif "id" in unpickled_json:
                    #     self.ID = unpickled_json["id"]
                    #     loading_text = "Both clients connected. Starting game"
                    #     loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_text, unpickled_json, ))
                    #     loading_thread.daemon = True
                    #     loading_thread.start()                                                                        
                    # elif "other_client_disconnected" in unpickled_json:
                    #     self.other_client_disconnected.set()
                    #     disconnect_msg = colored(unpickled_json['other_client_disconnected'], "red", attrs=['bold'])
                    #     with self.condition:
                    #         self.condition.notify()                        
                    #     self._set_up_to_terminate_program(disconnect_msg)
                    #     break
                    elif "status" in unpickled_json:                                                                             
                        loading_text = unpickled_json['status']                                  
                    # elif "waiting_for_name" in unpickled_json:
                    #     loading_text = unpickled_json['waiting_for_name']                                        
                    #     loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_text, unpickled_json, ))
                    #     loading_thread.daemon = True
                    #     loading_thread.start()
                    # elif "get_first_player_name" in unpickled_json:                                                               
                    #     self.connect4game._about_game()
                    #     loading_text = "Waiting for other player to enter their name"
                    #     loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_text, unpickled_json, ))
                    #     loading_thread.daemon = True
                    #     self.you = self.connect4game._get_player_name()
                    #     self.send_data({'you':self.you})
                    #     loading_thread.start()                        
                    # elif "opponent" in unpickled_json:                                                             
                    #     self.opponent = unpickled_json['opponent']
                    #     if not self.you:
                    #         self.connect4game._about_game()
                    #         self.you = self._get_other_player_name(self.opponent)
                    #         self.send_data({'you':self.you})                        
                    #     print("You are up against: ", self.opponent)                        
                    #     # Shuffling player names
                    #     if not self.ID:
                    #         first_player = self.connect4game._shuffle_players([self.you, self.opponent])
                    #         self.send_data({'first':first_player})                      
                    # elif "first" in unpickled_json:
                    #     first = unpickled_json['first'][0]
                    #     loading_text = f"Waiting for {self.opponent} to choose their color"
                    #     loading_thread = Thread(target=self.simulate_loading_with_spinner, args=(loading_text, unpickled_json, ))
                    #     loading_thread.daemon = True
                    #     if self.ID:
                    #         print("Randomly choosing who to go first . . .")                
                    #         print(f"{first} goes first")
                    #     if first == self.you:
                    #         colors = self.connect4game._get_players_colors(self.you)
                    #         self.send_data({'colors':colors})
                    #     else:
                    #         loading_thread.start()                            
                    # elif "colors" in unpickled_json:                                                                                     
                    #     colors = unpickled_json['colors']                        
                    #     if first == self.you:
                    #         self.your_turn = True
                    #         self.player = Player(self.you, colored('O', colors[0], attrs=['bold']))                            
                    #     else:
                    #         self.your_turn = False
                    #         self.player = Player(self.you, colored('O', colors[1], attrs=['bold']))                        
                    #     self.send_data({'opponent_player_object':self.player})
                    # elif "opponent_player_object" in unpickled_json:
                    #     self.opponent = unpickled_json['opponent_player_object']                        
                    #     main_game_thread = Thread(target=self.main_game_thread)
                    #     main_game_thread.daemon = True
                    #     with self.condition:
                    #         main_game_thread.start()
                    #     self.main_game_started.set()
                    # elif "board" in unpickled_json:
                    #     self.board = unpickled_json['board']
                    #     self.board_updated_event.set() 
                    #     with self.condition:
                    #         self.condition.notify()
                    # elif "round_over" in unpickled_json and "winner" in unpickled_json:
                    #     self.round_over_json = unpickled_json
                    #     self.round_over_event.set()
                    # elif 'play_again' in unpickled_json:
                    #     self.play_again_reply = unpickled_json['play_again']
                    #     self.play_again_reply_received.set()                        
                    #     with self.condition:
                    #         self.condition.notify()
                    # elif 'first_player' in unpickled_json:
                    #     self.first_player_for_next_round = unpickled_json['first_player']
                    #     self.first_player_received.set()
                    #     with self.condition:
                    #         self.condition.notify()
                    # elif 'timeout' in unpickled_json:
                    #     print(colored(unpickled_json['timeout'], "red", attrs=['bold']))
                    #     break                 
                except socket.error:
                    if not self.keyboard_interrupt:
                        print(self.color_error_msg_red(general_error_msg))
                        error = general_error_msg
                except Exception as e: # Catch EOFError and other exceptions
                    # NOTE: EOFError can also be raised when input() is interrupted with a Keyboard Interrupt
                    print(e)
                    if not self.keyboard_interrupt:
                        # print(self.color_error_msg_red(something_went_wrong_msg))
                        error = something_went_wrong_msg            

            pygame.display.flip()
            
    def color_error_msg_red(self, msg):
        return colored(msg, "red", attrs=['bold'])

    def validate_game_code(self, returned_input):
        validation = namedtuple("validation", "passed_validation, code_or_error")
        if returned_input.isalnum():
            return validation(True, returned_input)
        return validation(False, "Code can only contain letters and digits")
    
    def validate_ip_address(self, returned_input):
        pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        match = pattern.search(returned_input)
        validation = namedtuple("validation", "passed_validation, code_or_error")
        if match:
            return validation(True, returned_input)
        return validation(False, "That IP address is invalid")

    def terminate_program(self):
        self.keyboard_interrupt = True
        if self.client.client is not None:
            try:
                self.client.send_data({'DISCONNECT':self.client.DISCONNECT_MESSAGE, 'close_other_client':True})
            except socket.error:
                pass
            self.client.client.close()   
        error_msg = colored(f"Keyboard Interrupt: Program ended", "red", attrs=['bold'])        
        print(f"\n{error_msg}\n")           

if __name__ == "__main__":
    connect4 = Connect4()
    try:
        connect4.run_game()        
    except KeyboardInterrupt:
        connect4.terminate_program()