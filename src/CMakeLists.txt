PROJECT(vtkMultiIO)

cmake_minimum_required(VERSION 2.8)

# Mac needs hand holding
LINK_DIRECTORIES(/usr/local/lib)
INCLUDE_DIRECTORIES(/usr/local/include/vtk-6.1)

FIND_PACKAGE(PythonInterp)
FIND_PACKAGE(PythonLibs)

INCLUDE(${VTK_DIR}/UseVTK.cmake)
INCLUDE(${VTK_DIR}/CMake/vtkWrapPython.cmake)

SET(srcs
  vtkImageReader3.cxx
  vtkImageReader4.cxx
  vtkMultiIOEventObject.cxx
  vtkVFFReader.cxx
  vtkVFFWriter.cxx
)

SET(py_libs
  vtkWrappingPython27Core-6.1
  vtkCommonExecutionModelPython27D-6.1
  vtkIOImagePython27D-6.1
  vtkChartsCorePython27D-6.1
  vtkCommonCorePython27D-6.1
  vtkCommonExecutionModel-6.1
  vtkChartsCore-6.1
  vtkCommonDataModel-6.1
  vtkCommonCore-6.1
  vtkIOImage-6.1
  vtksys-6.1
  vtkIOImage-6.1
)

######################################################
# You do not need to change anything beyond this point.
######################################################

INCLUDE_DIRECTORIES(${PROJECT_SOURCE_DIR})
INCLUDE_DIRECTORIES(${PROJECT_BINARY_DIR})
INCLUDE_DIRECTORIES(${OPENSSL_INCLUDE_DIR})
INCLUDE_DIRECTORIES(${PYTHON_INCLUDE_DIR})
INCLUDE_DIRECTORIES(${VTK_SOURCE_DIR}/Wrapping/Python)
#INCLUDE(${CMAKE_ROOT}/Modules/FindVTK.cmake) ## deprecated in cmake 3.1

IF(VTK_FOUND)
  INCLUDE(${VTK_USE_FILE})
  INCLUDE(${VTK_DIR}/VTKConfig.cmake)
  INCLUDE(${VTK_CMAKE_DIR}/vtkWrapPython.cmake)
ENDIF(VTK_FOUND)

OPTION(BUILD_SHARED_LIBS "Build with shared libraries."
       ${VTK_BUILD_SHARED_LIBS})

IF(BUILD_SHARED_LIBS)
  SET(VTKLOCAL_BUILD_SHARED_LIBS_CONFIG 1)
ELSE(BUILD_SHARED_LIBS)
  SET(VTKLOCAL_BUILD_SHARED_LIBS_CONFIG 0)
ENDIF(BUILD_SHARED_LIBS)

SET(VTK_USE_INSTANTIATOR_NEW 1)

VTK_WRAP_PYTHON3("${PROJECT_NAME}Python" python_srcs "${srcs}")
ADD_LIBRARY("${PROJECT_NAME}Python" MODULE ${python_srcs} ${srcs} ${PROJECT_NAME}PythonInit.cxx)
#ADD_LIBRARY("${PROJECT_NAME}Python" MODULE ${python_srcs} ${srcs} ${instantiator_srcs})
TARGET_LINK_LIBRARIES("${PROJECT_NAME}Python"
                      ${py_libs}
                      ${OPENSSL_LIBRARIES}
                      ${libs}
                      # ${PYTHON_LIBRARY}
                      ) 

