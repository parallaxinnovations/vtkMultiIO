from __future__ import absolute_import
from builtins import str
from builtins import object
import vtk

import pydicom
from zope.interface import implementer
from PI.visualization.vtkMultiIO import interfaces
import logging
from PI.visualization.vtkMultiIO import MVImage

# list of image Writer capabilities
DEPTH_8 = 1 << 0
DEPTH_16 = 1 << 1
DEPTH_32 = 1 << 2
DEPTH_64 = 1 << 3
IMAGE_2D = 1 << 4
IMAGE_3D = 1 << 5
WHOLE_FILENAME = 1 << 6

logger = logging.getLogger(__name__)


class vtkWriterBase(object):

    __extensions__ = {'img': 'Generic image', 'hdr': 'Generic image'}
    __magic__ = [('', 0)]
    __classname__ = "vtkWriterBase"

    def GetClassName(self):
        return self.__classname__


@implementer((interfaces.IDimensionInformation,
                          interfaces.IImageInformation,
                          interfaces.IvtkImageWriter))
class vtkImageWriterBase(vtkWriterBase):

    __capabilities__ = (DEPTH_16)

    def __init__(self):
        self._ImageWriter = None
        self.__image = None
        self.ClearDICOMHeader()

    def GetDICOMHeader(self):
        return self._ds

    def SetDICOMHeader(self, ds):
        self._ds = ds

    def ClearDICOMHeader(self):
        self._ds = pydicom.dataset.Dataset()

    def ConvertTags(self, ds):

        tags = {}

        for tag in ds:
            if tag.VR in ('SQ', ):
                # ignore certain types of structures
                continue
            try:
                name = tag.name.replace(' ', '').replace("'", "")
                value = str(tag.value)
                # strip blank tags
                if value == '':
                    continue
                if name in ('Rows', 'Columns', 'BitsAllocated', 'BitsStored', 'PixelSpacing'):
                    # ignore certain tags
                    continue
                tags['dicom_{0}'.format(name)] = value
            except Exception as e:
                logger.error("Unable to convert tag {0}".format(name))

        return tags

    def __getattr__(self, attr):
        try:
            return getattr(self._ImageWriter, attr)
        except Exception as e:
            # hook left here so we can trace if needed
            raise e

    def GetDescriptiveName(self):
        """Returns a descriptive name for the file Writer"""
        return ''

    def GetFileExtensions(self):
        return []

    def GetInputData(self):
        return self.__image

    def GetInputConnection(self):
        return self._algorithm_output

    def SetInputConnection(self, algorithm_output):
        self._algorithm_output = algorithm_output
        self.SetInputData(algorithm_output.GetProducer().GetOutputDataObject(0))

    def SetInputData(self, image):
        self.__image = image
        if isinstance(image, MVImage.MVImage):
            real_image = image.GetRealImage()
            self.__image = image
        else:
            real_image = image
            self.__image = None
        # VTK-6
        if hasattr(self._ImageWriter, 'SetInputData'):
            self._ImageWriter.SetInputData(real_image)
        else:
            self._ImageWriter.SetInput(real_image)

    def SetImageWriter(self, writer):

        if self._ImageWriter:
            self._ImageWriter.GetOutput().RemoveAllObservers()

        self._ImageWriter = writer

    def SetupWriter(self):
        """Perform any writer initialization"""
        pass
