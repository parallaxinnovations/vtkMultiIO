set(DOCUMENTATION
"This package contains a set of VTK-compatible I/O classes"
)

vtk_module(vtkMultiIO
  DESCRIPTION
    "${DOCUMENTATION}"
  DEPENDS
    vtkCommonCore
    vtkCommonDataModel
    vtkCommonExecutionModel
    vtkIOImage
  PRIVATE_DEPENDS
    vtkCommonMisc
    vtkImagingCore
    vtkIOCore
    vtkzlib
  COMPILE_DEPENDS
    vtkImagingStatistics
    vtkInteractionStyle
    vtkRenderingImage
    vtkRendering${VTK_RENDERING_BACKEND}
)
