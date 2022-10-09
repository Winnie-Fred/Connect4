from collections import namedtuple

import pygame
from pygame.sprite import Sprite

from pygame_version.gamestate import GameState

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
                return self.action
        else:
            self.mouse_over = False
        return GameState.NO_ACTION

    def draw(self, surface):
        """ Draws element onto a surface """
        surface.blit(self.image, self.rect)

class ClickableOrUnclickableBtn(UIElement):
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
        self.clickable = False
        unclickable_btn_image = create_surface_with_text(
            text=text, font_size=font_size, text_rgb=grayed_out_text_rgb, bg_rgb=bg_rgb)
        self.images.append(unclickable_btn_image)
        self.rects.append(unclickable_btn_image.get_rect(center=center_position),)

    @property
    def image(self):
        if not self.clickable:
            return self.images[2]
        if self.mouse_over:
            return self.images[1]
        if not self.mouse_over: 
            return self.images[0]

    @property
    def rect(self):
        if not self.clickable:
            return self.rects[2]
        if self.mouse_over:
            return self.rects[1]
        if not self.mouse_over: 
            return self.rects[0]

    def update(self, mouse_pos, mouse_up, clickable):
        """ Updates the "mouse_over" and "clickable" variables and returns the button's
            action value when clicked.
        """
        if clickable:
            self.clickable = True
            if self.rect.collidepoint(mouse_pos):
                self.mouse_over = True
                if mouse_up:
                    return self.action
            else:
                self.mouse_over = False
        else:
            self.clickable = False
        return GameState.NO_ACTION

class InputBox(Sprite):
    def __init__(self, center_position, placeholder_text, font_size, bg_rgb, text_rgb, max_input_length):
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
        self.input_box = self.text_surface.get_rect(center=center_position)
        self.old_input_box = self.old_input.get_rect(center=center_position)
        self.active = False
        self.key_down = False       
        

    @property
    def image(self):
        return self.text_surface if self.key_down else self.old_input
            
    @property
    def rect(self):
        return self.input_box if self.key_down else self.old_input_box

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def update(self, mouse_pos, mouse_up, key_down, pressed_key, backspace, pasted_input):
        """ Updates the "key_down" variable and returns "after_input" that contains the "color" 
            of the input border, the input itself and returns whether the btn to submit the 
            input is "clickable" depending on whether or not the max_input_length has been reached.
        """
        if pasted_input is not None:
            pasted_input = pasted_input.strip()
            if len(pasted_input) > self.max_input_length:
                self.user_input = pasted_input[:self.max_input_length]
            else:
                self.user_input = pasted_input
            self.text_surface = create_surface_with_text(
                text=self.user_input, font_size=self.font_size, text_rgb=self.text_rgb, bg_rgb=self.bg_rgb
            )

        self.old_input = self.text_surface
        self.old_input_box = self.old_input.get_rect(center=self.center_position)
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
            self.input_box = self.text_surface.get_rect(center=self.center_position)
        after_input =  namedtuple("after_input", "color, submit_btn_clickable, returned_input")
        submit_btn_clickable = len(self.user_input)==self.max_input_length
        return after_input(self.color, submit_btn_clickable, self.user_input)

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
                self.mouse_up = True
                return self.action
            self.mouse_up = False
        return GameState.NO_ACTION


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
