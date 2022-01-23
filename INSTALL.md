vtkMultiIO Installation Instructions:
-------------------------------------

Prerequisites:
--------------

  In order to install vtkMultiIO on your system, first make certain that
you have the proper prerequisites.  vtkMultiIO requires python 2.3 or higher, the
python Numeric package and VTK 4.4 with python wrappers.  In addition, for
full functionality, the Python imaging libraries and Scientific
libraries must be installed.  A list of web-sites for these products is
listed below:

  - http://www.python.org
  - http://numpy.sourceforge.net
  - http://www.pythonware.com/products/pil/index.htm
  - http://public.kitware.com/VTK
  

Configuration:
--------------

  vtkMultiIO makes use of Python's built-in distutils package.  In order 
to make/install the vtkMultiIO package, un-pack the source distribution,
change directories to the main vtkMultiIO directory.  Edit the first few
lines of the installer script 'setup.py' to suit your build environment.
In particular, make sure that 'VTK_BASE' points to your VTK base source
directory.  If you've installed VTK from a binary distro, point this at
something like '/usr/include/vtk' under unix/linux, or 'C:\\VTK' under 
windows.  

Installation:
-------------

Next, execute:

  python setup.py install
  
If all required components are installed correctly, the binary library 
vtkReaderLocalPython will be created (with a .so extension under unix; a
.pyd extension under Windows), and the python files installed.

A nice windows installer can be created by executing:

  python setup.py bdist_wininst

If you run into problems with the installer bailing out with an error message
telling you to increase your compiler heap/stack size, find the distutils
directory in your Python distribution (likely in c:\Python22\Lib\distutils)
and edit msvccompiler.py. Search for self.compile_options and self.compile_options_debug and add '/Zm200' to the list of compile options.  

  
while linux RPMs can be made by using:

  python setup.py bdist_rpm
  
Good luck!

Jeremy Gill <jgill@parallax-innovations.com>

