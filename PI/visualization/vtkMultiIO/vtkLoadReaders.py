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
Loads as many different readers as is possible.
"""

import os
import logging
import vtk
import vtkImageReaderBase
import vtkMultiImageReader
import vtkMultiPolyDataReader
from PI.visualization.common import PluginHelper

# These next packages are needed to build standalone codebase
import xml.etree.ElementTree
try:
    import vtkgdcm
except:
    logging.warning("unable to import vtkgdcm!")
from vtk.util import vtkImageImportFromArray

from PI.egg.pkg_resources import iter_entry_points, working_set, Environment

_plugin_cache = None


def LoadImageReaders(reader=None, directories=['.'], cache=True):

    if reader is None:
        reader = vtkMultiImageReader.vtkMultiImageReader()

    # Make directory entries absolute
    for i in range(len(directories)):
        directories[i] = os.path.abspath(directories[i])

    PluginHelper.SetupPlugins(directories, cache=cache)

    for module in iter_entry_points(group='PI.vtk.ImageReader', name=None):

        try:

            # Load module
            _class = module.load()

            if vtkImageReaderBase.WHOLE_FILENAME & _class.__capabilities__:
                reader.registerWholeFileName(
                    _class.__extensions__, _class, _class.__capabilities__)
            else:
                reader.registerFileType(
                    _class.__extensions__, _class, _class.__magic__, _class.__capabilities__)

        except:
            logging.exception("vtkLoadReaders")

    return reader, reader.GetMatchingFormatStrings()


def LoadGeometryReaders(reader=None, directories=['.'], cache=True):

    if reader is None:
        reader = vtkMultiPolyDataReader.vtkMultiPolyDataReader()

    # Make directory entries absolute
    for i in range(len(directories)):
        directories[i] = os.path.abspath(directories[i])

    PluginHelper.SetupPlugins(directories)

    for module in iter_entry_points(group='PI.vtk.PolyDataReader', name=None):

        # Load module
        _class = module.load()

        reader.registerFileType(_class.__extensions__, _class)

    return reader, reader.GetMatchingFormatStrings()


def GetImageReaderByClassName(classname, directories=['.']):
    """
    Get an instance of a specific reader, specified by classname
    """

    global _plugin_cache

    # Make directory entries absolute
    for i in range(len(directories)):
        directories[i] = os.path.abspath(directories[i])

    if _plugin_cache:
        distributions, errors = _plugin_cache
    else:
        distributions, errors = _plugin_cache = working_set.find_plugins(
            Environment(directories))

    for dist in distributions:
        working_set.add(dist)

    for module in iter_entry_points(group='PI.vtk.ImageReader'):

        if module.module_name.endswith(classname):
            # Load module
            _class = module.load()
            return _class()

    logging.error(
        "Unable to find plugin that contains a '%s' reader!!" % classname)
