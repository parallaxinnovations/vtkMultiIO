
#ifndef VTKMULTIIO_EXPORT_H
#define VTKMULTIIO_EXPORT_H

#ifdef VTKMULTIIO_STATIC_DEFINE
#  define VTKMULTIIO_EXPORT
#  define VTKMULTIIO_NO_EXPORT
#else
#  ifndef VTKMULTIIO_EXPORT
#    ifdef VTKMULTIIO_EXPORTS
        /* We are building this library */
#      define VTKMULTIIO_EXPORT 
#    else
        /* We are using this library */
#      define VTKMULTIIO_EXPORT 
#    endif
#  endif

#  ifndef VTKMULTIIO_NO_EXPORT
#    define VTKMULTIIO_NO_EXPORT 
#  endif
#endif

#ifndef VTKMULTIIO_DEPRECATED
#  define VTKMULTIIO_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef VTKMULTIIO_DEPRECATED_EXPORT
#  define VTKMULTIIO_DEPRECATED_EXPORT VTKMULTIIO_EXPORT VTKMULTIIO_DEPRECATED
#endif

#ifndef VTKMULTIIO_DEPRECATED_NO_EXPORT
#  define VTKMULTIIO_DEPRECATED_NO_EXPORT VTKMULTIIO_NO_EXPORT VTKMULTIIO_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef VTKMULTIIO_NO_DEPRECATED
#    define VTKMULTIIO_NO_DEPRECATED
#  endif
#endif

#endif /* VTKMULTIIO_EXPORT_H */
