cmake_minimum_required(VERSION 3.0)

project(VTKMULTIIO)

# Allow custom cmake overrides
set(VTKMULTIIO_CMAKE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/CMake)
set(CMAKE_MODULE_PATH ${VTKMULTIIO_CMAKE_DIR} ${CMAKE_MODULE_PATH})

# Use ctest for dashboard submissions
include(CTest)

string(TIMESTAMP timestring %Y%m%d%H%M%S UTC)
set(VTKMULTIIO_MAJOR_VERSION 0)
set(VTKMULTIIO_MINOR_VERSION 7)
set(VTKMULTIIO_PATCH_VERSION 0)
set(VTKMULTIIO_SHORT_VERSION "${VTKMULTIIO_MAJOR_VERSION}.${VTKMULTIIO_MINOR_VERSION}")
set(VTKMULTIIO_VERSION "${VTKMULTIIO_SHORT_VERSION}.${VTKMULTIIO_PATCH_VERSION}")

set(VTKMULTIIO_TWEAK_VERSION ${timestring})

# Store the git hash of the current head (not working in top directory)
if(EXISTS "${VTKMULTIIO_SOURCE_DIR}/.git/HEAD")
  file(READ "${VTKMULTIIO_SOURCE_DIR}/.git/HEAD" VTKMULTIIO_SOURCE_VERSION)
  if("${VTKMULTIIO_SOURCE_VERSION}" MATCHES "^ref:")
    string(REGEX REPLACE "^ref: *([^ \n\r]*).*" "\\1"
      VTKMULTIIO_GIT_REF "${VTKMULTIIO_SOURCE_VERSION}")
    file(READ "${VTKMULTIIO_SOURCE_DIR}/.git/${VTKMULTIIO_GIT_REF}"
      VTKMULTIIO_SOURCE_VERSION)
  endif()
  string(STRIP "${VTKMULTIIO_SOURCE_VERSION}" VTKMULTIIO_SOURCE_VERSION)
endif()

string(TIMESTAMP VTKMULTIIO_BUILD_TIME "%H:%M:%S" UTC)
string(TIMESTAMP VTKMULTIIO_BUILD_DATE "%d %B %Y" UTC)

# Include directories
set(VTKMULTIIO_INCLUDE_DIRS
  "${VTKMULTIIO_SOURCE_DIR}/src"
  "${VTKMULTIIO_BINARY_DIR}/src")

# Is this CMakeLists.txt file being called directly by cmake?
if("${CMAKE_PROJECT_NAME}" STREQUAL "${PROJECT_NAME}")
  set(_VTKMULTIIO_direct_build ON)
else()
  set(_VTKMULTIIO_direct_build OFF)
endif()

set(VTKMULTIIO_EXTERNAL_BUILD ${_VTKMULTIIO_direct_build} CACHE BOOL
  "Building VTKMULTIIO module external to the VTK build")
mark_as_advanced(VTKMULTIIO_EXTERNAL_BUILD)

if(DEFINED VTK_MODULE_ENABLE_VTK_VTKMULTIIO AND NOT VTKMULTIIO_EXTERNAL_BUILD)
  # When building as a remote module for VTK 9 (or VTK 8.90+)
  message(STATUS "vtkMultiIO: Building vtkMultiIO as a Remote VTK Module")

  # Clear VTK_LIBS, linking will be handled by modular build
  set(VTK_LIBS)
  set(VTK_VTKMULTIIO_LINK_TARGET VTK::VTKMULTIIO)

  option(BUILD_VTKMULTIIO_PROGRAMS "Build the vtkMultiIO tools" OFF)
  option(BUILD_VTKMULTIIO_EXAMPLES "Build the vtkMultiIO examples" OFF)
  set(BUILD_PROGRAMS ${BUILD_VTKMULTIIO_PROGRAMS})
  set(BUILD_EXAMPLES ${BUILD_VTKMULTIIO_EXAMPLES})
else()
  # When building external to VTK (default)
  message(STATUS "vtkMultiIO: Building vtkMultiIO outside of VTK")

  # Find VTK and get VTK configuration information
  find_package(VTK REQUIRED)

  message(${VTK_VERSION})

  # define VTK_VERSION if not already defined
  if(NOT DEFINED VTK_VERSION)
    set(VTK_VERSION ${VTK_MAJOR_VERSION}.${VTK_MINOR_VERSION})
  endif()
  if(VTK_VERSION VERSION_LESS 8.90)
    message(FATAL_ERROR "VTK 8.90+ or later is required.")
  endif()

  # We are being built as a stand-alone package
  set(VTK_VTKMULTIIO_LINK_TARGET vtkMultiIO)

  option(BUILD_SHARED_LIBS "Build shared libraries." OFF)

  # Which parts of the package to build
  option(BUILD_TESTING "Build the tests" OFF)
  option(BUILD_PROGRAMS "Build some useful VTKMULTIIO tools" OFF)
  option(BUILD_EXAMPLES "Build the examples" OFF)

  # Wrap Python option
  if(VTK_WRAP_PYTHON)
    option(BUILD_PYTHON_WRAPPERS "Build python wrappers" ON)
  else()
    unset(BUILD_PYTHON_WRAPPERS CACHE)
  endif()

  # Defines CMAKE_INSTALL_LIBDIR
  include(GNUInstallDirs)

  # Set up our directory structure for output libraries and binaries
  # (Note: these are the build locations, not the install locations)
  if(NOT CMAKE_RUNTIME_OUTPUT_DIRECTORY)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${VTKMULTIIO_BINARY_DIR}/bin")
  endif()
  if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    if(UNIX)
      set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${VTKMULTIIO_BINARY_DIR}/lib")
    else()
      set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${VTKMULTIIO_BINARY_DIR}/bin")
    endif()
  endif()
  if(NOT CMAKE_ARCHIVE_OUTPUT_DIRECTORY)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${VTKMULTIIO_BINARY_DIR}/lib")
  endif()

  if(NOT VTK_VERSION VERSION_LESS 8.90)
    # When building as a stand-alone module for VTK 9
    message(STATUS "vtkMultiIO: Building as an External VTK Module")

    # Clear VTK_LIBS, linking will be handled by modular build
    set(VTK_LIBS)
    set(VTK_VTKMULTIIO_LINK_TARGET VTK::VTKMULTIIO)

    vtk_module_scan(
      MODULE_FILES        "${CMAKE_CURRENT_SOURCE_DIR}/src/VTKMULTIIO.module"
      REQUEST_MODULES     "VTK::VTKMULTIIO"
      PROVIDES_MODULES    VTKMULTIIO_modules
      ENABLE_TESTS        "${BUILD_TESTING}")

    vtk_module_build(
      MODULES             ${VTKMULTIIO_modules}
      INSTALL_EXPORT      VTKMULTIIO
      ARCHIVE_DESTINATION "lib"
      HEADERS_DESTINATION "include/VTKMULTIIO${VTKMULTIIO_SHORT_VERSION}"
      CMAKE_DESTINATION   "${CMAKE_INSTALL_LIBDIR}/cmake/vtk"
      LICENSE_DESTINATION "${CMAKE_INSTALL_LIBDIR}/vtk"
      HIERARCHY_DESTINATION "${CMAKE_INSTALL_LIBDIR}/vtk/hierarchy/${CMAKE_PROJECT_NAME}"
      LIBRARY_NAME_SUFFIX "${VTKMULTIIO_CUSTOM_LIBRARY_SUFFIX}"
      VERSION             "${VTKMULTIIO_VERSION}"
      SOVERSION           "1"
      TEST_DATA_TARGET    VTKMULTIIOData
      USE_EXTERNAL        "${VTKMULTIIO_USE_EXTERNAL}"
      TEST_INPUT_DATA_DIRECTORY   "${VTKMULTIIO_test_data_directory_input}"
      TEST_OUTPUT_DATA_DIRECTORY  "${VTKMULTIIO_test_data_directory_output}")

    if(BUILD_PYTHON_WRAPPERS)
      find_package(PythonInterp ${VTK_PYTHON_VERSION} QUIET)

      vtk_module_wrap_python(
        MODULES         ${VTKMULTIIO_modules}
        INSTALL_EXPORT  VTKMULTIIOPython
        PYTHON_PACKAGE  "vtk.modules"
        #MODULE_DESTINATION  ""
        CMAKE_DESTINATION   "${CMAKE_INSTALL_LIBDIR}/cmake/vtk"
        LIBRARY_DESTINATION "${CMAKE_INSTALL_LIBDIR}"
        BUILD_STATIC    OFF)
    endif()

  endif() #(NOT VTK_VERSION VERSION_LESS 8.90)

endif()

if(Module_vtkMultiIO)
  set(VTKMULTIIO_BIN_DIR ${VTK_INSTALL_RUNTIME_DIR})
  set(VTKMULTIIO_LIB_DIR ${VTK_INSTALL_LIBRARY_DIR})
  set(VTKMULTIIO_ARC_DIR ${VTK_INSTALL_ARCHIVE_DIR})
  set(VTKMULTIIO_INC_DIR ${VTK_INSTALL_INCLUDE_DIR})
endif()

# Set up our target directory structure for "make install"
set(VTKMULTIIO_BIN_DIR "bin") # for executables and ".dll" libraries
if(NOT VTKMULTIIO_LIB_DIR)
  set(VTKMULTIIO_LIB_DIR "lib") # for unix/linux/osx shared libraries
endif()
if(NOT VTKMULTIIO_ARC_DIR)
  set(VTKMULTIIO_ARC_DIR "${VTKMULTIIO_LIB_DIR}") # for static or ".lib" libraries
endif()
if(NOT VTKMULTIIO_INC_DIR)
  set(VTKMULTIIO_INC_DIR "include") # for header files
endif()
if(NOT VTKMULTIIO_DATA_DIR)
  set(VTKMULTIIO_DATA_DIR "share/VTKMULTIIO-${VTKMULTIIO_SHORT_VERSION}")
endif()
if(NOT VTKMULTIIO_PGK_DIR)
  set(VTKMULTIIO_PGK_DIR "${VTKMULTIIO_LIB_DIR}/VTKMULTIIO-${VTKMULTIIO_SHORT_VERSION}/cmake")
endif()

# Set the full paths to the install tree
set(VTKMULTIIO_RUNTIME_INSTALL_DEST ${CMAKE_INSTALL_PREFIX}/${VTKMULTIIO_BIN_DIR})
set(VTKMULTIIO_LIBRARY_INSTALL_DEST ${CMAKE_INSTALL_PREFIX}/${VTKMULTIIO_LIB_DIR})
set(VTKMULTIIO_ARCHIVE_INSTALL_DEST ${CMAKE_INSTALL_PREFIX}/${VTKMULTIIO_ARC_DIR})
set(VTKMULTIIO_INCLUDE_INSTALL_DEST ${CMAKE_INSTALL_PREFIX}/${VTKMULTIIO_INC_DIR})
set(VTKMULTIIO_DATA_INSTALL_DEST ${CMAKE_INSTALL_PREFIX}/${VTKMULTIIO_DATA_DIR})
set(VTKMULTIIO_CMAKE_INSTALL_DEST ${CMAKE_INSTALL_PREFIX}/${VTKMULTIIO_PGK_DIR})

if(NOT Module_vtkMultiIO)
  # Libraries
  set(VTKMULTIIO_LIBRARIES vtkMultiIO)

  # The library dependencies
  if(NOT VTK_VERSION VERSION_LESS 6)
    set(VTK_TARGET_PREFIX "VTK::")
    set(VTK_LIBS)
    # required libraries
    foreach(_lib CommonCore CommonMisc CommonDataModel FiltersCore ImagingCore IOCore IOImage)
      list(APPEND VTK_LIBS ${VTK_TARGET_PREFIX}${_lib})
    endforeach()

    # factory libraries (only needed if present)
    foreach(_lib IOMPIImage)
      list(FIND VTK_LIBRARIES ${VTK_TARGET_PREFIX}${_lib} _index)
      if(_index GREATER -1)
        list(APPEND VTK_LIBS ${VTK_TARGET_PREFIX}${_lib})
      endif()
    endforeach()
  endif()
endif()

# Disable C and C++ deprecation warnings for MSVC 2005 and later
if(MSVC_VERSION EQUAL 1400 OR MSVC_VERSION GREATER 1400 OR MSVC10)
  add_definitions(-D_CRT_SECURE_NO_DEPRECATE -D_CRT_NONSTDC_NO_DEPRECATE
                  -D_CRT_SECURE_NO_WARNINGS)
  add_definitions(-D_SCL_SECURE_NO_DEPRECATE -D_SCL_SECURE_NO_WARNINGS)
endif()

# TODO: If this can be avoided when building as a part of VTK 8.9+ (remove this)
if(NOT VTKMULTIIO_EXTERNAL_BUILD OR NOT DEFINED VTK_MODULE_ENABLE_VTK_VTKMULTIIO)
  # The main library, if not handled by the VTK 9 functions
  add_subdirectory(src)
endif()

# Subdirectories
if(BUILD_PROGRAMS)
  # add_subdirectory(Programs)
endif()

if(BUILD_EXAMPLES)
  # add_subdirectory(Examples)
endif()

if(VTKMULTIIO_EXTERNAL_BUILD OR NOT DEFINED VTK_MODULE_ENABLE_VTK_VTKMULTIIO)

#if(BUILD_TESTING)
#    enable_testing()
#    add_subdirectory(Testing)
#  endif()

  # Install files
  install(FILES Copyright.txt
    DESTINATION ${VTKMULTIIO_DATA_INSTALL_DEST})

endif()

if(NOT Module_vtkMultiIO AND NOT DEFINED VTK_MODULE_ENABLE_VTK_VTKMULTIIO)
  #---------------------------------------------------
  # Export information for other projects

  # Add all targets to the build-tree export set
  export(TARGETS ${VTKMULTIIO_LIBRARIES}
    ${VTKMULTIIO_PYTHON_LIBRARIES} ${VTKMULTIIO_JAVA_LIBRARIES}
    FILE "${VTKMULTIIO_BINARY_DIR}/VTKMULTIIOTargets.cmake")

  # Export the package for use from the build-tree
  # (this registers the build-tree with a global CMake-registry)
  export(PACKAGE VTKMULTIIO)

  # Create the VTKMULTIIOConfig.cmake and VTKMULTIIOConfigVersion.cmake files

  # ... for the build tree
  set(INCLUDE_DIRS_CONFIG ${VTKMULTIIO_INCLUDE_DIRS})
  set(LIBRARY_DIRS_CONFIG "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")
  configure_file(CMake/VTKMULTIIOConfig.cmake.in
    "${VTKMULTIIO_BINARY_DIR}/VTKMULTIIOConfig.cmake" @ONLY)

  # ... for the install tree
  file(RELATIVE_PATH REL_INCLUDE_DIR "${VTKMULTIIO_CMAKE_INSTALL_DEST}"
    "${VTKMULTIIO_INCLUDE_INSTALL_DEST}")
  set(INCLUDE_DIRS_CONFIG "\${VTKMULTIIO_PGK_DIR}/${REL_INCLUDE_DIR}")
  file(RELATIVE_PATH REL_LIBRARY_DIR "${VTKMULTIIO_CMAKE_INSTALL_DEST}"
    "${VTKMULTIIO_LIBRARY_INSTALL_DEST}")
  set(LIBRARY_DIRS_CONFIG "\${VTKMULTIIO_PGK_DIR}/${REL_LIBRARY_DIR}")
  configure_file(CMake/VTKMULTIIOConfig.cmake.in
    "${VTKMULTIIO_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/VTKMULTIIOConfig.cmake" @ONLY)

  # ... for both
  configure_file(CMake/VTKMULTIIOConfigVersion.cmake.in
    "${VTKMULTIIO_BINARY_DIR}/VTKMULTIIOConfigVersion.cmake" @ONLY)

  # Install the VTKMULTIIOConfig.cmake and VTKMULTIIOConfigVersion.cmake
  install(FILES
    "${VTKMULTIIO_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/VTKMULTIIOConfig.cmake"
    "${VTKMULTIIO_BINARY_DIR}/VTKMULTIIOConfigVersion.cmake"
    DESTINATION "${VTKMULTIIO_CMAKE_INSTALL_DEST}" COMPONENT Development)

  # Install the Use file in the build and install directories
  configure_file(${VTKMULTIIO_SOURCE_DIR}/CMake/UseVTKMULTIIO.cmake.in
    ${VTKMULTIIO_BINARY_DIR}/UseVTKMULTIIO.cmake COPYONLY IMMEDIATE)
  install(FILES
    "${VTKMULTIIO_BINARY_DIR}/UseVTKMULTIIO.cmake"
    DESTINATION "${VTKMULTIIO_CMAKE_INSTALL_DEST}" COMPONENT Development)

  # Install the export set for use with the install-tree
  install(EXPORT VTKMULTIIOTargets
    DESTINATION "${VTKMULTIIO_CMAKE_INSTALL_DEST}" COMPONENT Development)
endif()
