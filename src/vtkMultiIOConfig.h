#ifndef vtkMultiIOConfig_h
#define vtkMultiIOConfig_h

/* Configuration information. */
/* #undef VTKMULTIIO_BUILD_SHARED_LIBS */
#define VTKMULTIIO_BUILD_TESTING

/* Version number. */
#define VTKMULTIIO_MAJOR_VERSION 0
#define VTKMULTIIO_MINOR_VERSION 7
#define VTKMULTIIO_PATCH_VERSION 0
#define VTKMULTIIO_SHORT_VERSION "0.7"
#define VTKMULTIIO_VERSION "0.7.0"

/* Legacy (for backwards compatibility) */
#define VTKMULTIIO_BUILD_VERSION VTKMULTIIO_PATCH_VERSION

/* To support 'override' for C++11 compilers */
#define VTK_VTKMULTIIO_OVERRIDE override
/* To support '=delete' for C++11 compilers */
#define VTK_VTKMULTIIO_DELETE = delete

#endif
