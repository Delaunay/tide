import myproject.math as math

def add(a: float, b: float) -> float:
    return math.add(a, b)

import myproject.math


@struct(novirtual=1)
class Point:
    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y

    def sum(self) -> float:
        return self.x + self.y

    def __del__(self):
        return

    def __eq__(self, other: 'Point const&') -> bool:
        return self.x == other.x and self.y == other.y

    def other(self):
        pass

    @staticmethod
    def dist(a: 'Point', b: 'Point') -> float:
        v = a - b
        return math.sqrt(v * v)


if __name__ == '__main__':
    p = Point(2.0, 1.0)
