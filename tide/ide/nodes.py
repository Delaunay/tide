from tide.generators.nodes import *
from tide.ide.sdl import Text, DrawColor, SDL_Rect


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
            'constant': black,
            'background': white,
            'function': black,
            'arg_name': black,
            'arg_type': black,
            'arg_value': black,
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

    def __repr__(self):
        return f'<GNode>'

    def size(self):
        raise NotImplementedError()

    def render(self, renderer):
        raise NotImplementedError()

    def from_ast(self, node):
        return GNode.new_from_ast(node, parent=self.parent, theme=self.theme)

    def collision(self, x, y, recurse=True):
        raise NotImplementedError

    @staticmethod
    def new_from_ast(node, parent=None, theme=None):
        name = node.__class__.__name__

        ctor = DISPATCH.get(name)
        if ctor:
            return ctor(node, parent=parent, theme=theme)

        print(name)


class GText(GNode):
    CACHE = dict()

    def __init__(self, str, type='default', parent=None, theme=None):
        super(GText, self).__init__(parent=parent, theme=theme)
        self.text: Text = self._new_string(str, type)

    def _new_string(self, str, type):
        val = GText.CACHE.get((str, type))
        if val is None:
            val = self.theme.text(str, type)
            GText.CACHE[(str, type)] = val
        return val

    def __repr__(self):
        return f'<GText text={self.text.string}>'

    def string(self):
        return self.text.string

    def size(self):
        return self.text.size()

    def render(self, renderer):
        self.text.render(self.pos(False), renderer)

    def collision(self, tx, ty, recurse=True):
        x, y = self.pos(False)
        w, h = self.size()

        if x < tx < x + w and y < ty < y + h:
            return self

        return None


class GName(GText):
    def __init__(self, node: Name, type='default', parent=None, theme=None):
        super(GName, self).__init__(node.id, type=type, parent=parent, theme=theme)
        self.node = node

    def __repr__(self):
        return f'<GName text={self.text.string}>'


class GConstant(GText):
    def __init__(self, value: Constant, parent=None, theme=None):
        value_str = f'{value.value}'
        value_type = 'constant'
        self.node = value
        super(GConstant, self).__init__(value_str, type=value_type, parent=parent, theme=theme)

    def __repr__(self):
        return f'<GConstant text={self.text.string}>'


class GComposedNode(GNode):
    def __init__(self, parent=None, theme=None):
        super(GComposedNode, self).__init__(parent=parent, theme=theme)
        self.nodes = []
        self.cursor = (0, 0)
        self.w = 0
        self.h = self.theme.font.glyph_height()
        self.background_color = (0x7D, 0x7D, 0x7D, 0x3F)

    def size(self):
        return self.w, self.h

    def text(self, str, type='default'):
        self.append(GText(str, type, parent=self, theme=self.theme))

    def append(self, node: GNode):
        if node is None:
            return

        node.parent = self
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
        x, y = self.pos(False)
        w, h = self.size()

        with DrawColor(renderer, self.background_color):
            rect = SDL_Rect(x - 1, y - 1, w + 1, h + 1)
            renderer.fillrect(rect)

        for n in self.nodes:
            n.render(renderer)

    def is_contained(self, tx, ty):
        x, y = self.pos(False)
        w, h = self.size()

        if x < tx < x + w and y < ty < y + h:
            return True

        return False

    def collision(self, x, y, recurse=True):
        if not self.is_contained(x, y):
            return None

        if not recurse or len(self.nodes) == 0:
            return self

        for n in self.nodes:
            r = n.collision(x, y, recurse=True)

            if r is not None:
                return r

        # Should never happen
        return None

    def __repr__(self):
        return f'<GComposed>'


class GReturn(GComposedNode):
    def __init__(self, node: Return, parent=None, theme=None):
        super(GReturn, self).__init__(parent, theme)
        self.text('return ', 'keyword')
        self.append(self.from_ast(node.value))
        self.node =node

    def __repr__(self):
        return f'<GReturn>'


class GFunctionDef(GComposedNode):
    def __init__(self, node: FunctionDef, parent=None, theme=None):
        super(GFunctionDef, self).__init__(parent, theme)
        self.node = node
        self.text('def ', 'keyword')
        self.text(node.name, 'function')
        self.text('(', 'paren')
        self.args(node.args)
        self.text(')', 'paren')
        self.text(' -> ')
        self.append(self.from_ast(node.returns))
        self.text(':')
        self.newline()
        self.indent()
        for expr in node.body:
            self.append(self.from_ast(expr))
            self.newline()
        self.deindent()

    def generate_defaults(self, kwonlyargs, kw_defaults):
        defaults = [None for _ in kwonlyargs]
        n = len(kwonlyargs) - len(kw_defaults)
        for i, v in enumerate(kw_defaults):
            defaults[n + i] = v
        return defaults

    def args(self, args):
        need_comma = False
        defaults = self.generate_defaults(args.args, args.defaults)
        for i, (arg, value) in enumerate(zip(args.args, defaults)):
            self.text(arg.arg)

            if arg.annotation:
                self.text(': ')
                self.append(self.from_ast(arg.annotation))

            if value:
                self.text(' = ')
                self.append(self.from_ast(value))

            if i + 1 < len(args.args):
                self.text(', ')

            need_comma = True

        if args.vararg:
            if need_comma:
                self.text(', ')

            self.text('*')
            self.text(args.vararg.arg)

        if len(args.kwonlyargs) > 0:
            self.text(', ')

        kw_defaults = self.generate_defaults(args.kwonlyargs, args.kw_defaults)
        for i, (kw, value) in enumerate(zip(args.kwonlyargs, kw_defaults)):
            self.text(kw.arg)

            if kw.annotation:
                self.text(': ')
                self.append(self.from_ast(kw.annotation))

            if value:
                self.text(' = ')
                self.append(self.from_ast(value))

            if i + 1 < len(args.kwonlyargs):
                self.text(', ')

            need_comma = True

        if args.kwarg:
            if need_comma:
                self.text(', ')

            self.text('**')
            self.text(args.kwarg.arg)


class GBinOp(GComposedNode):
    BINARY_OP = {
        'Add': ' + ',
        'Mult': ' * ',
        'Sub': ' - ',
        'MatMult': ' @ ',
        'Div': ' / ',
        'Mod': ' % ',
        'Pow': ' ** '
    }

    def __init__(self, node: BinOp, parent=None, theme=None):
        super(GBinOp, self).__init__(parent, theme)
        self.node = node

        op = GBinOp.BINARY_OP[type(node.op).__name__]
        self.append(self.from_ast(node.left))
        self.text(op)
        self.append(self.from_ast(node.right))

    def render(self, renderer):
        super(GBinOp, self).render(renderer)


DISPATCH = {
    'Name': GName,
    'Constant': GConstant,
    'FunctionDef': GFunctionDef,
    'Return': GReturn,
    'BinOp': GBinOp
}


if __name__ == '__main__':
    import ast

    data: ast.Module = ast.parse("""
from dataclasses import dataclass
import time

def add(a: int, /, b: int=3, *arg, c=2, d=1, **kwargs) -> int:
    return a + b
    """)

    for elem in data.body:
        print(elem)
