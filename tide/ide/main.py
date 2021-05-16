import os
import sys
import ctypes
import signal
from sdl2 import *
from sdl2.sdlttf import *

from typing import *
from tide.log import info, debug


def show_trace(signum, frame):
    import traceback
    print(signum, frame)


# signal.signal(signal.SIGINT, show_trace)
# signal.signal(signal.SIGTERM, show_trace)
# signal.signal(signal.SIGSEGV, show_trace)
# signal.signal(signal.SIGABRT, show_trace)


class SDLError(Exception):
    pass


def check(val=None):
    if val is None:
        msg = SDL_GetError().decode('utf-8')
        if msg:
            SDL_ClearError()
            raise SDLError(msg)

    if isinstance(val, int) and val != 0:
        msg = SDL_GetError().decode('utf-8')
        SDL_ClearError()
        raise SDLError(f'Error {val}: {msg}')

    SDL_ClearError()
    return val


class Font:
    def __init__(self, handle):
        self.handle = handle

    def destroy(self):
        if self.handle is not None:
            # free = False
            # if not TTF_WasInit():
            #     TTF_Init()
            #     print('init')
            #     free = True

            # this cause a segmentation fault
            # TTF_CloseFont(self.handle)
            self.handle = None

            # if free:
            #     TTF_Quit()

    def __del__(self):
        self.destroy()

    @property
    def style(self):
        return TTF_GetFontStyle(self.handle)

    @property
    def outline(self):
        return TTF_GetFontOutline(self.handle)

    @property
    def hint(self):
        return TTF_GetFontHinting(self.handle)

    @property
    def kerning(self):
        return TTF_GetFontKerning(self.handle)

    def render(self, text, color):
        surface = TTF_RenderUTF8_Blended(self.handle, text.encode('utf-8'), color)
        return surface

    def size(self, text):
        w, h = c_int(), c_int()
        TTF_SizeUTF8(self.handle, text.encode('utf-8'), w, h)
        return w.value, h.value

    def glyph_width(self):
        w, _ = self.size(' ')
        return w

    def glyph_height(self):
        _, h = self.size(' ')
        return h


class Renderer:
    def __init__(self, handle):
        self.handle = handle

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self.handle is not None:
            SDL_DestroyRenderer(self.handle)
            self.handle = None

    @property
    def color(self):
        color = (ctypes.c_ubyte(), ctypes.c_ubyte(), ctypes.c_ubyte(), ctypes.c_ubyte())
        check(SDL_GetRenderDrawColor(self.handle, *color))
        return color

    @color.setter
    def color(self, colour):
        SDL_SetRenderDrawColor(self.handle, *colour)

    def clear(self, colour: Tuple[int, int, int, int] = (0xFF, 0xFF, 0xFF, 0xFF)):
        with DrawColor(self, colour):
            check(SDL_RenderClear(self.handle))

    def copy(self, texture: SDL_Texture, src_rect: Optional[SDL_Rect], dst_rect: SDL_Rect):
        check(SDL_RenderCopy(self.handle, texture, src_rect, dst_rect))

    def drawline(self, p1: Tuple[int, int], p2: Tuple[int, int]):
        check(SDL_RenderDrawLine(self.handle, *p1, *p2))

    def drawlines(self, points: List[Tuple[int, int]]):
        check(SDL_RenderDrawLines(self.handle, points, len(points)))

    def drawrect(self, rectangle: Optional[SDL_Rect]):
        check(SDL_RenderDrawRect(self.handle, rectangle))

    def present(self):
        # __main__.SDLError: Surface doesn't have a colorkey
        SDL_RenderPresent(self.handle)
        SDL_ClearError()

    def create_texture(self, surface):
        return SDL_CreateTextureFromSurface(self.handle, surface)


class DrawColor:
    def __init__(self, render: Renderer, color):
        self.render = render
        self.color = color
        self.old = None

    def __enter__(self):
        self.old = self.render.color
        self.render.color = self.color
        return self.render

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.render.color = self.old


class ResourceManager:
    def __init__(self):
        self.fonts = dict()

    def __enter__(self):
        check(TTF_Init())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for font in self.fonts.values():
            font.destroy()

        TTF_Quit()

    def font(self, name, size):
        if (name, size) in self.fonts:
            return self.fonts[(name, size)]

        path = os.path.dirname(__file__)
        path = os.path.join(path, '..', '..', 'assets', 'fonts')

        f = TTF_OpenFont(os.path.join(path, name).encode('utf-8'), size)
        self.fonts[(name, size)] = Font(f)
        return Font(f)


class Window:
    def __init__(self, handle):
        self.handle = handle
        self._renderer = None

    @property
    def uid(self):
        return SDL_GetWindowID(self.handle)

    @property
    def surface(self):
        return SDL_GetWindowSurface(self.handle)

    def destroy(self):
        if self._renderer is not None:
            self._renderer.destroy()

        if self.handle is not None:
            SDL_DestroyWindow(self.handle)
            self.handle = None

    def update_surface(self):
        SDL_UpdateWindowSurface(self.handle)

    def handle_event(self, event):
        print(event)

    @property
    def renderer(self):
        if self._renderer is None:
            render = SDL_CreateRenderer(self.handle, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
            self._renderer = Renderer(render)

        return self._renderer

    def __del__(self):
        self.destroy()

    @property
    def title(self):
        return SDL_GetWindowTitle(self.handle)

    @title.setter
    def title(self, name):
        SDL_SetWindowTitle(name)


class WindowManager:
    def __init__(self):
        self.windows = dict()
        self.event = SDL_Event()
        self.running = True
        self.current_window = None

    def __enter__(self):
        check(SDL_Init(SDL_INIT_EVERYTHING))

        # Anti-aliasing
        SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b"2")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for window in self.windows.values():
            window.destroy()
        SDL_Quit()

    def new_window(self, w=1280, h=720, *args, **kwargs):
        handle = SDL_CreateWindow(
            b"Hello World",
            SDL_WINDOWPOS_UNDEFINED,
            SDL_WINDOWPOS_UNDEFINED,
            w,
            h,
            SDL_WINDOW_SHOWN)

        window = Window(handle)
        self.windows[window.uid] = window
        return window

    def handle_event(self):
        while SDL_PollEvent(ctypes.byref(self.event)) != 0:
            if self.event.type == SDL_WINDOWEVENT:
                wuid = self.event.window.windowID
                self.current_window = self.windows.get(wuid)

                if self.current_window is not None:
                    self.current_window.handle_event(self.event)

                    if self.event.window.event == SDL_WINDOWEVENT_CLOSE:
                        self.current_window.destroy()
                        self.current_window = None
                        self.windows.pop(wuid, None)

            elif self.event.type == SDL_QUIT:
                self.running = False
                break

    def run(self):
        while self.running:
            self.handle_event()


class Text:
    def __init__(self, string, color, font):
        self.w = 100
        self.h = 100

        self.color = SDL_Color(*color)
        self.font = font

        self.surface = None
        self.texture = None
        self.string = string

    @property
    def string(self):
        return self._string

    @string.setter
    def string(self, string):
        self.destroy()
        self.surface = self.font.render(string, self.color)
        self._string = string
        self.w, self.h = self.font.size(self._string)

    def size(self):
        return self.w, self.h

    def _delete_surface(self):
        if self.surface is not None:
            SDL_FreeSurface(self.surface)
            self.surface = None

    def _delete_texture(self):
        if self.texture is not None:
            SDL_DestroyTexture(self.texture)
            self.texture = None

    def destroy(self):
        self._delete_surface()
        self._delete_texture()

    def __del__(self):
        self.destroy()

    def _texture(self, renderer):
        if self.texture is None:
            self.texture = check(renderer.create_texture(self.surface))
        return self.texture

    def render(self, pos, renderer):
        x, y = pos
        rect = SDL_Rect(x, y, self.w, self.h)
        renderer.copy(self._texture(renderer), None, rect)


def main(module):
    from tide.ide.render import TreeRender, Theme, GText, GFunctionDef

    with WindowManager() as manager:
        with ResourceManager() as resources:

            font = resources.font('DejaVuSansMono.ttf', 18)

            window = manager.new_window()

            theme = Theme(font)

            renderer = window.renderer

            renderer.clear()

            fun = module.body[-1]

            txt = GFunctionDef(fun, theme=theme)
            print(txt.pos(True), txt.pos(False))
            print(txt.size())
            txt.render(renderer)
            # r = TreeRender(renderer, (0, 0), theme)
            # renderer.color = (123, 123, 123, 0)
            # txt = Text("ABC", color=(0, 0, 0), font=font)
            #
            # txt.render(renderer)
            renderer.present()

            manager.run()

    return 0


if __name__ == "__main__":
    import ast

    module: ast.Module = ast.parse("""
from dataclasses import dataclass
import time

def add(a: int, b: int = 0, *arg, d=2, c=1, **kwargs) -> int:
    return a + b

""")

    sys.exit(main(module))
    pass

