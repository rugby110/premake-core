#ifndef lprofilers_h
#define lprofilers_h

#include <stdint.h>

void init_profiler();
void hook_profiler(lua_State* L);
int  shutdown_profiler();

void malloc_callback (uintptr_t id, size_t nsize);
void realloc_callback(uintptr_t id, uintptr_t ptr, size_t nsize);
void free_callback   (uintptr_t id);

#define LUA_PROFILE_START()
#define LUA_PROFILE_END()

#endif

