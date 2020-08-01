
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

extern int SDL_LockSurface(SDL_Surface * surface);

extern int SDL_SetSurfaceRLE(SDL_Surface * surface, int flag);

extern int SDL_SetColorKey(SDL_Surface * surface, int flag, Uint32 key);

extern int SDL_GetColorKey(SDL_Surface * surface,  Uint32 * key);

extern void SDL_GetClipRect(SDL_Surface * surface, SDL_Rect * rect);

extern SDL_bool SDL_SetClipRect(SDL_Surface * surface, const SDL_Rect * rect);
