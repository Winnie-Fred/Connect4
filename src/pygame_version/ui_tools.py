from collections import namedtuple

import pygame
import pygame.mixer
from pygame.sprite import Sprite

from pygame_version.gamestate import GameState


pygame.mixer.init()

click_sound = pygame.mixer.Sound('../../audio/mouse-click-sound-effect.wav')

class TextToDIsplay:
    def __init__(self, image, center_position):
        self.image = image
        self.rect = self.image.get_rect(center=center_position)
        self.center_position = center_position

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class UIElement(Sprite):
    """ An user interface element that can be added to a surface """

    def __init__(self, center_position, text, font_size, bg_rgb, text_rgb, action=None):
        """
        Args:
            center_position - tuple (x, y)
            text - string of text to write
            font_size - int
            bg_rgb (background colour) - tuple (r, g, b)
            text_rgb (text colour) - tuple (r, g, b)
            action - the gamestate change associated with this button
        """
        self.mouse_over = False

        default_image = create_surface_with_text(
            text=text, font_size=font_size, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        highlighted_image = create_surface_with_text(
            text=text, font_size=font_size * 1.2, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        self.images = [default_image, highlighted_image]

        self.rects = [
            default_image.get_rect(center=center_position),
            highlighted_image.get_rect(center=center_position),
        ]

        self.action = action

        super().__init__()

    @property
    def image(self):
        return self.images[1] if self.mouse_over else self.images[0]

    @property
    def rect(self):
        return self.rects[1] if self.mouse_over else self.rects[0]

    def update(self, mouse_pos, mouse_up):
        """ Updates the "mouse_over" variable and returns the button's
            action value when clicked.
        """
        if self.rect.collidepoint(mouse_pos):
            self.mouse_over = True
            if mouse_up:
                click_sound.play()
                return self.action
        else:
            self.mouse_over = False
        return GameState.NO_ACTION

    def draw(self, surface):
        """ Draws element onto a surface """
        surface.blit(self.image, self.rect)

class TokenButton(Sprite):
    def __init__(self, button_img, mouse_over_btn_img, top_left_position, action):
        super().__init__()
        self.mouse_over = False
        self.default_img = button_img
        self.mouse_over_btn_img = mouse_over_btn_img
        self.top_left_position = top_left_position
        self.action = action

    @property
    def image(self):
        return self.mouse_over_btn_img if self.mouse_over else self.default_img

    @property
    def rect(self):
        return self.mouse_over_btn_img.get_rect(topleft=self.top_left_position) if self.mouse_over else self.default_img.get_rect(topleft=self.top_left_position)

    def update(self, mouse_pos, mouse_up):
        """ Updates the "mouse_over" variable and returns the button's
            action value when clicked.
        """
        if self.rect.collidepoint(mouse_pos):
            self.mouse_over = True
            if mouse_up:
                click_sound.play()
                return self.action
        else:
            self.mouse_over = False
        return GameState.NO_ACTION

    def draw(self, surface):
        """ Draws element onto a surface """
        surface.blit(self.image, self.rect)


class DisabledOrEnabledBtn(UIElement):
    def __init__(self, center_position, text, font_size, bg_rgb, text_rgb, grayed_out_text_rgb, action=None):
        """
        Args:
            center_position - tuple (x, y)
            text - string of text to write
            font_size - int
            bg_rgb (background colour) - tuple (r, g, b)
            text_rgb (text colour) - tuple (r, g, b)
            grayed_out_text_rgb (colour to make text appear grayed out) - tuple (r, g, b)
            action - the gamestate change associated with this button
        """
        super().__init__(center_position, text, font_size, bg_rgb, text_rgb, action)
        self.enabled = False
        unclickable_btn_image = create_surface_with_text(
            text=text, font_size=font_size, text_rgb=grayed_out_text_rgb, bg_rgb=bg_rgb)
        self.images.append(unclickable_btn_image)
        self.rects.append(unclickable_btn_image.get_rect(center=center_position),)

    @property
    def image(self):
        if not self.enabled:
            return self.images[2]
        if self.mouse_over:
            return self.images[1]
        if not self.mouse_over: 
            return self.images[0]

    @property
    def rect(self):
        if not self.enabled:
            return self.rects[2]
        if self.mouse_over:
            return self.rects[1]
        if not self.mouse_over: 
            return self.rects[0]

    def update(self, mouse_pos, mouse_up, enabled, enter_key_pressed):
        """ Updates the "mouse_over" and "enabled" variables and returns the button's
            action value when clicked.
        """
        if enter_key_pressed:
            return self.action
        if enabled:
            self.enabled = True
            if self.rect.collidepoint(mouse_pos):
                self.mouse_over = True
                if mouse_up:
                    click_sound.play()
                    return self.action
            else:
                self.mouse_over = False
        else:
            self.enabled = False
        return GameState.NO_ACTION

class InputBox(Sprite):
    def __init__(self, center_position, placeholder_text, font_size, bg_rgb, text_rgb, max_input_length, min_input_length):
        """
        Args:
            center_position - tuple (x, y)
            placeholder_text - string of text to use as placeholder
            font_size - int
            bg_rgb (background colour) - tuple (r, g, b)
            text_rgb (text colour) - tuple (r, g, b)
            max_input_length - int
        """
        super().__init__()
        self.active = False
        self.center_position = center_position
        self.max_input_length = max_input_length
        self.min_input_length = min_input_length
        self.user_input = ''
        self.color_active = pygame.Color('lightskyblue3')
        self.color_inactive = (128, 128, 128)
        self.color = self.color_inactive
        self.placeholder_text = placeholder_text
        self.font_size = font_size
        self.bg_rgb = bg_rgb
        self.text_rgb = text_rgb
        self.text_surface = create_surface_with_text(
            text=self.placeholder_text, font_size=self.font_size, text_rgb=self.text_rgb, bg_rgb=self.bg_rgb
        )
        self.old_input = self.text_surface
        self.active = False
        self.key_down = False       
        

    @property
    def image(self):
        return self.text_surface if self.key_down else self.old_input
            
    @property
    def rect(self):
        return self.text_surface.get_rect(center=self.center_position) if self.key_down else self.old_input.get_rect(center=self.center_position)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self, mouse_pos, mouse_up, key_down, pressed_key, backspace, pasted_input, clear):
        """ Updates the "key_down" variable and returns "after_input" that contains the "color" 
            of the input border, the input itself and returns whether the btn to submit the 
            input is "enabled" depending on whether or not the min_input_length has been reached.
        """
        self.old_input = self.text_surface

        if clear:
            self.user_input = ''
            self.text_surface = create_surface_with_text(
                text=self.user_input, font_size=self.font_size, text_rgb=self.text_rgb, bg_rgb=self.bg_rgb
            )

        if pasted_input is not None:
            pasted_input = pasted_input.strip()
            if len(pasted_input) > self.max_input_length:
                self.user_input = pasted_input[:self.max_input_length]
            else:
                self.user_input = pasted_input
            self.text_surface = create_surface_with_text(
                text=self.user_input, font_size=self.font_size, text_rgb=self.text_rgb, bg_rgb=self.bg_rgb
            )

        if mouse_up:
            if self.rect.collidepoint(mouse_pos):
                self.color = self.color_active
                self.active = True
            else:
                self.active = False
                self.color = self.color_inactive

        if key_down:
            self.key_down = True
            if self.active:
                if backspace:
                    self.user_input = self.user_input[:-1]
                else:
                    if len(self.user_input) < self.max_input_length:
                        self.user_input += pressed_key
                self.text_surface = create_surface_with_text(
                    text=self.user_input, font_size=self.font_size, text_rgb=self.text_rgb, bg_rgb=self.bg_rgb
                )
        else:
            self.key_down = False

        if not self.user_input:
            self.text_surface = create_surface_with_text(
                text=self.placeholder_text, font_size=self.font_size, text_rgb=self.text_rgb, bg_rgb=self.bg_rgb
            )
        after_input =  namedtuple("after_input", "color, submit_btn_enabled, returned_input")
        submit_btn_enabled = len(self.user_input)>=self.min_input_length
        return after_input(self.color, submit_btn_enabled, self.user_input.strip())

class CopyButtonElement(UIElement):
    def __init__(self, center_position, text, font_size, bg_rgb, text_rgb, text_after_mouse_up_event, action=None):
        super().__init__(center_position, text, font_size, bg_rgb, text_rgb, action)
        clicked_image = create_surface_with_text(
            text=text_after_mouse_up_event, font_size=font_size * 1.2, text_rgb=text_rgb, bg_rgb=bg_rgb)
        self.images.append(clicked_image)
        self.rects.append(clicked_image.get_rect(center=center_position),)
        self.mouse_up = False

    @property
    def image(self):
        if self.mouse_up:
            return self.images[2]
        if self.mouse_over:
            return self.images[1]
        if not self.mouse_over: 
            return self.images[0]

    @property
    def rect(self):
        if self.mouse_up:
            return self.rects[2]
        if self.mouse_over:
            return self.rects[1]
        if not self.mouse_over: 
            return self.rects[0]

    def update(self, mouse_pos, mouse_up, enabled: bool):
        """ Updates the mouse_over and mouse_up variables and returns the button's
            action value when clicked.
        """
        if enabled:
            if self.rect.collidepoint(mouse_pos):
                self.mouse_over = True
            else:
                self.mouse_over = False
            if mouse_up:
                click_sound.play()
                self.mouse_up = True
                return self.action
            self.mouse_up = False
        return GameState.NO_ACTION

class FadeOutText(Sprite):
    def __init__(self, font_size, text_rgb, bg_rgb, center_position, text=''):
        self.font_size = font_size
        self.text_rgb = text_rgb
        self.bg_rgb = bg_rgb
        self.center_position = center_position
        self.text = text
        self.original_surf = create_surface_with_text(
            text=self.text, font_size=self.font_size, text_rgb=self.text_rgb, bg_rgb=self.bg_rgb
        )
        self.txt_surf = self.original_surf.copy()
        self.original_surf_copy = self.original_surf.copy()
        self.alpha = 255
        self.alpha_changed = False

    @property
    def image(self):
        return self.txt_surf if self.alpha_changed else self.original_surf_copy
            
    @property
    def rect(self):
        return self.txt_surf.get_rect(center=self.center_position) if self.alpha_changed else self.original_surf_copy.get_rect(center=self.center_position)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self, alpha):
        self.original_surf = create_surface_with_text(
            text=self.text, font_size=self.font_size, text_rgb=self.text_rgb, bg_rgb=self.bg_rgb
        )
        self.txt_surf = self.original_surf.copy()  # Don't modify the original text surf.
        self.alpha = alpha
        self.alpha_changed = (self.alpha == alpha)
        if self.alpha_changed:
            # Make text surface transparent with the alpha value and blit onto the screen
            self.txt_surf.set_alpha(self.alpha)
        else:
            self.original_surf_copy = self.original_surf

        return alpha # Return 0 or non-zero value corresponding to True or False


class ErrorNotifier(Sprite):
    def __init__(self, error: str, font_size: int, font_color: tuple):
        super().__init__()
        self.error_occured = False
        self.image = pygame.image.load('../../images/error notifier.png').convert_alpha()       
        font = pygame.freetype.SysFont("Courier", font_size, bold=True)
        text_surface, _ = font.render(text=error, fgcolor=font_color)
        self.image.blit(text_surface, text_surface.get_rect(center=self.image.get_rect().center))
        self.y_pos = 107
        self.static_position = (1313, self.y_pos)
        self.outside_position = (1620, self.y_pos)        
        self.speed = 7        
        self.max_vibrations = 6
        self.reset()
        
    def reset(self):
        self.current_position = self.outside_position       
        self.move_left = True
        self.incoming = False
        self.vibrating = False
        self.static = False
        self.outgoing = False
        self.vibrate_count = 0
        self.time_since_static = None

    def vibrate(self):
        return (self.static_position[0]-5, self.y_pos) if self.move_left else (self.static_position[0]+5, self.y_pos)

    @property
    def rect(self):
        return self.current_position

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self, error_occured):
        if error_occured:
            self.error_occured = True
            self.reset()
            self.incoming = True

        if self.error_occured:
            if self.incoming:
                self.current_position = self.static_position                
                self.vibrating = True
                self.incoming = False
                
            elif self.vibrating:
                self.current_position = self.vibrate()
                self.move_left = not self.move_left
                self.vibrate_count += 1
                if self.vibrate_count == self.max_vibrations:
                    self.vibrating = False
                    self.static = True
                    self.time_since_static = pygame.time.get_ticks()
                    self.current_position = self.static_position

            elif self.static:
                current_time = pygame.time.get_ticks()
                if self.time_since_static + 3000 <= current_time:
                    self.static = False
                    self.outgoing = True

            elif self.outgoing:
                self.current_position = (min(self.current_position[0] + self.speed, self.outside_position[0]), self.y_pos)


class StatusNotifier(Sprite):
    def __init__(self, opponent: str, font_size: int, font_color: tuple):
        super().__init__()
        self.y_pos = 107
        self.static_position = (1313, self.y_pos)
        self.outside_position = (1620, self.y_pos)
        self.speed = 7

        self.notifier_image = pygame.image.load('../../images/status notifier.png').convert_alpha()
               
        font = pygame.freetype.SysFont("Courier", font_size, bold=True)
        texts = ['Waiting for', opponent, 'to play']
        
        text_x_center_pos = 152
        text_y_pos = 28
        for text in texts:
            text_surface, _ = font.render(text=text, fgcolor=font_color)  
            self.notifier_image.blit(text_surface, text_surface.get_rect(center=(text_x_center_pos, text_y_pos)))
            text_y_pos += 28       

        self.loading_frames = []
        for i in range(6):
            self.loading_frames.append(pygame.image.load(f'../../images/notifier loading frames/notifier loading frame ({i}).png').convert_alpha())
        self.notifier_image_copy = self.notifier_image.copy()
        self.animation_cooldown = 1000        
        self.reset()
        
    def reset(self):
        self.last_animation_update = pygame.time.get_ticks()
        self.current_frame = 0
        self.current_position = self.outside_position        
        self.incoming = False
        self.static = False

    @property
    def image(self):       
        return self.notifier_image

    @property
    def rect(self):
        return self.current_position

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self, waiting_has_begun: bool, opponent_turn: bool):
        if waiting_has_begun:
            self.reset()
            self.incoming = True

        if opponent_turn:
            if self.incoming:
                self.current_position = (max(self.current_position[0]-self.speed, self.static_position[0]), self.y_pos)
                if self.current_position == self.static_position:
                    self.static = True
                    self.incoming = False

            elif self.static:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_animation_update >= self.animation_cooldown:
                    self.current_frame += 1
                    self.last_animation_update = current_time
                    if self.current_frame >= len(self.loading_frames):
                        self.current_frame = 0
                
                frame = self.loading_frames[self.current_frame]
                self.notifier_image = self.notifier_image_copy.copy()
                self.notifier_image.blit(frame, (91, 94))               
        else:
            if self.current_position != self.outside_position:
                self.current_position = (min(self.current_position[0] + self.speed, self.outside_position[0]), self.y_pos)


class ScoreBoard(Sprite):
    def __init__(self, token_color: str, font_color: tuple, name_font_size: int, player_name: str = "You"):
        super().__init__()
        self.scoreboard_image = pygame.image.load(f'../../images/player with {token_color} token scoreboard.png')
        self.font_color = font_color
        self.points = 0
        self.player_name = player_name

        font = pygame.freetype.SysFont("Courier", name_font_size, bold=True)
        text_surface, _ = font.render(text=f' {self.player_name} ', fgcolor=self.font_color, bgcolor=(72,161,120))  
        self.scoreboard_image.blit(text_surface, text_surface.get_rect(center=(110, 48)))
        self.original_scoreboard_image_copy = self.scoreboard_image.copy()

        self.font = pygame.freetype.SysFont("Courier", 30, bold=True)
        text_surface, _ = self.font.render(text=str(self.points), fgcolor=self.font_color)  
        self.scoreboard_image.blit(text_surface, text_surface.get_rect(center=(114, 73)))


    @property
    def image(self):
        return self.scoreboard_image

    @property
    def rect(self):
        return (69, 733) if self.player_name == 'You' else (1304, 733)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self, player_points:int):
        if self.points != player_points:
            self.points = player_points
            self.scoreboard_image = self.original_scoreboard_image_copy.copy()
            text_surface, _ = self.font.render(text=str(self.points), fgcolor=self.font_color)  
            self.scoreboard_image.blit(text_surface, text_surface.get_rect(center=(114, 73)))


class CurrentRoundBoard(Sprite):
    def __init__(self, font_color: tuple, current_round_font_size: int):
        super().__init__()
        self.current_round_board_image = pygame.image.load(f'../../images/current round board.png')
        self.font_color = font_color
        self.current_round = 1

        font = pygame.freetype.SysFont("Courier", 24, bold=True)
        text_surface, _ = font.render(text='Round', fgcolor=(128, 128, 128))  
        self.current_round_board_image.blit(text_surface, text_surface.get_rect(center=(152, 73)))
        self.original_current_round_board_image_copy = self.current_round_board_image.copy()

        self.font = pygame.freetype.SysFont("Courier", current_round_font_size, bold=True)
        text_surface, _ = self.font.render(text=str(self.current_round), fgcolor=self.font_color)  
        self.current_round_board_image.blit(text_surface, text_surface.get_rect(center=(152, 102)))


    @property
    def image(self):
        return self.current_round_board_image

    @property
    def rect(self):
        return (1230, 405)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self, current_round):
        if self.current_round != current_round:
            self.current_round = current_round
            self.current_round_board_image = self.original_current_round_board_image_copy.copy()
            text_surface, _ = self.font.render(text=str(self.current_round), fgcolor=self.font_color)  
            self.current_round_board_image.blit(text_surface, text_surface.get_rect(center=(152, 102)))


def create_surface_with_text(text, font_size, text_rgb, bg_rgb):
    """ Returns surface with text written on """
    font = pygame.freetype.SysFont("Courier", font_size, bold=True)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=bg_rgb)
    return surface.convert_alpha()

def create_text_to_draw(text, font_size, text_rgb, bg_rgb, center_position):
    """ Returns text to draw """
    font = pygame.freetype.SysFont("Courier", font_size, bold=True)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=bg_rgb)
    return TextToDIsplay(image=surface, center_position=center_position)

