cmake_minimum_required(VERSION 3.0)

# Configuration header
set(VTKMULTIIO_BUILD_SHARED_LIBS ${BUILD_SHARED_LIBS})
set(VTKMULTIIO_BUILD_TESTING ${BUILD_TESTING})

set(VTKMULTIIO_OVERRIDE " override")
set(VTKMULTIIO_DELETE " = delete")

configure_file("${VTKMULTIIO_CMAKE_DIR}/vtkMultiIOConfig.h.in"
  "${CMAKE_CURRENT_BINARY_DIR}/vtkMultiIOConfig.h" @ONLY)

configure_file("${VTKMULTIIO_CMAKE_DIR}/vtkMultiIOBuild.h.in"
  "${CMAKE_CURRENT_BINARY_DIR}/vtkMultiIOBuild.h" @ONLY)

# Include directories
include_directories(${VTKMULTIIO_INCLUDE_DIRS})

# Create the main library
set(LIB_NAME vtkMultiIO)

# Sources in the current directory (library sources only!)
set(LIB_SRCS
  vtkImageReader3.cxx
  vtkImageReader4.cxx
  vtkVFFWriter.cxx
)

# Headers without a matching .cxx file are listed here
set(LIB_HDRS
  ${CMAKE_CURRENT_BINARY_DIR}/vtkMultiIOBuild.h
  ${CMAKE_CURRENT_BINARY_DIR}/vtkMultiIOConfig.h
  ${CMAKE_CURRENT_BINARY_DIR}/vtkMultiIOModule.h
)

# Internal headers (not installed)
set(LIB_PRIVATE_HDRS
  ${CMAKE_CURRENT_BINARY_DIR}/vtkMultiIOBuild.h
)

# Sources that are abstract
set(LIB_ABSTRACT
)

# Sources that are not vtkObjects
set(LIB_SPECIAL
  #GamepadHandler.cxx
)

set_source_files_properties(${LIB_HDRS} ${LIB_SPECIAL}
  PROPERTIES WRAP_EXCLUDE ON)
set_source_files_properties(${LIB_ABSTRACT}
  PROPERTIES ABSTRACT ON)
set_source_files_properties(${LIB_PRIVATE_HDRS}
  PROPERTIES SKIP_HEADER_INSTALL ON)

# Third party library dependencies (none)



# Create the library

if(DEFINED VTK_MODULE_ENABLE_VTK_VTKMULTIIO)
  # When building as a module for VTK 8.90 or later
  set(LIB_SRC_HDRS)
  foreach(_src ${LIB_SRCS})
    get_filename_component(_base ${_src} NAME_WE)
    list(APPEND LIB_SRC_HDRS ${_base}.h)
  endforeach()
  vtk_module_add_module(VTK::VTKMULTIIO
    SOURCES ${LIB_SRCS} ${LIB_SPECIAL}
    HEADERS ${LIB_SRC_HDRS} ${LIB_HDRS})
  vtk_module_link(VTK::VTKMULTIIO
    PRIVATE )
endif()
