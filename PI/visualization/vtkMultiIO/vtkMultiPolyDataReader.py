# =========================================================================
#
# Copyright (c) 2000-2008 GE Healthcare
# Copyright (c) 2011-2015 Parallax Innovations Inc.
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
Multiple file-type reader - Superclass which understands file extension types.

Use vtkMultiPolyDataReader() as you would vtkPolyDataReader().  Notable differences
include the method registerFileType.  In order to extend this class from the
default class, call registerFileType(extension, classname).
"""

import collections
import os
import sys
import vtk
import logging


class vtkMultiPolyDataReader(object):

    def __init__(self):
        self._extension_map = {}
        self._all_readers = []
        self._reader = vtk.vtkPolyDataReader()

        # register file types
        self.registerFileTypes()

    def GetClassName(self):
        return "vtkMultiPolyDataReader"

    def registerFileTypes(self):

        # Add built in readers
        try:
            self.registerFileType({'.vtk': 'VTK'}, vtk.vtkDataSetReader)
        except:
            logging.error("Unable to find vtkDataSetReader")
        try:
            self.registerFileType({'.obj': 'Wavefront OBJ'}, vtk.vtkOBJReader)
        except:
            logging.error("Unable to find vtkOBJReader")
        try:
            self.registerFileType(
                {'.stl': 'Stereo Lithography'}, vtk.vtkSTLReader)
        except:
            logging.error("Unable to find vtkSTLReader")
        try:
            self.registerFileType({'.bin': 'PLOT3D'}, vtk.vtkPLOT3DReader)
        except:
            logging.error("Unable to find vtkPLOT3DReader")
        try:
            self.registerFileType({'.ply': 'PLY'}, vtk.vtkPLYReader)
        except:
            logging.error("Unable to find vtkPLYReader")
        try:
            self.registerFileType(
                {'.vtp': 'VTK XML'}, vtk.vtkXMLPolyDataReader)
        except:
            logging.error("Unable to find vtkXMLPolyDataReader")
        try:
            self.registerFileType({'.g': 'BYU'}, vtk.vtkBYUReader)
        except:
            logging.error("Unable to find vtkBYUReader")
        try:
            self.registerFileType(
                {'.vrt': 'proSTAR', '.cel': 'proSTAR'}, vtk.vtkProStarReader)
        except:
            logging.error("Unable to find vtkProStarReader")
        try:
            self.registerFileType({'.pdb': 'PDB'}, vtk.vtkPDBReader)
        except:
            logging.error("Unable to find vtkPDBReader")

    def registerFileType(self, extensions, classname):
        """
        extension is a dictionary similar to PIL.Image.EXTENSION dictionary
        """

        # keep track of all reader classes
        self._all_readers.append(classname)
        
        # iterate over all extensions
        for e in extensions:
            e_lower = e.lower()
            if e_lower not in self._extension_map:
                self._extension_map[e_lower] = []

            self._extension_map[e_lower].append(
                (extensions[e] + ' file', classname))

    def SetExtension(self, ext):
        ext = os.path.basename(ext).lower()
        if not ext in self._extension_map:
            raise AttributeError(
                'Unknown file extension.  Please re-enter filename\nwith an explicit extension.')
        # Create an object
        if self._reader is not None:
            self._reader = None
        self._reader = self._extension_map[ext][0][1]()
        return self._reader

    def SetFileName(self, filename):

        # first, iterate through all readers that have a 'CanReadFile' method
        self._reader = None

        for c in self._all_readers:
            if hasattr(c, 'CanReadFile'):
                # reader has a CanReadFile() method - let's use it
                reader = c()
                try:
                    if reader.CanReadFile(filename):
                        self._reader = reader
                        break
                except UnicodeEncodeError:
                    if reader.CanReadFile(filename.encode(sys.getfilesystemencoding() or 'UTF-8')):
                        self._reader = reader
                        break

        # fall back to extension-based method
        if self._reader is None:
            temp = os.path.basename(filename).lower()
            extension = os.path.splitext(temp)[-1]
            self.SetExtension(extension)

        # And call it's SetFileName() method
        try:
            ret = self._reader.SetFileName(filename)
        except UnicodeEncodeError:
            ret = self._reader.SetFileName(
                filename.encode(sys.getfilesystemencoding() or 'UTF-8'))
        return ret

    def __getattr__(self, attr):
        return getattr(self._reader, attr)

    def GetOutput(self):
        """Get the polydata object"""
        return self._reader.GetOutput()

    def GetExtensions(self):
        return self._extension_map.keys()

    def GetMatchingFormatStrings(self):
        formats = collections.OrderedDict()
        keys = self._extension_map.keys()
        keys.sort()
        for extension in keys:
            for entry in self._extension_map[extension]:
                description, classname = entry

                if extension.startswith('.'):
                    val = '*' + extension
                else:
                    val = extension

                if description not in formats:
                    formats[description] = []
                formats[description].append(val)

        return formats
