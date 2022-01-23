import vtk
from vtk.util import vtkAlgorithm
from vtk.util.numpy_support import vtk_to_numpy
import numpy as np


class vtkImageReader3(vtkAlgorithm.VTKPythonAlgorithmBase):
    """Python implementation of vtkImageReader3"""
    def __init__(self):
        self.FileName = None
        self.FilePrefix = None
        self.FileNames = None
        self.Finalized = False
        self.MD5Sum = 0
        self.HeaderSize = 0
        self.ManualHeaderSize = False
        self.Dimensionality = 0
        self.NumberOfScalarComponents = 1
        self.DataExtent = [0, -1, 0, -1, 0, -1]
        self.DataSpacing = [1, 1, 1]
        self.DataOrigin = [0, 0, 0]
        self.DataScalarType = vtk.VTK_SHORT
        self.DataByteOrder = 1

        vtkAlgorithm.VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1, outputType='vtkImageData')

    def __getattr__(self, attr):
        print("getattr: {}".format(attr))

    def SetFileName(self, filename):
        if filename:
            if self.Filename is filename:
                return
        self.FileName = filename
        self.FilePrefix = None
        self.FileNames = None
        self.Finalized = False
        self.MD5Sum = 0

    def SetFileNames(self, filenames):
        if filenames:
            if self.FileNames is filenames:
                return
        self.FileName = None
        self.FileNames = filenames
        self.FilePrefix = None
        self.Finalized = False
        self.MD5Sum = 0

    def FillOutputPortInformation(self, port, info):
        info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkImageData")
        return 1

    def RequestInformation(self, request, inInfo, outInfo):

        oinfo = outInfo.GetInformationObject(0)

        oinfo.Set(vtk.vtkAlgorithm.CAN_PRODUCE_SUB_EXTENT(), 1)

        if self.FileNames and self.FileNames.GetNumberOfValues() > 0:
            self.DataExtent[4] = 0
            self.DataExtent[5] = self.FileNames.GetNumberOfValues() - 1

        oinfo.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(), self.DataExtent, 6)

        oinfo.Set(vtk.vtkDataObject.SPACING(), (self.DataSpacing[0], self.DataSpacing[1], self.DataSpacing[2]), 3)
        oinfo.Set(vtk.vtkDataObject.ORIGIN(), self.DataOrigin, 3)
        vtk.vtkDataObject.SetPointDataActiveScalarInfo(oinfo, self.DataScalarType,
                                                       self.NumberOfScalarComponents)

        return 1

    def RequestData(self, request, inInfo, outInfoVec):
        outInfo = outInfoVec.GetInformationObject(0)
        oimage = outInfo.Get(vtk.vtkDataObject.DATA_OBJECT())
        oimage.SetExtent(outInfo.Get(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT()))
        oimage.AllocateScalars(outInfo)

        # get access to VTK image as a numpy array
        dims = oimage.GetDimensions()
        array_name = oimage.GetPointData().GetArrayName(0)
        arr = vtk_to_numpy(oimage.GetPointData().GetArray(array_name))
        arr.shape = dims[::-1]

        # go read data
        _file = None
        for z in range(dims[2]):

            self.UpdateProgress(float(z) / float(dims[2]))

            if self.FileNames:
                _file = open(self.FileNames.GetValue(z), 'rb')
                _file.seek(self.HeaderSize)
            else:
                if self.FileName and _file is None:
                    _file = open(self.FileName, 'rb')
                    _file.seek(self.HeaderSize)

            temp_arr = np.fromfile(_file, dtype=arr.dtype, count=dims[0]*dims[1])
            temp_arr.shape = dims[0:2][::-1]
            arr[z, :, :] = temp_arr

            if self.FileNames:
                _file.close()

        if not self.DataByteOrder:
            arr.byteswap(True)

        return 1

    def GetMD5Sum(self):
        if not self.Finalized:
            self.FinalizeDigest()
        return self.MD5Sum

    def SetHeaderSize(self, sz):
        if sz != self.HeaderSize:
            self.HeaderSize = sz
            self.Modified()
        self.ManualHeaderSize = True

    def SetFileDimensionality(self, dims):
        if dims != self.Dimensionality:
            self.Dimensionality = dims
            self.Modified()

    def GetNumberOfScalarComponents(self):
        return self.NumberOfScalarComponents

    def SetNumberOfScalarComponents(self, components):
        if components != self.NumberScalarComponents:
            self.NumberOfScalarComponents = components
            self.Modified()

    def GetDataExtent(self):
        return self.DataExtent

    def SetDataExtent(self, *extent):
        if extent != self.DataExtent:
            self.DataExtent = list(extent)
            self.Modified()

    def GetDataSpacing(self):
        return self.DataSpacing

    def SetDataSpacing(self, *spacing):
        if spacing != self.DataSpacing:
            self.DataSpacing = list(spacing)
            self.Modified()

    def GetDataOrigin(self):
        return self.DataOrigin

    def SetDataOrigin(self, *origin):
        if origin != self.DataOrigin:
            self.DataOrigin = list(origin)
            self.Modified()

    def SetDataScalarTypeToShort(self):
        self.DataScalarType = vtk.VTK_SHORT

    def GetDataByteOrder(self):
        return self.DataByteOrder

    def SetDataByteOrder(self, order):
        self.DataByteOrder = order

if __name__ == '__main__':
    r = vtkImageReader3()
    r.Update()
