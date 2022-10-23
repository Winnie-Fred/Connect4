from enum import Enum

class Choice(Enum):
    CREATE_GAME = 1
    JOIN_ANY_GAME = 2
    JOIN_GAME_WITH_CODE = 3

class TokenState(Enum):
    FALLING = 1
    JUST_LANDED = 2
    HAS_LANDED = 3