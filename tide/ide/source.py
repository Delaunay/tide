from tide.ide.sdl import Window, DrawColor, SDL_Rect, SDL_Event
from tide.ide.sdl import SDL_WindowEvent, SDL_WINDOWEVENT, SDL_WINDOWEVENT_RESIZED
from tide.ide.sdl import SDL_MouseButtonEvent, SDL_MOUSEBUTTONUP, SDL_MOUSEBUTTONDOWN, SDL_PRESSED, SDL_RELEASED
from tide.ide.sdl import SDL_MouseMotionEvent, SDL_MOUSEMOTION
from tide.ide.nodes import GNode


class Tide(Window):
    def __init__(self, handle):
        super(Tide, self).__init__(handle)
        self.module = None
        self.theme = None
        self.redraw = True
        self.root = None
        self.selected = None
        self.click = None
        self.cursor = None

        self.mouse_start = None
        self.mouse_end = None
        self.highlight_obj = set()

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

        self.click = (x, y)
        self.cursor = (x, y)
        self.redraw = True

        if mbevent.state == SDL_PRESSED:
            self.highlight_obj = set()
            self.mouse_start = (x, y)

        if mbevent.state == SDL_RELEASED:
            self.root.overlap(self.mouse_rect, select=self.highlight_obj)
            self.redraw = True
            self.mouse_end = None
            self.mouse_start = None

        if self.selected:
            print(self.selected.charoffset(*self.cursor), self.selected.char(*self.cursor))

    def handle_mouse_motion_event(self, mmevent: SDL_MouseMotionEvent):
        self.mouse_end = mmevent.x, mmevent.y

    def handle_event(self, event: SDL_Event):
        if event.type == SDL_WINDOWEVENT:
            self.handle_window_event(event.window)

        if event.type in (SDL_MOUSEBUTTONUP, SDL_MOUSEBUTTONDOWN):
            self.handle_mouse_button_event(event.button)

        if event.type == SDL_MOUSEMOTION:
            self.handle_mouse_motion_event(event.motion)

        if self.redraw:
            self.render()
            self.redraw = False

    def highlights(self, renderer):
        for n in self.highlight_obj:
            x, y = n.pos(False)
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

            x = (x // w) * w
            y = (y // h) * h
            renderer.fillrect(SDL_Rect(x, y + 2, 1, h - 4))

    def draw_selection(self, renderer):
        if self.mouse_start and self.mouse_end:
            with DrawColor(renderer, (0x00, 0xF8, 0x00, 0x68)):
                renderer.fillrect(self.mouse_rect)

    def draw(self, renderer):
        fun = self.module.body[-1]
        self.root = GNode.new_from_ast(fun, theme=self.theme)

        self.root.position = (0, 0)
        self.root.render(renderer)

        if self.click:
            self.draw_click(renderer)

        if self.cursor:
            self.draw_cursor(renderer)
