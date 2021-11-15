#include "util.h"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <direct.h>
#define mkdir(dir, mode) _mkdir(dir)
#else
#include <sys/stat.h>
#endif

#define _GNU_SOURCE
#include <assert.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#if defined _WIN32
# include <locale.h>
typedef _locale_t locale_t;
#else
# include <pthread.h>
# include <strings.h>
# if __APPLE__ || __FreeBSD__
#   include <xlocale.h>
# else
#   include <locale.h>
# endif
#endif

#include "idl/stream.h"
#include "idl/string.h"
static locale_t posix_locale(void);


FILE* idlpy_open_file(const char *pathname, const char *mode)
{
#if _MSC_VER
  FILE *fp = NULL;

  if (fopen_s(&fp, pathname, mode) != 0)
    return NULL;
  return fp;
#else
  return fopen(pathname, mode);
#endif
}

char *idlpy_strdup(const char *str)
{
#if _WIN32
  return _strdup(str);
#else
  return strdup(str);
#endif
}

/* requires posix_locale */
int idlpy_vfprintf(FILE *fp, const char *fmt, va_list ap)
{
  assert(fp);
  assert(fmt);

#if _WIN32
  /* _vfprintf_p_l supports positional parameters */
  return _vfprintf_p_l(fp, fmt, posix_locale(), ap);
#elif __APPLE__ || __FreeBSD__
  return vfprintf_l(fp, posix_locale(), fmt, ap);
#else
  int ret;
  locale_t loc, posixloc = posix_locale();
  loc = uselocale(posixloc);
  ret = vfprintf(fp, fmt, ap);
  loc = uselocale(loc);
  assert(loc == posixloc);
  return ret;
#endif
}

int idlpy_fprintf(FILE *fp, const char *fmt, ...)
{
  int ret;
  va_list ap;

  assert(fp);
  assert(fmt);

  va_start(ap, fmt);
  ret = idlpy_vfprintf(fp, fmt, ap);
  va_end(ap);

  return ret;
}


#if defined _WIN32
static DWORD locale = TLS_OUT_OF_INDEXES;

#if defined __MINGW32__
_Pragma("GCC diagnostic push")
_Pragma("GCC diagnostic ignored \"-Wmissing-prototypes\"")
#endif
void WINAPI idlpy_cdtor(PVOID handle, DWORD reason, PVOID reserved)
{
  locale_t loc;

  (void)handle;
  (void)reason;
  (void)reserved;
  switch (reason) {
    case DLL_PROCESS_ATTACH:
      if ((locale = TlsAlloc()) == TLS_OUT_OF_INDEXES)
        goto err_alloc;
      if (!(loc = _create_locale(LC_ALL, "C")))
        goto err_locale;
      if (TlsSetValue(locale, loc))
        return;
      _free_locale(loc);
err_locale:
      TlsFree(locale);
err_alloc:
      abort();
      /* never reached */
    case DLL_THREAD_ATTACH:
      assert(locale != TLS_OUT_OF_INDEXES);
      if (!(loc = _create_locale(LC_ALL, "C")))
        abort();
      if (TlsSetValue(locale, loc))
        return;
      _free_locale(loc);
      abort();
      break;
    case DLL_THREAD_DETACH:
      assert(locale != TLS_OUT_OF_INDEXES);
      loc = TlsGetValue(locale);
      if (loc && TlsSetValue(locale, NULL))
        _free_locale(loc);
      break;
    case DLL_PROCESS_DETACH:
      assert(locale != TLS_OUT_OF_INDEXES);
      loc = TlsGetValue(locale);
      if (loc)
        _free_locale(loc);
      TlsSetValue(locale, NULL);
      TlsFree(locale);
      locale = TLS_OUT_OF_INDEXES;
      break;
    default:
      break;
  }
}
#if defined __MINGW32__
_Pragma("GCC diagnostic pop")
#endif

#if defined __MINGW32__
  PIMAGE_TLS_CALLBACK __crt_xl_tls_callback__ __attribute__ ((section(".CRT$XLZ"))) = idl_cdtor;
#elif defined _WIN64
  #pragma comment (linker, "/INCLUDE:_tls_used")
  #pragma comment (linker, "/INCLUDE:tls_callback_func")
  #pragma const_seg(".CRT$XLZ")
  EXTERN_C const PIMAGE_TLS_CALLBACK tls_callback_func = idlpy_cdtor;
  #pragma const_seg()
#else
  #pragma comment (linker, "/INCLUDE:__tls_used")
  #pragma comment (linker, "/INCLUDE:_tls_callback_func")
  #pragma data_seg(".CRT$XLZ")
  EXTERN_C PIMAGE_TLS_CALLBACK tls_callback_func = idlpy_cdtor;
  #pragma data_seg()
#endif /* _WIN32 */

static locale_t posix_locale(void)
{
  return TlsGetValue(locale);
}
#else /* _WIN32 */
static pthread_key_t key;
static pthread_once_t once = PTHREAD_ONCE_INIT;

static void free_locale(void *ptr)
{
  freelocale((locale_t)ptr);
}

static void make_key(void)
{
  (void)pthread_key_create(&key, free_locale);
}

static locale_t posix_locale(void)
{
  locale_t locale;
  (void)pthread_once(&once, make_key);
  if ((locale = pthread_getspecific(key)))
    return locale;
#if __APPLE__ || __FreeBSD__
  locale = newlocale(LC_ALL_MASK, NULL, NULL);
#else
  locale = newlocale(LC_ALL, "C", (locale_t)0);
#endif
  pthread_setspecific(key, locale);
  return locale;
}
#endif /* _WIN32 */