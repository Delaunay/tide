from tide.ide.sdl import Window, DrawColor, SDL_Rect, SDL_Event
from tide.ide.sdl import SDL_WindowEvent, SDL_WINDOWEVENT, SDL_WINDOWEVENT_RESIZED
from tide.ide.sdl import SDL_MouseButtonEvent, SDL_MOUSEBUTTONUP, SDL_MOUSEBUTTONDOWN
from tide.ide.nodes import GNode


class Tide(Window):
    def __init__(self, handle):
        super(Tide, self).__init__(handle)
        self.module = None
        self.theme = None
        self.redraw = True
        self.root = None
        self.selected = None
        self.cursor = None

    def handle_window_event(self, wevent: SDL_WindowEvent):
        if wevent.event == SDL_WINDOWEVENT_RESIZED:
            self.redraw = True

    def handle_mouse_event(self, mbevent: SDL_MouseButtonEvent):
        x, y = mbevent.x, mbevent.y
        self.selected = self.root.collision(x, y)

        print(self.selected)

        self.cursor = (x, y)
        self.redraw = True

    def handle_event(self, event: SDL_Event):
        if event.type == SDL_WINDOWEVENT:
            self.handle_window_event(event.window)

        if event.type in (SDL_MOUSEBUTTONUP, SDL_MOUSEBUTTONDOWN):
            self.handle_mouse_event(event.button)

        if self.redraw:
            self.render()
            self.redraw = False

    def render(self):
        renderer = self.renderer
        renderer.clear()
        self.draw(renderer)
        renderer.present()

    def draw_click(self, renderer):
        with DrawColor(renderer, (0xFF, 0x00, 0x00, 0xFF)):
            renderer.fillrect(SDL_Rect(*self.cursor, 5, 5))

    def draw(self, renderer):
        fun = self.module.body[-1]
        self.root = GNode.new_from_ast(fun, theme=self.theme)

        self.root.position = (50, 50)
        self.root.render(renderer)

        if self.cursor:
            self.draw_click(renderer)
