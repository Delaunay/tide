from tide.generators.visitor import NodeVisitor
from tide.generators.nodes import *

from tide.ide.main import Text


class Theme:
    def __init__(self, font):
        self.font = font


class TreeRender(NodeVisitor):
    def __init__(self, renderer, pos, theme):
        self.pos = pos
        self.box = dict()
        self.theme = theme
        self.renderer = renderer

    def render(self, *txt):
        Text()

    def visit_FunctionDef(self, node: FunctionDef, depth, method=False, islambda=False, **kwargs):
        # Cache rendering
        elements = dict()
        if hasattr(node, '__render_cache__'):
            elements = getattr(node, '__render_cache__')
        else:
            setattr(node, '__render_cache__', elements)
        # <<<

        Text('def ', (0, 125, 0, 0), self.theme.font).render(self.renderer)
        Text(node.name, (125, 0, 0, 0), self.theme.font).render(self.renderer)
        Text('(', (125, 0, 0, 0), self.theme.font).render(self.renderer)

        for arg in node.args:
            Text(arg.arg, (125, 0, 0, 0), self.theme.font).render(self.renderer)

        Text(')', (125, 0, 0, 0), self.theme.font).render(self.renderer)
        Text(' -> ', (125, 0, 0, 0), self.theme.font).render(self.renderer)
        Text(node.returns, (125, 0, 0, 0), self.theme.font).render(self.renderer)
        Text(':\n', (125, 0, 0, 0), self.theme.font).render(self.renderer)
