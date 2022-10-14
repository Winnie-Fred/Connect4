import sys
import time
import socket
import pickle
import select
import re
import webbrowser
from cgitb import text
from collections import namedtuple

import pygame
import pygame.freetype
import pyperclip # type: ignore

from pygame.rect import Rect
from pygame.sprite import RenderUpdates

from basic_version.connect4 import Connect4Game

from core.player import Player
from core.level import Level
from core.board import Board

from pygame_version.client import Client
from pygame_version.choice import Choice
from pygame_version.gamestate import GameState
from pygame_version.ui_tools import UIElement, CopyButtonElement, DisabledOrEnabledBtn, TokenButton, InputBox, FadeOutText, create_text_to_draw

from termcolor import colored  # type: ignore

BLUE = (106, 159, 181)
RED = (204, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
MAX_GAME_CODE_LENGTH = 16
MAX_IP_ADDR_LENGTH = 15
MIN_IP_ADDR_LENGTH = 7
HELP_LINK = "https://github.com/Winnie-Fred/Connect4#finding-your-internal-ipv4-address"


class Connect4:
    POINTS_FOR_WINNING_ONE_ROUND = 10
    connect4game = Connect4Game()

    def __init__(self):
        self.client = Client()
        self.ID = None
        self.keyboard_interrupt = False
        self._reset_game()

    def _reset_game(self):
        self.ID = None
        self.you = ""
        self.opponent = Player(name='', marker='')
        self.player = Player(name='', marker='')
        self.your_turn = False
        self.level = Level()
        self._reset_for_new_round()

    def _reset_for_new_round(self):
        self.board = Board()
        self.play_again_reply = False
        self.first_player_for_next_round = Player(name='', marker='')
        self.round_over_json = {}
    
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

    def main_game_screen(self, screen, choice, ip, code=''):
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
        
        return self.play_game(screen, buttons, copy_btn, frames, choice=choice, ip=ip, code=code)

    def collect_ip_screen(self, screen, next_screen, **kwargs):
        default_ip = self.client.get_default_ip()
        submit_ip_btn = DisabledOrEnabledBtn(
            center_position=(350, 400),
            font_size=20,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            grayed_out_text_rgb=GRAY,
            text="Continue",
            action=GameState.CONTINUE,
        )

        help_btn = UIElement(
            center_position=(150, 400),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Help",
            action=GameState.HELP,
        )

        default_ip_btn = UIElement(
            center_position=(600, 400),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text=f"Continue with {default_ip}",
            action=GameState.CONTINUE_WITH_DEFAULT_IP,
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

        clear_btn = UIElement(
            center_position=(150, 200),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Clear",
            action=GameState.CLEAR,
        )

        input_box = InputBox(
            center_position = (350, 200),
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
            center_position=(350, 300))

        buttons = RenderUpdates(return_btn, paste_btn, clear_btn, default_ip_btn, help_btn)
        game_state_and_input = self.collect_input_loop(screen, buttons=buttons, submit_input_btn=submit_ip_btn, input_box=input_box, fade_out_text=fade_out_text, default_ip=default_ip)
        ui_action = game_state_and_input.game_state
        if ui_action != GameState.MENU:
            if 'choice' in kwargs:
                choice = kwargs['choice']
                return next_screen(screen, choice=choice, ip=game_state_and_input.input)
            return next_screen(screen, ip=game_state_and_input.input)
        return ui_action

    def collect_name_screen(self, screen, name=''):
        continue_btn = DisabledOrEnabledBtn(
            center_position=(400, 400),
            font_size=20,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            grayed_out_text_rgb=GRAY,
            text="Continue",
            action=GameState.SUBMIT_NAME,
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

        clear_btn = UIElement(
            center_position=(200, 200),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Clear",
            action=GameState.CLEAR,
        )

        input_box = InputBox(
            center_position = (400, 200),
            placeholder_text='Enter your name here',
            font_size=20,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            max_input_length=15,
            min_input_length=2,
        )

        fade_out_text = FadeOutText(
            font_size=15,
            text_rgb=RED,
            bg_rgb=BLUE,
            center_position=(400, 300))

        buttons = RenderUpdates(return_btn, paste_btn, clear_btn)
        return self.collect_input_loop(screen, buttons=buttons, submit_input_btn=continue_btn, input_box=input_box, fade_out_text=fade_out_text, name=name)       
    
    def choose_token_screen(self, screen, name=''):
        
        texts = []
        msg = "You go first"
        texts.append(create_text_to_draw(msg, 20, WHITE, BLUE, (400, 100)))
        msg = f"{name}, choose a token"
        texts.append(create_text_to_draw(msg, 25, WHITE, BLUE, (400, 150)))

        inactive_red_button_img = pygame.image.load('../../images/token buttons/inactive red token button.png').convert_alpha()
        mouse_over_red_button_img = pygame.image.load('../../images/token buttons/mouse over red token button.png').convert_alpha()
        inactive_yellow_button_img = pygame.image.load('../../images/token buttons/inactive yellow token button.png').convert_alpha()
        mouse_over_yellow_button_img = pygame.image.load('../../images/token buttons/mouse over yellow token button.png').convert_alpha()
        
        red_token_btn = TokenButton(
            button_img=inactive_red_button_img,
            mouse_over_btn_img=mouse_over_red_button_img,
            top_left_position=(150, 200),
            action=GameState.SELECT_RED_TOKEN,
        )

        yellow_token_btn = TokenButton(
            button_img=inactive_yellow_button_img,
            mouse_over_btn_img=mouse_over_yellow_button_img,
            top_left_position=(474, 200),
            action=GameState.SELECT_YELLOW_TOKEN,
        )
       
        return_btn = UIElement(
            center_position=(140, 570),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Return to main menu",
            action=GameState.MENU,
        )

        buttons = RenderUpdates(return_btn, red_token_btn, yellow_token_btn)
        return self.choose_token_loop(screen, buttons=buttons, texts=texts)

    def join_game_with_code_screen(self, screen, ip):
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

        clear_btn = UIElement(
            center_position=(200, 200),
            font_size=15,
            bg_rgb=BLUE,
            text_rgb=WHITE,
            text="Clear",
            action=GameState.CLEAR,
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

        buttons = RenderUpdates(return_btn, paste_btn, clear_btn)
        game_state_and_input = self.collect_input_loop(screen, buttons=buttons, submit_input_btn=join_game_btn, input_box=input_box, fade_out_text=fade_out_text)
        ui_action = game_state_and_input.game_state
        if ui_action != GameState.MENU:
            return self.main_game_screen(screen, choice=Choice.JOIN_GAME_WITH_CODE, ip=ip, code=game_state_and_input.input)
        return ui_action

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

    def collect_input_loop(self, screen, buttons, input_box, submit_input_btn, fade_out_text, default_ip=None, name=''):
        """ Collects input in loop until an action is return by a button in the
            buttons sprite renderer.
        """
        
        submit_btn_enabled = False
        error = ''
        returned_input = ''
        alpha = 255  # The current alpha value of the text surface.

        time_until_fade = 4000
        time_of_error = None   
        
        game_state_and_input = namedtuple("game_state_and_input", "game_state, input")

        while True:
            pasted_input = None
            clear = False
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
                    elif ui_action == GameState.CLEAR:
                        clear = True
                    elif ui_action == GameState.CONTINUE_WITH_DEFAULT_IP:
                        return game_state_and_input(ui_action, default_ip)
                    elif ui_action == GameState.HELP:
                        webbrowser.open(HELP_LINK, new=2)                        
                    else:                                              
                        return game_state_and_input(ui_action, '')

            buttons.draw(screen)

            ui_action = submit_input_btn.update(pygame.mouse.get_pos(), mouse_up, submit_btn_enabled)
            if ui_action != GameState.NO_ACTION:
                if ui_action == GameState.JOIN_GAME_WITH_ENTERED_CODE:
                    validation = self.validate_game_code(returned_input)
                elif ui_action == GameState.CONTINUE:
                    validation = self.validate_ip_address(returned_input)
                elif ui_action == GameState.SUBMIT_NAME:
                    validation = self.validate_name(returned_input, name)
                if validation is not None:
                    if validation.passed_validation:                        
                        return game_state_and_input(ui_action, validation.valid_input_or_error)
                    else:
                        # Validation failed
                        time_of_error = pygame.time.get_ticks()
                        error = validation.valid_input_or_error                    
                else:
                    return game_state_and_input(ui_action, '')
            submit_input_btn.draw(screen)

            after_input = input_box.update(pygame.mouse.get_pos(), mouse_up, key_down, pressed_key, backspace, pasted_input, clear)                   
            input_box.draw(screen)
            pygame.draw.rect(screen, after_input.color, (input_box.rect.left-3, input_box.rect.top-5, input_box.rect.w+10, input_box.rect.h*2), 2)
            submit_btn_enabled = after_input.submit_btn_enabled
            returned_input = after_input.returned_input

            pygame.display.flip()
    
    def choose_token_loop(self, screen, buttons, texts):
        """ Collects player's token in loop until an action is return by a button in the
            buttons sprite renderer.
        """
        
        while True:
            mouse_up = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_up = True                
                
            screen.fill(BLUE)

            for text in texts:
                text.draw(screen)

            for button in buttons:
                ui_action = button.update(pygame.mouse.get_pos(), mouse_up)
                if ui_action != GameState.NO_ACTION:
                    return ui_action

            buttons.draw(screen)
            pygame.display.flip()

    def play_game(self, screen, buttons, copy_btn, frames, choice, ip, code=''):

        def clear_screen():
            nonlocal loading_text, texts
            loading_text = ''
            texts = []

        last_update = pygame.time.get_ticks()
        last_click = None
        enabled = False
        time_until_enable = 3000
        time_of_status_msg_display = 1000
        animation_cooldown = 50
        frame = 0  

        game_started = False      

        errors = []
        loading_text = ''
        status_msg = ''

        general_error_msg = "Server closed the connection or other client may have disconnected"
        something_went_wrong_msg = "Oops! Something went wrong"
        code_to_display = None
        code_to_copy = ''
        unpickled_json = {}
        texts = []
        default_y_position_for_printing_error = 400

        full_msg = b''
        new_msg = True

        self._reset_game()
        text_and_error = self.client.connect_to_game(choice, ip, code)
        if text_and_error['error']:
            errors.append(text_and_error['text'])
        else: 
            print(text_and_error['text'])
            status_msg = text_and_error['text']
            status_msg_end_time = pygame.time.get_ticks() + time_of_status_msg_display


        while True:
            default_y_position_for_printing_error = 400
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

            
            for error in errors:
                if game_started:
                    pass
                else:
                    clear_screen()
                    error_text = create_text_to_draw(error, 15, RED, BLUE, (400, default_y_position_for_printing_error))
                    error_text.draw(screen)
                    default_y_position_for_printing_error += 50
                    

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


            if loading_text or status_msg:
                current_time = pygame.time.get_ticks()
                if current_time - last_update >= animation_cooldown:
                    frame += 1
                    last_update = current_time
                    if frame >= len(frames):
                        frame = 0

                screen.blit(frames[frame], (300, 50))
                if loading_text:            
                    loading_msg = create_text_to_draw(loading_text, 15, WHITE, BLUE, (400, 400))
                    loading_msg.draw(screen)
                    

            if not errors and not status_msg:
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
                            errors.append(error)
                            continue
                        except socket.error:
                            errors.append(general_error_msg)
                            continue
                        
                        if not msg: #  This breaks out of the loop when disconnect msg has been sent to server and/or client conn has been closed server-side
                            error_msg = ''
                            
                            if not self.keyboard_interrupt: 
                                # Connection was forcibly closed by server
                                error_msg = general_error_msg

                            errors.append(error_msg)
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
                                    texts.append(code_to_display)
                                    msg = "This is your special code. Send it to someone you wish to join this game."
                                    texts.append(create_text_to_draw(msg, 15, WHITE, BLUE, (400, 300)))
                                elif "no_games_found" in unpickled_json:
                                    # Result from unpickled_json is not used because it is too long and has to be broken 
                                    # to be printed on multiple lines                                    
                                    errors = ["No games exist with that code.", "Ask for an up-to-date code, "
                                                "try creating your own game ", "or try joining a different game"]
                                elif "game_full" in unpickled_json:
                                    errors.append(unpickled_json['game_full'])
                                elif "join_successful" in unpickled_json:
                                    status_msg = unpickled_json['join_successful']
                                    status_msg_end_time = pygame.time.get_ticks() + time_of_status_msg_display
                                    print(status_msg)
                                elif "id" in unpickled_json:
                                    clear_screen()
                                    self.ID = unpickled_json["id"]
                                    status_msg = "Both clients connected. Starting game"                                                                                               
                                    status_msg_end_time = pygame.time.get_ticks() + time_of_status_msg_display
                                    print(status_msg)
                                elif "other_client_disconnected" in unpickled_json:                       
                                    errors.append(unpickled_json['other_client_disconnected'])
                                elif "status" in unpickled_json:                                                                             
                                    loading_text = unpickled_json['status']                                
                                elif "waiting_for_name" in unpickled_json:
                                    loading_text = unpickled_json['waiting_for_name']                        
                                elif "get_first_player_name" in unpickled_json:                                                               
                                    loading_text = "Waiting for other player to enter their name"
                                    game_state_and_input = self.collect_name_screen(screen)
                                    if game_state_and_input.game_state == GameState.MENU:
                                        return game_state_and_input.game_state              
                                    self.you = game_state_and_input.input
                                    self.client.send_data({'you':self.you})
                                elif "opponent" in unpickled_json:                                                             
                                    self.opponent = unpickled_json['opponent']
                                    if not self.you:
                                        game_state_and_input = self.collect_name_screen(screen, name=self.opponent)
                                        if game_state_and_input.game_state == GameState.MENU:
                                            return game_state_and_input.game_state           
                                        self.you = game_state_and_input.input
                                        self.client.send_data({'you':self.you})                        
                                    print("You are up against: ", self.opponent)                        
                                    # Shuffling player names
                                    if not self.ID:
                                        first_player = self.connect4game._shuffle_players([self.you, self.opponent])
                                        self.client.send_data({'first':first_player})
                                    print("Randomly choosing who to go first . . .")                                                        
                                elif "first" in unpickled_json:
                                    first = unpickled_json['first'][0]                                                                        
                                    if first == self.you:
                                        msg = f"You go first"
                                        ui_action = self.choose_token_screen(screen, name=self.you)
                                        if ui_action == GameState.MENU:
                                            return ui_action
                                        if ui_action == GameState.SELECT_RED_TOKEN:
                                            colors = ('red', 'yellow')
                                        else:
                                            colors = ('yellow', 'red')
                                        self.client.send_data({'colors':colors})
                                    else:
                                        msg = f"{first} goes first"
                                        texts.append(create_text_to_draw(msg, 15, WHITE, BLUE, (400, 250)))
                                        loading_text = f"Waiting for {self.opponent} to choose their color"
                                    print(msg)
                                elif "colors" in unpickled_json:                                                                                     
                                    colors = unpickled_json['colors']                        
                                    if first == self.you:
                                        self.your_turn = True
                                        self.player = Player(self.you, colored('O', colors[0], attrs=['bold']))                            
                                    else:
                                        self.your_turn = False
                                        self.player = Player(self.you, colored('O', colors[1], attrs=['bold']))                        
                                    self.client.send_data({'opponent_player_object':self.player})
                                    print("Colors: ", colors)
                                    print("Player Object: ", self.player)
                                # elif "opponent_player_object" in unpickled_json:
                                #       game_started = True 
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

            if status_msg:
                current_time = pygame.time.get_ticks()
                if current_time < status_msg_end_time:
                    loading_msg = create_text_to_draw(status_msg, 15, WHITE, BLUE, (400, 400))
                    loading_msg.draw(screen)
                else:
                    status_msg = ''
            
            pygame.display.flip()
            
    def color_error_msg_red(self, msg):
        return colored(msg, "red", attrs=['bold'])

    def validate_game_code(self, returned_input):
        validation = namedtuple("validation", "passed_validation, valid_input_or_error")        
        if returned_input.isalnum():
            return validation(True, returned_input)
        return validation(False, "Code may only contain letters and digits")
    
    def validate_ip_address(self, returned_input):
        pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        match = pattern.search(returned_input)
        validation = namedtuple("validation", "passed_validation, valid_input_or_error")
        if returned_input.lower() == "localhost":
            return validation(True, returned_input)
        if match:
            return validation(True, returned_input)
        return validation(False, "That IP address is invalid")

    def validate_name(self, returned_input, name):
        validation = namedtuple("validation", "passed_validation, valid_input_or_error")
        if returned_input.isalnum():            
            if returned_input.lower() == name.lower():
                return validation(False, "A player already exists with that name. Choose another name")
            return validation(True, returned_input)
        return validation(False, "Your name may only contain letters and digits")

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
        pygame.quit()        

if __name__ == "__main__":
    connect4 = Connect4()
    try:
        connect4.run_game()        
    except KeyboardInterrupt:
        connect4.terminate_program()