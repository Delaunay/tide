import myproject.math as math

def add(a: float, b: float) -> float:
    return math.add(a, b)

import myproject.math


class Point:
   def __init__(self, x: float, y: float):
       self.x: float = x
       self.y: float = y

   def sum(self) -> float:
       return self.x + self.y

   def __del__(self):
       return

   def other(self):
       pass

   @staticmethod
   def dist(a: Point, b: Point) -> float:
       v = a - b
       return sqrt(v * v)
