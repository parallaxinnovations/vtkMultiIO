# =========================================================================
#
# Copyright (c) 2000-2008 GE Healthcare
# Copyright (c) 2011-2015 Parallax Innovations Inc
#
# Use, modification and redistribution of the software, in source or
# binary forms, are permitted provided that the following terms and
# conditions are met:
#
# 1) Redistribution of the source code, in verbatim or modified
#   form, must retain the above copyright notice, this license,
#   the following disclaimer, and any notices that refer to this
#   license and/or the following disclaimer.
#
# 2) Redistribution in binary form must include the above copyright
#    notice, a copy of this license and the following disclaimer
#   in the documentation or with other materials provided with the
#   distribution.
#
# 3) Modified copies of the source code must be clearly marked as such,
#   and must not be misrepresented as verbatim copies of the source code.
#
# EXCEPT WHEN OTHERWISE STATED IN WRITING BY THE COPYRIGHT HOLDERS AND/OR
# OTHER PARTIES, THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE
# SOFTWARE "AS IS" WITHOUT EXPRESSED OR IMPLIED WARRANTY INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE.  IN NO EVENT UNLESS AGREED TO IN WRITING WILL
# ANY COPYRIGHT HOLDER OR OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
# THE SOFTWARE UNDER THE TERMS OF THIS LICENSE BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, LOSS OF DATA OR DATA BECOMING INACCURATE OR LOSS OF PROFIT OR
# BUSINESS INTERRUPTION) ARISING IN ANY WAY OUT OF THE USE OR INABILITY TO
# USE THE SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
#
# =========================================================================

#
# This file represents a derivative work by Parallax Innovations Inc.
#

"""
vtkMultiImageReader - an image reader that automatically creates an instance of an appropriate basic VTK
reader to perform image I/O, based on either the contents of the header of an inputted file, or the file
extension.  Think of it as a 'super' VTK image reader that understands all kinds of image formats.
"""


"""
Multiple file-type reader - Superclass which understands file extension types.

Use vtkMultiImageReader() as you would vtkDataSetReader().  Notable differences
include the method registerFileType.  In order to extend this class from the
default class, call registerFileType(extension, classname).
"""

import dicom
import os
import gc
import sys
import vtk
import logging
import collections
from zope import event
import vtkImageReaderBase
import _vtkMultiIO
import HeaderDictionary
from PI.dicom import convert

############################################################


class MyVTKDataSetReader(vtkImageReaderBase.vtkImageReaderBase):

    __extensions__ = {'.vtk': 'VTK'}
    __magic__ = [('# vtk', 0)]

    def __init__(self):
        vtkImageReaderBase.vtkImageReaderBase.__init__(self)
        self.SetImageReader(vtk.vtkDataSetReader())

    def CanReadFile(self, filename, magic=None):

        if not os.path.exists(filename):
            return 0

        try:
            self._ImageReader.SetFileName(filename)
            if self._ImageReader.IsFileStructuredPoints():
                return 1
        except:
            return 0


class MyXMLImageDataReader(vtkImageReaderBase.vtkImageReaderBase):

    __extensions__ = {'.vti': 'VTK'}
    __magic__ = [('# vtk', 0)]

    def __init__(self):
        vtkImageReaderBase.vtkImageReaderBase.__init__(self)
        self.SetImageReader(vtk.vtkXMLImageDataReader())

    def CanReadFile(self, filename, magic=None):

        if not os.path.exists(filename):
            return 0

        try:
            return self._ImageReader.CanReadFile(filename)
        except:
            return 0


############################################################


class MyMetaImageReader(vtkImageReaderBase.vtkImageReaderBase):

    __extensions__ = {'.mha': 'UNC Meta', '.mhd': 'UNC Meta'}
    __magic__ = [('ObjectType =', 0)]

    def __init__(self):
        vtkImageReaderBase.vtkImageReaderBase.__init__(self)
        self.SetImageReader(vtk.vtkMetaImageReader())
        self._converter = convert.VFFToDicomConverter()

    def SetFileName(self, filename):

        vtkImageReaderBase.vtkImageReaderBase.SetFileName(self, filename)
        self.SetMeasurementUnitToMM()
        self.UpdateDICOMHeaderInfo(filename)

    def UpdateDICOMHeaderInfo(self, filename):

        vtkImageReaderBase.vtkImageReaderBase.UpdateDICOMHeaderInfo(
            self, filename)

        # re-read metafile header - it may contain additional DICOM tags (MicroView specific)
        header = {}

        try:
            with open(filename, 'rt') as _f:
                for line in _f:
                    key, value = [s.strip() for s in line.split('=', 1)]
                    if key.startswith('dicom_'):
                        header[key] = value
        except:
            pass

        ds = self.GetOutput().GetDICOMHeader()
        self._converter.convert_canonical_tags(ds, header)

############################################################


class MyPNMImageReader(vtkImageReaderBase.vtkImageReaderBase):

    __extensions__ = {'.pnm': 'Portable pixmap', '.ppm':
                      'Portable pixmap', '.pbm': 'Portable pixmap'}
    __magic__ = [('', 0)]

    def __init__(self):
        vtkImageReaderBase.vtkImageReaderBase.__init__(self)
        self.SetImageReader(vtk.vtkPNMReader())

############################################################


class MyBMPImageReader(vtkImageReaderBase.vtkImageReaderBase):

    __extensions__ = {'.bmp': 'Windows bitmap'}
    __magic__ = [('\x42\x4d', 0)]

    def __init__(self):
        vtkImageReaderBase.vtkImageReaderBase.__init__(self)
        self.SetImageReader(vtk.vtkBMPReader())

############################################################


class MyMINCImageReader(vtkImageReaderBase.vtkImageReaderBase):

    __extensions__ = {'.mnc': 'MINC'}
    __magic__ = [('CDF', 0)]

    def __init__(self):
        vtkImageReaderBase.vtkImageReaderBase.__init__(self)
        self.SetImageReader(vtk.vtkMINCImageReader())

    def SetFileName(self, filename):

        vtkImageReaderBase.vtkImageReaderBase.SetFileName(self, filename)
        self.SetMeasurementUnitToMM()

############################################################


class MySLCImageReader(vtkImageReaderBase.vtkImageReaderBase):

    __extensions__ = {'.slc': 'SLC'}
    __magic__ = [('', 0)]

    def __init__(self):
        vtkImageReaderBase.vtkImageReaderBase.__init__(self)
        self.SetImageReader(vtk.vtkSLCReader())

    def CanReadFile(self, filename, magic=None):

        if not os.path.exists(filename):
            return 0

        if os.path.splitext(filename.lower())[-1] == '.slc':
            return 1
        else:
            return 0

############################################################


class vtkMultiImageReader(object):

    def __init__(self):
        self._extension_map = {}
        self._wholefilename_map = {}
        self._reader = None
        self._method = {}
        self._header = None
        self._dimensions = None
        self._usemm = 'pixel'

        self._reader_classname = None

        # register file types
        self.registerFileTypes()

    def __del__(self):
        print 'deleting {0}'.format(self.__class__)
        self.tearDown()

    def tearDown(self):

        self._method = {}
        self._reader = None
        self._header = None
        self._extension_map = {}
        self._wholefilename_map = {}

    def SetCoordinateSystem(self, val):
        self._reader.SetCoordinateSystem(val)

    def GetCoordinateSystem(self):
        return self._reader.GetCoordinateSystem()

    def clear_reader(self):
        self._reader = None
        gc.collect()

    def registerFileTypes(self):

        # These are the only built-in image readers that are guaranteed to
        # exist
        self.registerFileType({'.vtk': 'VTK'}, MyVTKDataSetReader, [('# vtk', 0)], (
            vtkImageReaderBase.DEPTH_8 | vtkImageReaderBase.DEPTH_16 | vtkImageReaderBase.DEPTH_32 |
            vtkImageReaderBase.DEPTH_64 | vtkImageReaderBase.IMAGE_2D | vtkImageReaderBase.IMAGE_3D))
        self.registerFileType({'.vti': 'VTK'}, MyXMLImageDataReader, [('', 0)], (
            vtkImageReaderBase.DEPTH_8 | vtkImageReaderBase.DEPTH_16 | vtkImageReaderBase.DEPTH_32 |
            vtkImageReaderBase.DEPTH_64 | vtkImageReaderBase.IMAGE_2D | vtkImageReaderBase.IMAGE_3D))
        self.registerFileType({'.pnm': 'Portable pixmap', '.ppm': 'Portable pixmap', '.pbm': 'Portable pixmap'}, MyPNMImageReader, [
                              ('', 0)], (vtkImageReaderBase.DEPTH_8 | vtkImageReaderBase.IMAGE_2D), 0)
        self.registerFileType({'.bmp': 'Windows bitmap'}, MyBMPImageReader, [(
            '\x42\x4d', 0)], (vtkImageReaderBase.DEPTH_8 | vtkImageReaderBase.IMAGE_2D), 0)
        self.registerFileType({'.mha': 'UNC Meta', '.mhd': 'UNC Meta'}, MyMetaImageReader, [('ObjectType =', 0)], (
            vtkImageReaderBase.DEPTH_8 | vtkImageReaderBase.DEPTH_16 | vtkImageReaderBase.DEPTH_32 |
            vtkImageReaderBase.DEPTH_64 | vtkImageReaderBase.IMAGE_2D | vtkImageReaderBase.IMAGE_3D))
        self.registerFileType({'.slc': 'SLC'}, MySLCImageReader, [('', 0)], (
            vtkImageReaderBase.DEPTH_8 | vtkImageReaderBase.DEPTH_16 | vtkImageReaderBase.DEPTH_32 |
            vtkImageReaderBase.DEPTH_64 | vtkImageReaderBase.IMAGE_3D))

        # Register MINC
        if 'vtkMINCImageReader' in dir(vtk):
            self.registerFileType({'.mnc': 'MINC'}, MyMINCImageReader, [('CDF', 0)], (
                vtkImageReaderBase.DEPTH_8 | vtkImageReaderBase.DEPTH_16 | vtkImageReaderBase.DEPTH_32 | vtkImageReaderBase.IMAGE_3D))

    def GetClassName(self):
        return "vtkMultiImageReader"

    def SetHeader(self, header):
        """Sets an image header dictionary"""
        if hasattr(self._reader, "SetHeader"):
            self._reader.SetHeader(header)
        else:
            self._header = HeaderDictionary.HeaderDictionary(header)

    def GetHeader(self):
        """returns header dictionary"""

        if hasattr(self._reader, "GetHeader"):
            return self._reader.GetHeader()
        else:
            if self._header is None:
                self._header = HeaderDictionary.HeaderDictionary()
            return self._header

    def GetDICOMHeader(self):
        """Get DICOM header for image"""
        if hasattr(self._reader, "GetDICOMHeader"):
            return self._reader.GetDICOMHeader()
        else:
            logging.error("reader is missing GetDICOMHeader")
            return vtkImageReaderBase.vtkImageReaderBase().GetDICOMHeader()

    # TODO: Check that the next two methods are needed by VTK-6 port

    def UpdateInformation(self):
        self._reader.UpdateInformation()

    def Update(self):
        self._reader.Update()

    def registerFileType(self, extensions, classname, magic, capabilities, usemm=1):
        """
        extension is a dictionary similar to PIL.Image.EXTENSION dictionary
        """
        # iterate over all extensions
        for e in extensions:
            e_lower = e.lower()
            if e_lower not in self._extension_map:
                self._extension_map[e_lower] = []

            self._extension_map[e_lower].append((extensions[
                e] + ' file', classname, magic, capabilities, usemm))

    def registerWholeFileName(self, extensions, classname, capabilities):

        for i in extensions:
            filename = i.lower()
            description = extensions[i]

            if filename not in self._wholefilename_map:
                self._wholefilename_map[filename] = []

            self._wholefilename_map[filename].append((
                description + ' file', classname, capabilities))

    def SetWholeName(self, filename):

        # convert filename to given locale
        if isinstance(filename, unicode):
            filename = filename.encode(sys.getfilesystemencoding() or 'UTF-8')

        f = filename.lower()
        if (f in self._wholefilename_map):
            if (self._reader != None):
                self._reader = None

            description, classname, capabilities = self._wholefilename_map[
                f][0]
            self._reader = classname()
            self._reader_classname = classname
            self._header = None

            # If any Progress methods have been registered, attach them now
            for k in self._method.keys():
                for meth in self._method[k][:]:
                    self._reader.AddObserver(k, meth)
            return True
        else:
            return False

    def SetFileDimensionality(self, dims):
        # not all readers can handle 2D/3D image differences
        if hasattr(self._reader, 'SetFileDimensionality'):
            return self._reader.SetFileDimensionality(dims)

    def SetDataSpacing(self, *spacing):
        return self._reader.SetDataSpacing(*spacing)

    def SetDataExtent(self, *extent):
        return self._reader.SetDataExtent(*extent)

    def GetDataByteOrder(self):
        return self._reader.GetDataByteOrder()

    def SetExtension(self, ext, filename):

        # convert filename to given locale
        if isinstance(filename, unicode):
            filename = filename.encode(sys.getfilesystemencoding() or 'UTF-8')

        # Start by trying to perform the mapping by checking for a magic number
        classname, reader = self.SetReaderByMagicNumber(filename)

        if classname is not None:
            if self._reader is not None:
                if self._reader.GetOutput():
                    self._reader.GetOutput().ReleaseData()
                self._reader = None
            self._reader_classname = classname
            self._reader = reader
            self._header = None
        else:
            return False

        # If any Progress methods have been registered, attach them now
        for k in self._method.keys():
            for meth in self._method[k][:]:
                self._reader.AddObserver(k, meth)
        return True

    def SetReaderByMagicNumber(self, filename):

        # convert filename to given locale
        if isinstance(filename, unicode):
            filename = filename.encode(sys.getfilesystemencoding() or 'UTF-8')

        keys = self._extension_map.keys()
        keys.sort()

        # examine most likely classes first
        base, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext in keys:
            keys.remove(ext)
            keys.insert(0, ext)

        classname_list = []

        for extension in keys:

            for entry in self._extension_map[extension]:

                description, classname, magic, _capabilities, usemm = entry

                # have we examined this type of class already?
                if classname in classname_list:
                    continue

                classname_list.append(classname)

                if hasattr(classname, 'CanReadFile'):

                    reader = classname()
                    if reader.CanReadFile(filename) > 0:
                        self._usemm = usemm
                        return (classname, reader)
                else:
                    # rely on code in vtkImageReaderBase
                    if vtkImageReaderBase.vtkImageReaderBase().CanReadFile(filename, magic=magic) > 0:
                        self._usemm = usemm
                        return (classname, classname())

        return None, None

    def SetFilePattern(self, pat):

        # convert filename to given locale
        if isinstance(pat, unicode):
            pat = pat.encode(sys.getfilesystemencoding() or 'UTF-8')

        if (self._reader == None):
            logging.error("Set extension first")
            return

        # And call it's SetFilePattern() method
        return self._reader.SetFilePattern(pat)

    def SetFilePrefix(self, prefix):

        # convert filename to given locale
        if isinstance(prefix, unicode):
            prefix = prefix.encode(sys.getfilesystemencoding() or 'UTF-8')

        if (self._reader == None):
            logging.error("Set extension first")
            return

        # And call it's SetFilePrefix() method
        return self._reader.SetFilePrefix(prefix)

    def SetFileNames(self, filename_array, **kw):
        """load image from a collection of slices"""

        self._header = None

        # extract first filename from array
        filename = filename_array.GetValue(0)

        # convert filename to given locale
        if isinstance(filename, unicode):
            filename = filename.encode(sys.getfilesystemencoding() or 'UTF-8')

        # adjust reader so it understands the first file slice
        extension = os.path.basename(filename).lower().split('.')[-1]
        ret = self.SetExtension(extension, filename)

        # And call it's SetFileNames() method
        if not ret:
            logging.error("Unable to load images")
            return ret
        else:
            ret = self._reader.SetFileNames(filename_array, **kw)
            if ret is None:
                ret = True
            return ret

    def SetFileName(self, filename, **kw):

        self._header = None

        # convert filename to given locale
        if isinstance(filename, unicode):
            filename = filename.encode(sys.getfilesystemencoding() or 'UTF-8')

        temp = os.path.basename(filename).lower()

        # attempt to map by the whole filename
        ret = self.SetWholeName(temp)

        # if this fails, map by the file's extension
        if not ret:
            extension = temp.split('.')[-1]
            ret = self.SetExtension(extension, filename)

        # And call it's SetFileName() method
        if not ret:
            logging.error("Unable to load %s" % filename)
            return ret
        else:
            ret = self._reader.SetFileName(filename, **kw)
            if ret is None:
                ret = True
            return ret

    def GetFileName(self):
        if hasattr(self._reader, 'GetFileName'):
            return self._reader.GetFileName()
        else:
            return 'unknown'

    def SetOutput(self, output):
        if hasattr(self._reader, 'SetOutput'):
            return self._reader.SetOutput(output)
        else:
            return None

    def GetOutput(self):
        return self._reader.GetOutput()

    def GetOutputPort(self):
        return self._reader.GetOutputPort()

    def __repr__(self):
        """
        Return the readers registered
        """
        return str(self._extension_map)

    def GetExtensions(self):
        return self._extension_map.keys()

    def GetDataSpacing(self):
        try:
            ret = self._reader.GetDataSpacing()
        except:
            ret = self._reader.GetOutput().GetSpacing()
        return ret

    def AddObserver(self, event, method):
        if (not event in self._method):
            self._method[event] = []
        self._method[event].append(method)
        if (self._reader != None):
            return self._reader.AddObserver(event, method)

    def GetMatchingFormatStrings(self, capabilities=0):
        formats = collections.OrderedDict()
        keys = self._extension_map.keys()
        keys.sort()
        for extension in keys:
            for entry in self._extension_map[extension]:
                description, classname, magic, _capabilities, usemm = entry

                if extension.startswith('.'):
                    val = '*' + extension
                else:
                    val = extension

                if (capabilities == 0) or ((_capabilities & capabilities) == capabilities):
                    if description not in formats:
                        formats[description] = []
                    formats[description].append(val)
        return formats

    def GetReaderClassName(self):
        if self._reader_classname is None:
            return None
        else:
            return self._reader_classname.__name__

    def SetProgressText(self, text):
        self._reader.SetProgressText(text)
