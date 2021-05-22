import math
import time
from typing import List

from tide.ide.sdl import Window, DrawColor, SDL_Rect, SDL_Event
from tide.ide.sdl import SDL_WindowEvent, SDL_WINDOWEVENT, SDL_WINDOWEVENT_RESIZED
from tide.ide.sdl import SDL_MouseButtonEvent, SDL_MOUSEBUTTONUP, SDL_MOUSEBUTTONDOWN, SDL_PRESSED, SDL_RELEASED
from tide.ide.sdl import SDL_MouseMotionEvent, SDL_MOUSEMOTION
from tide.ide.sdl import SDL_KeyboardEvent, SDL_KEYDOWN, SDL_KEYUP, KMOD_SHIFT, KMOD_CAPS, SDLK_BACKSPACE
from tide.ide.nodes import GNode, GText, GNewline, GIndent, GDeindent
from tide.ide.speedup import select_line


class TextEdit:
    def __init__(self, node: GText, offset):
        self.node = node
        self.i = offset
        self.string = [s for s in node.string]

    def update(self):
        new = ''.join(self.string)
        self.node.string = new

    def insert(self, c):
        self.string.insert(self.i, c)
        self.update()
        self.i += 1

    def remove(self):
        self.string.pop(self.i - 1)
        self.update()
        self.i -= 1

    def key_event(self, kevent: SDL_KeyboardEvent):
        if kevent.state == SDL_PRESSED:
            return False

        keysym = kevent.keysym

        if keysym.sym == SDLK_BACKSPACE and self.i > 0:
            self.remove()
            return True

        if not (0 <= keysym.sym <= 0x10ffff):
            return False

        key = chr(keysym.sym).lower()
        mod = keysym.mod

        if key.isalnum():
            if mod & KMOD_SHIFT | mod & KMOD_CAPS:
                key = key.upper()

            self.insert(key)

        return True


class Tide(Window):
    def __init__(self, handle):
        super(Tide, self).__init__(handle)
        self._module = None
        self.theme = None
        self.redraw = True
        self.root = None
        self.selected = None
        self.click = None
        self.cursor = None

        self.mouse_start = None
        self.mouse_end = None
        self.highlight_obj = set()
        self.editor = None
        self.last_redraw = 0
        self.entities: List[GNode] = []

    @property
    def module(self):
        return self._module

    @module.setter
    def module(self, mod):
        self._module = mod
        fun = self._module.body[-1]
        self.root = GNode.new_from_ast(fun, theme=self.theme)
        self.root.track(self.entities)

        for n in self.entities:
            print(type(n))

    @property
    def mouse_rect(self):
        if not self.mouse_start or not self.mouse_end:
            return SDL_Rect(0, 0, 0, 0)

        sx, sy = self.mouse_start
        x, y = self.mouse_end

        def swap(x, y):
            return y, x

        if sx > x:
            x, sx = swap(x, sx)

        if sy > y:
            y, sy = swap(y, sy)

        return SDL_Rect(sx, sy, x - sx, y - sy)

    def handle_window_event(self, wevent: SDL_WindowEvent):
        if wevent.event == SDL_WINDOWEVENT_RESIZED:
            self.redraw = True

    def handle_mouse_button_event(self, mbevent: SDL_MouseButtonEvent):
        x, y = mbevent.x, mbevent.y
        self.selected = self.root.collision(x, y)

        if self.selected:
            self.editor = TextEdit(self.selected, self.selected.charoffset(x, y))
        else:
            self.editor = None

        self.click = (x, y)
        self.cursor = (x, y)
        self.redraw = True

        if mbevent.state == SDL_PRESSED:
            self.highlight_obj = set()
            self.mouse_start = (x, y)

        if mbevent.state == SDL_RELEASED:
            #
            self.select_line()
            self.redraw = True
            self.mouse_end = None
            self.mouse_start = None

        if self.selected:
            print(self.selected.charoffset(*self.cursor), self.selected.char(*self.cursor))

    def handle_mouse_motion_event(self, mmevent: SDL_MouseMotionEvent):
        self.mouse_end = mmevent.x, mmevent.y
        self.redraw = True

    def handle_event(self, event: SDL_Event):
        if event.type == SDL_WINDOWEVENT:
            self.handle_window_event(event.window)

        if event.type in (SDL_MOUSEBUTTONUP, SDL_MOUSEBUTTONDOWN):
            self.handle_mouse_button_event(event.button)

        if event.type == SDL_MOUSEMOTION:
            self.handle_mouse_motion_event(event.motion)

        if event.type in (SDL_KEYDOWN, SDL_KEYUP) and self.editor:
            self.redraw = self.editor.key_event(event.key)

        # SDL_MOUSEWHEEL

        # SDL_TEXTEDITING/SDL_TEXTINPUT

        # limit the FPS to ~30 so we do not overload the cpu on event
        # we do not see since rendering is costly (full ast traversal)
        if self.redraw and time.time() - self.last_redraw > 0.03:
            self.render()
            self.last_redraw = time.time()
            self.redraw = False

    def highlights(self, renderer):
        for n in self.highlight_obj:
            x, y = n.pos(True)
            w, h = n.size()

            with DrawColor(renderer, self.theme.select_color):
                rect = SDL_Rect(x, y, w, h)
                renderer.fillrect(rect)

    def render(self):
        renderer = self.renderer
        renderer.clear()
        self.draw_selection(renderer)
        self.highlights(renderer)
        self.draw(renderer)
        renderer.present()

    def draw_click(self, renderer):
        with DrawColor(renderer, (0xFF, 0x00, 0x00, 0xFF)):
            renderer.fillrect(SDL_Rect(*self.click, 2, 2))

    def draw_cursor(self, renderer):
        with DrawColor(renderer, (0x00, 0x00, 0x00, 0xFF)):
            x, y = self.click
            h = self.theme.font.lineskip
            w = self.theme.font.glyph_width()

            x = ((x - self.root.position[0]) // w) * w + self.root.position[0]
            y = ((y - self.root.position[1]) // h) * h + self.root.position[1]
            renderer.fillrect(SDL_Rect(x, y + 2, 1, h - 4))

    def draw_selection(self, renderer):
        if self.mouse_start and self.mouse_end:
            with DrawColor(renderer, self.theme.select_color):
                renderer.fillrect(self.mouse_rect)

    def select_2d(self):
        """Does a 2D intersection select"""
        self.root.overlap(self.mouse_rect, select=self.highlight_obj)

    def select_line(self):
        """Does a text line select"""
        fh = self.theme.font.lineskip
        fw = self.theme.font.glyph_width()

        x, y = self.root.position
        result = select_line(self.entities, self.mouse_rect, fh, fw, x, y)

        self.highlight_obj = result

    def draw_module(self, renderer):
        cursor = self.root.position

        print('s')
        for n in self.entities:
            s = ''
            if hasattr(n, 'string'):
                s = n.string

            if isinstance(n, GNewline):
                x = 0
                _, y = cursor
                if n.parent:
                    x, _ = n.parent.position
                cursor = x + self.root.position[1], y + self.theme.font.lineskip
                continue

            if isinstance(n, GIndent):
                x, y = cursor
                cursor = x + self.theme.indent_size(), y
                continue

            if isinstance(n, GDeindent):
                x, y = cursor
                cursor = x - self.theme.indent_size(), y
                continue

            x, y = cursor
            n.position = x, y
            w, h = n.size()

            ws = self.theme.font.glyph_width()
            print(f'{type(n).__name__:>15} n={w / ws} p=({x:3d} x {y:3d}) s=({w:3d} x {h:3d}) - {s}')

            self.show_bounds(renderer, x, y, w, h)
            n.render(renderer)
            cursor = x + w, y
        print('done')

    def show_bounds(self, renderer, x, y, w, h):
        with DrawColor(renderer, (0x00, 0xFF, 0x00, 0xFF)):
            renderer.fillrect(SDL_Rect(x, y + h, w - 5, 2))

        with DrawColor(renderer, (0xFF, 0x00, 0xFF, 0xFF)):
            renderer.fillrect(SDL_Rect(x + w - 5, y + h, 5, 2))

    def draw(self, renderer):
        self.root.position = (50, 50)
        # self.root.render(renderer)
        self.draw_module(renderer)

        if self.click:
            self.draw_click(renderer)

        if self.cursor:
            self.draw_cursor(renderer)

#         str = """
#
#
#
# from dataclasses import dataclass
# import time
#
# def add(a: int, /, b: int=3, *arg, c=2, d=1, **kwargs) -> int:
#     return a + b
# """
#         # GText(str, theme=self.theme).render(renderer)
