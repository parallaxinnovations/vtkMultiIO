from __future__ import print_function
from __future__ import absolute_import
from builtins import range
from builtins import object
import os
import vtk
from zope.interface import implementer
from . import interfaces
from . import MVImage
from datetime import datetime
from PI.visualization.common.CoordinateSystem import CoordinateSystem
from PI.dicom import convert

# list of image reader capabilities
DEPTH_8 = 1 << 0
DEPTH_16 = 1 << 1
DEPTH_32 = 1 << 2
DEPTH_64 = 1 << 3
IMAGE_2D = 1 << 4
IMAGE_3D = 1 << 5
WHOLE_FILENAME = 1 << 6

##########################################################################

@implementer((interfaces.IImageInformation,
              interfaces.IvtkImageReader))
class vtkImageReaderBase(object):


    __extensions__ = {'.img': 'Generic image', '.hdr': 'Generic image'}
    __magic__ = [('', 0)]
    __capabilities__ = DEPTH_16

    def __init__(self):
        self._ImageReader = None
        self._output = None
        self._filename = None
        self._coordinate_system = CoordinateSystem.vtk_coords
        self.dicom_converter = convert.BaseDicomConverter()

        # contains slice-by-slice dicom tags for each slice in image
        self._dicom_slice_headers = {}

    def __del__(self):
        print('deleting {0}'.format(self.__class__))

    def SetCoordinateSystem(self, val):
        self._coordinate_system = val

    def GetCoordinateSystem(self):
        return self._coordinate_system

    def SetSliceDICOMHeaders(self, headers):
        self._dicom_slice_headers = headers

    def GetSliceDICOMHeaders(self):
        return self._dicom_slice_headers

    def SetMeasurementUnitToMM(self):
        for dim in self.GetOutput().GetDimensionInformation():
            if dim.GetTypeName() == 'Distance':
                dim.SetUnit('mm')

    def AddObserver(self, evt, method):
        if self._ImageReader:
            if hasattr(self._ImageReader, 'AddObserver'):
                self._ImageReader.AddObserver(evt, method)

    def GetOutput(self):

        if self._output is None:
            # returns either a vtk.vtkAlgorithm or a MVImage object
            output = self._ImageReader.GetOutputPort()
            # wrap output image if we need to
            if isinstance(output, vtk.vtkObject):
                mv_image = MVImage.MVImage(output)
                mv_image.SetFileName(self._filename)
                mv_image.SetDICOMConverter(self.dicom_converter)
                self._output = mv_image
            else:
                self._output = output
        return self._output

    def SetImageReader(self, reader):

        if self._ImageReader:
            self._ImageReader.GetOutput().RemoveAllObservers()

        self._ImageReader = reader

    def CanReadFile(self, filename, magic=None):

        # sanity check
        if not os.path.exists(filename):
            return 0

        valid = True

        if magic is None:
            magic = self.__magic__

        for e in magic:
            _magic, _offset = e

            # abort early if there's no magic string for this format
            if _magic == '':
                valid = False
                break
            # determine maximum amount to read -- negative offsets indicate
            # line-based magic number check
            if _offset >= 0:
                with open(filename, 'rb') as f:
                    l = _offset + len(_magic)
                    offset = _offset
                    arr = f.read(l)

                # was read of header successful?
                if len(arr) == 0:
                    class MyError(Exception):

                        def __str__(self):
                            return '[Error 100]: Truncated image'
                    raise MyError()
            else:
                with open(filename, 'rt') as f:
                    numlines = -_offset
                    for n in range(numlines + 1):
                        arr = f.readline()
                offset = 0

            if arr[offset:offset + len(_magic)] != _magic:
                valid = False
                break

        if valid:
            return 3
        else:
            return 0

    def SetFileName(self, filename):

        # pass on to our reader
        self._ImageReader.SetFileName(filename)

        # remember it ourselves
        self._filename = filename

        # update DICOM
        self.UpdateDICOMHeaderInfo(filename)

    def __getattr__(self, attr):
        return getattr(self._ImageReader, attr)

    def UpdateDICOMHeaderInfo(self, filename):
        # TODO: this is deprecated - moved to MVImage - remove me
        return

    #
    # These next methods help make this base reader look like
    # VTK4 image readers -- eventually we may use vtk readers directly
    #

    def GetFileExtensions(self):
        s = ' '
        for key in self.__extensions__:
            s = s[:-1] + key + ' '
        return s[:-1]
