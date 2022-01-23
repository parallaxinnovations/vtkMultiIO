import sys
from builtins import str

def GetVTKCompatibleFilename(filename):

    # a work-around to accommodate for both Window's lack of utf-8 support and
    # VTK's lack of Unicode support
    if sys.platform == 'win32':

        # convert filename to short path variant
        import win32api
        try:
            filename = win32api.GetShortPathName(str(filename))
        except:
            pass

    # convert filename to given locale
    #if isinstance(filename, str):
    #    filename = filename.encode(sys.getfilesystemencoding() or 'UTF-8')

    return filename