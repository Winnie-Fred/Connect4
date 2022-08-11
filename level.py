class Level:
    def __init__(self):
        self._current_level = 1

    @property
    def current_level(self):
        return self._current_level

    @current_level.setter
    def current_level(self, value):
        if type(value) == int:
            if value - self._current_level == 1:
                self._current_level = value
            else:
                raise ValueError("Levels can only increase in steps of 1")
        else:
            raise ValueError("Level must be an integer")
