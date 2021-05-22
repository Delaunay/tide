
import math
from sdl2 import SDL_Rect


cdef int line_number(y: int, fh: int):
    return y // fh


cdef int col_number(x: int, fw: int):
    return x // fw


cpdef list select_line(entities: list, mouse_rect: SDL_Rect, fh: int, fw: int, offset_x: int, offset_y :int):
    """Does a text line select"""
    m = mouse_rect
    highlight_obj = list()

    cdef int line_s = line_number(m.y - offset_y, fh)
    cdef int line_e = line_number(m.y + m.h - offset_y, fh)

    cdef int col_s = col_number(m.x - offset_x, fw)
    cdef int col_e = col_number(m.x + m.w - offset_x, fw)

    cdef int x = 0
    cdef int y = 0
    cdef int w = 0
    cdef int h = 0
    cdef int line = 0
    cdef int col_min = 0
    cdef int col_max = 0

    for n in entities:
        n.selected = False
        p = n.pos(True)
        s = n.size()

        x = p[0]
        y = p[1]
        w = s[0]
        h = s[1]

        line = line_number(y - offset_y, fh)
        col_min = col_number(x - offset_x, fw)
        col_max = col_number(x + w - offset_x, fw)

        if line_s == line_e:
            if line_s == line and (col_s < col_min <= col_e or col_s < col_max <= col_e):
                highlight_obj.append(n)
                n.selected = True

        elif line_s == line and col_max >= col_s:
            highlight_obj.append(n)
            n.selected = True

        elif line_s < line < line_e:
            highlight_obj.append(n)
            n.selected = True

        elif line_e == line and col_max <= col_e:
            highlight_obj.append(n)
            n.selected = True

    return highlight_obj
