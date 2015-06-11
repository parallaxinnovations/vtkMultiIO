import os

if os.name == 'posix':
    from libvtkMultiIOPython import *
else:
    from vtkMultiIOPython import *
