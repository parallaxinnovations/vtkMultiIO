# =========================================================================
#
# Copyright (c) 2000-2002 Enhanced Vision Systems
# Copyright (c) 2002-2008 GE Healthcare
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

import sys
import os
import shutil
from distutils.core import setup
from distutils.command.build_ext import build_ext as _build_ext
from distutils.core import Extension

#
# We need to kludge a cmake-build dynamic library into a python distutils build process.
# This is done by hooking into distutils directly
#


class build_ext(_build_ext):

    def __init__(self, dist):
        _build_ext.__init__(self, dist)
        if sys.platform == 'win32':
            self._extension = 'vtkMultiIOPython.pyd'
        else:
            self._extension = 'libvtkMultiIOPython.so'

    def find_binary(self):
        """
        search folder for the python extension
        """
        ret = ''
        for _dirpath, _dirnames, filenames in os.walk('.'):
            for file in filenames:
                if file.lower().endswith('.so') or file.lower().endswith('.dll') or file.lower().endswith('.pyd'):
                    ret = os.path.join(_dirpath, file)
                    break
        return ret

    def build_extensions(self):
        src = self.find_binary()
        dest = os.path.join(
            self.build_lib, 'PI', 'visualization', 'vtkMultiIO', self._extension)
        print "Copying cmake-built extension into build output directory (%s => %s)" % (src, dest)
        if os.path.abspath(src) != os.path.abspath(dest):
            shutil.copy(src, dest)

desc = """
Here's a set of python classes for Kitware's VTK software, to hide the
details of getting both 2D and 3D image data, and geometry data into and
out of your code.  The classes wrap a number of different file format
handlers into a single set of 'super' classes. The classes use a
late-binding approach which is activated in the reader/writer's
SetFileName() method.
"""


__init__py = """
try:
  __import__('pkg_resources').declare_namespace(__name__)
except:
  __path__ = __import__('pkgutil').extend_path(__path__, __name__)

PACKAGE_VERSION = "2.5.0"
PACKAGE_SHA1 = "NA"
"""
print >> open(os.path.join(os.path.dirname(sys.argv[
              0]), 'PI', 'visualization', 'vtkMultiIO', '__init__.py'), 'wt'), __init__py.strip()

setup(name='vtkMultiIO',
      version="2.5.0",
      description="VTK/Python Multiple format reader and writer classes",
      long_description=desc,
      author="Jeremy D. Gill",
      author_email="jgill@parallax-innovations.com",
      maintainer="Jeremy D. Gill",
      maintainer_email="jgill@parallax-innovations.com",
      url="http://www.parallax-innovations.com/microview",
      packages=['PI', 'PI.visualization', 'PI.visualization.vtkMultiIO'],
      # override some built commands
      cmdclass={'build_ext': build_ext},
      ext_modules=[Extension('libvtkMultiIOPython', [''])],
      license="MIT",
      )
