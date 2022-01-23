# =========================================================================
#
# Copyright (c) 2000-2002 Enhanced Vision Systems
# Copyright (c) 2002-2008 GE Healthcare
# Copyright (c) 2011-2022 Parallax Innovations Inc.
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

Use vtkMultiPolyDataWriter() as you would vtkPolyDataWriter().  Notable differences
include the method registerFileType.  In order to extend this class from the
default class, call registerFileType(extension, classname).
"""

from builtins import object
import collections
import os
import sys
import logging
import vtk


class vtkMultiPolyDataWriter(object):

    def __init__(self):
        self._extension_map = {}
        self._scalars_name = 'scalars'
        self._writer = vtk.vtkPolyDataWriter()

        # register file types
        self.registerFileTypes()

    def registerFileTypes(self):
        # Add built in writers
        self.registerFileType({'.vtk': 'VTK PolyData'}, vtk.vtkPolyDataWriter)
        self.registerFileType({'.iv': 'OpenInventor'}, vtk.vtkIVWriter)
        self.registerFileType({
                              '.stl': 'Stereo Lithography'}, vtk.vtkSTLWriter)
        self.registerFileType({'.ply': 'Stanford PLY'}, vtk.vtkPLYWriter)
        self.registerFileType({
                              '.obj': 'MNI surface mesh'}, vtk.vtkMNIObjectWriter)
        self.registerFileType({'.vtp': 'VTK XML'}, vtk.vtkXMLPolyDataWriter)

    def registerFileType(self, extensions, classname):

        # iterate over all extensions
        for e in extensions:
            e_lower = e.lower()
            if e_lower not in self._extension_map:
                self._extension_map[e_lower] = []

            self._extension_map[e_lower].append(
                (extensions[e] + ' file', classname))

    def GetClassName(self):
        return "vtkMultiPolyDataWriter"

    def SetExtension(self, ext):
        ext = os.path.basename(ext).lower()
        if not ext in self._extension_map:
            raise AttributeError(
                'Unknown file extension. Please re-enter filename with an explicit extension.')
        # Create an object
        if self._writer is not None:
            self._writer = None

        # only consider the first writer that can handle this extension
        # TODO: we could extend this by passing a description of writer -- can wx filedialogs return the
        # extension we selected?
        _, classname = self._extension_map[ext][0]

        self._writer = classname()

    def SetFileName(self, filename):
        temp = os.path.basename(filename).lower()
        extension = os.path.splitext(temp)[-1]
        self.SetExtension(extension)
        # And call it's SetFileName() method
        try:
            ret = self._writer.SetFileName(filename)
        except UnicodeEncodeError:
            ret = self._writer.SetFileName(
                filename.encode(sys.getfilesystemencoding() or 'UTF-8'))
        return ret

    def __getattr__(self, attr):
        return getattr(self._writer, attr)

    def GetExtensions(self):
        return list(self._extension_map.keys())

    def GetScalarsName(self):
        if (hasattr(self._writer, 'GetScalarsName')):
            return self._writer.GetScalarsName()
        else:
            return self._scalars_name

    def SetScalarsName(self, name):
        if hasattr(self._writer, 'SetScalarsName'):
            self._writer.SetScalarsName(name)
        else:
            self._scalars_name = name

    def GetMatchingFormatStrings(self):

        formats = collections.OrderedDict()
        keys = list(self._extension_map.keys())
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
