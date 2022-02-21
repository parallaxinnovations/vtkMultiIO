from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from future.utils import python_2_unicode_compatible
from builtins import str, ascii
from builtins import map
from past.utils import old_div
from builtins import object
import copy
import io
import pydicom
import pydicom.dataset
from enum import Enum
import os
import time
from . import interfaces
import vtk
import logging
from vtk.util.numpy_support import vtk_to_numpy
import numpy as np
from zope.interface import implementer
from PI.visualization.common.CoordinateSystem import CoordinateSystem
from PI.dicom.convert import BaseDicomConverter

logger = logging.getLogger(__name__)

@implementer(interfaces.IDimension)
class Dimension(object):

    """An object representing on of the dimensions of a data-type"""

    def __init__(self, name, unit):
        self.SetName(name)
        self.SetUnit(unit)

    def GetName(self):
        return self._name

    def SetName(self, name):
        self._name = name

    def SetUnit(self, unit):
        self._unit = unit

    def GetUnit(self):
        return self._unit

    def GetTypeName(self):
        return self.__class__.__name__

    def __str__(self):

        s = io.StringIO()
        s.write(u'Dimension: "{0}" (a {1}) measured in {2}\n'.format(
            self.GetName(), self.GetTypeName(), self.GetUnit()))
        return s.getvalue()


class Distance(Dimension):

    """
    A dimension representing a distance, typically measured in millimeters

    Usage:

    >>> d = Distance('x')
    >>> d.GetName()
    'x'
    >>> d.GetUnit()
    'pixels'
    """

    def __init__(self, name, unit='pixels'):
        Dimension.__init__(self, name, unit)


class Slice(Dimension):

    """
    A dimension representing a collection of slices with no set association

    Usage:

    >>> d = Slice()
    >>> d.GetName()
    'Slice'
    >>> d.GetUnit()
    '#'
    """

    def __init__(self, name='slice', unit='#'):
        Dimension.__init__(self, name, unit)


class Time(Dimension):

    """
    A dimension representing time, typically in milliseconds

    Usage:

    >>> t = Time()
    >>> t.GetName()
    'time'
    >>> t.GetUnit()
    'ms'
    """

    def __init__(self, name='time', unit='ms'):
        Dimension.__init__(self, name, unit)


class Wavelength(Dimension):

    """
    A dimension representing a wavelength, measured in nanometers

    Usage:

    >>> w = Wavelength()
    >>> w.GetName()
    'wavelength'
    >>> w.GetUnit()
    'nm'
    """

    def __init__(self, name='wavelength', unit='nm'):
        Dimension.__init__(self, name, unit)


class DICOMHeaderDict(dict):
    """Emulates a standard python dictionary - build pydicom entries on a
    slice-by-slice basis by combining a base set of tags with one or
    more slice-specific tags.
    """
    def __init__(self, *args, **kwargs):
        super(DICOMHeaderDict, self).__init__(*args, **kwargs)
        self._metadata = None
        self._slice_dict = {}

    def set_meta_data(self, metadata):
        self._metadata = metadata

    def get_meta_data(self):
        return self._metadata

    def set_slice_dict(self, slice_dict):
        self._slice_dict = slice_dict

    def get_slice_dict(self):
        return self._slice_dict

    def __getitem__(self, ii):
        ds = copy.deepcopy(self._metadata)
        if ii in self._slice_dict:
            for _tag in self._slice_dict[ii]:
                ds[_tag.tag] = _tag
        return ds

    def __delitem__(self, ii):
        print('not implemented!')

    def __setitem__(self, ii, val):
        print('not implemented')

    def insert(self, ii, val):
        print('not implemented')

    def append(self, val):
        print('not implemented')

    @python_2_unicode_compatible
    def __str__(self):
        return str(self._metadata)

    @python_2_unicode_compatible
    def __repr__(self):
        return str(self._metadata)


@implementer(interfaces.IDimensionInformation)
class MVImage(object):

    """
    A python object that connects a DICOM dictionary of header info and dimension
    information with a VTK-style image.  Also bridges the gap between VTK4 and VTK6.
    """

    def __init__(self, image_data, **kw):

        # for zope
        self.__component_name__ = u''

        self._algorithm_output = None
        self._image_data_object = image_data
        self.__reference_count = 1
        self.__x_values = None
        self.__y_values = None
        self.__z_values = None

        self._header = {}  # header values that don't map to DICOM easily
        self.__value_name = 'Gray Scale Value'  # what does the pixel value mean?
        self.__unit = 'arb. units'                       # default unit
        self._dimensions = []
        self.__stencil_data = None
        self.__stencil_owner = None
        self._filename = kw.get('filename', None)
        self.__histogram_stats = vtk.vtkImageHistogramStatistics()

        # DICOM-related stuff
        datadir = '/'
        if self._filename:
            datadir = os.path.dirname(self._filename)
        self.dicom_converter = BaseDicomConverter(datadir=datadir)
        self.station_id = '0001'
        self.parallax_base_uid = '1.2.826.0.1.3680043.9.1613'
        self._coordinate_system = CoordinateSystem.vtk_coords
        self._dicom_header = None
        self._dicom_slice_headers = DICOMHeaderDict()  # slice-by-slice dicom headers (buffer)
        self._dicom_mtime = -1

        # make sure image_data is correct type
        if isinstance(image_data, vtk.vtkImageData):
            self.SetInputData(image_data)
        elif isinstance(image_data, vtk.vtkAlgorithmOutput):
            self.SetInputConnection(image_data)
        else:
            raise TypeError("MVImage must be created with a VTK image object")

        # Don't do this here - image may not have been loaded yet
        # Create default DICOM header
        #self.ClearDICOMHeader()

        # Create default dimensions
        self.SetDefaultDimensionInformation()

        if ('input' in kw) and isinstance(kw['input'], MVImage):
            ci = kw['input']
            self.CopyInfo(ci)
            if ci.GetXSlicePositions() is not None:
                self.__x_values = ci.GetXSlicePositions().copy()
            if ci.GetYSlicePositions() is not None:
                self.__y_values = ci.GetYSlicePositions().copy()
            if ci.GetZSlicePositions() is not None:
                self.__z_values = ci.GetZSlicePositions().copy()

        if 'slice_headers' in kw:
            self.SetSliceDICOMHeaders(kw['slice_headers'])

    def GetValueName(self):
        return  self.__value_name

    def SetValueName(self, v):
        self.__value_name = v

    def GetUnitName(self):
        return self.__unit

    def SetUnitName(self, u):
        self.__unit = u

    def SetDICOMConverter(self, converter):
        self.dicom_converter = converter

    def GetDICOMConverter(self):
        return self.dicom_converter

    def IncrementReferenceCount(self):
        self.__reference_count += 1

    def DecrementReferenceCount(self):
        self.__reference_count -= 1
        if self.__reference_count <= 0:
            self._image_data_object.ReleaseData()

    def SetCoordinateSystem(self, val):
        self._coordinate_system = val

    def GetCoordinateSystem(self):
        return self._coordinate_system

    def SetSliceDICOMHeaders(self, headers):
        self._dicom_slice_headers = headers

    def GetSliceDICOMHeaders(self):
        """Return entire DICOM slice array"""
        return self._dicom_slice_headers

    def GetSliceDICOMHeader(self, idx):
        return self._dicom_slice_headers[idx]

    def GetDICOMImage(self, idx):

        # start by grabbing dicom header (deep copy)
        ds = copy.deepcopy(self.GetSliceDICOMHeaders()[idx])

        # append image data
        arr = self.get_array()[idx]

        ds.PixelData = arr.tostring()
        # how is the data represented?
        # TODO: how do we handle floating point vff images?
        if ds.BitsAllocated == 8:
            ds[0x7FE0, 0x010].VR = 'OB'
        else:
            ds[0x7FE0, 0x010].VR = 'OW'

        return ds

    def get_array(self):

        dims = list(self._image_data_object.GetDimensions())
        scalars = self._image_data_object.GetPointData().GetScalars()
        if scalars is not None:
            numC = scalars.GetNumberOfComponents()
        else:
            numC = self._image_data_object.GetNumberOfScalarComponents()

        if numC > 1:
            dims.insert(0, numC)

        # drop trailing ones
        if dims[-1] == 1:
            dims = dims[:-1]

        # get access to vtk image as a numpy array
        array_name = self._image_data_object.GetPointData().GetArrayName(0)
        arr = vtk_to_numpy(
            self._image_data_object.GetPointData().GetArray(array_name))
        arr.shape = dims[::-1]

        return arr

    def get_itk_image(self):
        """
        return an ITK image view of this image
        """
        try:
            import itk
        except:
            from PI.visualization.common.PluginHelper import install_package
            install_package("itk", pip = True)
            logger.error("Unable to import ITK")
            return

        # get numpy representation of image data
        arr = self.get_array()

        dtype_map = {np.dtype('uint8'): itk.ctype('unsigned char'),
                     np.dtype('int8'): itk.ctype('signed char'),
                     np.dtype('uint16'): itk.ctype('unsigned short'),
                     np.dtype('int16'): itk.ctype('signed short'),
                     np.dtype('uint32'): itk.ctype('unsigned int'),
                     np.dtype('int32'): itk.ctype('signed int'),
                     np.dtype('float32'): itk.ctype('float'),
                     np.dtype('float64'): itk.ctype('double')}

        PixelType = dtype_map[arr.dtype]
        Dimensions = len(arr.shape)
        ImageType = itk.Image[PixelType, Dimensions]

        itk_image = itk.PyBuffer[ImageType].GetImageViewFromArray(arr)
        return itk_image

    def ScalarsModified(self):
        self.GetPointData().GetScalars().Modified()
        self.__histogram_stats.Modified()

    def SetInputConnection(self, algorithm_output):
        self._algorithm_output = algorithm_output
        self.SetInputData(algorithm_output.GetProducer().GetOutputDataObject(0))

    def GetOutputPort(self):
        return self._algorithm_output

    def SetInputData(self, data_object):

        if self._algorithm_output is None:
            algorithm = vtk.vtkTrivialProducer()
            algorithm.SetOutput(data_object)
            self._algorithm_output = algorithm.GetOutputPort()

        self._image_data_object = data_object

        if self.__histogram_stats is None:
            self.__histogram_stats = vtk.vtkImageHistogramStatistics()

        # VTK-6
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            self.__histogram_stats.SetInputConnection(self._algorithm_output)
        else:
            self.__histogram_stats.SetInput(self._image_data_object)

    def SetFileName(self, filename):
        self._filename = filename

    def SetStencilData(self, stencil_data, owner=None):
        self.__stencil_owner = owner
        self.__stencil_data = stencil_data

    def GetStencilData(self):
        return self.__stencil_data

    def GetStencilDataOwner(self):
        return self.__stencil_owner

    def GetRank(self):
        rank = 3
        for i in self.GetRealImage().GetDimensions():
            if i == 1:
                rank -= 1
        return rank

    def GetMeasurementUnit(self):
        return self.GetDimensionInformation()[0].GetUnit()

    def GetXSlicePositions(self):
        return self.__x_values

    def GetYSlicePositions(self):
        return self.__y_values

    def GetZSlicePositions(self):
        return self.__z_values

    def SetXSlicePositions(self, val):
        self.__x_values = val

    def SetYSlicePositions(self, val):
        self.__y_values = val

    def SetZSlicePositions(self, val):
        self.__z_values = val

    def SetMeasurementUnitToMM(self):
        for dim in self.GetDimensionInformation():
            if isinstance(dim, Dimension):
                dim.SetUnit('mm')

    def GetHistogramStatistics(self):

        self.SetInputData(self._image_data_object)

        return self.__histogram_stats

    def ResetWindowLevelValues(self):

        # reset window/level dicom header values
        h = self.GetHistogramStatistics()
        h.Update()
        _min, _max = h.GetAutoRange()
        ds = self.GetDICOMHeader()
        ds.WindowWidth = '%0.1f' % (_max - _min)
        ds.WindowCenter = '%0.1f' % (old_div((_max + _min), 2.0))

    def SetHistogramStencilData(self, stencil_data):

        image = self._image_data_object

        # make sure stencil extents match image - generate a temporary stencil
        # if the extents don't match
        if stencil_data:
            if image.GetExtent() != stencil_data.GetExtent():
                new_stencil_data = vtk.vtkImageStencilData()
                new_stencil_data.SetExtent(image.GetExtent())
                new_stencil_data.AllocateExtents()
                new_stencil_data.Add(stencil_data)
                stencil_data = new_stencil_data

        # VTK-6
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            self.__histogram_stats.SetStencilData(stencil_data)
        else:
            self.__histogram_stats.SetStencil(stencil_data)

    def GetHistogramStencilData(self):
        return self.__histogram_stats.GetStencil()

    def GetFilename(self):
        return self._filename

    def pad_string(self, val):

        s = str(val)
        if len(s) % 2 == 1:
            s = ' ' + s
        return s

    def CopyInfo(self, input_image):

        # Copy dimensional information
        self._dimensions = input_image._dimensions

        # make sure current image header is set up
        if self._dicom_header is None:
            self.GetDICOMHeader()

        # Copy DICOM tags
        if input_image._dicom_header is not None:
            for tag in input_image._dicom_header:
                self._dicom_header[tag.tag] = tag

        # Copy non-DICOM keyword/value pairs
        header = input_image.GetHeader()
        for key in header:
            self._header[key] = header[key]

    def __str__(self):
        s = io.StringIO()
        s.write(str(self._image_data_object))
        s.write(str('\nFilename: {0}\n'.format(self._filename)))
        s.write(str('\nDICOM Header:\n'))
        self.UpdateDICOMHeader()
        s.write(str(self._dicom_header))
        return s.getvalue()

    def SetDefaultDimensionInformation(self, unit='pixels'):

        self.SetDimensionInformation(
            [Distance('x', unit=unit), Distance('y', unit=unit), Distance('z', unit=unit)])

    def GetDimensionInformation(self):

        return self._dimensions

    def SetDimensionInformation(self, dims):

        # we must be passed a list of Dimension objects
        assert(isinstance(dims, list))
        for i in dims:
            assert(isinstance(i, Distance))

        self._dimensions = dims

    def ClearDICOMHeader(self):
        """Generate default DICOM header for image"""

        header = self.GetHeader()

        # go for broke
        ds, info, header = self.dicom_converter.get_dcm_header(
            image=self._image_data_object,
            filename=self._filename,
            header=header)

        if ds.get('Manufacturer','') == '':
            # add some MicroView-specific tags
            ds.Manufacturer = 'Parallax Innovations'
            ds.file_meta.ImplementationClassUID += '.2.6.0'
            ds.file_meta.ImplementationVersionName = '2.6.0'

        return ds

    def Update(self):
        """Update the underlying vtkImageData object

        This exists to smooth over the backward-incompatible changes between VTK5 and VTK6"""
        logger.warning("We shouldn't call Update() on a MVImage object!")

        # if we're running interactively, hit a breakpoint here to help track down bad Update() calls
        import sys
        if not hasattr(sys, 'frozen'):
            import pdb; pdb.set_trace()

        if self.GetRealImage().GetExtent()[1] == -1:
            # force an update (no longer works with VTK 6.2)
            self._algorithm_output.GetProducer().Update()

    def UpdateInformation(self):
        # likely no longer works with VTK 6.2
        self._algorithm_output.GetProducer().UpdateInformation()

    def UpdateDICOMHeader(self):
        """Update DICOM header based on current image contents"""

        init_required = False

        if self._dicom_header is None:
            init_required = True
            self._dicom_header = self.ClearDICOMHeader()
            # the default patient orientation will work using VTK-style view of world
            # and is appropriate for an image of e.g. a prone animal
            self._dicom_header.ImageOrientationPatient = [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        mt = self._image_data_object.GetMTime()
        if self._dicom_mtime >= mt:
            return
        else:
            self._dicom_mtime = mt

        # Update information

        # TODO: port to VTK6
        # self._source.UpdateInformation()
        extent = self.GetExtent()
        spacing = self.GetSpacing()
        _min, _max = self.GetScalarRange()

        ds = self._dicom_header

        ds.BitsAllocated = self.GetScalarSize() * 8
        ds.BitsStored = ds.BitsAllocated

        ds.HighBit = ds.BitsStored - 1

        # 2016-07-20
        # This next line was disabled for RT-IMAGE modalities -- perhaps it
        # shouldn't be there at all
        #if ds.Modality != 'RTIMAGE':
        #    ds.PixelSpacing = ds.NominalScannedPixelSpacing = map(
        #        str, spacing[0:2])

        _type = self.GetScalarType()
        if _type in (vtk.VTK_UNSIGNED_CHAR, vtk.VTK_UNSIGNED_SHORT, vtk.VTK_UNSIGNED_INT, vtk.VTK_UNSIGNED_LONG):
            ds.PixelRepresentation = 0
        else:
            ds.PixelRepresentation = 1

        ##ds.SliceThickness = ascii(spacing[2])

        ds.Columns = extent[1] + 1
        ds.Rows = extent[3] + 1

        #ds.SpacingBetweenSlices = spacing[2]  # is this okay for all modalities?

        # is image data loaded from disk?
        if not((extent[1] == -1) and (extent[3] == -1)):
            if self.GetScalarType() < 10:

                if 'unsigned' in self.GetScalarTypeAsString():
                    vr_type = 'US'
                else:
                    vr_type = 'SS'

                ds.SmallestPixelValueInSeries = int(_min)
                ds[0x0028, 0x0108].VR = vr_type
                ds.LargestPixelValueInSeries = int(_max)
                ds[0x0028, 0x0109].VR = vr_type
                # only specify window center and width if it isn't already
                # present - default to 99% of data
                # window center and width apply _after_ rescale slope/intercept
                # are applied
                if 'WindowCenter' not in ds and 'RescaleSlope' in ds and 'RescaleIntercept' in ds:
                    _min = _min * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
                    _max = _max * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
                    self.SetHistogramStencilData(None)
                    stats = self.GetHistogramStatistics()
                    stats.SetAutoRangePercentiles(1, 99)
                    stats.Update()
                    _min, _max = stats.GetAutoRange()
                    ds.WindowCenter = ascii(int(old_div((_min + _max), 2.0)))
                    ds.WindowWidth = ascii(_max - _min)

        # remove PixelData if it exists
        if 'PixelData' in ds:
            del(ds.PixelData)

        # perhaps here we should update slice-by-slice data if it doesn't already exist?
        # re-generate slice-by-slice headers

        if init_required:
            slice_headers = self.GetSliceDICOMHeaders()
            slice_headers.set_meta_data(None)
            slice_headers.get_slice_dict().clear()
            slice_dict = slice_headers.get_slice_dict()

            slice_headers.set_meta_data(ds)

            # adjust slice info -- this should end up being generated on-the-fly
            for i in range(self.GetRealImage().GetDimensions()[2]):
                slice_dict[i] = pydicom.dataset.Dataset()
                slice_dict[i].InstanceNumber = int(ds.InstanceNumber) + i
                _split = ds.SOPInstanceUID.split('.')
                _base = '.'.join(_split[:-1])
                _num = _split[-1]

                # this is needed by MicroView's `default` image
                slice_dict[i].SOPInstanceUID = _base + '.' + str(int(_num) + i)
                #slice_dict[i].MediaStorageSOPInstanceUID = _base + '.' + str(int(_num) + i)

                pos = ds.ImagePositionPatient
                pos[2] += spacing[2] * i  # TODO: does direction cosines enter in here?
                slice_dict[i].ImagePositionPatient = pos
                slice_dict[i].SliceLocation = pos[2]
                slice_dict[i].InstancetNumber = i

            # remove SOPInstanceUID from top-level dicom ds
            if 'SOPInstanceUID' in ds:
                del ds.SOPInstanceUID

    def GetDirectionCosines(self):
        cosines = self.GetDICOMHeader().get('ImageOrientationPatient', None)
        if cosines:
            return np.array(list(map(float, cosines[0:3]))), np.array(list(map(float, cosines[3:6])))
        else:
            return np.array([1,0,0], dtype='float'), np.array([0,1,0], dtype='float')

    def GetDICOMHeader(self):
        self.UpdateDICOMHeader()
        return self._dicom_header

    def GetHeader(self):
        return self._header

    def SetHeader(self, header):
        self._header = header.copy()

    def GetExtent(self):
        return self._image_data_object.GetExtent()

    def GetSpacing(self):
        return self._image_data_object.GetSpacing()

    def GetScalarRange(self):
        return self._image_data_object.GetScalarRange()

    def GetScalarSize(self):
        return self._image_data_object.GetScalarSize()

    def GetNumberOfScalarComponents(self):
        return self._image_data_object.GetNumberOfScalarComponents()

    def GetScalarType(self):
        return self._image_data_object.GetScalarType()

    def GetScalarTypeAsString(self):
        return self._image_data_object.GetScalarTypeAsString()

    def __getattr__(self, attr):
        return getattr(self._image_data_object, attr)

    def GetRealImage(self):
        return self._image_data_object

    def GetDate(self):
        """Returns the date of the scan"""
        _d = ''
        for name in ['ContentDate', 'AcquisitionDate', 'SeriesDate', 'StudyDate']:
            if name in self._dicom_header:
                _d = str(self._dicom_header.get(name))
                if _d:
                    break
        return _d

    def GetTime(self):
        """Returns the time of the scan"""
        _d = ''
        for name in ['ContentTime', 'AcquisitionTime', 'SeriesTime', 'StudyTime']:
            if name in self._dicom_header:
                _d = str(self._dicom_header.get(name))
                if _d:
                    break
        return _d

    def GetModality(self):
        """returns DICOM modality"""
        return self._dicom_header.get('Modality', '')

    def GetShift(self):
        return self._dicom_header.RescaleIntercept

    def GetScale(self):
        return self._dicom_header.RescaleSlope

    def GetStudy(self):
        """return the study ID"""
        return self._dicom_header.StudyID

    def GetSeries(self):
        """return the study ID"""
        return self._dicom_header.SeriesNumber

    def GetPatientName(self):
        """return patient name"""
        return self._dicom_header.PatientName

    def GetPatientID(self):
        """return patient ID"""
        return self._dicom_header.PatientID

    def GetPatientAge(self):
        """return patient age"""
        try:
            return self._dicom_header.PatientAge
        except:
            return None

    def GetDescriptiveName(self):
        """Returns a descriptive name for the file reader"""
        return ''
