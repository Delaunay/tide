from tide.runtime.kiwi import *

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

    def astuple(self) -> Tuple[float, float]:
        return self.x, self.y

    @const
    def __eq__(self, other: 'Point const&') -> bool:
        return self.x == other.x and self.y == other.y

    @const
    def __sub__(self, other: 'Point const&') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)

    @const
    def __add__(self, other: 'Point const&') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)

    @const
    def __mul__(self, other: 'Point const&') -> 'Point':
        return Point(self.x * other.x, self.y * other.y)

    @const
    def dot(self, other: 'Point const&') -> float:
        return self.x * other.x + self.y * other.y

    def other(self):
        pass

    def dist(self) -> float:
        return math.sqrt(self.dot(self))

    @staticmethod
    def distance(a: 'Point const&', b: 'Point const&') -> float:
        v = a - b
        return v.dist()


zero: Point = Point(0, 0)

if __name__ == '__main__':
    p = Point(2.0, 1.0)
