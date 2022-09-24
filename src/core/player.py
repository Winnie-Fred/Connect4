class Player:
    def __init__(self, name, marker):
        self.name = name
        self.marker = marker
        self._points = 0

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, value):
        if type(value) == int:
            if (value % 10) == 0:
                self._points = value
            else:
                raise ValueError("Point must be a multiple of 10")
        else:
            raise ValueError("Point must be an integer")