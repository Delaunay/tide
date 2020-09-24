import sys
sys.path.append('../../output')

import sdl2gen.sdl2 as sdl2

import sys
import ctypes


def main():
    sdl2.init(sdl2.SDL_INIT_VIDEO)

    window = sdl2.Window.create(
        b"Hello World",
      sdl2.SDL_WINDOWPOS_UNDEFINED, sdl2.SDL_WINDOWPOS_UNDEFINED,
      592, 460, sdl2.WindowFlags.SHOWN)

    windowsurface = window.get_surface()

    # image = SDL_LoadBMP(b"exampleimage.bmp")
    # SDL_BlitSurface(image, None, windowsurface, None)

    # SDL_UpdateWindowSurface(window)
    # SDL_FreeSurface(image)

    running = True
    event = sdl2.Event()
    while running:
        while event.poll() != 0:
            if event.type == sdl2.EventType.QUIT:
                running = False
                break

        window.update_surface()

    window.destroy()
    sdl2.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
