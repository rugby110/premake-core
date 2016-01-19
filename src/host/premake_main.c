/**
 * \file   premake_main.c
 * \brief  Program entry point.
 * \author Copyright (c) 2002-2013 Jason Perkins and the Premake project
 */

#include "premake.h"
#include "luaprofiler/luaprofiler.h"
#include <string.h>
#include <stdlib.h>

void setup_profiler(int argc, const char** argv)
{
	int i;
	for (i = 1; i < argc; ++i)
	{
		if (strcmp(argv[i], "/profile") == 0 || strcmp(argv[i], "--profile") == 0)
		{
			init_profiler();
			return;
		}
	}
}

static void* profile_alloc(void* ud, void* ptr, size_t osize, size_t nsize)
{
	(void)ud;
	(void)osize;

	void* result;

	// free.
	if (nsize == 0)
	{
		if (ptr != NULL)
		{
			free_callback((uintptr_t)ptr);
			free(ptr);
		}
		return NULL;
	}

	// malloc.
	if (ptr == NULL)
	{
		result = malloc(nsize);
		malloc_callback((uintptr_t)result, nsize);
		return result;
	}

	// realloc.
	result = realloc(ptr, nsize);
	realloc_callback((uintptr_t)result, (uintptr_t)ptr, nsize);
	return result;
}


int main(int argc, const char** argv)
{
	lua_State* L;
	int z;

	setup_profiler(argc, argv);

	L = lua_newstate(profile_alloc, NULL);
	luaL_openlibs(L);

	hook_profiler(L);

	z = premake_init(L);

	if (z == OKAY) {
		z = premake_execute(L, argc, argv, "src/_premake_main.lua");
	}

	shutdown_profiler();

	return z;
}
