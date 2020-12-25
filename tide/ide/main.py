import os
import sys
import ctypes
import signal

os.environ['PYSDL2_DLL_PATH'] = 'F:\KiwiLib'
from sdl2 import *
from sdl2.sdlttf import *

import OpenGL.GL as gl

import imgui
from imgui.integrations.sdl2 import SDL2Renderer

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
        return w, h

    def glyph_width(self):
        w, _ = self.size(' ')
        return w

    def glyph_height(self):
        _, h = self.size(' ')
        return h


class Renderer:
    def __init__(self, handle, imgui_impl, window):
        self.handle = handle
        self.imgui_impl = imgui_impl
        self.window = window

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

        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

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
        imgui.render()
        self.imgui_impl.render(imgui.get_draw_data())

        SDL_GL_SwapWindow(self.window)
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
    def __init__(self, handle, glhandle, comp):
        self.handle = handle
        self.gl_context = glhandle
        self._renderer = None
        self.imgui_impl = SDL2Renderer(handle)
        self.comp = comp

    def make_current(self):
        SDL_GL_MakeCurrent(self.handle, self.gl_context)

    @property
    def uid(self):
        return SDL_GetWindowID(self.handle)

    @property
    def surface(self):
        return SDL_GetWindowSurface(self.handle)

    def destroy(self):
        if self._renderer is not None:
            self._renderer.destroy()

        if self.gl_context is not None:
            SDL_GL_DeleteContext(self.gl_context)

        if self.handle is not None:
            SDL_DestroyWindow(self.handle)
            self.handle = None

    def update_surface(self):
        SDL_UpdateWindowSurface(self.handle)

    def handle_event(self, event):
        print(f'{event.type:x}')
        self.imgui_impl.process_event(event)

    @property
    def renderer(self):
        if self._renderer is None:
            render = SDL_CreateRenderer(self.handle, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
            self._renderer = Renderer(render, self.imgui_impl, self.handle)

        return self._renderer

    def tick(self):
        self.imgui_impl.process_inputs()
        self.renderer.clear()
        self.comp._render()
        self.renderer.present()

    def __del__(self):
        self.destroy()

    @property
    def title(self):
        return SDL_GetWindowTitle(self.handle)

    @title.setter
    def title(self, name):
        SDL_SetWindowTitle(name)


class WindowComponent:
    def __init__(self, name='', w=1280, h=720):
        self.name = name
        self.w = w
        self.h = h

    def _render(self):
        imgui.new_frame()
        self.draw()


    def function(self, fun):
        import tide.generators.nodes as nodes
        f: nodes.FunctionDef = fun

        imgui.begin_group()
        imgui.text('def');  imgui.same_line()
        imgui.input_text('nolavel', f.name); imgui.same_line()
        imgui.text('('); imgui.same_line()
        imgui.text(')'); imgui.same_line()
        imgui.text('->'); imgui.same_line()
        imgui.text(str(f.returns)); imgui.same_line()
        imgui.text(':')

        imgui.end_group()


    def draw(self):
        import ast
        module = ast.parse("""
        |def add(a: float, b: float) -> float:
        |    return a + b
        |""".replace('        |', ''))

        imgui.begin("Module", True)
        fun = module.body[0]
        self.function(fun)
        imgui.end()

        # imgui.begin("Custom window", True)
        # imgui.text("Bar")
        # imgui.text_colored("Eggs", 0.2, 1., 0.)
        # imgui.end()

        #
        # imgui.begin("Custom window", True)
        # imgui.text("Bar")
        # # imgui.begin_group()
        # # imgui.text('def')
        # # imgui.text('function')
        # # imgui.text('(')
        # # imgui.text('')
        # # imgui.end_group()
        # imgui.end()


class WindowManager:
    def __init__(self):
        self.windows = dict()
        self.event = SDL_Event()
        self.running = True
        self.current_window = None
        imgui.create_context()

    def __enter__(self):
        check(SDL_Init(SDL_INIT_EVERYTHING))

        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24)
        SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)
        SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
        SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 16)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 4)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE)

        # Anti-aliasing
        SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b"2")
        SDL_SetHint(SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1")
        SDL_SetHint(SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")
        SDL_GL_SetSwapInterval(1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for window in self.windows.values():
            window.destroy()
        SDL_Quit()

    def new_window(self, comp):
        handle = SDL_CreateWindow(
            comp.name.encode('utf-8'),
            SDL_WINDOWPOS_CENTERED,
            SDL_WINDOWPOS_CENTERED,
            comp.w,
            comp.h,
            SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE)

        gl_context = SDL_GL_CreateContext(handle)
        window = Window(handle, gl_context, comp)
        window.make_current()
        self.windows[window.uid] = window
        self.current_window = window
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

            if self.current_window:
                self.current_window.handle_event(self.event)

    def tick(self):
        for _, w in self.windows.items():
            w.tick()

    def run(self):
        while self.running:
            self.handle_event()
            self.tick()


class Text:
    def __init__(self, string, color, font):
        self.x = 0
        self.y = 0
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

    def render(self, renderer):
        rect = SDL_Rect(self.x, self.y, self.w, self.h)
        renderer.copy(self._texture(renderer), None, rect)


def main():
    with WindowManager() as manager:
        with ResourceManager() as resources:
            font = resources.font('DejaVuSansMono.ttf', 18)

            window = manager.new_window(WindowComponent())
            renderer = window.renderer
            renderer.color = (123, 123, 123, 0)

            # txt = Text("ABC", color=(0, 0, 0), font=font)
            # renderer.clear()
            # txt.render(renderer)
            # renderer.present()

            manager.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
