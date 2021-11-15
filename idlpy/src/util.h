#ifndef IDLPY_UTIL_H
#define IDLPY_UTIL_H

#ifdef WIN32
#include <direct.h>
#define mkdir(dir, mode) _mkdir(dir)
#else
#include <sys/stat.h>
#endif
#include <stdio.h>

FILE* idlpy_open_file(const char *pathname, const char *mode);
char* idlpy_strdup(const char* str);
int idlpy_vfprintf(FILE *fp, const char *fmt, va_list ap);
int idlpy_fprintf(FILE *fp, const char *fmt, ...);

#endif // IDLPY_UTIL_H