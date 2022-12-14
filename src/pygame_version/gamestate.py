from enum import Enum

class GameState(Enum):
    CREDITS = -3
    NO_ACTION = -2
    QUIT = -1
    MENU = 0
    CREATE_GAME = 1
    JOIN_ANY_GAME = 2
    JOIN_GAME_WITH_CODE = 3
    JOIN_GAME_WITH_ENTERED_CODE = 4
    COPY = 5
    PASTE = 6
    CLEAR = 7
    CONTINUE = 8
    CONTINUE_WITH_DEFAULT_IP = 9
    HELP = 10
    SUBMIT_NAME = 11
    SELECT_RED_TOKEN = 12
    SELECT_YELLOW_TOKEN = 13