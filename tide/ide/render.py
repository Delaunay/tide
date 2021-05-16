from tide.generators.visitor import NodeVisitor
from tide.generators.nodes import *

from tide.ide.main import Text


class Theme:
    def __init__(self, font):
        self.font = font
        white = (255, 255, 255)
        black = (0, 0, 0)
        self.space_count = 4
        self.colors = {
            'keyword': (0, 125, 0, 0),
            'paren': (125, 0, 0, 0),
            'bracket': (125, 0, 0, 0),
            'default': (125, 0, 0, 0),
            'background': white,
            'function': black,
            'arg_name': black,
            'arg_type': black,
            'arg_value':black,
            'colon': black,
            'equal_assign': black,
            'arrow': black,
        }

    def text(self, str, type):
        return Text(str, self.colors[type], self.font)

    def keyword(self, str):
        return self.text(str, 'keyword')

    def normal(self, str):
        return self.text(str, 'default')

    def indent_size(self):
        return self.font.glyph_width() * self.space_count


class GNode:
    def __init__(self, parent=None, theme=None):
        self.theme = theme
        self.position = (0, 0)
        self.parent = parent

    def pos(self, relative=True):
        if relative or self.parent is None:
            return self.position

        x, y = self.position
        xx, yy = self.parent.pos(False)
        return x + xx, y + yy

    def size(self):
        raise NotImplementedError()

    def render(self, renderer):
        raise NotImplementedError()

    @staticmethod
    def from_ast(node):
        pass


class GText(GNode):
    CACHE = dict()

    def __init__(self, str, type='default', parent=None, theme=None):
        super(GText, self).__init__(parent, theme)
        self.text = self._new_string(str, type)

    def _new_string(self, str, type):
        val = GText.CACHE.get((str, type))
        if val is None:
            val = self.theme.text(str, type)
            GText.CACHE[(str, type)] = val
        return val

    def size(self):
        return self.text.size()

    def render(self, renderer):
        self.text.render(self.pos(False), renderer)


class GComposedNode(GNode):
    def __init__(self, parent=None, theme=None):
        super(GComposedNode, self).__init__(parent, theme)
        self.nodes = []
        self.cursor = (0, 0)
        self.w = 0
        self.h = 0

    def size(self):
        return self.w, self.h

    def text(self, str, type='default'):
        self.append(GText(str, type, parent=self, theme=self.theme))

    def append(self, node: GNode):
        node.position = self.cursor
        self.nodes.append(node)
        x, y = self.cursor
        w, _ = node.size()
        self.cursor = x + w, y
        self.w = max(self.w, self.cursor[0])

    def indent(self):
        x, y = self.cursor
        self.cursor = x + self.theme.indent_size(), y

    def deindent(self):
        x, y = self.cursor
        self.cursor = x - self.theme.indent_size(), y

    def newline(self):
        px, py = self.pos()
        x, y = self.cursor
        self.cursor = px, y + self.theme.font.glyph_height()
        self.w = max(self.w, self.cursor[0])
        self.h = max(self.h, self.cursor[1])

    def render(self, renderer):
        for n in self.nodes:
            n.render(renderer)


class GName(GText):
    def __init__(self, node: Name, type='default', parent=None, theme=None):
        super(GName, self).__init__(node.id, type=type, parent=parent, theme=theme)


class GFunctionDef(GComposedNode):
    def __init__(self, node: FunctionDef, parent=None, theme=None):
        super(GFunctionDef, self).__init__(parent, theme)
        self.text('def ', 'keyword')
        self.text(node.name, 'function')
        self.text('(', 'paren')

        self.text(')', 'paren')
        self.text(' -> ')
        self.text(node.returns.id, 'arg_type')
        self.text(':')
        self.newline()
        self.indent()
        self.text('pass', 'keyword')



        # self.nodes = [
        #     self.text('def', 'keyword'),
        #     self.text(node.name),
        #     self.text('(', 'paren'),
        # ]
        #
        # for arg in node.args.args:
        #     self.nodes.append(self.text(arg.arg, 'arg_name'))
        #     self.nodes.append(self.text(': ', 'colon'))
        #     self.nodes.append(self.text(arg.annotation, 'arg_type'))
        #     self.nodes.append(self.text(' = ', 'equal_assign'))
        #     # default_value = node.args.defaults[arg.arg]
        #     self.nodes.append(self.text(arg.arg, 'arg_value'))
        #
        # self.nodes.append(self.text(' -> ', 'arrow'))
        # self.nodes.append(self.text(node.returns, 'arg_type'))
        # self.nodes.append(self.text(': ', 'colon'))
        # self.nodes.append(GNewline())


class TreeRender(NodeVisitor):
    def __init__(self, renderer, pos, theme):
        self.pos = pos
        self.box = dict()
        self.theme = theme
        self.renderer = renderer

    # def render(self, *txt):
    #     Text()
    #
    # def visit_FunctionDef(self, node: FunctionDef, depth, method=False, islambda=False, **kwargs):
    #     # Cache rendering
    #     elements = dict()
    #     if hasattr(node, '__render_cache__'):
    #         elements = getattr(node, '__render_cache__')
    #     else:
    #         setattr(node, '__render_cache__', elements)
    #     # <<<
    #
    #     Text('def ', (0, 125, 0, 0), self.theme.font).render(self.renderer)
    #     Text(node.name, (125, 0, 0, 0), self.theme.font).render(self.renderer)
    #     Text('(', (125, 0, 0, 0), self.theme.font).render(self.renderer)
    #
    #     for arg in node.args:
    #         Text(arg.arg, (125, 0, 0, 0), self.theme.font).render(self.renderer)
    #
    #     Text(')', (125, 0, 0, 0), self.theme.font).render(self.renderer)
    #     Text(' -> ', (125, 0, 0, 0), self.theme.font).render(self.renderer)
    #     Text(node.returns, (125, 0, 0, 0), self.theme.font).render(self.renderer)
    #     Text(':\n', (125, 0, 0, 0), self.theme.font).render(self.renderer)


if __name__ == '__main__':
    import ast

    data: ast.Module = ast.parse("""
from dataclasses import dataclass
import time

def add(a: int, b: int = 0, *arg, d=2, c=1, **kwargs) -> int:
    return a + b
    """)

    for elem in data.body:
        print(elem)
