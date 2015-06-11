import copy
import cStringIO
import dicom
import dicom.dataset
from enum import Enum
import os
import time
import interfaces
import vtk
import logging
from vtk.util.numpy_support import vtk_to_numpy
from zope import interface
from PI.visualization.common.CoordinateSystem import CoordinateSystem
from PI.dicom.convert import BaseDicomConverter

class Dimension(object):

    """An object representing on of the dimensions of a data-type"""

    interface.implements(interfaces.IDimension)

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

        s = cStringIO.StringIO()
        s.write('Dimension: "{0}" (a {1}) measured in {2}\n'.format(
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


class MVImage(object):

    """
    A python object that connects a DICOM dictionary of header info and dimension
    information with a VTK-style image.  Also bridges the gap between VTK4 and VTK6.
    """

    interface.implements(interfaces.IDimensionInformation)

    def __init__(self, image_data, **kw):

        # for zope
        self.__component_name__ = u''

        self._algorithm = None
        self._image_data_object = image_data
        self.__reference_count = 1
        self.__x_values = None
        self.__y_values = None
        self.__z_values = None

        self._header = {}  # header values that don't map to DICOM easily
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
        self._dicom_slice_headers = []  # slice-by-slice dicom headers (buffer)
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

    def SetSliceDICOMHeader(self, idx, ds):
        if isinstance(ds, dicom.dataset.Dataset):
            # save slice headers as strings
            dcm_buffer = cStringIO.StringIO()
            ds.save_as(dcm_buffer)
            ds = dcm_buffer.getvalue()
        self._dicom_slice_headers[idx] = ds

    def GetSliceDICOMHeader(self, idx):
        """Return DICOM dictionary for a given slice or None if nothing exists"""
        try:
            dicom_header = dicom.read_file(cStringIO.StringIO(self._dicom_slice_headers[idx]))
        except:
            dicom_header = self._dicom_header  # return default header

        return self.fix_dicom(dicom_header)

    def fix_dicom(self, dicom_header):

        return dicom_header

        # tweak dicom info here if needed
        # TODO: can we retire this?

        # we need a valid (non-blank) patient ID
        patient_id = dicom_header.get('PatientID', '')
        if not patient_id:
            logging.info("Inserting missing PatientID value")
            if self._filename:
                patient_id = os.path.split(self._filename)[-1]
            else:
                patient_id = 'MICROVIEW^USER^000'
            dicom_header.PatientID = patient_id

        # we need a patient birth date (default is 0)
        patient_bdate = dicom_header.get('PatientBirthDate', '')
        if not patient_bdate:
            logging.info("Inserting missing PatientBirthDate value")
            patient_bdate = '10010101'
            dicom_header.PatientBirthDate = patient_bdate

        # we need a patient gender (default to 'other')
        patient_sex = dicom_header.get('PatientSex', '')
        if not patient_sex:
            logging.info("Inserting missing PatientSex value")
            patient_sex = 'O'
            dicom_header.PatientSex = patient_sex

        # we need a referring physician
        referring_physician = dicom_header.get('ReferringPhysicianName', '')
        if not referring_physician:
            logging.info("Inserting missing ReferringPhysicianName value")
            referring_physician = '?'
            dicom_header.ReferringPhysicianName = referring_physician

        # add a valid (non-blank) patient Name for good measure
        patient_name = dicom_header.get('PatientName', '')
        if not patient_name:
            logging.info("Inserting missing PatientName value")
            if self._filename:
                patient_name = os.path.split(self._filename)[-1]
            else:
                patient_name = 'MICROVIEW^USER'
            dicom_header.PatientName = patient_name

        # we need a valid (non-blank) study instance UID
        study_iuid = dicom_header.get('StudyInstanceUID', '')
        if not study_iuid:
            # lifted from convert.py
            t = time.time()
            study_iuid = self.parallax_base_uid + \
                '.' + str(int(self.station_id)) + '.' + str(t)
            dicom_header.StudyInstanceUID = study_iuid
            logging.info("Inserting missing StudyInstanceUID value")

        study_id = dicom_header.get('StudyID', '')
        if not study_id:
            study_id = 'MICROVIEW^STUDY'
            dicom_header.StudyID = study_id

        # we need a valid (non-blank) series instance UID
        series_iuid = dicom_header.get('SeriesInstanceUID', '')
        if not series_iuid:
            # lifted from convert.py
            sn = '1'
            # an 'unknown' image
            series_iuid = study_iuid + '.' + sn + '.99'
            dicom_header.SeriesInstanceUID = series_iuid
            logging.info("Inserting missing SeriesInstanceUID value")

        return dicom_header

    def GetDICOMImage(self, idx):

        # start by grabbing dicom header (deep copy)
        ds = copy.deepcopy(self.GetSliceDICOMHeader(idx))

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

    def ScalarsModified(self):
        self.GetPointData().GetScalars().Modified()
        self.__histogram_stats.Modified()

    def SetInputConnection(self, algorithm):
        self._algorithm = algorithm
        self.SetInputData(algorithm.GetProducer().GetOutputDataObject(0))

    def GetOutputPort(self):
        return self._algorithm

    def SetInputData(self, data_object):

        if self._algorithm is None:
            self._algorithm = vtk.vtkTrivialProducer()
            self._algorithm.SetOutput(data_object)

        self._image_data_object = data_object

        if self.__histogram_stats is None:
            self.__histogram_stats = vtk.vtkImageHistogramStatistics()

        # VTK-6
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            self.__histogram_stats.SetInputConnection(self._algorithm)
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
        ds.WindowCenter = '%0.1f' % ((_max + _min) / 2.0)

    def SetHistogramStencil(self, stencil_data):

        # VTK-6
        if vtk.vtkVersion().GetVTKMajorVersion() > 5:
            self.__histogram_stats.SetStencilData(stencil_data)
        else:
            self.__histogram_stats.SetStencil(stencil_data)

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
        for tag in input_image._dicom_header:
            self._dicom_header[tag.tag] = tag

        # Copy non-DICOM keyword/value pairs
        header = input_image.GetHeader()
        for key in header:
            self._header[key] = header[key]

    def __str__(self):

        s = cStringIO.StringIO()
        s.write(str(self._image_data_object))
        s.write('\nFilename: {0}\n'.format(self._filename))
        s.write('\nDICOM Header:\n')
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
            ds.file_meta.ImplementationClassUID += '.2.5.0'
            ds.file_meta.ImplementationVersionName = '2.5.0'

        return ds

    def Update(self):
        """Update the underlying vtkImageData object

        This exists to smooth over the backward-incompatible changes between VTK5 and VTK6"""
        logging.warning("We shouldn't call Update() on a MVImage object!")

        if self.GetRealImage().GetExtent()[1] == -1:
            # force an update
            self._algorithm.GetProducer().Update()

    def UpdateInformation(self):
        self._algorithm.GetProducer().UpdateInformation()

    def UpdateDICOMHeader(self):
        """Update DICOM header based on current image contents"""

        if self._dicom_header is None:
            self._dicom_header = self.ClearDICOMHeader()

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
        ds.PixelSpacing = ds.NominalScannedPixelSpacing = map(
            str, spacing[0:2])
        ds.PixelRepresentation = 1
        ds.SliceThickness = str(spacing[2])
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        ds.Columns = extent[1] + 1
        ds.Rows = extent[3] + 1

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
                if 'WindowCenter' not in ds:
                    self.SetHistogramStencil(None)
                    stats = self.GetHistogramStatistics()
                    stats.SetAutoRangePercentiles(1, 99)
                    stats.Update()
                    _min, _max = stats.GetAutoRange()
                    ds.WindowCenter = str(int((_min + _max) / 2.0))
                    ds.WindowWidth = str(_max - _min)

        # remove PixelData if it exists
        if 'PixelData' in ds:
            del(ds.PixelData)

    def GetDICOMHeader(self):
        self.UpdateDICOMHeader()
        #self._dicom_header = self.fix_dicom(self._dicom_header)
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
        return self._dicom_header.Modality

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
