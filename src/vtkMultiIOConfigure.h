/*=========================================================================
This source has no copyright.  It is intended to be copied by users
wishing to create their own VTK classes locally.
=========================================================================*/
#ifndef __Configure_h
#define __Configure_h

#if 1
# define vtkMultiIO_SHARED
#endif

#if defined(_MSC_VER) && defined(vtkMultiIO_SHARED)
# pragma warning ( disable : 4275 )
#endif

#if defined(_WIN32) && defined(vtkMultiIO_SHARED)
# define VTK_vtkMultiIO_EXPORT __declspec( dllexport ) 
#else
# define VTK_vtkMultiIO_EXPORT
#endif

#endif // __vtkMultiIOConfigure_h
