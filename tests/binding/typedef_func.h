#ifndef SDL_events_h_
#define SDL_events_h_

#ifdef __cplusplus
extern "C" {
#endif

typedef struct SDL_Event {} SDL_Event;

typedef int (* SDL_EventFilter) (void *userdata, SDL_Event * event);

void SDL_SetEventFilter(SDL_EventFilter filter,  void *userdata);

int SDL_GetEventFilter(SDL_EventFilter * filter, void **userdata);

#ifdef __cplusplus
}
#endif
#endif