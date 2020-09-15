import sys
sys.path.append('../../output')

from sdl2gen.sdl2 import *


import sys
import ctypes


def main():
    SDL_Init(0x00000020)
    window = SDL_CreateWindow(b"Hello World",
                              0, 0,
                              592, 460, SDL_WINDOW_SHOWN)
    windowsurface = SDL_GetWindowSurface(window)

    image = SDL_LoadBMP(b"exampleimage.bmp")
    SDL_BlitSurface(image, None, windowsurface, None)

    SDL_UpdateWindowSurface(window)
    SDL_FreeSurface(image)

    running = True
    event = SDL_Event()
    while running:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
                break

    SDL_DestroyWindow(window)
    SDL_Quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())