from zope import interface
from PI.visualization.common.interfaces import IProgress


##########################################################################

class IDimension(interface.Interface):

    """
    Interface that describes a dimension - this includes both common spatial dimensions (e.g.
    X, Y and Z axes) and other linear, measurable quantities (e.g. time, wavelength, temperature etc.)
    """

    name = interface.Attribute("""Name of dimension""")
    _unit = interface.Attribute("""Dimension unit""")


##########################################################################

class IDimensionInformation(interface.Interface):

    """
    Interface that provides mechanisms to manage information about a collection of dimensions for
    an image or image stack.  This includes a list of dimension names, dimension types
    and dimension units.  Example dimensions might be:

        - ("X axis", "Distance", "millimeters")
        - ("Y axis", "Wavelength", "nm")

    While an individual dimension must implement the IDimension interface, this interface represents
    the collection of dimensions that an image or image stack possesses.
    """

    def GetDimensionInformation():
        """
        Gets the list of dimension objects that describe the image's dimensions
        """

    def SetDimensionInformation(dims):
        """
        Sets the list of dimension objects that describe the image's dimensions
        """

##########################################################################


class IImageInformation(interface.Interface):

    """
    Interface that provides image information (e.g keyword pairs) for a given image.
    """

    def SetKeyword(key, value):
        """
        Set a given keyword to the provided value
        """

    def GetKeyword(key):
        """
        Get the value of a given keyword
        """

    def ClearHeader():
        """
        Remove all keyword values
        """

##########################################################################


class IvtkImageReader(IProgress, IDimensionInformation, IImageInformation):

    """
    Base interface representing a VTK image reader
    """

    def GetClassName():
        """
        Gets the classname of this image reader
        """

    def CanReadFile(filename, magic):
        """
        Determines whether a given file can be read by a given reader
        """

    def GetDescriptiveName():
        """
        Get a descriptive name for the file reader
        """

    def GetFileExtensions():
        """
        Get a list of extensions that this reader can read
        """

##########################################################################


class IvtkImageWriter(IProgress, IDimensionInformation, IImageInformation):

    """
    Base interface representing a VTK image writer
    """

    def GetDescriptiveName():
        """Returns a descriptive name for the file Writer"""

    def GetFileExtensions():
        """Returns file extensions for writer"""
