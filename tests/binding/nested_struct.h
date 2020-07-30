
typedef int Uint32;
typedef struct {} SDL_PixelFormat;

typedef struct SDL_Surface
{
    Uint32 flags;               /**< Read-only */
    SDL_PixelFormat *format;    /**< Read-only */

    /** info for fast blit mapping to other surfaces */
    struct SDL_BlitMap *map;    /**< Private */

    /** Reference count -- used when freeing surface */
    int refcount;               /**< Read-mostly */
} SDL_Surface;
