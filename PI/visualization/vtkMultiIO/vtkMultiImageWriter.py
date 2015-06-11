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
Multiple file-type writer - Superclass which understands file extension types.

Use vtkMultiImageWriter() as you would vtkDataSetWriter().  Notable differences
include the method registerFileType.  In order to extend this class from the
default class, call registerFileType(extension, classname).
"""

import collections
import os
import logging
import sys
import vtk
import vtkImageWriterBase
import _vtkMultiIO

from PI.visualization.vtkMultiIO import MVImage
from PI.visualization.vtkMultiIO import vtkImageWriterBase


class MyVTKDataSetWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.vtk': 'VTK'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(vtk.vtkDataSetWriter())

############################################################


class MyMetaImageWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.mha': 'UNC Meta', '.mhd': 'UNC Meta'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(vtk.vtkMetaImageWriter())

    def Write(self):

        # write image
        self._ImageWriter.Write()

        # adjust header values
        filename = self._ImageWriter.GetFileName()
        header = collections.OrderedDict()

        try:
            with open(filename, 'rt') as _f:
                for line in _f:
                    key, value = [s.strip() for s in line.split('=', 1)]
                    header[key] = value
        except:
            pass

        # migrate DICOM values as well
        header2 = self.ConvertTags(self.GetDICOMHeader())

        try:
            with open(filename, 'wt') as _f:
                for key in header:
                    _f.write("{0} = {1}\n".format(key, header[key]))
                for key in header2:
                    _f.write("{0} = {1}\n".format(key, header2[key]))
        except:
            pass

############################################################


class MyPNMImageWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.pnm': 'Portable pixmap', '.ppm':
                      'Portable pixmap', '.pbm': 'Portable pixmap'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(vtk.vtkPNMWriter())

############################################################


class MyBMPImageWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.bmp': 'Windows bitmap'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(vtk.vtkBMPWriter())

############################################################


class MyMINCImageWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.mnc': 'MINC'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(vtk.vtkMINCImageWriter())

############################################################


class MyTIFFWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.tif': 'TIFF', '.tiff': 'TIFF'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(vtk.vtkTIFFWriter())

    def SetupWriter(self):
        self._ImageWriter.SetCompressionToNoCompression()

############################################################


class MyPNGWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.png': 'PNG'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(vtk.vtkPNGWriter())

############################################################


class MyJPEGWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.jpg': 'JPEG', '.jpeg': 'JPEG'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(vtk.vtkJPEGWriter())

############################################################


class MyVFFWriter(vtkImageWriterBase.vtkImageWriterBase):

    __extensions__ = {'.vff': 'VFF'}

    def __init__(self):
        vtkImageWriterBase.vtkImageWriterBase.__init__(self)
        self.SetImageWriter(_vtkMultiIO.vtkVFFWriter())

    def SetInput(self, image):

        vtkImageWriterBase.vtkImageWriterBase.SetInput(self, image)

        # migrate DICOM values to vff header values here
        header = self.ConvertTags(self.GetDICOMHeader())
        for key in header:
            try:
                self.SetKeyword(key, header[key])
            except Exception, e:
                logging.error("Unable to convert tag {0}".format(name))

############################################################


class vtkMultiImageWriter(object):

    def __init__(self):
        self._extension_map = {}
        self._wholefilename_map = {}
        self._writer = vtk.vtkDataSetWriter()
        self._writer.SetFileTypeToBinary()
        self._observers = {}
        self._date = ""
        self._time = ""
        self._observer_id = 0
        self._ds = None

        # register file types
        self.registerFileTypes()

    def SetInput(self, image):

        if image:
            if isinstance(image, MVImage.MVImage):
                ds = image.GetDICOMHeader()
                header = image.GetHeader()
                ##image = image.GetRealImage()
                # might as well set header from this
                self.SetDICOMHeader(ds)
                self.SetHeader(header)

        # a TIFF hack -- TIFF writer needs unsigned shorts rather than signed
        # shorts
        if image and self._writer.GetClassName() in ('vtkTIFFWriter',):
            if image.GetScalarTypeAsString() == 'short':
                cast = vtk.vtkImageCast()
                cast.SetInput(image)
                cast.SetOutputScalarTypeToUnsignedShort()
                image = cast.GetOutput()

        self._writer.SetInput(image)

    def registerFileTypes(self):

        # These are the only built-in image writers that are guaranteed to
        # exist
        self.registerFileType({'.vtk': 'VTK'}, MyVTKDataSetWriter, (
            vtkImageWriterBase.DEPTH_8 | vtkImageWriterBase.DEPTH_16 | vtkImageWriterBase.DEPTH_32 |
            vtkImageWriterBase.IMAGE_3D))
        self.registerFileType({'.pnm': 'Portable anymap',
                               '.ppm': 'Portable pixmap',
                               '.pbm': 'Portable bitmap'}, MyPNMImageWriter,
                              (vtkImageWriterBase.DEPTH_8 | vtkImageWriterBase.IMAGE_2D))
        self.registerFileType({'.tiff': 'TIFF', '.tif': 'TIFF'}, MyTIFFWriter, (
            vtkImageWriterBase.DEPTH_8 | vtkImageWriterBase.DEPTH_16 | vtkImageWriterBase.IMAGE_2D))
        self.registerFileType({'.png': 'PNG'}, MyPNGWriter, (
            vtkImageWriterBase.DEPTH_8 | vtkImageWriterBase.IMAGE_2D))
        self.registerFileType({'.jpg': 'JPEG', '.jpeg': 'JPEG'}, MyJPEGWriter, (
            vtkImageWriterBase.DEPTH_8 | vtkImageWriterBase.IMAGE_2D))
        self.registerFileType({'.bmp': 'Windows BMP'}, MyBMPImageWriter, (
            vtkImageWriterBase.DEPTH_8 | vtkImageWriterBase.IMAGE_2D))
        self.registerFileType({'.mhd': 'UNC Meta', '.mha': 'UNC Meta'}, MyMetaImageWriter, (
            vtkImageWriterBase.DEPTH_8 | vtkImageWriterBase.DEPTH_16 | vtkImageWriterBase.DEPTH_32 |
            vtkImageWriterBase.IMAGE_3D))

        # Register VFF
        self.registerFileType({'.vff': 'VFF'}, MyVFFWriter, (
            vtkImageWriterBase.DEPTH_8 | vtkImageWriterBase.DEPTH_16 | vtkImageWriterBase.DEPTH_32 |
            vtkImageWriterBase.IMAGE_2D | vtkImageWriterBase.IMAGE_3D))

    def Write(self):
        """Write the image to disk - capture and forward VTK errors as python errors"""
        self._writer.Write()
        if hasattr(self._writer, 'GetErrorCode'):
            code = self._writer.GetErrorCode()
            if code > 0:
                errmessage = {1: 'File Not Found Error',
                              2: 'Cannot Open File Error',
                              3: 'Unrecognized FileType Error',
                              4: 'Premature End of File Error',
                              5: 'File Format Error',
                              6: 'No FileName Error',
                              7: 'Out of Disk Space Error',
                              8: 'Unknown Error'}[code]
                raise IOError(code, errmessage)

    def GetClassName(self):
        return "vtkMultiImageWriter"

    def registerFileType(self, extensions, classname, capabilities):

        # iterate over all extensions
        for e in extensions:
            e_lower = e.lower()
            if e_lower not in self._extension_map:
                self._extension_map[e_lower] = []

            self._extension_map[e_lower].append(
                (extensions[e] + ' file', classname, capabilities))

    def registerWholeFileName(self, extensions, classname, capabilities):

        for i in extensions:
            filename = i.lower()
            description = extensions[i]

            if filename not in self._wholefilename_map:
                self._wholefilename_map[filename] = []

            self._wholefilename_map[filename].append((
                description + ' file', classname, capabilities))

    def SetWholeName(self, filename):
        f = filename.lower()
        if (f in self._wholefilename_map):
            if (self._writer != None):
                self._writer = None
            self._writer = self._wholefilename_map[f]()
            self._writer.SetupWriter()
            # If any Progress methods have been registered, attach them now
            for val in self._observers.values():
                self._writer.AddObserver(val[0], val[1])
            return True
        else:
            return False

    def SetWriterByFileExtension(self, filename):

        flower = filename.lower()

        self._writer = None

        for entry in self._extension_map:
            if flower.endswith(entry):
                self._writer = self._extension_map[entry][0][1]()

        if self._writer is None:
            raise AttributeError(
                'Unknown file extension. Please re-enter filename with an explicit extension.')

        self._writer.SetupWriter()

        # Handle built-in type initializations
        if self._writer.IsA('vtkDataSetWriter'):
            self._writer.SetFileTypeToBinary()

        # If any Progress methods have been registered, attach them now
        for val in self._observers.values():
            self._writer.AddObserver(val[0], val[1])
        return True

    def SetFileName(self, filename):

        if type(filename) is unicode:
            filename = filename.encode(sys.getfilesystemencoding() or 'UTF-8')

        temp = os.path.basename(filename).lower()

        # attempt to map by the whole filename
        ret = self.SetWholeName(temp)

        # if this fails, map by the file's extension
        if not ret:
            ret = self.SetWriterByFileExtension(filename)

        # And call it's SetFileName() method
        ret = self._writer.SetFileName(filename)

        self._writer.SetupWriter()

        return ret

    def __getattr__(self, attr):
        return getattr(self._writer, attr)

    def GetExtensions(self):
        return self._extension_map.keys()

    def AddObserver(self, event, method):
        self._observer_id += self._observer_id
        index = self._observer_id
        self._observers[self._observer_id] = (event, method)
        if self._writer is not None:
            index = self._writer.AddObserver(event, method)
        return index

    def RemoveObserver(self, handle):
        del(self._observers[handle])
        if self._writer is not None:
            self._writer.RemoveObserver(handle)

    def SetDICOMHeader(self, ds):
        if hasattr(self._writer, 'SetDICOMHeader'):
            # let image writer handle DICOM tags directly
            self._writer.SetDICOMHeader(ds)
        elif hasattr(self._writer, 'SetKeyword'):
            # extract useful DICOM tags and convert to keyword/value pairs
            for tag in ds:
                if tag.VR in ('DA', 'TM', 'UI', 'SH', 'CS', 'LO', 'PN', 'UL', 'DS', 'IS', 'FD'):
                    try:
                        name = 'dicom_' + \
                            tag.name.replace(' ', '').replace("'", '')
                        value = str(tag.value)
                        if tag.name not in ('Group Length', 'SOP Class UID'):
                            if tag.VR in ('DA', 'TM'):
                                value = "'" + value + "'"
                            self.SetKeyword(name, value)
                    except:
                        logging.exception("vtkMultiImageWriter")

    def SetHeader(self, v):

        # if writer has a '_SetHeader()' method, then call it directly
        # otherwise, if writer has 'SetKeyword', call method for each
        # keyword
        if hasattr(self._writer, '_SetHeader'):
            self._writer._SetHeader(v)
        elif hasattr(self._writer, 'SetKeyword'):
            for i in v:
                # ignore lists
                if not isinstance(v[i], list):
                    try:
                        self._writer.SetKeyword(i, str(v[i]))
                    except:
                        pass

    def GetMatchingFormatStrings(self, capabilities=0):
        formats = collections.OrderedDict()
        keys = self._extension_map.keys()
        keys.sort()
        for extension in keys:
            for entry in self._extension_map[extension]:
                description, classname, _capabilities = entry

                if extension.startswith('.'):
                    val = '*' + extension
                else:
                    val = extension

                if (capabilities == 0) or ((_capabilities & capabilities) == capabilities):
                    if description not in formats:
                        formats[description] = []
                    formats[description].append(val)

        return formats
