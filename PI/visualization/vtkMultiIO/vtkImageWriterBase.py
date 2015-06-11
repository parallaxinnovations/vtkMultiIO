import vtk

import dicom
from zope import interface
import interfaces
from PI.visualization.vtkMultiIO import MVImage

# list of image Writer capabilities
DEPTH_8 = 1 << 0
DEPTH_16 = 1 << 1
DEPTH_32 = 1 << 2
DEPTH_64 = 1 << 3
IMAGE_2D = 1 << 4
IMAGE_3D = 1 << 5
WHOLE_FILENAME = 1 << 6


class vtkWriterBase(object):

    __extensions__ = {'img': 'Generic image', 'hdr': 'Generic image'}
    __magic__ = [('', 0)]
    __classname__ = "vtkWriterBase"

    def GetClassName(self):
        return self.__classname__


class vtkImageWriterBase(vtkWriterBase):

    interface.implements((interfaces.IDimensionInformation,
                          interfaces.IImageInformation,
                          interfaces.IvtkImageWriter))

    __capabilities__ = (DEPTH_16)

    def __init__(self):
        self._ImageWriter = None
        self._image = None
        self.ClearDICOMHeader()

    def GetDICOMHeader(self):
        return self._ds

    def SetDICOMHeader(self, ds):
        self._ds = ds

    def ClearDICOMHeader(self):
        self._ds = dicom.dataset.Dataset()

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
            except Exception, e:
                logging.error("Unable to convert tag {0}".format(name))

        return tags

    def __getattr__(self, attr):
        try:
            return getattr(self._ImageWriter, attr)
        except Exception, e:
            # hook left here so we can trace if needed
            raise e

    def GetDescriptiveName(self):
        """Returns a descriptive name for the file Writer"""
        return ''

    def GetFileExtensions(self):
        return []

    def GetInput(self):
        return self._image

    def SetInput(self, image):
        if isinstance(image, MVImage.MVImage):
            real_image = image.GetRealImage()
            self._image = image
        else:
            real_image = image
            self._image = None
        self._ImageWriter.SetInput(real_image)

    def SetImageWriter(self, writer):

        if self._ImageWriter:
            self._ImageWriter.GetOutput().RemoveAllObservers()

        self._ImageWriter = writer

    def SetupWriter(self):
        """Perform any writer initialization"""
        pass
