from enum import Enum

class GameState(Enum):
    NO_ACTION = -2
    QUIT = -1
    MENU = 0
    CREATE_GAME = 1
    JOIN_ANY_GAME = 2
    JOIN_GAME_WITH_CODE = 3
    COPY = 4
    PASTE = 5
    CONTINUE = 6
    CONTINUE_WITH_DEFAULT_IP = 7
    HELP = 8