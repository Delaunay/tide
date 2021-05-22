import pyximport
pyximport.install()

from tide.ide.sdl import WindowManager, ResourceManager
from tide.ide.nodes import Theme
from tide.ide.source import Tide


def main(module):
    with WindowManager() as manager:
        with ResourceManager() as resources:
            font = resources.font('dejavu/DejaVuSansMono.ttf', 18)
            t = Theme(font)

            window = manager.new_window(Tide)
            window.theme = t
            window.module = module

            # window = manager.new_window(Tide)
            # window.theme = t
            # window.module = module

            manager.run()

    return 0


if __name__ == "__main__":
    import ast
    import sys

    module: ast.Module = ast.parse("""
from dataclasses import dataclass
import time

def add(a: int, b: int = 0, *arg, d=2, c=1, **kwargs) -> int:
    return a + b

""")

    sys.exit(main(module))
    pass

