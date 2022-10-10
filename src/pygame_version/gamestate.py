from enum import Enum

class GameState(Enum):
    NO_ACTION = -2
    QUIT = -1
    MENU = 0
    CREATE_GAME = 1
    JOIN_ANY_GAME = 2
    JOIN_GAME_WITH_CODE = 3
    JOIN_GAME_WITH_ENTERED_CODE = 4
    COPY = 5
    PASTE = 6
    CONTINUE = 7