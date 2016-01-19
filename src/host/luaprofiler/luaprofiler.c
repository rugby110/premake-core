/*
** LuaProfiler
** Copyright Kepler Project 2005-2007 (http://www.keplerproject.org/luaprofiler)
** $Id: lua50_profiler.c,v 1.16 2008-05-20 21:16:36 mascarenhas Exp $
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _MSC_VER
#   include <intrin.h>
#else
static unsigned long long __rdtsc(void)
{
	unsigned int hi, lo;
	__asm__ __volatile__("rdtsc" : "=a"(lo), "=d"(hi));
	return (unsigned long long)lo | ((unsigned long long)hi << 32);
}
#endif

#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
#include "hashset.h"
#include "luaprofiler.h"
#include "../premake.h"

static FILE* profile_file;
static hashset_t string_table;

static unsigned long define_string(const char* str)
{
	unsigned long id;
	size_t len = str ? strlen(str) : 0;
	if (len <= 0)
		return 0;

	id = do_hash(str, 5381);
	if (hashset_add(string_table, id) == 1)
	{
		fprintf(profile_file, "declstr,%x,%s\n", (unsigned int)id, str);
		fflush(profile_file);
	}

	return id;
}

static void enter_hook(lua_State *L, lua_Debug *ar, int tail)
{
	unsigned long name, source;
	size_t             func;
	unsigned long long tick;

	lua_getinfo(L, "nS", ar);
	name = define_string(ar->name);
	source = define_string(ar->source);
	func = *(size_t*)ar->i_ci;
	tick = __rdtsc();

	fprintf(profile_file, "enter,%x,%x,%x,%d,%llu\n",
		(unsigned int)func,
		(unsigned int)name,
		(unsigned int)source,
		tail, tick);
	fflush(profile_file);
}

static void leave_hook()
{
	unsigned long long tick = __rdtsc();
	fprintf(profile_file, "leave,%llu\n", tick);
	fflush(profile_file);
}

static void callhook(lua_State *L, lua_Debug *ar)
{
	switch (ar->event)
	{
	case LUA_HOOKCALL:
		enter_hook(L, ar, 0);
		break;
	case LUA_HOOKTAILCALL:
		enter_hook(L, ar, 1);
		break;
	case LUA_HOOKRET:
		leave_hook();
		break;
	}
}

void malloc_callback(uintptr_t id, size_t nsize)
{
	if (!profile_file)
		return;

	fprintf(profile_file, "malloc,%llu,%llu\n",
		(long long unsigned int)id,
		(long long unsigned int)nsize);
	fflush(profile_file);
}

void realloc_callback(uintptr_t id, uintptr_t ptr, size_t nsize)
{
	if (!profile_file)
		return;

	fprintf(profile_file, "realloc,%llu,%llu,%llu\n",
		(long long unsigned int)id,
		(long long unsigned int)ptr,
		(long long unsigned int)nsize);
	fflush(profile_file);
}

void free_callback(uintptr_t id)
{
	if (!profile_file)
		return;

	fprintf(profile_file, "free,%llu\n", (long long unsigned int)id);
	fflush(profile_file);
}


char* my_asctime(const struct tm *timeptr)
{
	static const char mon_name[][4] = {
		"Jan", "Feb", "Mar", "Apr", "May", "Jun",
		"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
	};
	static char result[26];
	sprintf(result, "%.3s,%3d %d %d",
		mon_name[timeptr->tm_mon],
		timeptr->tm_mday,
		1900 + timeptr->tm_year,
		(timeptr->tm_hour * 3600) + (timeptr->tm_min * 60) + timeptr->tm_sec);
	return result;
}

void init_profiler()
{
	char fileName[260];
	time_t rawtime;
	struct tm * timeinfo;

	time(&rawtime);
	timeinfo = localtime(&rawtime);
	sprintf(fileName, "lprof (%s).out", my_asctime(timeinfo));

	profile_file = fopen(fileName, "wb");
	if (!profile_file)
	{
		printf("Profiler error: output file could not be opened!");
		exit(-1);
	}

	string_table = hashset_create();
	if (!string_table)
	{
		fclose(profile_file);
		profile_file = NULL;

		printf("Profiler error: unable to create string table!");
		exit(-1);
	}

	printf("Profiler enabled\n");
}


void hook_profiler(lua_State* L)
{
	if (profile_file)
	{
		lua_sethook(L, (lua_Hook)callhook, LUA_MASKCALL | LUA_MASKRET, 0);
	}
}


int shutdown_profiler()
{
	if (string_table)
	{
		hashset_destroy(string_table);
		string_table = NULL;
	}

	if (profile_file)
	{
		fclose(profile_file);
		profile_file = NULL;
	}

	return 0;
}

